from d2rloader.core.store.base import BaseService
from d2rloader.core.storage import StorageService, StorageType
from d2rloader.models.account import Account
from d2rloader.models.setting import Setting


class AccountService(BaseService[Account]):
    def __init__(self, storage: StorageService, setting: Setting):
        super().__init__(storage, StorageType.Account, setting.accounts_path)
