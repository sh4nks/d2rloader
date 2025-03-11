import os
import sys

from pydantic import BaseModel, Field

from d2rloader.constants import CONFIG_BASE_DIR


def get_default_wineprefix():
    if sys.platform == "linux":
        return os.path.join(CONFIG_BASE_DIR, "wineprefixes")
    return ""


def get_default_accounts_path():
    return os.path.join(CONFIG_BASE_DIR, "accounts.json")


class Setting(BaseModel):
    theme: str
    accounts_path: str = Field(default_factory=get_default_accounts_path)
    handle_path: str
    game_path: str
    log_level: str = Field(default="INFO")
    log_file: bool = Field(default=True)
    wineprefix: str = Field(default_factory=get_default_wineprefix)
    token: str | None = Field(default=None)
    token_username: str | None = Field(default=None)
