"""Generate the AppStream ``<releases>`` section from CHANGELOG.md.

Every ``## Version X.Y.Z`` section of the changelog becomes one ``<release>``.
Sections marked ``Unreleased`` are skipped, and a section without a
``Released <Month> <day>, <year>`` line is dated today.
"""

import argparse
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

VERSION_HEADER = re.compile(r"^## (?:Version )?(\d+\.\d+\.\d+)\s*$")
RELEASE_DATE = re.compile(
    rf"^Released ({'|'.join(MONTHS)}) (\d{{1,2}})(?:st|nd|rd|th)?, (\d{{4}})$"
)
INLINE_CODE = re.compile(r"(``|`)(.+?)\1")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
RELEASES_BLOCK = re.compile(
    r"^[ \t]*<releases>.*?</releases>", re.DOTALL | re.MULTILINE
)


@dataclass(frozen=True)
class Release:
    version: str
    date: str
    description: list[str]

    def to_xml(self) -> str:
        description = "\n        ".join(self.description)
        return (
            f'    <release version="{self.version}" date="{self.date}">\n'
            "      <description>\n"
            f"        {description}\n"
            "      </description>\n"
            "    </release>"
        )


def inline_html(markdown: str) -> str:
    """Convert inline Markdown to the HTML subset AppStream accepts."""
    text = escape(markdown.strip())
    text = INLINE_CODE.sub(r"<code>\2</code>", text)
    text = BOLD.sub(r"\1", text)
    return LINK.sub(r"\1", text)


def description_elements(lines: list[str]) -> list[str]:
    """Turn the Markdown body of a release into ``<p>`` and ``<ul>`` elements.

    AppStream has no heading element, so ``### Heading`` lines become paragraphs.
    """
    elements: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []

    def flush() -> None:
        if paragraph:
            elements.append(f"<p>{inline_html(' '.join(paragraph))}</p>")
            paragraph.clear()
        if items:
            elements.append("<ul>")
            elements.extend(f"  <li>{inline_html(item)}</li>" for item in items)
            elements.append("</ul>")
            items.clear()

    for line in map(str.strip, lines):
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            elements.append(f"<p>{inline_html(line[4:])}</p>")
        elif line.startswith("- "):
            if paragraph:
                flush()
            items.append(line[2:])
        elif items:
            items[-1] += f" {line}"
        else:
            paragraph.append(line)
    flush()
    return elements


def split_sections(changelog: str) -> Iterator[tuple[str, list[str]]]:
    """Yield ``(version, body_lines)`` for every version section of the changelog."""
    version: str | None = None
    body: list[str] = []
    for line in changelog.splitlines():
        if match := VERSION_HEADER.match(line):
            if version:
                yield version, body
            version, body = match[1], []
        elif version:
            body.append(line)
    if version:
        yield version, body


def parse_release(version: str, body: list[str]) -> Release | None:
    """Build a release from its changelog section, or ``None`` if it is unreleased."""
    released = date.today().isoformat()
    description_lines: list[str] = []
    for line in map(str.strip, body):
        if line.lower() == "unreleased":
            return None
        if match := RELEASE_DATE.match(line):
            month, day, year = match.groups()
            released = date(int(year), MONTHS.index(month) + 1, int(day)).isoformat()
        elif not line.startswith("**Full Changelog**"):
            description_lines.append(line)
    elements = description_elements(description_lines)
    return Release(version, released, elements) if elements else None


def parse_changelog(changelog: str) -> list[Release]:
    return [
        release
        for version, body in split_sections(changelog)
        if (release := parse_release(version, body))
    ]


def releases_xml(releases: list[Release]) -> str:
    return "\n".join(
        ["  <releases>", *(release.to_xml() for release in releases), "  </releases>"]
    )


def update_appdata(appdata_path: Path, releases: str) -> None:
    content = appdata_path.read_text(encoding="utf-8")
    updated, replaced = RELEASES_BLOCK.subn(lambda _: releases, content, count=1)
    if not replaced:
        sys.exit(f"error: no <releases> section found in {appdata_path}")
    appdata_path.write_text(updated, encoding="utf-8")
    print(f"Updated <releases> section in {appdata_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--changelog",
        type=Path,
        default=DEFAULT_CHANGELOG,
        help="Changelog to read (default: %(default)s)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="AppStream XML file whose <releases> section is replaced. "
        "Prints the XML to stdout when omitted.",
    )
    args = parser.parse_args()

    for path in filter(None, (args.changelog, args.output_file)):
        if not path.is_file():
            parser.error(f"file not found: {path}")

    releases = releases_xml(parse_changelog(args.changelog.read_text(encoding="utf-8")))
    if args.output_file:
        update_appdata(args.output_file, releases)
    else:
        print(releases)


if __name__ == "__main__":
    main()
