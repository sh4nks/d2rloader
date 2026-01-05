import subprocess

from loguru import logger


def get_window_list() -> list[str]:
    try:
        windows = (
            subprocess.check_output(["wmctrl", "-lp"])
            .decode("utf-8")
            .strip()
            .splitlines()
        )
    except subprocess.CalledProcessError as e:
        logger.error("Couldn't call 'wmctrl -lp'", e)
        return []
    return windows


def get_window_by_title(title: str):
    windows = get_window_list()
    if len(windows) < 1:
        return (None, None)

    for wm_id in windows:
        window_id, _, window_pid, _, window_title = wm_id.split(sep=None, maxsplit=4)
        if title == window_title:
            return (window_id, window_pid)

    return (None, None)


def get_window_by_pid(pid: int):
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


def set_window_title(pid: int, title: str):
    window_id, _ = get_window_by_pid(pid)
    if window_id is None:
        return

    logger.debug(f"Updating title for window id '{window_id}' to '{title}'")
    subprocess.Popen(["wmctrl", "-i", "-r", window_id, "-N", title])  # pyright: ignore[reportUnusedCallResult]
