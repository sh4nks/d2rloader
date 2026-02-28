import importlib.metadata
import json
import urllib.request

from loguru import logger

from d2rloader.constants import REPO_NAME, REPO_OWNER


def get_current_version() -> str:
    try:
        return importlib.metadata.version("d2rloader")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def parse_version_str(version_string: str) -> tuple[int, ...]:
    if version_string.startswith("v"):
        version_string = version_string[1:]
    # Compare versions as tuples of integers for accuracy (1.10 > 1.2)
    return tuple(map(int, version_string.split(".")))


def is_update_available():
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

    current_version_str = get_current_version()

    try:
        headers = {"User-Agent": "D2RLoader"}
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

            # Compare versions as tuples of integers for accuracy (e.g., 1.10 > 1.2)
            current_version = parse_version_str(current_version_str)
            latest_version = parse_version_str(data["tag_name"])

            return ".".join(map(str, latest_version)), latest_version > current_version

    except Exception as e:
        logger.error(f"Couldn't check for new updates {e}")
        return None, False
