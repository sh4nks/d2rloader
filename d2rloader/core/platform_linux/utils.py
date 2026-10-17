import functools
import os
import shutil
import subprocess
from pathlib import Path

from loguru import logger


@functools.cache
def find_wmctrl() -> str | None:
    wmctrl = shutil.which("wmctrl")
    if wmctrl is None:
        logger.warning(
            "'wmctrl' not found. Running instances can't be detected and "
            "window titles can't be changed."
        )
    return wmctrl


def get_window_list() -> list[str]:
    wmctrl = find_wmctrl()
    if wmctrl is None:
        return []

    try:
        windows = (
            subprocess.check_output([wmctrl, "-lp"])
            .decode("utf-8")
            .strip()
            .splitlines()
        )
    except (subprocess.CalledProcessError, OSError) as e:
        logger.error(f"Couldn't call 'wmctrl -lp': {e}")
        return []
    return windows


def get_window_by_title(title: str) -> tuple[str, str] | tuple[None, None]:
    windows = get_window_list()
    if len(windows) < 1:
        return (None, None)

    for wm_id in windows:
        window_id, _, window_pid, _, window_title = wm_id.split(sep=None, maxsplit=4)
        if title == window_title:
            return (window_id, window_pid)

    return (None, None)


def get_window_by_pid(pid: int) -> tuple[str, str] | tuple[None, None]:
    windows = get_window_list()
    if len(windows) < 1:
        return (None, None)

    str_pid = str(pid)
    for wm_id in windows:
        if str_pid in wm_id:
            window_id, _, window_pid, _, _ = wm_id.split(sep=" ", maxsplit=4)
            return (window_id, window_pid)

    logger.debug(f"No windows found for pid {pid}")
    return (None, None)


def set_window_title(pid: int, title: str) -> None:
    window_id, _ = get_window_by_pid(pid)
    if window_id is None:
        return

    logger.debug(f"Updating title for window id '{window_id}' to '{title}'")
    subprocess.Popen(["wmctrl", "-i", "-r", window_id, "-N", title])  # pyright: ignore[reportUnusedCallResult]


def run_wine_cmd(
    cmd: list[Path | str], wineprefix: str | Path
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        cmd,
        capture_output=True,
        env={
            **os.environ,
            "PROTON_VERB": "runinprefix",
            "WINEDEBUG": "-all",
            "WINEPREFIX": f"{wineprefix}",
        },
    )
