import os
from pathlib import Path
import re
import unidecode
from loguru import logger
from d2rloader.models.account import Account
from d2rloader.models.setting import Setting

START_SCRIPT = """
#!/bin/bash


# Environment variables
export __GL_SHADER_DISK_CACHE="1"
export __GL_SHADER_DISK_CACHE_PATH="{WINEPREFIX}"
export LD_LIBRARY_PATH="{LUTRIS_PATH}/runners/proton/ge-proton/files/lib:{LUTRIS_PATH}/runners/proton/ge-proton/files/lib64:/usr/lib:/usr/lib32:/usr/lib/libfakeroot:/usr/lib64"
export DXVK_STATE_CACHE_PATH="/media/Data/Games/Battle.NET"
export STAGING_SHARED_MEMORY="1"
export WINEDEBUG="-all"
export DXVK_LOG_LEVEL="debug"
export UMU_LOG="debug"
export WINEARCH="win64"
export WINE="{LUTRIS_PATH}/runners/proton/ge-proton/files/bin/wine"
export WINE_MONO_CACHE_DIR="{LUTRIS_PATH}/runners/wine/ge-proton/mono"
export WINE_GECKO_CACHE_DIR="{LUTRIS_PATH}/runners/wine/ge-proton/gecko"
export WINEPREFIX="{WINEPREFIX}"
export WINEESYNC="1"
export WINEFSYNC="1"
export DXVK_NVAPIHACK="0"
export DXVK_ENABLE_NVAPI="1"
export WINEDLLOVERRIDES="d3d10core,d3d11,d3d12,d3d12core,d3d8,d3d9,d3dcompiler_33,d3dcompiler_34,d3dcompiler_35,d3dcompiler_36,d3dcompiler_37,d3dcompiler_38,d3dcompiler_39,d3dcompiler_40,d3dcompiler_41,d3dcompiler_42,d3dcompiler_43,d3dcompiler_46,d3dcompiler_47,d3dx10,d3dx10_33,d3dx10_34,d3dx10_35,d3dx10_36,d3dx10_37,d3dx10_38,d3dx10_39,d3dx10_40,d3dx10_41,d3dx10_42,d3dx10_43,d3dx11_42,d3dx11_43,d3dx9_24,d3dx9_25,d3dx9_26,d3dx9_27,d3dx9_28,d3dx9_29,d3dx9_30,d3dx9_31,d3dx9_32,d3dx9_33,d3dx9_34,d3dx9_35,d3dx9_36,d3dx9_37,d3dx9_38,d3dx9_39,d3dx9_40,d3dx9_41,d3dx9_42,d3dx9_43,dxgi,nvapi,nvapi64=n;winemenubuilder="
export WINE_LARGE_ADDRESS_AWARE="1"
export TERM="xterm"

# Working Directory
cd '{GAME_PATH}'

# Command
gamemoderun {LUTRIS_UMU_LAUNCHER} '{GAME_PATH}/D2R.exe' -w -username {USERNAME} -password {PASSWORD} -address {REGION}
"""

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.+]+')


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
        return Path(
            self.settings.wineprefix,
            self.normalize_username_name(),
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
            USERNAME=self.account.username,
            PASSWORD=self.account.password,
            REGION=self.account.region.value,
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
            s = f.write(self.render_start_script())
            logger.debug(f"Start script {self.start_script_path} saved [{s} bytes]")
        return True

    def normalize_username_name(self, delim: str = "-"):
        text = unidecode.unidecode(self.account.username)
        result: list[str] = []
        for word in _punct_re.split(text.lower()):
            if word:
                result.append(word)
        return str(delim.join(result))
