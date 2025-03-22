import os
import re
import subprocess
from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from d2rloader.core.core import D2RLoaderState

import psutil
from loguru import logger
from PySide6.QtCore import QObject, QThreadPool, Signal

from d2rloader.constants import UPDATE_HANDLE
from d2rloader.core.exception import ProcessingError
from d2rloader.core.worker import Worker
from d2rloader.models.account import Account, AuthMethod
from d2rloader.models.setting import Setting

from .regedit import (
    get_web_token,
    is_changed_web_token,
    protect_data,
    update_region_value,
    update_web_token_value,
)
from .utils import (
    change_window_title,
    kill_process_by_pid,
)


class ProcessManager(QObject):
    process_finished: Signal = Signal(bool, Account, int)
    process_error: Signal = Signal(Account, str)

    def __init__(self, parent: QObject, appstate: "D2RLoaderState") -> None:
        super().__init__()
        self._state: "D2RLoaderState" = appstate
        self.threadpool = QThreadPool()
        self.handle: HandleManager = HandleManager(self._state.settings.data)
        self.threadpool: QThreadPool = QThreadPool()

    def kill(self, pid: int):
        kill_process_by_pid(pid)

    def start(self, account: Account):
        worker = Worker(self._start_instance, account)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.success.connect(self._handle_worker_success)
        self.threadpool.start(worker)

    def find_active_instances(self, accounts: list[Account]):
        instances: dict[int, Account] = {}
        return instances

    def _handle_worker_error(self, err: tuple[ProcessingError, str]):
        msg, *_ = err[0].args
        logger.error(f"Could not start instance due to: {msg}")
        self.process_error.emit(None, msg)

    def _handle_worker_success(self, result: tuple[bool, Account | None, int]):
        logger.success("Instance started successfully")
        self.process_finished.emit(result[0], result[1], result[2])

    def _start_instance(self, account: Account):
        cmd = os.path.join(self._state.settings.data.game_path, "D2R.exe")
        game_settings = self._state.game_settings.get_game_settings(account)

        if not os.path.exists(cmd):
            raise ProcessingError(
                f"Could not find 'D2R.exe' in '{self._state.settings.data.game_path}'"
            )

        params: list[str] = []
        if account.params is not None:
            params = [param.strip() for param in account.params.split(" ")]

        if account.auth_method == AuthMethod.Token:
            self._process_auth_token(account, params)
        elif account.auth_method == AuthMethod.Password:
            self._process_auth_password(account, params)

        game_settings.set_account_game_settings()

        self.handle.kill(silent=True)
        try:
            proc = subprocess.Popen(
                [cmd, *params], creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.debug(
                f"Launching instance with auth method {account.auth_method.value} and parameters: {' '.join([cmd, *self._log_params(params)])}"
            )
        except OSError | ValueError as e:
            logger.error(e)
            raise ProcessingError(f"Error occured during executing {cmd}", e)

        if proc.pid:
            return self._handle_instance_start(account, proc.pid)

        raise ProcessingError("No PID returned")

    def _process_auth_token(self, account: Account, params: list[str]):
        if account.token is None:
            raise ProcessingError(
                "Token authentication is selected but no token was provided."
            )

        protected_token: bytes | None = protect_data(account.token)
        if protected_token is None:
            raise ProcessingError("Could not encrypt token")

        update_region_value(account.region)
        update_web_token_value(protected_token)
        params.extend(["-uid", "osi"])

    def _process_auth_password(self, account: Account, params: list[str]):
        if not account.password:
            raise ProcessingError(
                "Password authentication is selected but no password was provided."
            )

        params.extend(
            [
                "-username",
                account.email,
                "-password",
                account.password,
                "-address",
                account.region.value,
            ]
        )

    def _handle_instance_start(self, account: Account, pid: int):
        logger.trace(f"process id: {pid}")
        sleep(1)  # give D2R a chance to start
        change_window_title(account, pid)
        sleep(0.5)
        self.handle.kill()

        if account.auth_method == AuthMethod.Password:
            return True, account, pid

        logged_in = False

        timeout = 300  # abort after waiting for 5 minutes
        counter = 0
        wait_time = 0.5

        token = get_web_token()
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

    def _log_params(self, params: list[str]):
        try:
            idx = params.index("-password")
            params[idx + 1] = "*****"
            return params
        except ValueError:
            return params


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
        output = subprocess.run(
            cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
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
        result = subprocess.run(
            cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode != 0:
            if not silent:
                logger.error(f"Couldn't kill handle: {result.stdout}")
            return False
        logger.info(f"Killed handle '{UPDATE_HANDLE}' for pid {process.get('d2pid')}")
        return True
