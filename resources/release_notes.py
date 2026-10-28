"""Print the CHANGELOG.md section of one version, for use as GitHub release notes.

Defaults to the version in pyproject.toml.
"""

import argparse
import sys
import tomllib
from pathlib import Path

from generate_appdata_releases import DEFAULT_CHANGELOG, split_sections

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def project_version() -> str:
    with PYPROJECT.open("rb") as f:
        return str(tomllib.load(f)["project"]["version"])


def release_notes(changelog: str, version: str) -> str:
    for section_version, body in split_sections(changelog):
        if section_version == version:
            return "\n".join(body).strip() + "\n"
    sys.exit(f"error: no changelog section for version {version}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "version",
        nargs="?",
        default=project_version(),
        help="Version to print the notes for (default: %(default)s)",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=DEFAULT_CHANGELOG,
        help="Changelog to read (default: %(default)s)",
    )
    args = parser.parse_args()
    if not args.changelog.is_file():
        parser.error(f"file not found: {args.changelog}")

    changelog = args.changelog.read_text(encoding="utf-8")
    sys.stdout.write(release_notes(changelog, args.version))


if __name__ == "__main__":
    main()
