import functools
import importlib.metadata
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger
from PySide6.QtCore import Slot
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QMessageBox

from d2rloader.constants import REPO_NAME, REPO_OWNER
from d2rloader.core.state import D2RLoaderState


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


def compare_versions(current_version_str: str, latest_version_str: str):
    # Compare versions as tuples of integers for accuracy (e.g., 1.10 > 1.2)
    current_version = parse_version_str(current_version_str)
    latest_version = parse_version_str(latest_version_str)

    return ".".join(map(str, latest_version)), latest_version > current_version


class UpdateChecker:
    def __init__(self, d2rloader: D2RLoaderState):
        self.d2rloader: D2RLoaderState = d2rloader

    def check_update(self):
        if (
            not self.d2rloader.settings.data.check_update
            or self.d2rloader.network_manager is None
        ):
            return

        api_url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        )
        request = QNetworkRequest(api_url)
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "D2RLoader")
        reply = self.d2rloader.network_manager.get(request)
        reply.finished.connect(functools.partial(self.on_finished, reply))
        reply.errorOccurred.connect(self.on_error)

    def process_response(self, reply: dict[Any, Any]):
        interval = timedelta(minutes=15)  # check every 15mins
        now = datetime.now(UTC)
        if self.d2rloader.settings.data.last_update_check is None:
            next_check = now
        else:
            next_check = self.d2rloader.settings.data.last_update_check + interval

        if next_check > now:
            return

        logger.info("Checking for updates...")
        self.d2rloader.settings.set(last_update_check=now)
        version, has_update = compare_versions(
            get_current_version(), reply.get("tagName", "v0.0.0")
        )

        if has_update and version:
            new_version_url = f"{REPO_NAME}/releases/tag/v{version}"
            current_version = importlib.metadata.version("d2rloader")
            logger.info("Update available!")
            logger.info(f"Found new version {version}: {new_version_url}")
            QMessageBox.information(
                None,
                "New Update Available!",
                (
                    f"<p><center>Version {version} (current: {current_version}) is now available!</center><p>"
                    f"<p><center><a href='{new_version_url}'>{new_version_url}</a></center></p>"
                ),
                QMessageBox.StandardButton.Ok,
            )

        else:
            logger.info("No updates available!")

    @Slot(QNetworkReply)
    def on_finished(self, reply: QNetworkReply):
        response = reply.readAll()

        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status != 200:
            logger.error(f"Update server returned '{status}' - {response}")
            reply.deleteLater()
            return

        json_response = json.loads(response.data())  # pyright: ignore
        logger.trace(f"Requested Data: {type} -> {json_response}")
        self.process_response(json_response)
        reply.deleteLater()

    @Slot(QNetworkReply.NetworkError)
    def on_error(self, code: QNetworkReply.NetworkError):
        """Show a message if an error happen"""
        logger.error(f"Couldn't fetch data from API: {code}")
