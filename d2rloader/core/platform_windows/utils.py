import win32api
import win32con
import win32gui
import win32pdhutil
from loguru import logger

from d2rloader.constants import D2R_PROCESS_TITLE, WINDOW_TITLE_FORMAT
from d2rloader.models.account import Account


def change_window_title(account: Account, pid: int):
    win32gui.EnumWindows(window_title_callback, account)


def window_title_callback(hwnd: int, account: Account):
    title = win32gui.GetWindowText(hwnd)

    if title == D2R_PROCESS_TITLE:
        window_title = WINDOW_TITLE_FORMAT.format(
            account.username, account.region.value
        )
        logger.debug(f"Setting Window Handle '{hwnd}' to '{window_title}'")
        win32gui.SetWindowText(hwnd, window_title)  # pyright: ignore


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
