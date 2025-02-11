from typing import Final
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QTabWidget, QTableWidget, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager

from d2rloader.core.core import D2RLoaderState


class InfoTabsWidget(QTabWidget):
    def __init__(self, state: D2RLoaderState, parent: QWidget | None = None):
        """ Initialize the InfoTabsWidget. """
        super().__init__(parent)
        self.networkmanager = QNetworkAccessManager(self)
        self.dcinfo: DCInfoWidget = DCInfoWidget(self)
        self.tzinfo: TZInfoWidget = TZInfoWidget(self)
        self.application_output: ApplicationOutputWidget = ApplicationOutputWidget(self)
        self.addTab(self.dcinfo, "Diablo Clone")
        self.addTab(self.tzinfo, "Terror Zones")
        self.addTab(self.application_output, "Application Output")
        self.setFixedHeight(200)


class TZInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """ Initialize the TZInfoWidget. """
        super().__init__(parent)

        layout = QVBoxLayout()
        tzinfo = QTextEdit("Terrorized")
        tzinfo.setReadOnly(True)
        layout.addWidget(tzinfo)
        self.setLayout(layout)

class DCInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """ Initialize the DCInfoWidget. """
        super().__init__(parent)

        layout = QHBoxLayout()
        _columns: Final = [
            "Region",
            "Mode",
            "Ladder",
            "Non Ladder",
        ]
        table = QTableWidget()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setColumnCount(len(_columns))
        table.setHorizontalHeaderLabels(_columns)
        layout.addWidget(table)
        self.setLayout(layout)


class ApplicationOutputWidget(QWidget):
    output: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        """ Initialize the ApplicationOutputWidget. """
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
