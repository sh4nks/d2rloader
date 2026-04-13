import os
import sys
from datetime import datetime

from pydantic import BaseModel, Field

from d2rloader.constants import CONFIG_BASE_DIR, CONFIG_PLUGINS_DIR


def get_default_wineprefix():
    if sys.platform == "linux":
        return os.path.join(CONFIG_BASE_DIR, "wineprefixes")
    return ""


def get_default_accounts_path():
    return os.path.join(CONFIG_BASE_DIR, "accounts.json")


def get_default_plugins_path():
    return CONFIG_PLUGINS_DIR


class Setting(BaseModel):
    theme: str
    accounts_path: str = Field(default_factory=get_default_accounts_path)
    handle_path: str
    game_path: str
    log_level: str = Field(default="INFO")
    log_file: bool = Field(default=True)
    check_update: bool = Field(default=True)
    last_update_check: datetime | None = Field(default=None)
    wineprefix: str = Field(default_factory=get_default_wineprefix)
    protonpath: str | None = Field(default=None)
    plugins_path: str = Field(default_factory=get_default_plugins_path)
    d2rreg_version: str | None = Field(default=None)
    token: str | None = Field(default=None)
    token_username: str | None = Field(default=None)
    d2rinfo: bool = Field(default=True)
    rotw: bool = Field(default=True)
