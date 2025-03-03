from __future__ import annotations
import functools
from typing import Final

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtCore import Slot
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QStyleFactory,
    QDialogButtonBox,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from d2rloader.models.setting import Setting
from d2rloader.ui.utils.utils import init_widget


class SettingDialogWidget(QDialog):
    """A dialog to add a new address to the addressbook."""

    def __init__(self, parent: QWidget | None, setting: Setting):
        super().__init__(parent)
        # self.setFixedHeight(350)
        self.setFixedWidth(500)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding
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
        self.handle_path_button: Final = QPushButton(
            self.setting.handle_path or "Select..."
        )
        self.handle_path_button.clicked.connect(
            functools.partial(
                self.select_file,
                "handle_path",
                self.handle_path_button,
                "handle.exe; handle64.exe",
            )
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
        wineprefix_path_label: Final = QLabel("Account Settings: ", self)
        self.wineprefix_path_button: Final = QPushButton(
            self.setting.accounts_path or "Select..."
        )
        self.wineprefix_path_button.clicked.connect(
            functools.partial(
                self.select_file, "wineprefix", self.wineprefix_path_button, "*.json"
            )
        )
        advanced_form.addRow(wineprefix_path_label, self.wineprefix_path_button)


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
        return self.setting

    def show_advanced_settings(self):
        print(self.advanced_settings.isChecked())
        if not self.advanced_settings.isChecked():
            self.advanced_settings.setChecked(False)
            self.advanced_frame.hide()
        else:
            self.advanced_settings.setChecked(True)
            self.advanced_frame.show()
        # QtCore.QTimer.singleShot(0, self.layout().adjustSize)
        # self.advanced_settings.adjustSize

    @Slot()
    def select_directory(self, setting_key: str, button: QPushButton):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setDirectory(self._get_setting_value(setting_key))
        if dialog.exec():
            if len(dialog.selectedFiles()) > 0:
                button.setText(dialog.selectedFiles()[0])
                setattr(self.setting, setting_key, dialog.selectedFiles()[0])

    @Slot()
    def select_file(self, setting_key: str, button: QPushButton, file_filter: str):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        # dialog.setNameFilter((file_filter))
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
        logger.debug(f"Current theme: {default_style_name}")
        for style in QStyleFactory.keys():
            if style.lower() == default_style_name:
                result.insert(0, style)
            else:
                result.append(style)
        return result
