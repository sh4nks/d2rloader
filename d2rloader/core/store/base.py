from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel

from d2rloader.core.storage import StorageService, StorageType

T = TypeVar("T", bound="BaseModel")


class BaseService(Generic[T]):
    _state: list[T] | None = []

    def __init__(
        self, storage: StorageService, type: StorageType, path: str | None = None
    ):
        self.storage_type: StorageType = type
        self.storage: StorageService = storage
        self.path: str | None = path
        self.load()

    @property
    def data(self) -> list[T]:
        return self._state or []

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

    def add(self, item: T | None, index: int | None = None, commit: bool = True):
        if item is None:
            return

        if self._state is None:
            self._state = []

        if index is not None:
            self._state[index] = item

        else:
            self._state.append(item)

        if commit:
            self.storage.save(self._state, self.storage_type, self.path)

    def delete(self, index: int):
        # Unpack[T] not possible - see: https://github.com/python/typing/issues/1399
        self.data.pop(index)
        self.storage.save(self._state, self.storage_type, self.path)

    def load(self):
        self._state = cast(list[T], self.storage.load(self.storage_type, self.path))
