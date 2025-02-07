import functools
import os
import re
import subprocess
from time import sleep
import winreg

import win32api
import win32con
import win32crypt
import win32gui
import win32pdhutil
from loguru import logger
from PySide6.QtCore import QObject, QProcess, Signal, Slot

from d2rloader.models.account import Account, Region
from d2rloader.models.setting import Setting

REG_BATTLE_NET_PATH = (
    "SOFTWARE\\Blizzard Entertainment\\Battle.net\\Launch Options\\OSI"
)

ENTROPY = bytes([0xc8, 0x76, 0xf4, 0xae, 0x4c, 0x95, 0x2e, 0xfe, 0xf2, 0xfa, 0x0f, 0x54, 0x19, 0xc0, 0x9c,0x43])

WINDOW_TITLE_FORMAT = "{0} ({1})"

UPDATE_HANDLE = "DiabloII Check For Other Instances"


# TODO: Move this off of the mainloop to not block the GUI
class ProcessManager(QObject):
    process_finished: Signal = Signal(Account, int)
    process_error: Signal = Signal(Account, str)

    def __init__(self, settings: Setting) -> None:
        super().__init__()
        self.settings: Setting = settings
        self.handle: HandleManager = HandleManager(self.settings)

    def start_instance(self, qprocess: QProcess, account: Account):
        cmd = os.path.join(self.settings.game_path, "D2R.exe")

        if not os.path.exists(cmd):
            msg = f"Could not find 'D2R.exe' in '{self.settings.game_path}'"
            logger.error(msg)
            self.process_error.emit(account, msg)
            return

        # TODO: Implement password based authentication
        if account.token is None:
            msg = "Token-based authentication is selected but no token was provided."
            logger.error(msg)
            self.process_error.emit(account, msg)
            self.process_error.disconnect()
            return

        protected_token: bytes | None = protect_data(account.token)
        if protected_token is None:
            msg = "Could not encrypt token"
            logger.error(msg)
            self.process_error.emit(account, msg)
            self.process_error.disconnect()
            return

        update_region_value(account.region)
        update_web_token_value(protected_token)

        params: list[str] = []
        if account.params is not None:
            params = [param.strip() for param in account.params.split(" ")]

        self.handle.kill(silent=True)
        qprocess.started.connect(
            functools.partial(self._process_start_finished, protected_token, account, qprocess)
        )
        qprocess.start(self.settings.game_path + "/D2R.exe", params)
        qprocess.waitForStarted(5000)

    @Slot()  # pyright:ignore
    def _process_start_finished(self, token: bytes, account: Account, qprocess: QProcess):
        logger.debug(f"process id: {qprocess.processId()}")
        sleep(1)  # give D2R a chance to start
        change_window_title(account, qprocess.processId())
        sleep(0.5)
        self.handle.kill()
        logged_in = False

        timeout = 300  # abort after waiting for 5 minutes
        counter = 0
        wait_time = 0.5
        while not logged_in:
            logged_in = is_changed_web_token(token)
            counter += wait_time
            sleep(wait_time)

            if timeout == counter:
                break

        logger.debug(
            f"Waited for {counter} seconds till until log in ({logged_in}) or timeout."
        )

        if logged_in:
            self.process_finished.emit(account, qprocess.processId())
        else:
            self.process_finished.emit(None, qprocess.processId())
        self.process_finished.disconnect()


class HandleManager:
    _search_regex: re.Pattern[str] = re.compile(
        r"pid:\s+(?P<d2pid>\d+)\s+type:\s+Event\s+(?P<eventHandle>\w+):"
    )

    def __init__(self, settings: Setting) -> None:
        self.settings: Setting = settings

    def search(self):
        handle_search_args = [
            "-accepteula",
            "-a",
            "-p",
            "D2R.exe",
            "Check For Other Instances",
            "-nobanner",
        ]
        if not self.settings.handle_path:
            logger.error("HANDLE_PATH not set!")
            return

        cmd = [self.settings.handle_path, *handle_search_args]
        output = subprocess.run(cmd, capture_output=True)
        matches = self._search_regex.search(output.stdout.decode("utf-8"))
        if matches is None:
            return None
        return matches.groupdict()

    def kill(self, silent: bool = False):
        process = self.search()

        if (
            process is None
            or process.get("d2pid", None) is None
            or process.get("eventHandle", None) is None
        ):
            if not silent:
                logger.error("D2R.exe PID or eventHandle not found!")

            return False

        handle_kill_args = [
            "-c",
            process["eventHandle"],
            "-p",
            process["d2pid"],
            "-y",
        ]
        cmd = [self.settings.handle_path, *handle_kill_args]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            if not silent:
                logger.error(f"Couldn't kill handle: {result.stdout}")
            return False
        return True


def change_window_title(account: Account, pid: int):
    win32gui.EnumWindows(window_title_callback, account)


def window_title_callback(hwnd: int, account: Account):
    title = win32gui.GetWindowText(hwnd)

    if title == "Diablo II: Resurrected":
        window_title = WINDOW_TITLE_FORMAT.format(
            account.username, account.region.value
        )
        logger.debug(f"Setting Window Handle '{hwnd}' to '{window_title}'")
        # fmt: off
        win32gui.SetWindowText(
            hwnd,  # pyright: ignore
            WINDOW_TITLE_FORMAT.format(account.username, account.region.value),
        )
        # fmt: on


def kill_process_by_name(procname: str):
    try:
        win32pdhutil.GetPerformanceAttributes("Process", "ID Process", procname)
    except:
        pass

    pids: list[int] = win32pdhutil.FindPerformanceAttributesByName(procname)

    try:
        pids.remove(win32api.GetCurrentProcessId())
    except ValueError:
        pass

    if len(pids) == 0:
        logger.error(f"Can't find {procname}")
        return

    for pid in pids:
        logger.info(f"Killing {procname} with pid {pid}")
        kill_process_by_pid(pid)


def kill_process_by_pid(pid: int):
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
    win32api.TerminateProcess(handle, 0)
    win32api.CloseHandle(handle)


def protect_data(token: str):
    protected_token: bytes = win32crypt.CryptProtectData(bytes(token, "utf-8"), None, ENTROPY)
    return protected_token or None


def update_region_value(value: Region):
    shortcode = value.value.split(".")[0].upper()  # eu.actual.battle.net -> EU
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_BATTLE_NET_PATH, 0, winreg.KEY_WRITE
    ) as key:
        logger.debug(f"Setting REGION to: {shortcode}")
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
