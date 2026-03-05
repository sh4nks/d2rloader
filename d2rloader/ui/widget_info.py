import enum
import functools
import json
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
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from d2rloader.constants import DIABLO_LEVELS
from d2rloader.core.state import D2RLoaderState

URI_TZ_INFO = "https://d2emu.com/api/v1/tz"
URI_DC_INFO = "https://d2emu.com/api/v1/dclone"
URI_D2RINFO = "https://d2.someblocks.com/api/d2rinfo"

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
    "cnLadder": {"status": 8, "updated_at": 1739385783},
    "cnLadderHardcore": {"status": 8, "updated_at": 1739326809},
    "cnNonLadder": {"status": 9, "updated_at": 1739366084},
    "cnNonLadderHardcore": {"status": 9, "updated_at": 1739326809},
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
    ALL = enum.auto()


class InfoTabsWidget(QTabWidget):
    refresh: Signal = Signal()

    def __init__(self, d2rloader: D2RLoaderState, parent: QWidget | None = None):
        """Initialize the InfoTabsWidget."""
        super().__init__(parent)
        self.d2rloader: D2RLoaderState = d2rloader
        self.networkmanager: QNetworkAccessManager = (
            d2rloader.network_manager or QNetworkAccessManager(self)
        )
        self.dcinfo: DCInfoWidget = DCInfoWidget(self, d2rloader)
        self.tzinfo: TZInfoWidget = TZInfoWidget(self)
        self.application_output: ApplicationOutputWidget = ApplicationOutputWidget(self)
        # self.refresh.connect(lambda: asyncio.ensure_future(self._update_info()))
        self.addTab(self.dcinfo, "Diablo Clone")
        self.addTab(self.tzinfo, "Terror Zones")
        self.addTab(self.application_output, "Application Log")

        refresh_button = QToolButton()
        refresh_button.setText("Refresh TZ/DC Info")
        refresh_button.clicked.connect(self.update_info)
        self.setCornerWidget(refresh_button, Qt.Corner.TopRightCorner)

        self.d2rloader.plugins.hook.d2rloader_info_tabbar(
            d2rloader=d2rloader, tabbar=self
        )

        self.setFixedHeight(250)

    @Slot()
    def update_info(self):
        # self.tzinfo.process(TEST_DATA_TZINFO)
        # self.dcinfo.process(TEST_DATA_DCLONE)
        logger.info("Refreshing TZ/DC Info...")
        if self.d2rloader.settings.data.d2rinfo:
            self.send_request(URI_D2RINFO, RequestType.ALL)
        else:
            self.send_request(URI_TZ_INFO, RequestType.TZ)
            self.send_request(URI_DC_INFO, RequestType.DC)

    def send_request(self, url: str, type: RequestType):
        request = QNetworkRequest(url)
        if type == RequestType.ALL:
            request.setHeader(
                QNetworkRequest.KnownHeaders.UserAgentHeader,
                "D2RLoader",
            )
        else:
            request.setHeader(
                QNetworkRequest.KnownHeaders.UserAgentHeader,
                "D2RLoader (https://github.com/sh4nks/d2rloader)",
            )
            request.setRawHeader(
                b"x-emu-username",
                f"{self.d2rloader.settings.data.token_username}".encode("utf-8"),
            )
            request.setRawHeader(
                b"x-emu-token", f"{self.d2rloader.settings.data.token}".encode("utf-8")
            )
        reply = self.networkmanager.get(request)
        reply.finished.connect(functools.partial(self.on_finished, reply, type))
        reply.errorOccurred.connect(self.on_error)

    @Slot(QNetworkReply, RequestType)
    def on_finished(self, reply: QNetworkReply, type: RequestType):
        response = reply.readAll()

        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status != 200:
            logger.error(f"DC/TZ Info server returned '{status}' - {response}")
            reply.deleteLater()
            return

        json_response = json.loads(response.data())  # pyright: ignore
        logger.trace(f"Requested Data: {type} -> {json_response}")

        if type == RequestType.TZ:
            self.tzinfo.process(json_response)
        elif type == RequestType.DC:
            self.dcinfo.process(json_response)
        elif type == RequestType.ALL:
            self.tzinfo.process(json_response["tz"])
            self.dcinfo.process(json_response["dclone"])

        reply.deleteLater()

    @Slot(QNetworkReply.NetworkError)
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
    region_mapping: dict[str, str] = {
        "eu": "Europe",
        "us": "America",
        "kr": "Asia",
        "cn": "China",
    }

    # there is sure as hell a better way to do this
    row_data: dict[str, dict[str, int | str]] = {
        "euSoftcore": {"index": 0, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "euHardcore": {"index": 1, "mode": "Harcore", "ladder": 0, "nonLadder": 0},
        "usSoftcore": {"index": 2, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "usHardcore": {"index": 3, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
        "krSoftcore": {"index": 4, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "krHardcore": {"index": 5, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
        "cnSoftcore": {"index": 6, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "cnHardcore": {"index": 7, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
        # Rotw
        "euSoftcoreRotw": {"index": 0, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "euHardcoreRotw": {"index": 1, "mode": "Harcore", "ladder": 0, "nonLadder": 0},
        "usSoftcoreRotw": {"index": 2, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "usHardcoreRotw": {"index": 3, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
        "krSoftcoreRotw": {"index": 4, "mode": "Softcore", "ladder": 0, "nonLadder": 0},
        "krHardcoreRotw": {"index": 5, "mode": "Hardcore", "ladder": 0, "nonLadder": 0},
    }

    def __init__(self, parent: QWidget, d2rloader: D2RLoaderState):
        """Initialize the DCInfoWidget."""
        super().__init__(parent)
        self.d2rloader: D2RLoaderState = d2rloader

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

        self.hbox_layout: QHBoxLayout = QHBoxLayout()
        self.courtesy_label: QLabel = QLabel(
            "DClone Info provided by <a href='https://d2emu.com/dclone'>d2emu.com</a>"
        )
        self.rotw_checkbox: QCheckBox = QCheckBox("Return of the Warlock")
        self.rotw_checkbox.setChecked(self.d2rloader.settings.data.rotw or False)
        self.rotw_checkbox.checkStateChanged.connect(self.rotw_toggle)

        self.hbox_layout.addWidget(self.courtesy_label, 1)
        self.hbox_layout.addWidget(self.rotw_checkbox)

        layout.addWidget(self.table)
        layout.addLayout(self.hbox_layout)
        self.setLayout(layout)

    @Slot()
    def rotw_toggle(self, checked: Qt.CheckState):
        if checked == Qt.CheckState.Checked:
            self.d2rloader.settings.set(rotw=True)
        else:
            self.d2rloader.settings.set(rotw=False)

        self._create_rows(self.d2rloader.settings.data.rotw)

    def process(self, info: DCloneInfo):
        self._fill_row_data(info)
        self._create_rows(self.d2rloader.settings.data.rotw)

    def _fill_row_data(self, info: DCloneInfo):
        for key, value in info.items():
            self._process_item(key, value)

    def _create_rows(self, rotw: bool | None = None):
        self.table.setRowCount(0)
        for key, value in self.row_data.items():
            if not rotw and "Rotw" in key or rotw and "Rotw" not in key:
                continue
            self.create_row(key[:2], value)

    def _process_item(self, key: str, value: dict[str, int]):
        region = key[:2]

        if region not in self.region_mapping.keys():
            logger.debug(f"Region not supported {key}")
            return

        mode = "Hardcore" if "Hardcore" in key else "Softcore"
        addon = "Rotw" if "Rotw" in key else ""

        # Determine the ladder type
        key_r = key[2:]
        if key_r.startswith("Ladder"):
            ladder_type = "ladder"
        elif key_r.startswith("Non"):
            ladder_type = "nonLadder"
        else:
            logger.error(f"Unknown DClone Info key format: {key}")
            return

        row_key = region + mode + addon
        self.row_data[row_key][ladder_type] = value.get("status", 0)

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
