
import sys
from typing import Final
from PySide6.QtCore import QItemSelection, QObject, Signal
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QHeaderView, QTabWidget, QTableWidget, QTextEdit, QVBoxLayout, QWidget

from d2rloader.core.core import D2RLoaderState


class InfoTabsWidget(QTabWidget):
    """ The central widget of the application. Most of the addressbook's
        functionality is contained in this class.
    """
    def __init__(self, state: D2RLoaderState, parent: QWidget | None = None):
        """ Initialize the AddressWidget. """
        super().__init__(parent)
        self.dcinfo = DCInfoWidget(self)
        self.tzinfo = TZInfoWidget(self)
        self.application_output = ApplicationOutputWidget(self)
        self.addTab(self.dcinfo, "Diablo Clone")
        self.addTab(self.tzinfo, "Terror Zones")
        self.addTab(self.application_output, "Application Output")
        self.setFixedHeight(200)


class TZInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """ Initialize the AddressWidget. """
        super().__init__(parent)

        layout = QVBoxLayout()
        tzinfo = QTextEdit("Terrorized")
        tzinfo.setReadOnly(True)
        layout.addWidget(tzinfo)
        self.setLayout(layout)

class DCInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """ Initialize the AddressWidget. """
        super().__init__(parent)

        layout = QHBoxLayout()
        _columns: Final = [
            "Region",
            "Mode",
            "Ladder",
            "Non Ladder",
        ]
        table = QTableWidget()
        # table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setColumnCount(len(_columns))
        table.setHorizontalHeaderLabels(_columns)
        layout.addWidget(table)
        self.setLayout(layout)


class ApplicationOutputWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        """ Initialize the AddressWidget. """
        super().__init__(parent)

        layout = QVBoxLayout()
        out = QTextEdit("TEST CONTENT")
        out.setReadOnly(True)
        layout.addWidget(out)
        self.setLayout(layout)


class OutputWrapper(QObject):
    outputWritten = Signal(object, object)

    def __init__(self, parent: QObject, stdout=True):
        super().__init__(parent)
        if stdout:
            self._stream = sys.stdout
            sys.stdout = self
        else:
            self._stream = sys.stderr
            sys.stderr = self
        self._stdout = stdout

    def write(self, text):
        self._stream.write(text)
        self.outputWritten.emit(text, self._stdout)

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __del__(self):
        try:
            if self._stdout:
                sys.stdout = self._stream
            else:
                sys.stderr = self._stream
        except AttributeError:
            pass
