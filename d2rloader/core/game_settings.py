import os
import shutil
import sys
from typing import cast

from loguru import logger

from d2rloader.constants import CONFIG_GAME_SETTINGS_DIR
from d2rloader.models.account import Account
from d2rloader.models.setting import Setting


class GameSetting:
    def __init__(self, settings: Setting, account: Account):
        self.settings: Setting = settings
        self.account: Account = account

    @property
    def saved_game_folder(self):
        if sys.platform == "linux":
            wineprefix = Account.wineprefix_account(self.settings, self.account)
            path = os.path.join(
                wineprefix, "drive_c", "users", "steamuser", "Saved Games"
            )
        else:
            from win32com.shell import shell, shellcon  # pyright: ignore

            path: str = shell.SHGetKnownFolderPath(  # pyright: ignore
                shellcon.FOLDERID_SavedGames,
                0,  # see KNOWN_FOLDER_FLAG
                0,  # current user
            )

        if not path:
            return ""

        return os.path.join(cast(str, path), "Diablo II Resurrected")

    @property
    def current_game_settings(self):
        return os.path.join(self.saved_game_folder, "Settings.json")

    @property
    def account_game_settings(self):
        settings_filename = f"settings.{self.account.profile_normalized}.json"
        return os.path.join(CONFIG_GAME_SETTINGS_DIR, settings_filename)

    def _get_basename(self, path: str):
        return os.path.basename(path)

    def set_account_game_settings(self):
        if not self.account.game_settings:
            return
        elif not os.path.exists(self.account.game_settings):
            logger.warning("Configured game settings don't exist!")
            return

        logger.info(
            f"Using game settings: {os.path.basename(self.account.game_settings)}"
        )
        if os.path.exists(self.current_game_settings):
            shutil.move(self.current_game_settings, f"{self.current_game_settings}.bak")

        if sys.platform == "linux":
            os.makedirs(os.path.dirname(self.current_game_settings), exist_ok=True)

        shutil.copy2(self.account.game_settings, self.current_game_settings)

    def copy_current_settings(self, overwrite_ok: bool = False):
        """Returns a tuple containing the destination path and if the path exists"""
        if not self.account.profile_name:
            logger.error("Please choose a profile name first")
            return (None, None)

        logger.debug(f"game settings path: {self.current_game_settings}")

        os.makedirs(CONFIG_GAME_SETTINGS_DIR, exist_ok=True)

        if os.path.exists(self.account_game_settings) and not overwrite_ok:
            logger.info(
                f"Settings file '{self._get_basename(self.account_game_settings)}' already exists!"
            )
            return (self.account_game_settings, True)

        logger.info(
            f"Copying current game settings to '{self._get_basename(self.account_game_settings)}'"
        )
        shutil.copy2(self.current_game_settings, self.account_game_settings)
        return (self.account_game_settings, False)


class GameSettingsService:
    def __init__(self, settings: Setting):
        self.settings: Setting = settings

    def get_game_settings(self, account: Account):
        return GameSetting(self.settings, account)
