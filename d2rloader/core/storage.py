import enum
import os
import pathlib
from typing import Any

from pydantic import TypeAdapter

from d2rloader.constants import CONFIG_BASE_DIR
from d2rloader.models.account import Account
from d2rloader.models.setting import Setting


class StorageType(enum.Enum):
    Account = enum.auto()
    Setting = enum.auto()


class StorageService:
    SETTINGS_PATH: pathlib.Path = pathlib.Path(CONFIG_BASE_DIR, "settings.json")
    STORAGE_MAPPING: dict[
        StorageType, TypeAdapter[None | list[Account]] | TypeAdapter[Setting]
    ] = {
        StorageType.Account: TypeAdapter(list[Account]),
        StorageType.Setting: TypeAdapter(Setting),
    }

    def load(self, type: StorageType, path: str | None = None):
        settings = self._get_path(type, path)
        try:
            content = settings.read_text("UTF8")
        except FileNotFoundError:
            return None

        if not content:
            return None
        return self.STORAGE_MAPPING[type].validate_json(content)

    def save(self, content: Any, type: StorageType, path: str | None = None):
        settings = self._get_path(type, path)
        os.makedirs(os.path.dirname(settings), exist_ok=True)
        with open(settings, "wb") as fp:
            fp.write(self.get_storage_content_json(content, type))

    def _get_path(self, type: StorageType, path: str | None = None):
        if path is not None:
            settings = pathlib.Path(path)
        elif type == StorageType.Setting:
            settings = self.SETTINGS_PATH
        else:
            raise NotImplementedError(
                f"StorageType {type} is not implemented in path finding"
            )
        return settings

    def get_storage_content_json(self, content: Any, type: StorageType):
        return self.STORAGE_MAPPING[type].dump_json(content, indent=4)
