import enum
import re
from pathlib import Path

import unidecode
from pydantic import BaseModel, Field

from d2rloader.models.setting import Setting

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.+]+')


class Region(enum.Enum):
    Europe = "eu.actual.battle.net"
    Americas = "us.actual.battle.net"
    Asia = "kr.actual.battle.net"
    China = "cn.actual.battlenet.com.cn"  # no idea which address

    @classmethod
    def from_name(cls, name: str) -> "Region | None":
        for key, value in cls.__members__.items():
            if name == key:
                return value
        return None


class AuthMethod(enum.Enum):
    Token = "token"
    Password = "password"
    Steam = "steam"

    @classmethod
    def from_name(cls, name: str) -> "AuthMethod | None":
        for key, value in cls.__members__.items():
            if name == key:
                return value
        return None


class Account(BaseModel):
    profile_name: str | None = Field(default=None, frozen=False)
    email: str = Field(default="", repr=False)
    auth_method: AuthMethod
    token: str | None = Field(default=None, repr=False)
    password: str | None = Field(default=None, repr=False)
    region: Region
    params: str | None
    runtime: float | None = Field(default=0)
    game_settings: str | None = Field(default=None)
    protonpath: str | None = Field(default=None)
    game_path: str | None = Field(default=None)

    @property
    def id(self) -> str:
        if self.profile_name is not None:
            return self.profile_normalized
        return self.email_normalized

    @property
    def displayname(self) -> str:
        if self.profile_name is None or self.profile_name == "":
            return self.email
        return self.profile_name

    @property
    def email_normalized(self) -> str:
        return _normalize_str(self.email)

    @property
    def profile_normalized(self) -> str:
        if self.profile_name:
            return _normalize_str(self.profile_name)
        return ""

    @classmethod
    def wineprefix_account(cls, settings: Setting, account: "Account") -> Path:
        if account.auth_method == AuthMethod.Steam:
            return Path(Path.home(), ".steam/steam/steamapps/compatdata/2536520/pfx/")
        if account.profile_normalized:
            return Path(
                settings.wineprefix,
                account.profile_normalized,
            )
        return Path(
            settings.wineprefix,
            account.email_normalized,
        )

    @classmethod
    def game_path_account(cls, settings: Setting, account: "Account") -> str:
        if account.game_path:
            return account.game_path
        return settings.game_path

    @classmethod
    def default_account(cls) -> "Account":
        return Account(
            profile_name=None,
            email="",
            auth_method=AuthMethod.Password,
            password=None,
            token=None,
            region=Region.Europe,
            params=None,
            protonpath=None,
            game_path=None,
        )


def _normalize_str(s: str, delim: str = "-") -> str:
    text = unidecode.unidecode(s)
    result: list[str] = []
    for word in _punct_re.split(text.lower()):
        if word:
            result.append(word)
    return delim.join(result)
