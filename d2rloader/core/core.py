import pathlib
import sys
from typing import override

from loguru import logger
from d2rloader.core import BASE_DIR
from d2rloader.core.process import ProcessManager
from d2rloader.core.store.settings import SettingService
from d2rloader.core.store.accounts import AccountService
from d2rloader.core.storage import StorageService


class D2RLoaderState:
    def __init__(self):
        self.storage: StorageService = StorageService()
        self.settings: SettingService = SettingService(self.storage)
        self._setup_logger()
        self.accounts: AccountService = AccountService(self.storage, self.settings.data)
        self.process_manager: ProcessManager = ProcessManager(self.settings.data)

    @override
    def __repr__(self) -> str:
        return f"D2RLoaderState - Settings: {self.settings.data}, Accounts: {self.accounts.data}"

    def _setup_logger(self):
        if self.settings.data.log_file:
            logger.remove()
            logger.add(pathlib.Path(BASE_DIR, "d2rloader.log"), level=self.settings.data.log_level.upper())
        elif self.settings.data.log_level.upper() != 'DEBUG':
            logger.remove()
            logger.add(sys.stderr, level=self.settings.data.log_level)
