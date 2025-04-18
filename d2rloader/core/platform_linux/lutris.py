import os
from pathlib import Path

from loguru import logger

from d2rloader.models.account import Account
from d2rloader.models.setting import Setting

# The initial version of this script was auto-generated by Lutris
# using "lutris -b ~/start.sh diablo-2-resurrected"
START_SCRIPT = """
#!/bin/bash

# This file is autogenerated. Do not edit!

# Environment variables
export __GL_SHADER_DISK_CACHE="1"
export __GL_SHADER_DISK_CACHE_PATH="{WINEPREFIX}"
export LD_LIBRARY_PATH="{LUTRIS_PATH}/runners/proton/ge-proton/files/lib:{LUTRIS_PATH}/runners/proton/ge-proton/files/lib64:/usr/lib:/usr/lib32:/usr/lib/libfakeroot:/usr/lib64:{LUTRIS_PATH}/runtime/Ubuntu-18.04-i686:{LUTRIS_PATH}/runtime/steam/i386/lib/i386-linux-gnu:{LUTRIS_PATH}/runtime/steam/i386/lib:{LUTRIS_PATH}/runtime/steam/i386/usr/lib/i386-linux-gnu:{LUTRIS_PATH}/runtime/steam/i386/usr/lib:{LUTRIS_PATH}/runtime/Ubuntu-18.04-x86_64:{LUTRIS_PATH}/runtime/steam/amd64/lib/x86_64-linux-gnu:{LUTRIS_PATH}/runtime/steam/amd64/lib:{LUTRIS_PATH}/runtime/steam/amd64/usr/lib/x86_64-linux-gnu:{LUTRIS_PATH}/runtime/steam/amd64/usr/lib"
export DXVK_STATE_CACHE_PATH="{WINEPREFIX}"
export STAGING_SHARED_MEMORY="1"
export WINEDEBUG="-all"
export DXVK_LOG_LEVEL="error"
export UMU_LOG="1"
export WINEARCH="win64"
export WINE="{LUTRIS_PATH}/runners/proton/ge-proton/files/bin/wine"
export WINE_MONO_CACHE_DIR="{LUTRIS_PATH}/runners/proton/ge-proton/files/mono"
export WINE_GECKO_CACHE_DIR="{LUTRIS_PATH}/runners/proton/ge-proton/files/gecko"
export WINEPREFIX="{WINEPREFIX}"
export WINEESYNC="1"
export WINEFSYNC="1"
export DXVK_NVAPIHACK="0"
export DXVK_ENABLE_NVAPI="1"
export PROTON_DXVK_D3D8="1"
export WINEDLLOVERRIDES="winemenubuilder="
export WINE_LARGE_ADDRESS_AWARE="1"
export TERM="xterm"

# Working Directory
cd '{GAME_PATH}'

# Command

# Use gamemode if available
if ! [ -x "$(command -v gamemoderun)" ]; then
    echo 'gamemode is not installed - starting D2R.exe without gamemoderun' >&2
    {LUTRIS_UMU_LAUNCHER} '{GAME_PATH}/D2R.exe' -w -username {USERNAME} -password {PASSWORD} -address {REGION} {PARAMS}
else
    gamemoderun {LUTRIS_UMU_LAUNCHER} '{GAME_PATH}/D2R.exe' -w -username {USERNAME} -password {PASSWORD} -address {REGION} {PARAMS}
fi
"""


class LutrisManager:
    home: Path = Path.home()

    def __init__(self, settings: Setting, account: Account) -> None:
        self.settings: Setting = settings
        self.account: Account = account

    @property
    def lutris_home(self):
        return Path(self.home, ".local/share/lutris")

    @property
    def lutris_umu_launcher(self):
        return Path(self.lutris_home, "runtime/umu/umu-run")

    @property
    def wineprefix_account(self):
        return Account.wineprefix_account(
            self.settings,
            self.account,
        )

    @property
    def start_script_log_path(self):
        return Path(self.wineprefix_account, "umu.log")

    @property
    def start_script_path(self):
        return Path(self.wineprefix_account, "start.sh")

    def render_start_script(self):
        return START_SCRIPT.format(
            WINEPREFIX=self.wineprefix_account,
            GAME_PATH=self.settings.game_path,
            LUTRIS_PATH=self.lutris_home,
            LUTRIS_UMU_LAUNCHER=self.lutris_umu_launcher,
            USERNAME=self.account.email,
            PASSWORD=self.account.password,
            REGION=self.account.region.value,
            PARAMS=self.account.params,
        )

    def save_start_script(self, force: bool = True):
        if (
            not force
            and self.wineprefix_account.exists()
            and self.start_script_path.exists()
        ):
            logger.warning("Wineprefix already exists!")
            return
        else:
            os.makedirs(self.wineprefix_account, exist_ok=True)

        logger.debug(f"Writing file '{self.start_script_path}'...")

        with open(self.start_script_path, "w") as f:
            f.write(self.render_start_script())
        return True
