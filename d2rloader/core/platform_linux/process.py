import subprocess
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING

from d2rloader.constants import WINDOW_TITLE_FORMAT
from d2rloader.core.platform_linux.utils import get_window_by_title, set_window_title

if TYPE_CHECKING:
    from d2rloader.core.state import D2RLoaderState

import psutil
from loguru import logger
from PySide6.QtCore import QObject, QThreadPool, Signal

from d2rloader.core.exception import ProcessingError
from d2rloader.core.platform_linux.umu import UmuManager
from d2rloader.core.worker import Worker
from d2rloader.models.account import Account, AuthMethod


class ProcessManager(QObject):
    process_finished: Signal = Signal(bool, Account, int)
    process_error: Signal = Signal(Account, str)

    def __init__(self, parent: QObject, appstate: "D2RLoaderState") -> None:
        super().__init__()
        self._state: "D2RLoaderState" = appstate
        self.threadpool = QThreadPool()
        self.threadpool: QThreadPool = QThreadPool()

    def start(self, account: Account):
        worker = Worker(self._start_instance, account)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.success.connect(self._handle_worker_success)
        self.threadpool.start(worker)

    def kill(self, pid: int):
        logger.info(f"Killing instance with pid: {pid}")
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    def find_active_instances(self, accounts: list[Account]) -> dict[int, Account]:
        instances: dict[int, Account] = {}
        for account in accounts:
            title = WINDOW_TITLE_FORMAT.format(
                account.displayname, account.region.value
            )
            window_id, window_pid = get_window_by_title(title)
            if window_id is None or window_pid is None:
                continue

            p_parents = psutil.Process(int(window_pid)).parents()
            pid = None
            for p in p_parents:
                if p.name() == "srt-bwrap":
                    pid = p.pid
                    break

            if pid is not None:
                logger.info(f"Running instance found: {title}")
                instances[pid] = account

        return instances

    def _handle_worker_error(self, err: tuple[Exception, str]):
        logger.debug(err)
        msg, *_ = err[0].args
        logger.error(f"Could not start instance due to: {msg}")
        self.process_error.emit(None, msg)

    def _handle_worker_success(self, result: tuple[bool, Account | None, int]):
        logger.debug(f"Instance started: {result}")
        self.process_finished.emit(result[0], result[1], result[2])

    def _start_instance(self, account: Account):
        umu_manager = UmuManager(self._state.settings.data, account)
        game_settings = self._state.game_settings.get_game_settings(account)
        self._validate_start(account)

        if umu_manager.save_start_script():
            try:
                with open(umu_manager.start_script_log_path, "w") as logfile:
                    game_settings.set_account_game_settings()
                    logger.info(
                        f"Launching instance: {umu_manager.start_script_path.absolute()}"
                    )
                    logger.debug(f"Using GAME_PATH: {game_settings.settings.game_path}")
                    proc = subprocess.Popen(
                        ["sh", umu_manager.start_script_path], stderr=logfile
                    )

                    if self._is_d2r_started(proc.pid):
                        self._rename_window_title(proc.pid, account)

                    return None, account, proc.pid
            except Exception as e:
                logger.error(e)
                raise ProcessingError(
                    f"Error occured during executing {umu_manager.start_script_path}", e
                )

    def _validate_start(self, account: Account):
        if not Path(self._state.settings.data.game_path, "D2R.exe").exists():
            raise ProcessingError(
                f"Could not find 'D2R.exe' in '{self._state.settings.data.game_path}'"
            )

        if account.auth_method == AuthMethod.Token:
            raise ProcessingError(
                "Token-based authentication is not supported under Linux/Wine."
            )

        if (
            len(account.email) == 0
            or account.password is None
            or len(account.password) == 0
        ):
            raise ProcessingError("No email/password provided")

    def _is_d2r_started(self, parent_pid: int):
        parent = psutil.Process(parent_pid)
        pid = None
        timeout = 30  # abort after 30 seconds
        counter = 0
        while True:
            pid = self._get_d2r_exe_pid(None, parent)
            if pid is not None:
                logger.debug("D2R.exe process found!")
                break
            sleep(0.5)

            counter += 0.5
            if counter == timeout:
                logger.error("D2R.exe not found after looking for it for 30 seconds")
                break

        return pid is not None

    def _get_d2r_exe_pid(
        self, parent_pid: int | None, process: psutil.Process | None = None
    ):
        if parent_pid is None and process is None:
            return None

        if parent_pid and process:
            return None

        if parent_pid is not None:
            parent = psutil.Process(parent_pid)
        elif process is not None:
            parent = process
        else:
            return None

        for child in parent.children(recursive=True):
            if child.name() == "Main":
                return child
        return None

    def _rename_window_title(self, pid: int, account: Account):
        # Once Wine Wayland is the only thing that works we gotta reinvestigate how to
        # fix this. Perhaps it's possible to change it directly in Wine?
        # And then we can use something like
        # this https://github.com/jmazzola/window-title-spoofer/tree/master
        #
        # For now, with XWayland we can use xdotool or wmctrl to change
        # the window title
        process = self._get_d2r_exe_pid(pid)
        if process is None:
            logger.error(f"Couldn't set window title for pid {pid}. No process found.")
            return

        window_title = WINDOW_TITLE_FORMAT.format(
            account.displayname, account.region.value
        )
        sleep(1)
        set_window_title(process.pid, window_title)
