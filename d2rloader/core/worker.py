import sys
import traceback

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

    def __init__(self, fn, *args, **kwargs):  # pyright: ignore
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn  # pyright: ignore
        self.args = args  # pyright: ignore
        self.kwargs = kwargs  # pyright: ignore
        self.signals: WorkerSignals = WorkerSignals()

    @Slot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)  # pyright: ignore
        except:  # noqa: E722
            _, value = sys.exc_info()[:2]
            self.signals.error.emit((value, traceback.format_exc()))
        else:
            self.signals.success.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
