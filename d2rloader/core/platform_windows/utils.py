from ctypes import windll

import win32api
import win32con
import win32gui
import win32pdhutil
import win32ui
import win32com.client
from loguru import logger
from PIL import Image

from d2rloader.constants import D2R_PROCESS_TITLE, WINDOW_TITLE_FORMAT
from d2rloader.core.exception import ProcessingError
from d2rloader.models.account import Account


def change_window_title(account: Account, pid: int):
    win32gui.EnumWindows(window_title_callback, account)


def window_title_callback(hwnd: int, account: Account):
    title = win32gui.GetWindowText(hwnd)

    if title == D2R_PROCESS_TITLE:
        window_title = WINDOW_TITLE_FORMAT.format(
            account.displayname, account.region.value
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
    try:
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)
    except Exception:
        raise ProcessingError(f"Couldn't kill pid {pid}")


def get_window_size(hwnd: int):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    return (width, height)


def send_key():
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys("{ENTER}", 0)


def take_screenshot(hwnd: int):
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    width, height = get_window_size(hwnd)

    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(save_bitmap)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
    bmpinfo = save_bitmap.GetInfo()
    bmpstr = save_bitmap.GetBitmapBits(True)
    im = Image.frombuffer(
        "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1
    )

    win32gui.DeleteObject(save_bitmap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if result == 1:
        return im

    im.close()
    return None
