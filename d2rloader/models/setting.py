from pydantic import BaseModel, Field
import os
from d2rloader.core import BASE_DIR

def _get_default_accounts_path():
    return os.path.join(BASE_DIR, "accounts.json")

class Setting(BaseModel):
    theme: str
    accounts_path: str = Field(default_factory=_get_default_accounts_path)
    handle_path: str
    game_path: str
    log_level: str = Field(default="INFO")
    log_file: bool = Field(default=True)
