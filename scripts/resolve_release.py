from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from typing import Iterable


IMAGE_INPUT_PATHS = ("src", "Dockerfile", "pyproject.toml", "uv.lock")


@dataclass(frozen=True)
class ReleaseDecision:
    revision: int
    should_publish: bool

    def tag_for(self, marker_version: str) -> str:
        return f"v{marker_version}-r{self.revision}"


def release_revisions(tags: Iterable[str], marker_version: str) -> list[int]:
    pattern = re.compile(rf"^v{re.escape(marker_version)}-r([1-9][0-9]*)$")
    return [int(match.group(1)) for tag in tags if (match := pattern.fullmatch(tag))]


def decide_release(
    tags: Iterable[str], marker_version: str, image_inputs_changed: bool
) -> ReleaseDecision:
    revisions = release_revisions(tags, marker_version)
    if not revisions:
        return ReleaseDecision(revision=1, should_publish=True)

    latest_revision = max(revisions)
    if image_inputs_changed:
        return ReleaseDecision(revision=latest_revision + 1, should_publish=True)
    return ReleaseDecision(revision=latest_revision, should_publish=False)


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def image_inputs_changed(release_tag: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", f"{release_tag}..HEAD", "--", *IMAGE_INPUT_PATHS],
        check=False,
    )
    if result.returncode > 1:
        raise RuntimeError(f"could not compare image inputs with {release_tag}")
    return result.returncode == 1


def resolve(marker_version: str) -> ReleaseDecision:
    tags = git_output("tag", "--list", f"v{marker_version}-r*").splitlines()
    revisions = release_revisions(tags, marker_version)
    if not revisions:
        return decide_release(tags, marker_version, image_inputs_changed=False)

    latest_tag = f"v{marker_version}-r{max(revisions)}"
    return decide_release(tags, marker_version, image_inputs_changed(latest_tag))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("marker_version")
    args = parser.parse_args()

    decision = resolve(args.marker_version)
    print(f"release_revision={decision.revision}")
    print(f"release_tag={decision.tag_for(args.marker_version)}")
    print(f"should_publish={str(decision.should_publish).lower()}")


if __name__ == "__main__":
    main()
