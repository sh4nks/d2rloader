from typing import Any, cast
from d2rloader.core.storage import StorageService, StorageType
from d2rloader.core.store.settings import SettingService
from d2rloader.models.account import Account


class AccountService:
    _current_accounts: list[Account] | None = []

    def __init__(self, storage: StorageService, setting: SettingService):
        self._storage: StorageService = storage
        self._setting: SettingService = setting
        self.load()

    @property
    def data(self) -> list[Account]:
        return self._current_accounts or []

    def update(self, index: int, **fields: Any):
        # Unpack[T] not possible - see: https://github.com/python/typing/issues/1399
        item = self.data[index]

        for key, value in fields.items():
            if key in item.model_fields.keys():
                setattr(item, key, value)

        self.add(item, index)

    def get(self, index: int):
        try:
            return self.data[index]
        except IndexError:
            return None

    def add(self, item: Account | None, index: int | None = None, commit: bool = True):
        if item is None:
            return

        if self._current_accounts is None:
            self._current_accounts = []

        if index is not None:
            self._current_accounts[index] = item

        else:
            self._current_accounts.append(item)

        if commit:
            self._storage.save(
                self._current_accounts,
                StorageType.Account,
                self._setting.data.accounts_path,
            )

    def delete(self, index: int):
        # Unpack[T] not possible - see: https://github.com/python/typing/issues/1399
        self.data.pop(index)
        self._storage.save(
            self._current_accounts,
            StorageType.Account,
            self._setting.data.accounts_path,
        )

    def load(self):
        self._current_accounts = cast(
            list[Account],
            self._storage.load(StorageType.Account, self._setting.data.accounts_path),
        )
