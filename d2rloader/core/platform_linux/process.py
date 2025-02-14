from loguru import logger
from PySide6.QtCore import QObject, QThreadPool, Signal

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
        self.threadpool: QThreadPool = QThreadPool()

    def start(self, account: Account):
        worker = Worker(self._start_instance, account)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.success.connect(self._handle_worker_success)
        self.threadpool.start(worker)

    def kill(self, pid: int):
        pass

    def _handle_worker_error(self, err: tuple[ProcessingError, str]):
        msg, *_ = err[0].args
        logger.error(f"Could not start instance due to: {msg}")
        self.process_error.emit(None, msg)

    def _handle_worker_success(self, result: tuple[bool, Account | None, int]):
        logger.info(f"Instance started and user logged in: {result[0]}")
        self.process_finished.emit(result[0], result[1], result[2])

    def _start_instance(self, account: Account):
        raise NotImplementedError("ProcessManager for Linux/Wine is not yet implemented")
