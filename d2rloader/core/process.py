import sys

if sys.platform == "linux":
    from .platform_linux.process import ProcessManager
else:
    from .platform_windows.process import ProcessManager  # noqa: F401
