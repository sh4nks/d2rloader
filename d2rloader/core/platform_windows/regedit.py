import winreg
from typing import cast

import win32crypt
from loguru import logger

from d2rloader.constants import ENTROPY, REG_BATTLE_NET_PATH
from d2rloader.models.account import Region


def protect_data(token: str):
    protected_token: bytes = win32crypt.CryptProtectData(
        bytes(token, "utf-8"), None, ENTROPY
    )
    if not protected_token:
        return None
    return cast(bytes, protected_token)


def update_region_value(value: Region):
    shortcode = value.value.split(".")[0].upper()  # eu.actual.battle.net -> EU
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_BATTLE_NET_PATH, 0, winreg.KEY_WRITE
    ) as key:
        logger.trace(f"Setting REGION to: {shortcode}")
        try:
            winreg.SetValueEx(key, "REGION", 1, winreg.REG_SZ, shortcode)
        except Exception as e:
            logger.error(f"Couldn't set registry key 'REGION' to '{shortcode}'", e)
            raise e


def update_web_token_value(value: bytes):
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_BATTLE_NET_PATH, 0, winreg.KEY_WRITE
    ) as key:
        try:
            winreg.SetValueEx(key, "WEB_TOKEN", 1, winreg.REG_BINARY, value)
        except Exception as e:
            logger.error("Couldn't set registry key 'WEB_TOKEN'", e)
            raise e


def get_web_token() -> bytes:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_BATTLE_NET_PATH, 0, winreg.KEY_READ
    ) as key:
        try:
            value = winreg.QueryValueEx(key, "WEB_TOKEN")
        except Exception as e:
            logger.error("Couldn't read registry key 'WEB_TOKEN'", e)
            raise e

        if not value:
            return b""

        return value[0]

def is_changed_web_token(previous_value: bytes):
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_BATTLE_NET_PATH, 0, winreg.KEY_READ
    ) as key:
        try:
            value = winreg.QueryValueEx(key, "WEB_TOKEN")
        except Exception as e:
            logger.error("Couldn't read registry key 'WEB_TOKEN'", e)
            raise e

        if not value:
            return False

        return value[0] != previous_value
