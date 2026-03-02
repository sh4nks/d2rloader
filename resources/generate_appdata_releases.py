import argparse
import os
import re
import sys
from datetime import datetime


# Helper to convert Markdown inline elements to AppStream-compliant HTML
def markdown_to_appstream_html(text: str) -> str:
    # Process double backticks first to prevent single backtick regex from partial matching
    text = re.sub(r"``([^`\n]+?)``", r"<code>\1</code>", text)
    # Handle single backticks
    text = re.sub(r"`([^`\n]+?)`", r"<code>\1</code>", text)
    # Handle bold
    text = re.sub(r"\*\*([^*]+?)\*\*", r"\1", text)
    # Handle links
    text = re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", r"\1", text)
    return text


def parse_changelog(changelog_path: str) -> list[dict]:
    """
    Parses the CHANGELOG.md file and extracts release information.
    """
    releases = []
    version_header_pattern = re.compile(r"##(?: Version)?\s*(\d+\.\d+\.\d+)")
    release_date_pattern = re.compile(
        r"Released\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,\s*(\d{4})"
    )

    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }

    with open(changelog_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        version_match = version_header_pattern.match(line)

        if not version_match:
            i += 1
            continue

        version = version_match.group(1)

        # Find the end of the current release block
        next_header_idx = len(lines)
        for k in range(i + 1, len(lines)):
            if version_header_pattern.match(lines[k]):
                next_header_idx = k
                break

        # Extract content for this release block
        block_content_lines = lines[i + 1 : next_header_idx]

        is_unreleased = False
        actual_release_date = None
        description_lines_to_format = []

        # First pass over the block to find metadata
        date_line_content = ""
        for block_line in block_content_lines:
            stripped_line = block_line.strip()
            if not stripped_line:
                continue

            if stripped_line.lower() == "unreleased":
                is_unreleased = True
                break

            date_match = release_date_pattern.match(stripped_line)
            if date_match:
                month_name, day, year = date_match.groups()
                actual_release_date = datetime(
                    int(year), month_map[month_name], int(day)
                ).strftime("%Y-%m-%d")
                date_line_content = (
                    stripped_line  # remember the date line to skip it later
                )
                break  # Found date, stop looking for it

        if is_unreleased:
            i = next_header_idx
            continue

        # Second pass to collect description lines
        for block_line in block_content_lines:
            stripped_line = block_line.strip()
            # Skip empty lines, the date line, and changelog links
            if (
                not stripped_line
                or stripped_line == date_line_content
                or stripped_line.startswith("**Full Changelog**")
            ):
                continue
            description_lines_to_format.append(block_line)

        if not actual_release_date:
            actual_release_date = datetime.now().strftime("%Y-%m-%d")

        # --- Formatting description for AppStream XML ---
        formatted_blocks = []
        current_paragraph_lines = []
        current_list_items_buffer = []
        current_block_type = None

        def _flush_paragraph_buffer():
            nonlocal current_paragraph_lines, formatted_blocks
            if current_paragraph_lines:
                text = markdown_to_appstream_html(
                    " ".join(current_paragraph_lines).strip()
                )
                if text:
                    formatted_blocks.append(f"<p>{text}</p>")
                current_paragraph_lines = []

        def _flush_list_buffer():
            nonlocal current_list_items_buffer, formatted_blocks
            if current_list_items_buffer:
                formatted_blocks.append("<ul>")
                for item_content in current_list_items_buffer:
                    item_html = markdown_to_appstream_html(item_content.strip())
                    formatted_blocks.append(f"  <li>{item_html}</li>")
                formatted_blocks.append("</ul>")
                current_list_items_buffer = []

        for raw_line in description_lines_to_format:
            stripped_line = raw_line.strip()

            if not stripped_line:
                if current_block_type == "paragraph":
                    _flush_paragraph_buffer()
                current_block_type = None  # Reset state on blank line
                continue

            if stripped_line.startswith("### "):
                _flush_paragraph_buffer()
                _flush_list_buffer()
                header_text = stripped_line[4:].strip()
                formatted_blocks.append(
                    f"<p>{markdown_to_appstream_html(header_text)}</p>"
                )
                current_block_type = "header"
            elif stripped_line.startswith("- "):
                if current_block_type != "list":
                    _flush_paragraph_buffer()
                    _flush_list_buffer()  # Should not be needed, but safe
                current_list_items_buffer.append(stripped_line[2:])
                current_block_type = "list"
            elif current_block_type == "list":
                # Line continuation for list item
                if current_list_items_buffer:
                    current_list_items_buffer[-1] += " " + stripped_line
            else:
                if current_block_type != "paragraph":
                    _flush_list_buffer()
                current_paragraph_lines.append(stripped_line)
                current_block_type = "paragraph"

        _flush_paragraph_buffer()
        _flush_list_buffer()

        description_text_formatted = "\n        ".join(formatted_blocks)

        if description_text_formatted.strip():
            releases.append(
                {
                    "version": version,
                    "date": actual_release_date,
                    "description": description_text_formatted,
                }
            )

        i = next_header_idx

    return releases


def generate_appdata_releases_xml(releases: list[dict]) -> str:
    """
    Generates the <releases> XML block for AppStream metadata.
    """
    if not releases:
        return "  <releases>\n  </releases>"

    xml_parts = ["  <releases>"]
    for release in releases:
        xml_parts.append(
            f'    <release version="{release["version"]}" date="{release["date"]}">'
        )
        xml_parts.append("      <description>")
        xml_parts.append(f"        {release['description']}")
        xml_parts.append("      </description>")
        xml_parts.append("    </release>")
    xml_parts.append("  </releases>")
    return "\n".join(xml_parts)


def update_appdata_file(appdata_file_path: str, new_releases_xml: str):
    """
    Replaces the <releases> section in an existing AppStream XML file
    using text-based search and replace.
    """
    try:
        with open(appdata_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Regex to find the entire <releases>...</releases> block, including its surrounding whitespace.
        releases_block_pattern = re.compile(
            r"^\s*<releases>.*?</releases>\s*$", re.DOTALL | re.MULTILINE
        )

        # Check if the pattern is found in the content
        if releases_block_pattern.search(content):
            # Replace the found block with the new XML content.
            # The new_releases_xml already contains the correct indentation.
            modified_content = releases_block_pattern.sub(
                new_releases_xml, content, count=1
            )

            with open(appdata_file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            print(f"Successfully updated <releases> section in {appdata_file_path}")
        else:
            print(
                f"Warning: <releases> tag not found in {appdata_file_path}. File not modified.",
                file=sys.stderr,
            )

    except FileNotFoundError:
        print(f"Error: AppData file not found at {appdata_file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(
            f"An unexpected error occurred while updating the AppData file: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse CHANGELOG.md and generate AppStream <releases> XML."
    )
    parser.add_argument(
        "--output-file",
        help="Optional: Path to an existing .appdata.xml file to update. If not provided, XML is printed to stdout.",
    )
    args = parser.parse_args()

    changelog_file = os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md")

    if not os.path.exists(changelog_file):
        print(f"Error: CHANGELOG.md not found at {changelog_file}", file=sys.stderr)
        sys.exit(1)

    parsed_releases = parse_changelog(changelog_file)
    appdata_xml = generate_appdata_releases_xml(parsed_releases)

    if args.output_file:
        update_appdata_file(args.output_file, appdata_xml)
    else:
        print(appdata_xml)
