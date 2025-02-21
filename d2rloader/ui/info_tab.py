import enum
import functools
import json
import logging
from typing import Final

from loguru import logger
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase, Qt
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from d2rloader.constants import DIABLO_LEVELS
from d2rloader.core.core import D2RLoaderState

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)

URI_TZ_INFO = "https://d2emu.com/api/v1/tz"
URI_DC_INFO = "https://d2emu.com/api/v1/dclone"


type DCloneInfo = dict[str, dict[str, int]]
type TZInfo = dict[str, list[str] | list[int] | int]

TEST_DATA_DCLONE: DCloneInfo = {
    "euLadder": {"status": 4, "updated_at": 1739381087},
    "euLadderHardcore": {"status": 4, "updated_at": 1739326785},
    "euNonLadder": {"status": 5, "updated_at": 1739326785},
    "euNonLadderHardcore": {"status": 5, "updated_at": 1739326785},
    "krLadder": {"status": 6, "updated_at": 1739380350},
    "krLadderHardcore": {"status": 6, "updated_at": 1739326760},
    "krNonLadder": {"status": 7, "updated_at": 1739375164},
    "krNonLadderHardcore": {"status": 7, "updated_at": 1739326760},
    "usLadder": {"status": 8, "updated_at": 1739385783},
    "usLadderHardcore": {"status": 8, "updated_at": 1739326809},
    "usNonLadder": {"status": 9, "updated_at": 1739366084},
    "usNonLadderHardcore": {"status": 9, "updated_at": 1739326809},
}
TEST_DATA_TZINFO: TZInfo = {
    "current": ["33", "34", "35", "36", "37"],
    "current_immunities": ["ph", "f", "c", "l"],
    "current_num_boss_packs": [27, 35],
    "current_superuniques": ["Bone Ash", "Andariel"],
    "delay": 600,
    "next": ["20", "21", "22", "23", "24", "25"],
    "next_available_time_utc": 1739390999,
    "next_immunities": ["ph", "f", "c", "l"],
    "next_num_boss_packs": [15, 20],
    "next_superuniques": ["The Countess"],
    "next_terror_time_utc": 1739394000,
}


class RequestType(enum.Enum):
    TZ = enum.auto()
    DC = enum.auto()


class InfoTabsWidget(QTabWidget):
    refresh: Signal = Signal()

    def __init__(self, state: D2RLoaderState, parent: QWidget | None = None):
        """Initialize the InfoTabsWidget."""
        super().__init__(parent)
        self.state: D2RLoaderState = state
        self.networkmanager: QNetworkAccessManager = QNetworkAccessManager(self)
        self.dcinfo: DCInfoWidget = DCInfoWidget(self)
        self.tzinfo: TZInfoWidget = TZInfoWidget(self)
        self.application_output: ApplicationOutputWidget = ApplicationOutputWidget(self)
        # self.refresh.connect(lambda: asyncio.ensure_future(self._update_info()))
        self.addTab(self.dcinfo, "Diablo Clone")
        self.addTab(self.tzinfo, "Terror Zones")
        self.addTab(self.application_output, "Application Log")
        self.setFixedHeight(250)

    def update_info(self):
        # self.tzinfo.process(TEST_DATA_TZINFO)
        # self.dcinfo.process(TEST_DATA_DCLONE)
        self.send_request(URI_TZ_INFO, RequestType.TZ)
        self.send_request(URI_DC_INFO, RequestType.DC)

    def send_request(self, url: str, type: RequestType):
        request = QNetworkRequest(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            "D2RLoader (https://github.com/sh4nks/d2rloader)",
        )
        request.setRawHeader(
            b"x-emu-username",
            f"{self.state.settings.data.token_username}".encode("utf-8"),
        )
        request.setRawHeader(
            b"x-emu-token", f"{self.state.settings.data.token}".encode("utf-8")
        )
        reply = self.networkmanager.get(request)
        reply.finished.connect(functools.partial(self.on_finished, reply, type))
        reply.errorOccurred.connect(self.on_error)

    @Slot(QNetworkReply, RequestType)  # pyright: ignore
    def on_finished(self, reply: QNetworkReply, type: RequestType):
        response = reply.readAll()
        json_response = json.loads(response.data())  # pyright: ignore
        logger.trace(f"Requested Data: {type} -> {json_response}")

        if type == RequestType.TZ:
            self.tzinfo.process(json_response)
        elif type == RequestType.DC:
            self.dcinfo.process(json_response)

        reply.deleteLater()

    @Slot(QNetworkReply.NetworkError)  # pyright: ignore
    def on_error(self, code: QNetworkReply.NetworkError):
        """Show a message if an error happen"""
        logger.error(f"Couldn't fetch data from API: {code}")


class TZInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """Initialize the TZInfoWidget."""
        super().__init__(parent)

        layout = QVBoxLayout()
        self.out: QTextEdit = QTextEdit(
            "No TZ Info fetched yet. Press 'Refresh' to fetch TZ Info."
        )
        self.out.setReadOnly(True)
        layout.addWidget(self.out)
        layout.addWidget(
            QLabel("TZ Info provided by <a href='https://d2emu.com/tz'>d2emu.com</a>")
        )
        self.setLayout(layout)

    def process(self, info: TZInfo):
        current_tz = info.get("current", None)
        next_tz = info.get("next", None)

        curr_tz_list: list[str] = []
        if current_tz is not None and isinstance(current_tz, list):
            for tz in current_tz:
                curr_tz_list.append(DIABLO_LEVELS[str(tz)])

        next_tz_list: list[str] = []
        if next_tz is not None and isinstance(next_tz, list):
            for tz in next_tz:
                next_tz_list.append(DIABLO_LEVELS[str(tz)])

        # make this prettier
        tz_info_text = f"""<div style="font-size: 14px">
            <p>
            Current Terror Zones: <span style="font-weight: bold">{", ".join(curr_tz_list)}</span>
            </p>

            <p>
            Next Terror Zones: <span style="font-weight: bold">{", ".join(next_tz_list)}</span>
            </p>
            </div>
        """
        self.out.setHtml(tz_info_text)


class DCInfoWidget(QWidget):
    region_mapping: dict[str, str] = {"eu": "Europe", "us": "America", "kr": "Asia"}

    # there is sure as hell a better way to do this
    row_data: dict[str, dict[str, int | str]] = {
        "euSoftcore": {"index": 0, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "euHardcore": {"index": 1, "mode": "Harcore", "ladder": 0, "nonLadder": 0},
        "usSoftcore": {"index": 2, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "usHardcore": {"index": 3, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
        "krSoftcore": {"index": 4, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "krHardcore": {"index": 5, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
    }

    def __init__(self, parent: QWidget | None = None):
        """Initialize the DCInfoWidget."""
        super().__init__(parent)

        layout = QVBoxLayout()
        _columns: Final = [
            "Region",
            "Mode",
            "Ladder",
            "Non Ladder",
        ]
        self.table: QTableWidget = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setColumnCount(len(_columns))
        self.table.setHorizontalHeaderLabels(_columns)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        layout.addWidget(
            QLabel(
                "DClone Info provided by <a href='https://d2emu.com/dclone'>d2emu.com</a>"
            )
        )
        self.setLayout(layout)

    def process(self, info: DCloneInfo):
        for key, value in info.items():
            self._process_item(key, value)

        for key, value in self.row_data.items():
            self.create_row(key[:2], value)

    def _process_item(self, key: str, value: dict[str, int]):
        region = key[:2]
        key_r = key[2:]
        if key_r.startswith("Non") and key.endswith("Hardcore"):
            self.row_data[region + "Hardcore"]["nonLadder"] = value.get("status", 0)
        elif key_r.startswith("Non"):
            self.row_data[region + "Softcore"]["nonLadder"] = value.get("status", 0)
        elif key_r.startswith("Ladder") and key.endswith("Hardcore"):
            self.row_data[region + "Hardcore"]["ladder"] = value.get("status", 0)
        elif key_r.startswith("Ladder"):
            self.row_data[region + "Softcore"]["ladder"] = value.get("status", 0)
        else:
            logger.error(f"Unknown DClone Info key {key}")

    def create_row(self, region: str, item: dict[str, int | str]):
        row_index = int(item["index"])

        region_item = QTableWidgetItem(f"{self.region_mapping[region]}")
        region_item.setFlags(region_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        mode_item = QTableWidgetItem(f"{item['mode']}")
        mode_item.setFlags(mode_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        ladder_item = QTableWidgetItem(f"{item['ladder']}")
        ladder_item.setFlags(ladder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        non_ladder_item = QTableWidgetItem(f"{item['nonLadder']}")
        non_ladder_item.setFlags(non_ladder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        non_ladder_item = QTableWidgetItem(f"{item['nonLadder']}")
        non_ladder_item.setFlags(non_ladder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.table.removeRow(row_index)
        self.table.insertRow(row_index)

        self.table.setItem(row_index, 0, region_item)
        self.table.setItem(row_index, 1, mode_item)
        self.table.setItem(row_index, 2, ladder_item)
        self.table.setItem(row_index, 3, non_ladder_item)


class ApplicationOutputWidget(QWidget):
    output: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        """Initialize the ApplicationOutputWidget."""
        super().__init__(parent)

        layout = QVBoxLayout()
        self.out: QTextEdit = QTextEdit()
        self.out.setReadOnly(True)
        fixedFont: QFont = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.out.setFont(fixedFont)
        self.output.connect(self._update)
        layout.addWidget(self.out)
        self.setLayout(layout)

    def _update(self, msg: str):
        self.out.append(msg.strip("\n").strip("\t").strip("\r"))
        # self.out.append(f"<span style='color: red'>{msg.strip("\n").strip("\t").strip("\r")}</span>")
