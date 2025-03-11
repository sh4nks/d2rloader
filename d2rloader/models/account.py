import enum
import re

import unidecode
from pydantic import BaseModel, Field

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.+]+')


class Region(enum.Enum):
    Europe = "eu.actual.battle.net"
    Americas = "us.actual.battle.net"
    Asia = "kr.actual.battle.net"

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
    email: str
    auth_method: AuthMethod
    token: str | None
    token_protected: bytes | None = Field(default=None)
    password: str | None
    region: Region
    params: str | None
    runtime: float | None = Field(default=0)
    game_settings: str | None = Field(default=None)

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
        print(self)
        if self.profile_name:
            return _normalize_str(self.profile_name)
        return ""

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
