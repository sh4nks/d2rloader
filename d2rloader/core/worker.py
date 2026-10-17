import sys
import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are::
        finished
            No data

        error
            tuple (value, traceback.format_exc())

        success
            object data returned from processing, anything
    """

    finished: Signal = Signal()
    error: Signal = Signal(tuple)
    success: Signal = Signal(object)


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__[**P](
        self, fn: Callable[P, object], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn: Callable[..., object] = fn
        self.args: tuple[object, ...] = args
        self.kwargs: dict[str, object] = kwargs
        self.signals: WorkerSignals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:  # noqa: E722
            _, value = sys.exc_info()[:2]
            self.signals.error.emit((value, traceback.format_exc()))
        else:
            self.signals.success.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
