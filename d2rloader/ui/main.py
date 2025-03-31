from __future__ import annotations

import importlib.metadata
import signal
import sys

from d2rloader.ui.utils import create_action
from d2rloader.ui.widget_main import MainTabsWidget

try:
    from ctypes import windll  # Only exists on Windows.

    d2rloader_id = "com.github.sh4nks.d2rloader"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(d2rloader_id)
except ImportError:
    pass

import PySide6
from loguru import logger
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)

from d2rloader.constants import BASE_DIR, ICON_PATH
from d2rloader.core.state import D2RLoaderState
from d2rloader.core.storage import StorageType

from .dialog_setting import SettingDialogWidget
from .widget_info import InfoTabsWidget


class MainWidget(QWidget):
    def __init__(self, d2rloader: D2RLoaderState):
        super().__init__()
        self.d2rloader: D2RLoaderState = d2rloader
        main_layout = QGridLayout(self)

        self.main_tab_widget: MainTabsWidget = MainTabsWidget(d2rloader)
        self.info_tab_widget: InfoTabsWidget = InfoTabsWidget(d2rloader)

        table_layout = self.create_table_layout()
        main_layout.addLayout(
            table_layout, 0, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignTop
        )
        main_layout.setRowStretch(1, 7)

        info_layout = self.create_console_layout()
        main_layout.addLayout(
            info_layout, 1, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignBottom
        )

        self._register_logger_output_panel()

    def create_table_layout(self):
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.main_tab_widget)
        return table_layout

    def create_console_layout(self):
        console_layout = QVBoxLayout()
        console_layout.addWidget(self.info_tab_widget)
        return console_layout

    def _register_logger_output_panel(self):
        fmt = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> - <level>{message}</level>"
        logger.add(
            self.info_tab_widget.application_output.output.emit,
            format=fmt,
            level=self.d2rloader.settings.data.log_level or "INFO",
        )


class MainWindow(QMainWindow):
    def __init__(self, d2rloader: D2RLoaderState):
        super().__init__()
        self.d2rloader: D2RLoaderState = d2rloader
        self.d2rloader.register_process_manager(self)

        self.main_widget: MainWidget = MainWidget(d2rloader)
        self.setWindowTitle("D2RLoader")

        if sys.platform == "linux":
            self.setWindowIcon(QtGui.QIcon.fromTheme("d2rloader"))
        else:
            self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.setCentralWidget(self.main_widget)

        file_menu = self.menuBar().addMenu("&File")
        account_menu = self.menuBar().addMenu("&Account")
        # Populate the File menu
        file_menu.addAction(create_action(self, "Settings", self.open_settings))
        file_menu.addSeparator()
        file_menu.addAction(
            create_action(self, "&Load Account Settings...", self.open_file)
        )
        file_menu.addAction(
            create_action(self, "&Save Account Settings As...", self.save_file)
        )
        file_menu.addSeparator()
        file_menu.addAction(create_action(self, "&About", self.open_about))
        file_menu.addSeparator()
        file_menu.addAction(create_action(self, "E&xit", self.close))

        # Populate the Tools menu
        account_menu.addAction(
            create_action(
                self,
                "&Add Account...",
                self.main_widget.main_tab_widget.d2rloader_table.add_entry,
            )
        )

        self.d2rloader.plugins.hook.d2rloader_mainwindow_plugin_menu(
            d2rloader=d2rloader, parent=self, menu=self.menuBar()
        )

    @Slot()
    def open_about(self):
        version_string = importlib.metadata.version("d2rloader")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        qt_version = f"{PySide6.__version__}"
        about_content = f"""
            <center>
            <h3 style="margin-bottom: 0; padding-bottom: 0">D2RLoader</h3>
            <small>A Cross-platform and Open Source Diablo 2 Resurrected Loader written in Python/Qt</small> <br />
            <br />
            <b>Donate: </b> <a href="https://forums.d2jsp.org/gold.php?i=314054">d2jsp FG</a><br /><br />
            <b>Install Path: </b> {BASE_DIR} <br />
            <b>Version: </b> {version_string}<br />
            <b>Python: </b> {python_version}, <b>Qt: </b> {qt_version}<br />
            <b>Source Code: </b> <a href="https://github.com/sh4nks/d2rloader">Link</a><br />
            <b>License: </b> MIT<br />
            <br />
            <b>TZ Info and DClone Info provided by <a href="https://d2emu.com">D2Emu.com</a>
            </center>
        """

        QMessageBox.about(self, "About", about_content)

    @Slot()
    def open_settings(self):
        settings_dialog = SettingDialogWidget(self, self.d2rloader.settings.data)
        prev_accounts_path = self.d2rloader.settings.data.accounts_path
        if settings_dialog.exec():
            self.d2rloader.settings.update(settings_dialog.data)
            if prev_accounts_path != settings_dialog.data.accounts_path:
                self.d2rloader.accounts.load()
                self.main_widget.main_tab_widget.d2rloader_table.reload_table()

    @Slot()
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self)
        if not filename:
            return
        self.d2rloader.settings.set(accounts_path=filename)
        self.d2rloader.accounts.load()
        self.main_widget.main_tab_widget.d2rloader_table.reload_table()

    @Slot()
    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self)
        if not filename:
            return
        self.d2rloader.storage.save(
            self.d2rloader.accounts.data, StorageType.Account, path=filename
        )


class D2RLoaderUI:
    ui_app: QApplication | None = None
    ui: MainWindow | None = None

    def __init__(self, d2rloader: D2RLoaderState | None = None) -> None:
        if d2rloader is not None:
            self.init_ui(d2rloader)

    def init_ui(self, d2rloader: D2RLoaderState):
        self.ui_app = QApplication(sys.argv)
        self.ui_app.setApplicationName("D2RLoader")
        self.ui_app.setApplicationVersion(importlib.metadata.version("d2rloader"))
        if sys.platform == "linux":
            self.ui_app.setWindowIcon(QtGui.QIcon.fromTheme("d2rloader"))
            self.ui_app.setDesktopFileName("d2rloader")
        else:
            self.ui_app.setWindowIcon(QtGui.QIcon(ICON_PATH))

        if d2rloader.settings.data.theme:
            QApplication.setStyle(QStyleFactory.create(d2rloader.settings.data.theme))

        self.ui = MainWindow(d2rloader)
        self.ui.resize(800, 600)

    def run(self):
        if self.ui is None or self.ui_app is None:
            raise Exception("UI has not been initialized.")
        self.ui.show()

        logger.info("D2RLoader started")
        # cant use QtAsyncio yet due to:
        # NotImplementedError('QAsyncioEventLoop.getaddrinfo() is not implemented yet')
        # qtasyncio_run(keep_running=True, quit_qapp=True, handle_sigint=True)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(self.ui_app.exec())
