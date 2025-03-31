import pathlib
import sys
from typing import override

from loguru import logger
from pluggy import PluginManager
from PySide6.QtCore import QObject

from d2rloader.constants import CONFIG_BASE_DIR
from d2rloader.core.game_settings import GameSettingsService
from d2rloader.core.plugins.loader import register_plugins
from d2rloader.core.process import ProcessManager
from d2rloader.core.storage import StorageService
from d2rloader.core.store.accounts import AccountService
from d2rloader.core.store.settings import SettingService


class D2RLoaderState:
    process_manager: ProcessManager | None = None

    def __init__(self):
        self.storage: StorageService = StorageService()
        self.settings: SettingService = SettingService(self.storage)
        self._setup_logger()
        self.accounts: AccountService = AccountService(self.storage, self.settings)
        self.game_settings: GameSettingsService = GameSettingsService(
            self.settings.data
        )
        self.plugins: PluginManager = self.register_plugin_manager()

    @override
    def __repr__(self) -> str:
        return f"D2RLoaderState - Settings: {self.settings.data}, Accounts: {self.accounts.data}"

    def register_process_manager(self, parent: QObject):
        self.process_manager = ProcessManager(parent, self)

    def register_plugin_manager(self):
        pm = register_plugins(self.settings.data.plugins_path)
        return pm

    def _setup_logger(self):
        log_level = self.settings.data.log_level or "INFO"

        if self.settings.data.log_file:
            logger.remove()
            logger.add(
                pathlib.Path(CONFIG_BASE_DIR, "d2rloader.log"),
                level=log_level,
            )

        elif self.settings.data.log_level.upper() != "DEBUG":
            logger.remove()
            logger.add(sys.stderr, level=log_level)
