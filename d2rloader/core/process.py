import os
import re
import subprocess
from time import sleep

import psutil
from loguru import logger
from PySide6.QtCore import QObject, QThreadPool, Signal

from d2rloader.constants import UPDATE_HANDLE
from d2rloader.core.process_utils import change_window_title
from d2rloader.core.regedit import (
    is_changed_web_token,
    protect_data,
    update_region_value,
    update_web_token_value,
)
from d2rloader.core.worker import Worker
from d2rloader.models.account import Account
from d2rloader.models.setting import Setting


class ProcessingError(Exception):
    pass


class ProcessManager(QObject):
    process_finished: Signal = Signal(bool, Account, int)
    process_error: Signal = Signal(Account, str)

    def __init__(self, parent: QObject, settings: Setting) -> None:
        super().__init__()
        self.settings: Setting = settings
        self.threadpool = QThreadPool()
        self.handle: HandleManager = HandleManager(self.settings)
        self.threadpool: QThreadPool = QThreadPool()

    def start(self, account: Account):
        worker = Worker(self._start_instance, account)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.success.connect(self._handle_worker_success)
        self.threadpool.start(worker)

    def _handle_worker_error(self, err: tuple[ProcessingError, str]):
        msg, *_ = err[0].args
        logger.error(f"Could not start instance due to: {msg}")
        self.process_error.emit(None, msg)

    def _handle_worker_success(self, result: tuple[bool, Account | None, int]):
        logger.info(f"Instance started and user logged in: {result[0]}")
        self.process_finished.emit(result[0], result[1], result[2])

    def _start_instance(self, account: Account):
        logger.debug("_start_instance")
        cmd = os.path.join(self.settings.game_path, "D2R.exe")

        protected_token: bytes | None = self._validate_start(cmd, account)
        if not protected_token:
            return

        update_region_value(account.region)
        update_web_token_value(protected_token)

        params: list[str] = []
        if account.params is not None:
            params = [param.strip() for param in account.params.split(" ")]

        self.handle.kill(silent=True)
        try:
            proc = subprocess.Popen([cmd, *params])
            logger.trace(f"Launching instance: {[cmd, *params]}")
        except OSError | ValueError as e:
            logger.error(e)
            raise ProcessingError(f"Error occured during executing {cmd}", e)

        logger.debug(f"{proc.pid}")
        if proc.pid:
            return self._handle_instance_start(protected_token, account, proc.pid)

        raise ProcessingError("No PID returned")

    def _validate_start(self, cmd: str, account: Account):
        if not os.path.exists(cmd):
            raise ProcessingError(
                f"Could not find 'D2R.exe' in '{self.settings.game_path}'"
            )

        # TODO: Implement password based authentication
        if account.token is None:
            raise ProcessingError(
                "Token-based authentication is selected but no token was provided."
            )

        protected_token: bytes | None = protect_data(account.token)
        if protected_token is None:
            raise ProcessingError("Could not encrypt token")

        return protected_token

    def _handle_instance_start(self, token: bytes, account: Account, pid: int):
        logger.debug(f"process id: {pid}")
        sleep(1)  # give D2R a chance to start
        change_window_title(account, pid)
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

            if timeout == counter or not psutil.pid_exists(pid):
                break

        sleep(0.5)  # make sure pid exists
        if psutil.pid_exists(pid):
            logger.debug(
                f"Waited for {counter} seconds till until log in ({logged_in}) or timeout."
            )
            return logged_in, account, pid

        raise ProcessingError(
            f"Instance closed or killed - pid {pid} doesn't exist anymore"
        )


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
        logger.info(f"Killed handle '{UPDATE_HANDLE}' for pid {process.get('d2pid')}")
        return True
