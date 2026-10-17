from __future__ import annotations

import os
import sys
from typing import Final, cast

from loguru import logger
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from d2rloader.constants import CONFIG_GAME_SETTINGS_DIR
from d2rloader.core.game_settings import GameSetting
from d2rloader.core.state import D2RLoaderState
from d2rloader.models.account import Account, AuthMethod, Region


class AccountDialogWidget(QDialog):
    """A dialog to add a new address to the addressbook."""

    def __init__(
        self, parent: QWidget, d2rloader: D2RLoaderState, account: Account | None = None
    ):
        super().__init__(parent)
        self.d2rloader: D2RLoaderState = d2rloader
        if account is None:
            self.account: Account = Account.default_account()
        else:
            self.account = account

        self.game_settings: GameSetting = d2rloader.game_settings.get_game_settings(
            self.account
        )

        self.setMinimumWidth(760)
        main_layout = QVBoxLayout()
        options_group_box = QGroupBox("Options")

        left_layout = QFormLayout()
        right_layout = QFormLayout()
        for form_layout in (left_layout, right_layout):
            form_layout.setHorizontalSpacing(12)
            form_layout.setVerticalSpacing(10)

        self.button_box: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        profile_name_label: Final = QLabel("Profile Name:", self)
        self.profile_name: Final = QLineEdit()
        self.profile_name.textChanged.connect(self.change_profile_name)
        left_layout.addRow(profile_name_label, self.profile_name)

        email_label: Final = QLabel("Account:", self)
        self.email: Final = QLineEdit()
        left_layout.addRow(email_label, self.email)

        auth_label: Final = QLabel("Auth Method:", self)
        self.auth_combobox: Final = QComboBox()
        self.auth_combobox.addItem(AuthMethod.Token.name, AuthMethod.Token)
        self.auth_combobox.addItem(AuthMethod.Password.name, AuthMethod.Password)
        self.auth_combobox.addItem(AuthMethod.Steam.name, AuthMethod.Steam)
        self.auth_combobox.currentTextChanged.connect(self.change_password_token_widget)
        left_layout.addRow(auth_label, self.auth_combobox)

        region_label: Final = QLabel("Region:", self)
        self.region_combobox: Final = QComboBox()
        self.region_combobox.addItem(Region.Europe.name, Region.Europe)
        self.region_combobox.addItem(Region.Americas.name, Region.Americas)
        self.region_combobox.addItem(Region.Asia.name, Region.Asia)
        self.region_combobox.addItem(Region.China.name, Region.China)
        right_layout.addRow(region_label, self.region_combobox)

        self.password_label: Final = QLabel("Password:", self)
        self.password: PasswordWidget = PasswordWidget("")
        left_layout.addRow(self.password_label, self.password)

        params_label: Final = QLabel("Start Parameters:", self)
        self.params: Final = QLineEdit()
        right_layout.addRow(params_label, self.params)

        game_path_label: Final = QLabel("Game Path:", self)
        self.game_path_widget: GamePathWidget = GamePathWidget(
            self.account.game_path, d2rloader.settings.data.game_path
        )
        right_layout.addRow(game_path_label, self.game_path_widget)

        self.token_label: Final = QLabel("Token:", self)
        self.token: Final = QTextEdit()
        self.token.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        right_layout.addRow(self.token_label, self.token)

        game_settings_label: Final = QLabel("Game Settings:", self)
        self.game_setting_widget: GameSettingWidget = GameSettingWidget(
            self.account, self.game_settings
        )
        left_layout.addRow(game_settings_label, self.game_setting_widget)

        protonpath_label: Final = QLabel("PROTONPATH:", self)
        self.protonpath: Final = QLineEdit()

        if sys.platform == "linux":
            left_layout.addRow(protonpath_label, self.protonpath)

        if account is not None:
            self.profile_name.setText(account.profile_name or "")
            self.email.setText(account.email)
            account_idx = self.auth_combobox.findData(account.auth_method)
            self.auth_combobox.setCurrentIndex(account_idx)
            region_idx = self.region_combobox.findData(account.region)
            self.region_combobox.setCurrentIndex(region_idx)
            self.params.setText(account.params or "")
            self.password.password.setText(account.password or "")
            self.token.setText(account.token or "")
            self.protonpath.setText(account.protonpath)

        main_form_layout = QHBoxLayout()
        main_form_layout.setContentsMargins(12, 12, 12, 12)
        main_form_layout.setSpacing(24)
        main_form_layout.addLayout(left_layout, 1)
        main_form_layout.addLayout(right_layout, 1)
        options_group_box.setLayout(main_form_layout)
        main_layout.addWidget(options_group_box)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addLayout(main_layout)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.resize(self.minimumSizeHint())

        if account is None:
            self.setWindowTitle("Add a new Account")
        else:
            window_title = (
                account.email
                if not account.profile_name
                else f"{account.profile_name} ({account.email})"
            )
            self.setWindowTitle(f"Edit Account - {window_title}")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    @property
    def data(self):
        return Account(
            profile_name=self.profile_name.text(),
            email=self.email.text(),
            auth_method=cast(
                AuthMethod,
                self.auth_combobox.itemData(self.auth_combobox.currentIndex()),
            ),
            password=self.password.password.text(),
            token=self.token.toPlainText(),
            region=cast(
                Region,
                self.region_combobox.itemData(self.region_combobox.currentIndex()),
            ),
            params=self.params.text(),
            game_settings=self.game_setting_widget.value,
            protonpath=self.protonpath.text(),
            game_path=self.game_path_widget.game_path.text(),
        )

    @Slot()
    def change_profile_name(self):
        name = self.profile_name.text()
        sender: QLineEdit = self.sender()  # pyright: ignore[reportAssignmentType]

        error = False
        if len(name) < 1:  # minimum 1 characters
            error = True

        if (
            self.d2rloader.accounts.validate_name(name) > 0
            and name != self.account.profile_name
        ):
            error = True

        if error:
            color = "#f6989d"  # red
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        else:
            color = ""
            self.account.profile_name = f"{name}"
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

        sender.setStyleSheet(f"QLineEdit {{ background-color: {color} }}")

    @Slot()
    def change_password_token_widget(self, activated: str | None = None):
        if activated is None or AuthMethod.from_name(activated) is None:
            return


class PasswordWidget(QHBoxLayout):
    def __init__(self, password: str):
        super().__init__()
        self.setSpacing(6)
        self.password: QLineEdit = QLineEdit(f"{password}")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.hiddenOrShowButton: QPushButton = QPushButton("Show")
        self.hiddenOrShowButton.clicked.connect(self.hiddenOrShow)

        self.addWidget(self.password)
        self.addWidget(self.hiddenOrShowButton)

    def hiddenOrShow(self) -> None:
        if self.password.echoMode() == QLineEdit.EchoMode.Password:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.hiddenOrShowButton.setText("Hide")
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.hiddenOrShowButton.setText("Show")


class GamePathWidget(QHBoxLayout):
    def __init__(self, game_path: str | None, default_game_path: str):
        super().__init__()
        self.setSpacing(6)
        self.game_path: QLineEdit = QLineEdit(game_path or "")
        self.game_path.setPlaceholderText(default_game_path)
        self.game_path.setToolTip(
            "Leave empty to use the Game Path from File -> Settings"
        )

        self.select_game_path: QPushButton = QPushButton("Select...")
        self.select_game_path.clicked.connect(self.select_directory)

        self.addWidget(self.game_path, 1)
        self.addWidget(self.select_game_path)

    @Slot()
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self.widget(),
            "Select Game Path",
            self.game_path.text() or self.game_path.placeholderText(),
        )
        if directory:
            logger.debug(f"selected game path: {directory}")
            self.game_path.setText(directory)


class GameSettingWidget(QHBoxLayout):
    def __init__(self, account: Account, game_settings: GameSetting):
        super().__init__()
        self.setSpacing(6)
        self.game_settings: GameSetting = game_settings
        self.account: Account = account
        self.value: str | None = None
        if account.game_settings is not None:
            self.value = account.game_settings

        self.select_game_settings: QPushButton = QPushButton(self._get_display_value())
        self.select_game_settings.clicked.connect(self.select_settings)

        self.copy_game_settings: QPushButton = QPushButton("Copy")
        self.copy_game_settings.setToolTip("Copy Current D2R Settings")
        self.copy_game_settings.clicked.connect(self.copy_settings)

        self.addWidget(self.select_game_settings, 1)
        self.addWidget(self.copy_game_settings)

    def _get_display_value(self):
        if self.value:
            return os.path.basename(self.value)
        return "Select..."

    @Slot()
    def copy_settings(self):
        dst_path, exists = self.game_settings.copy_current_settings()

        if dst_path is None and exists is None:
            return

        if exists:
            ret = QMessageBox.question(
                self.widget(),
                "File exists",
                f"Settings file '{dst_path}' already exists! <br />"
                + "Do you want to override the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret == QMessageBox.StandardButton.No:
                return
            dst_path, _ = self.game_settings.copy_current_settings(True)

        self.value = dst_path
        self.select_game_settings.setText(self._get_display_value())

    @Slot()
    def select_settings(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.widget(), "Select Game Settings", CONFIG_GAME_SETTINGS_DIR
        )
        if filename:
            logger.debug(f"selected settings: {filename}")
            self.value = filename
            self.select_game_settings.setText(self._get_display_value())


def list_game_settings():
    settings: list[str] = []
    if os.path.exists(CONFIG_GAME_SETTINGS_DIR):
        settings = os.listdir(CONFIG_GAME_SETTINGS_DIR)
    return settings
