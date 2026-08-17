from fastapi.testclient import TestClient

from app import app


def test_health_returns_ready_status() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_marker_rejects_empty_upload() -> None:
    response = TestClient(app).post(
        "/marker",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "uploaded file is empty"}


def test_marker_returns_markdown_and_rendered_payload(monkeypatch) -> None:
    import app as main

    monkeypatch.setattr(
        main,
        "convert_bytes",
        lambda content, suffix: {"markdown": "# Document", "blocks": [{"id": 1}]},
    )

    response = TestClient(app).post(
        "/marker",
        files={"file": ("document.pdf", b"pdf", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {"markdown": "# Document", "blocks": [{"id": 1}]}
