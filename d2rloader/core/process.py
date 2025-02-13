import sys

if sys.platform == 'linux':
    from .process_linux.manager import ProcessManager
else:
    from .process_windows.manager import ProcessManager  # noqa: F401
