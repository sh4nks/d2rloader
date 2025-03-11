import pathlib
import sys
from typing import override

from loguru import logger
from PySide6.QtCore import QObject

from d2rloader.constants import CONFIG_BASE_DIR
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

    @override
    def __repr__(self) -> str:
        return f"D2RLoaderState - Settings: {self.settings.data}, Accounts: {self.accounts.data}"

    def register_process_manager(self, parent: QObject):
        self.process_manager = ProcessManager(parent, self.settings.data)

    def _setup_logger(self):
        if self.settings.data.log_file:
            logger.remove()
            logger.add(
                pathlib.Path(CONFIG_BASE_DIR, "d2rloader.log"),
                level=self.settings.data.log_level.upper() or "INFO",
            )
        elif self.settings.data.log_level.upper() != "DEBUG":
            logger.remove()
            logger.add(sys.stderr, level=self.settings.data.log_level)
