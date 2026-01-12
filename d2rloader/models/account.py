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
    # China = "cn.actual.battle.net" # no idea which address

    @classmethod
    def from_name(cls, name: str):
        for key, value in cls.__members__.items():
            if name == key:
                return value
        return None


class AuthMethod(enum.Enum):
    Token = "token"
    Password = "password"

    @classmethod
    def from_name(cls, name: str):
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

    @property
    def id(self):
        if self.profile_name is not None:
            return self.profile_normalized
        return self.email_normalized

    @property
    def displayname(self):
        if self.profile_name is None or self.profile_name == "":
            return self.email
        return self.profile_name

    @property
    def email_normalized(self):
        return _normalize_str(self.email)

    @property
    def profile_normalized(self):
        if self.profile_name:
            return _normalize_str(self.profile_name)
        return ""

    @classmethod
    def wineprefix_account(cls, settings: Setting, account: "Account"):
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
    def default_account(cls):
        return Account(
            profile_name=None,
            email="",
            auth_method=AuthMethod.Password,
            password=None,
            token=None,
            region=Region.Europe,
            params=None,
        )


def _normalize_str(s: str, delim: str = "-"):
    text = unidecode.unidecode(s)
    result: list[str] = []
    for word in _punct_re.split(text.lower()):
        if word:
            result.append(word)
    return str(delim.join(result))
