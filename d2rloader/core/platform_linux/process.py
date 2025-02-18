import os
from pathlib import Path
import signal
import subprocess
from loguru import logger
from PySide6.QtCore import QObject, QThreadPool, Signal

from d2rloader.core.exception import ProcessingError
from d2rloader.core.platform_linux.lutris import LutrisManager
from d2rloader.core.worker import Worker
from d2rloader.models.account import Account, AuthMethod
from d2rloader.models.setting import Setting


class ProcessManager(QObject):
    process_finished: Signal = Signal(bool, Account, int)
    process_error: Signal = Signal(Account, str)

    def __init__(self, parent: QObject, settings: Setting) -> None:
        super().__init__()
        self.settings: Setting = settings
        self.threadpool = QThreadPool()
        self.threadpool: QThreadPool = QThreadPool()

    def start(self, account: Account):
        worker = Worker(self._start_instance, account)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.success.connect(self._handle_worker_success)
        self.threadpool.start(worker)

    def kill(self, pid: int):
        logger.info(f"Killing instance with pid: {pid}")
        os.kill(pid, signal.SIGKILL)

    def _handle_worker_error(self, err: tuple[Exception, str]):
        logger.debug(err)
        msg, *_ = err[0].args
        logger.error(f"Could not start instance due to: {msg}")
        self.process_error.emit(None, msg)

    def _handle_worker_success(self, result: tuple[bool, Account | None, int]):
        logger.info(f"Instance started and user logged in: {result[0]}")
        self.process_finished.emit(result[0], result[1], result[2])

    def _start_instance(self, account: Account):
        lutris = LutrisManager(self.settings, account)
        self._validate_start(account)

        if lutris.save_start_script():
            try:
                with open(lutris.start_script_log_path, "w") as logfile:
                    logger.debug(
                        f"Launching instance: {lutris.start_script_path, account.params}"
                    )
                    proc = subprocess.Popen(["sh", lutris.start_script_path], stderr=logfile)
                    return None, account, proc.pid
            except Exception as e:
                logger.error(e)
                raise ProcessingError(
                    f"Error occured during executing {lutris.start_script_path}", e
                )

    def _validate_start(self, account: Account):
        if not Path(self.settings.game_path, "D2R.exe").exists():
            raise ProcessingError(
                f"Could not find 'D2R.exe' in '{self.settings.game_path}'"
            )

        # TODO: Implement password based authentication
        if account.auth_method == AuthMethod.Token:
            raise ProcessingError(
                "Password-based authentication is not supported under Linux/Wine."
            )

        if (
            len(account.username) == 0
            or account.password is None
            or len(account.password) == 0
        ):
            raise ProcessingError("No username/password provided")
