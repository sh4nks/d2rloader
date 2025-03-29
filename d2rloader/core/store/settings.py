import os
from typing import Any, cast

from loguru import logger

from d2rloader.core.storage import StorageService, StorageType
from d2rloader.models.setting import Setting


class SettingService:
    _current_setting: Setting

    def __init__(self, storage: StorageService):
        self._storage: StorageService = storage
        self.load()

        if self._current_setting is None:
            self._current_setting = self._default_settings

    @property
    def data(self) -> Setting:
        return self._current_setting

    @property
    def _default_settings(self):
        return Setting(theme="", game_path="", handle_path="")

    def set(self, **kwargs: Any):  # pyright: ignore
        for key, value in kwargs.items():
            setattr(self._current_setting, key, value)

        self._storage.save(self._current_setting, type=StorageType.Setting)

    def update(self, setting: Setting | None):
        if setting is None:
            return
        self._current_setting = setting
        self._storage.save(self._current_setting, type=StorageType.Setting)

    def load(self, path: str | None = None):
        self._current_setting = cast(
            Setting, self._storage.load(StorageType.Setting, path=path)
        )

        if not self._current_setting:
            logger.info("Creating default settings...")
            self.update(self._default_settings)

        if self._current_setting and not os.path.exists(
            self._current_setting.handle_path
        ):
            self._current_setting.handle_path = ""
