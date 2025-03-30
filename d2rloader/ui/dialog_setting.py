from __future__ import annotations

import functools
import os
import shutil
import sys
from typing import Callable, Final

from loguru import logger
from PySide6 import QtWidgets
from PySide6.QtCore import (
    QIODevice,
    QSaveFile,
    Slot,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)

from d2rloader.constants import CONFIG_HANDLE_DIR, HANDLE_URL, HANDLE_URL_FILENAME
from d2rloader.models.setting import Setting
from d2rloader.ui.utils.utils import init_widget


class SettingDialogWidget(QDialog):
    """A dialog to add a new address to the addressbook."""

    def __init__(self, parent: QWidget | None, setting: Setting):
        super().__init__(parent)
        # self.setFixedHeight(350)
        self.setFixedWidth(530)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )
        self.setting: Setting = setting

        form_layout = QFormLayout()

        game_path_label: Final = QLabel("Game Path: ", self)
        self.game_path_button: Final = QPushButton(
            self.setting.game_path or "Select..."
        )
        self.game_path_button.clicked.connect(
            functools.partial(self.select_directory, "game_path", self.game_path_button)
        )
        form_layout.addRow(game_path_label, self.game_path_button)

        account_path_label: Final = QLabel("Account Settings: ", self)
        self.account_path_button: Final = QPushButton(
            self.setting.accounts_path or "Select..."
        )
        self.account_path_button.clicked.connect(
            functools.partial(
                self.select_file, "accounts_path", self.account_path_button, "*.json"
            )
        )
        form_layout.addRow(account_path_label, self.account_path_button)

        handle_path_label: Final = QLabel("Handle Path: ", self)
        self.handle_path_button: DownloadHandleWidget = DownloadHandleWidget(
            setting, self.select_file
        )
        form_layout.addRow(handle_path_label, self.handle_path_button)

        self.style_combobox: Final = QComboBox()
        init_widget(self.style_combobox, "styleComboBox", "Style")
        self.style_combobox.addItems(self.style_names(parent))
        self.style_combobox.textActivated.connect(self.change_style)
        default_style = setting.theme
        if not default_style and parent is not None:
            default_style = parent.style().name()
        style_idx = self.style_combobox.findText(default_style)
        self.style_combobox.setCurrentIndex(style_idx or 0)

        style_label = QLabel("Theme: ")
        init_widget(style_label, "style_label", "Select Theme")
        style_label.setBuddy(self.style_combobox)
        form_layout.addRow(style_label, self.style_combobox)

        main_layout = QVBoxLayout()
        main_form_layout = QHBoxLayout()
        main_form_layout.addLayout(form_layout)
        options_group_box = QGroupBox("Settings")
        options_group_box.setLayout(main_form_layout)
        main_layout.addWidget(options_group_box)

        advanced_form = QFormLayout()
        d2emu_token_user_label: Final = QLabel("D2Emu Token Username: ", self)
        self.d2emu_token_user: Final = QLineEdit()
        self.d2emu_token_user.setText(setting.token_username or "")
        advanced_form.addRow(d2emu_token_user_label, self.d2emu_token_user)

        d2emu_token_label: Final = QLabel("D2Emu Token: ", self)
        self.d2emu_token: Final = QLineEdit()
        self.d2emu_token.setText(setting.token or "")
        advanced_form.addRow(d2emu_token_label, self.d2emu_token)

        wineprefix_path_label: Final = QLabel("Wineprefix (Linux): ", self)
        self.wineprefix_path_button: Final = QPushButton(
            self.setting.wineprefix or "Select..."
        )
        self.wineprefix_path_button.clicked.connect(
            functools.partial(
                self.select_directory, "wineprefix", self.wineprefix_path_button
            )
        )
        advanced_form.addRow(wineprefix_path_label, self.wineprefix_path_button)

        plugins_path_label: Final = QLabel("Plugins: ", self)
        self.plugins_path_button: Final = QPushButton(
            self.setting.plugins_path or "Select..."
        )
        self.plugins_path_button.clicked.connect(
            functools.partial(
                self.select_directory, "plugins_path", self.plugins_path_button
            )
        )
        advanced_form.addRow(plugins_path_label, self.plugins_path_button)

        log_level_label: Final = QLabel("Log Level: ", self)
        self.log_level_combobox: Final = QComboBox()
        self.log_level_combobox.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_idx = self.log_level_combobox.findText(setting.log_level)
        self.log_level_combobox.setCurrentIndex(log_level_idx)

        advanced_form.addRow(log_level_label, self.log_level_combobox)
        log_file_label: Final = QLabel("Log To File: ", self)
        self.log_file: Final = QCheckBox()
        self.log_file.setChecked(setting.log_file or False)
        advanced_form.addRow(log_file_label, self.log_file)

        self.advanced_frame: QFrame = QFrame()
        advanced_layout = QVBoxLayout()
        self.advanced_frame.setLayout(advanced_layout)
        self.advanced_frame.hide()
        advanced_form_layout = QHBoxLayout()
        advanced_form_layout.addLayout(advanced_form)
        advanced_options_group_box = QGroupBox("Advanced Settings")
        advanced_options_group_box.setLayout(advanced_form_layout)
        advanced_layout.addWidget(options_group_box)
        advanced_layout.addWidget(advanced_options_group_box)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        self.advanced_settings: QPushButton = QPushButton("Advanced Settings")
        self.advanced_settings.setCheckable(True)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.advanced_settings)
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        _layout: QVBoxLayout = QVBoxLayout()
        _layout.addLayout(main_layout)
        _layout.addWidget(self.advanced_frame)
        _layout.addLayout(button_layout)
        _layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.setLayout(_layout)

        self.setWindowTitle("D2RLoader Settings")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.advanced_settings.clicked.connect(self.show_advanced_settings)

    @property
    def data(self):
        self.setting.theme = self.style_combobox.itemText(
            self.style_combobox.currentIndex()
        )
        self.setting.token_username = self.d2emu_token_user.text()
        self.setting.token = self.d2emu_token.text()
        self.setting.log_file = self.log_file.isChecked()
        self.setting.log_level = self.log_level_combobox.itemText(
            self.log_level_combobox.currentIndex()
        )
        return self.setting

    def show_advanced_settings(self):
        if not self.advanced_settings.isChecked():
            self.advanced_settings.setChecked(False)
            self.advanced_frame.hide()
        else:
            self.advanced_settings.setChecked(True)
            self.advanced_frame.show()

    @Slot(str, QPushButton)  # pyright: ignore
    def select_directory(self, setting_key: str, button: QPushButton):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setDirectory(self._get_setting_value(setting_key))
        if dialog.exec():
            if len(dialog.selectedFiles()) > 0:
                button.setText(dialog.selectedFiles()[0])
                setattr(self.setting, setting_key, dialog.selectedFiles()[0])

    @Slot(str, QPushButton, str)  # pyright: ignore
    def select_file(self, setting_key: str, button: QPushButton, file_filter: str):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setNameFilter((file_filter))
        dialog.setDirectory(self._get_setting_value(setting_key))
        if dialog.exec():
            if len(dialog.selectedFiles()) > 0:
                button.setText(dialog.selectedFiles()[0])
                setattr(self.setting, setting_key, dialog.selectedFiles()[0])

    def _get_setting_value(self, setting_key: str) -> str:
        return getattr(self.setting, setting_key)

    @Slot()
    def change_style(self, style_name: str | None = None):
        if style_name is not None and QtWidgets.QApplication.instance() is not None:
            QtWidgets.QApplication.instance().setStyle(QStyleFactory.create(style_name))  # pyright: ignore

    def style_names(self, parent: QWidget | None) -> list[str]:
        """Return a list of styles, default platform style first"""
        result: list[str] = []
        if parent is None:
            return result

        default_style_name = parent.style().objectName().lower()
        for style in QStyleFactory.keys():
            if style.lower() == default_style_name:
                result.insert(0, style)
            else:
                result.append(style)
        return result


class DownloadHandleWidget(QHBoxLayout):
    def __init__(
        self, setting: Setting, filechooser: Callable[[str, QPushButton, str], None]
    ):
        super().__init__()
        self.HANDLE_DOWNLOAD_FILE: str = os.path.join(
            CONFIG_HANDLE_DIR, HANDLE_URL_FILENAME
        )

        self.networkmanager: QNetworkAccessManager = QNetworkAccessManager(self)
        self.file: QSaveFile = QSaveFile(self.HANDLE_DOWNLOAD_FILE)
        self.reply: QNetworkReply | None = None

        self.setting: Setting = setting

        self.handle_path_button: Final = QPushButton(
            self.setting.handle_path or "Select..."
        )
        self.handle_path_button.clicked.connect(
            functools.partial(
                filechooser,
                "handle_path",
                self.handle_path_button,
                "handle.exe;handle64.exe",
            )
        )

        self.download_button: QPushButton = QPushButton("Download")
        self.download_button.clicked.connect(self.download_handle)

        if sys.platform == "linux":
            self.handle_path_button.setDisabled(True)
            self.download_button.setDisabled(True)

        self.addWidget(self.handle_path_button, 1)
        self.addWidget(self.download_button)

    def download_handle(self):
        self.handle_path_button.setDisabled(True)
        self.download_button.setDisabled(True)

        if os.path.exists(os.path.join(CONFIG_HANDLE_DIR, "handle64.exe")):
            logger.info("handle64.exe already downloaded!")
            ret = QMessageBox.question(
                self.widget(),
                "File exists",
                "Do you want to override the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret == QMessageBox.StandardButton.No:
                self.set_handle_path(os.path.join(CONFIG_HANDLE_DIR, "handle64.exe"))
                self.handle_path_button.setDisabled(False)
                self.download_button.setDisabled(False)
                return
        else:
            os.makedirs(CONFIG_HANDLE_DIR, exist_ok=True)

        logger.info(f"Saving to '{self.file.fileName()}'")
        self.send_request()

    def send_request(self):
        request = QNetworkRequest(HANDLE_URL)
        if not self.file.open(QIODevice.OpenModeFlag.WriteOnly):
            error = self.file.errorString()
            logger.error(f"Cannot open device: {error}")
            return

        self.reply = self.networkmanager.get(request)
        self.reply.downloadProgress.connect(self.on_progress)
        self.reply.finished.connect(self.on_finished)
        self.reply.readyRead.connect(self.on_ready_read)
        self.reply.errorOccurred.connect(self.on_error)

    @Slot(QNetworkReply)
    def on_finished(self):
        if self.reply:
            self.reply.deleteLater()

        if self.file:
            self.file.commit()

        shutil.unpack_archive(self.HANDLE_DOWNLOAD_FILE, CONFIG_HANDLE_DIR)

        self.set_handle_path(os.path.join(CONFIG_HANDLE_DIR, "handle64.exe"))
        self.handle_path_button.setDisabled(False)
        self.download_button.setDisabled(False)

    @Slot(QNetworkReply.NetworkError)  # pyright: ignore
    def on_error(self, code: QNetworkReply.NetworkError):
        """Show a message if an error happen"""
        logger.error(f"Couldn't download handle64.exe: {code}")

    @Slot()
    def on_ready_read(self):
        """Get available bytes and store them into the file"""
        if self.reply:
            if self.reply.error() == QNetworkReply.NetworkError.NoError:
                self.file.write(self.reply.readAll())

    @Slot(int, int)  # pyright: ignore
    def on_progress(self, bytesReceived: int, bytesTotal: int):
        """Update progress bar"""
        logger.info(
            f"Downloading handle.exe - {bytesReceived / 1000} kb of {bytesTotal or 0 / 1000} kb recieved"
        )

    def set_handle_path(self, path: str):
        self.setting.handle_path = path
        self.handle_path_button.setText(self.setting.handle_path)
