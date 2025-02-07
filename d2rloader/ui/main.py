from __future__ import annotations
import os
import sys
import signal

import PySide6
from PySide6.QtCore import Slot

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyleFactory,
    QWidget,
    QGridLayout,
)

from PySide6.QtGui import QAction

from d2rloader.core.core import D2RLoaderState
from d2rloader.core.storage import StorageType
from d2rloader.ui.setting_dialog import SettingDialogWidget
from d2rloader.ui.table import D2RLoaderTableWidget


class MainWidget(QWidget):
    def __init__(self, state: D2RLoaderState):
        super().__init__()
        self.state: D2RLoaderState = state
        main_layout = QGridLayout(self)
        self.table_widget: D2RLoaderTableWidget = D2RLoaderTableWidget(state)
        top_layout = self.create_top_layout()
        main_layout.addLayout(top_layout, 0, 0, 1, 2)

        table_layout = self.create_table_layout()
        main_layout.addLayout(table_layout, 1, 0, 1, 2)

    def create_top_layout(self):
        top_layout = QHBoxLayout()

        top_layout.addStretch(1)
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.table_widget.add_entry)
        clone_button = QPushButton("Clone")
        clone_button.clicked.connect(self.table_widget.clone_entry)
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.table_widget.edit_entry)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.table_widget.delete_entry)
        top_layout.addWidget(add_button)
        top_layout.addWidget(clone_button)
        top_layout.addWidget(edit_button)
        top_layout.addWidget(delete_button)
        return top_layout

    def create_table_layout(self):
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table_widget)
        return table_layout


class MainWindow(QMainWindow):
    def __init__(self, state: D2RLoaderState):
        super().__init__()
        self.state: D2RLoaderState = state

        self.main_widget: MainWidget = MainWidget(state)
        self.setWindowTitle("D2RLoader")
        self.setCentralWidget(self.main_widget)

        file_menu = self.menuBar().addMenu("&File")
        account_menu = self.menuBar().addMenu("&Account")

        # Populate the File menu
        self.setting_action: QAction = self.create_action(
            "Settings", file_menu, self.open_settings
        )
        file_menu.addSeparator()
        self.open_action: QAction = self.create_action(
            "&Load Account Settings...", file_menu, self.open_file
        )
        self.save_action: QAction = self.create_action(
            "&Save Account Settings As...", file_menu, self.save_file
        )
        file_menu.addSeparator()
        self.info_action: QAction = self.create_action(
            "&About", file_menu, self.open_about
        )
        file_menu.addSeparator()
        self.exit_action: QAction = self.create_action("E&xit", file_menu, self.close)

        # Populate the Tools menu
        self.add_action: QAction = self.create_action(
            "&Add Account...", account_menu, self.main_widget.table_widget.add_entry
        )

    def create_action(self, text: str, menu: QMenu, slot: object) -> QAction:
        """Helper function to save typing when populating menus
        with action.
        """
        action = QAction(text, self)
        menu.addAction(action)
        action.triggered.connect(slot)
        return action

    @Slot()
    def open_about(self):
        import importlib.metadata

        version_string = importlib.metadata.version("d2rloader")
        install_path = os.path.abspath(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        qt_version = f"{PySide6.__version__}"
        about_content = f"""
            <center>
            <h3>Diablo 2 Resurrected Loader</h3>
            <br />
            <b>Install Path: </b> {install_path} <br /><br />
            <b>Version: </b> {version_string}<br />
            <b>Python: </b> {python_version}, <b>Qt: </b> {qt_version}<br />
            <b>Source Code: </b> <a href="https://github.com/sh4nks/d2r-loader">Link</a><br />
            <b>License: </b> MIT<br />
            </center>
        """

        QMessageBox.about(self, "About", about_content)

    @Slot()
    def open_settings(self):
        settings_dialog = SettingDialogWidget(self, self.state.settings.data)
        if settings_dialog.exec():
            print(settings_dialog.data)
            self.state.settings.update(settings_dialog.data)

    @Slot()
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self)
        self.state.accounts.load(filename)
        self.main_widget.table_widget.reload_table()

    @Slot()
    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self)
        self.state.storage.save(self.state.accounts.data, StorageType.Account, filename)


class D2RLoaderUI:
    ui_app: QApplication | None = None
    ui: MainWindow | None = None

    def __init__(self, state: D2RLoaderState | None = None) -> None:
        if state is not None:
            self.init_ui(state)

    def init_ui(self, state: D2RLoaderState):
        self.ui_app = QApplication(sys.argv)
        if state.settings.data.theme:
            QApplication.setStyle(QStyleFactory.create(state.settings.data.theme))

        self.ui = MainWindow(state)
        self.ui.resize(800, 600)

    def run(self):
        if self.ui is None or self.ui_app is None:
            raise Exception("UI has not been initialized.")
        self.ui.show()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(self.ui_app.exec())
