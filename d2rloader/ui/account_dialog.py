from __future__ import annotations

import os
from typing import Final, cast

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
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
from d2rloader.core.core import D2RLoaderState
from d2rloader.core.game_settings import GameSetting
from d2rloader.models.account import Account, AuthMethod, Region


class AccountDialogWidget(QDialog):
    """A dialog to add a new address to the addressbook."""

    def __init__(
        self, parent: QWidget, appstate: D2RLoaderState, account: Account | None = None
    ):
        super().__init__(parent)
        if account is None:
            self.account: Account = Account.default_account()
        else:
            self.account = account

        self.game_settings: GameSetting = appstate.game_settings.get_game_settings(
            self.account
        )

        self.setFixedHeight(230)
        self.setFixedWidth(700)
        main_layout = QVBoxLayout()
        options_group_box = QGroupBox("Options")

        options_group_box_layout = QGridLayout()
        options_group_box_layout.setColumnStretch(0, 0)
        options_group_box_layout.setColumnStretch(4, 0)

        left_layout = QFormLayout()
        right_layout = QFormLayout()

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
        self.auth_combobox.currentTextChanged.connect(self.change_password_token_widget)
        left_layout.addRow(auth_label, self.auth_combobox)

        region_label: Final = QLabel("Region:", self)
        self.region_combobox: Final = QComboBox()
        self.region_combobox.addItem(Region.Europe.name, Region.Europe)
        self.region_combobox.addItem(Region.Americas.name, Region.Americas)
        self.region_combobox.addItem(Region.Asia.name, Region.Asia)
        right_layout.addRow(region_label, self.region_combobox)

        self.password_label: Final = QLabel("Password:", self)
        self.password: PasswordWidget = PasswordWidget("")
        left_layout.addRow(self.password_label, self.password)

        params_label: Final = QLabel("Start Parameters:", self)
        self.params: Final = QLineEdit()
        right_layout.addRow(params_label, self.params)

        self.token_label: Final = QLabel("Token:", self)
        self.token: Final = QTextEdit()
        self.token.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        right_layout.addRow(self.token_label, self.token)

        game_settings_label: Final = QLabel("Game Settings")
        self.game_setting_widget: GameSettingWidget = GameSettingWidget(
            self.account, self.game_settings
        )
        left_layout.addRow(game_settings_label, self.game_setting_widget)

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

        # options_group_box.setLayout(options_group_box_layout)
        main_form_layout = QHBoxLayout()
        main_form_layout.addLayout(left_layout)
        main_form_layout.addLayout(right_layout)
        options_group_box.setLayout(main_form_layout)
        main_layout.addWidget(options_group_box)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

        if account is None:
            self.setWindowTitle("Add a new Account")
        else:
            self.setWindowTitle(f"Edit Account - email: {account.email}")

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

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
        )

    def change_profile_name(self):
        name = self.profile_name.text()
        self.account.profile_name = f"{name}"

    @Slot()
    def change_password_token_widget(self, activated: str | None = None):
        if activated is None or AuthMethod.from_name(activated) is None:
            return


class PasswordWidget(QHBoxLayout):
    def __init__(self, password: str):
        super().__init__()
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


class GameSettingWidget(QHBoxLayout):
    def __init__(self, account: Account, game_settings: GameSetting):
        super().__init__()
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
        filename = QFileDialog.getOpenFileName(
            self.widget(), "Select Game Settings", CONFIG_GAME_SETTINGS_DIR
        )
        if filename[0]:
            self.value = filename[0]
            self.select_game_settings.setText(self._get_display_value())
        else:
            self.value = None
            self.select_game_settings.setText(self._get_display_value())


def list_game_settings():
    settings: list[str] = []
    if os.path.exists(CONFIG_GAME_SETTINGS_DIR):
        settings = os.listdir(CONFIG_GAME_SETTINGS_DIR)
    return settings
