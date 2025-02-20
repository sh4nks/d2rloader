from pydantic import BaseModel, Field
import enum
from typing import override
from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

# https://github.com/pyside/Examples/blob/master/examples/itemviews/editabletreemodel/editabletreemodel.py


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

    @property
    def displayname(self):
        if self.profile_name is None or self.profile_name == "":
            return self.email
        return self.profile_name


# TODO: Unused at the moment - switch to QTableView first
class AccountModel(QAbstractItemModel):
    def __init__(
        self, accounts: list[Account] | None = None, parent: QObject | None = None
    ):
        super().__init__(parent)
        self.accounts: list[Account] = accounts or []

    @override
    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role == Qt.ItemDataRole.DisplayRole:
            # See below for the data structure.
            account: Account = self.accounts[index.row()]
            # Return the todo text only.
            return account
        return None

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None):
        return len(self.accounts)

    def addRow(self, account: Account):
        pass

    def editRow(self, index: int):
        pass

    def deleteRow(self, index: int):
        pass
