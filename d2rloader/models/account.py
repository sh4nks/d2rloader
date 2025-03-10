import enum

from pydantic import BaseModel, Field


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
    profile_name: str | None = Field(default=None)
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
