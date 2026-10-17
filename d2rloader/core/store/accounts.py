from typing import Any, cast

from d2rloader.core.storage import StorageService, StorageType
from d2rloader.core.store.settings import SettingService
from d2rloader.models.account import Account
from d2rloader.models.setting import get_default_accounts_path


class AccountService:
    _current_accounts: list[Account] | None = []

    def __init__(self, storage: StorageService, setting: SettingService) -> None:
        self._storage: StorageService = storage
        self._setting: SettingService = setting
        self.load()

    @property
    def data(self) -> list[Account]:
        return self._current_accounts or []

    def update(self, index: int, **fields: Any) -> None:
        # Unpack[T] not possible - see: https://github.com/python/typing/issues/1399
        item = self.data[index]

        for key, value in fields.items():
            if key in item.model_fields:
                setattr(item, key, value)

        self.add(item, index)

    def get(self, index: int) -> Account | None:
        try:
            return self.data[index]
        except IndexError:
            return None

    def clone(self, index: int) -> int | None:
        try:
            account = self.data[index]
            cloned = account.model_copy(deep=True)
            cloned.profile_name = self._generate_name(cloned.profile_name)
            return self.add(cloned)
        except IndexError:
            return None

    def add(
        self, item: Account | None, index: int | None = None, commit: bool = True
    ) -> int | None:
        if item is None:
            return None

        if self._current_accounts is None:
            self._current_accounts = []

        if index is not None:
            self._current_accounts[index] = item
        else:
            self._current_accounts.append(item)
            index = len(self._current_accounts) - 1

        if commit:
            self._storage.save(
                self._current_accounts,
                StorageType.Account,
                path=self._setting.data.accounts_path,
            )
        return index

    def delete(self, index: int) -> None:
        # Unpack[T] not possible - see: https://github.com/python/typing/issues/1399
        self.data.pop(index)
        self._storage.save(
            self._current_accounts,
            StorageType.Account,
            path=self._setting.data.accounts_path,
        )

    def load(self) -> None:
        if not self._setting.data.accounts_path:
            self._setting.set(accounts_path=get_default_accounts_path())

        self._current_accounts = cast(
            list[Account],
            self._storage.load(
                StorageType.Account, path=self._setting.data.accounts_path
            ),
        )

    def _generate_name(self, name: str | None) -> str:
        name_suffix: str = "1"
        if name is None:
            name = "Generated Profile"
        elif name[-1].isdigit():
            name_suffix = str(int(name[-1]) + 1)
            name = name[:-1]
        name = f"{name}{name_suffix}"

        while self.validate_name(name) > 0:
            name = self._generate_name(name)

        return name

    def validate_name(self, name: str) -> int:
        found_names = 0
        for account in self._current_accounts or []:
            if account.profile_name == name:
                found_names += 1
        return found_names
