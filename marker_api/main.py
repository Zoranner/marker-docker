import logging
import tempfile
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool


app = FastAPI(title="marker-service")
logger = logging.getLogger(__name__)

_converter_lock = threading.Lock()
_artifact_dict: dict[str, Any] | None = None
_markdown_converter: Any | None = None
_json_converter: Any | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/marker")
async def marker(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    suffix = Path(file.filename or "upload").suffix
    try:
        return await run_in_threadpool(convert_bytes, content, suffix)
    except Exception as error:
        logger.exception("marker conversion failed")
        raise HTTPException(status_code=500, detail="marker conversion failed") from error


def convert_bytes(content: bytes, suffix: str) -> dict[str, Any]:
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.output import text_from_rendered

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        with _converter_lock:
            markdown_rendered = get_markdown_converter(PdfConverter)(str(temp_path))
            json_rendered = get_json_converter(ConfigParser, PdfConverter)(str(temp_path))
        markdown, _, _ = text_from_rendered(markdown_rendered)
        payload = to_jsonable(json_rendered)
        if not isinstance(payload, dict):
            payload = {"rendered": payload}
        payload["markdown"] = markdown
        return payload
    finally:
        temp_path.unlink(missing_ok=True)


def get_markdown_converter(pdf_converter: Any) -> Any:
    global _markdown_converter
    if _markdown_converter is None:
        _markdown_converter = pdf_converter(artifact_dict=get_artifact_dict())
    return _markdown_converter


def get_json_converter(config_parser_type: Any, pdf_converter: Any) -> Any:
    global _json_converter
    if _json_converter is None:
        config_parser = config_parser_type({"output_format": "json"})
        _json_converter = pdf_converter(
            config=config_parser.generate_config_dict(),
            artifact_dict=get_artifact_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
    return _json_converter


def get_artifact_dict() -> dict[str, Any]:
    global _artifact_dict
    if _artifact_dict is None:
        from marker.models import create_model_dict

        _artifact_dict = create_model_dict()
    return _artifact_dict


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value
