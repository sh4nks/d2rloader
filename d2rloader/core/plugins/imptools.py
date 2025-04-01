"""
Copyright (c) 2020 Danijar Hafner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Note:
This code is untouched except the formatting by 'ruff' and the added types.
This code was included to make packaging easier on Linux.
"""

from pathlib import Path
from typing import Literal


def import_path(
    path: str | Path,
    name: str | None = None,
    notfound: Literal["error", "ignore"] = "error",
    reload: bool = False,
):
    """
    Import a module from any path on the filesystem.

    Usually, this would be achieved by adding the parent directory of the module
    to `sys.path` or the `PYTHONPATH` environment variable and then importing it
    normally. However, this pollutes Python's import path, which can lead to
    accidentally importing the wrong modules. The function `import_path()` avoids
    this problem by importing a package from a path on the filesystem without
    modifying the Python import path.

    The module can be either a directory containing `__init__.py` or a single
    file.

    Relative paths are resolved relative to the directory of the source file that
    calls `import_path()`.

    ```
    import imptools

    my_module = imptools.import_path('../path/to/my_module')
    ```

    ```
    import imptools

    my_module = imptools.import_path(
        '../path/to/my_module',  # Path to a module directory or single file.
        notfound='error',        # Raise 'error' or 'ignore' if not found.
        reload=False,            # Whether to import if already available.
    )

    import my_module  # Import statement also works.
    ```

    Args:
      path (str or Path): The filesystem path to the module to import. This
        should be either a directory containing an `__init__.py` file or a single
        file with `.py` extension. The path can be relative.
      name (str, optional): A name that is compared to the directory name of
        `path` and must match it. Useful for relative paths.
      notfound (str): A string indicating what to do if the module is not found.
        Values can be `error` to raise an exception or `ignore` to return `None`
        from this function.
      reload (bool): A boolean indicating whether to reload the package if it is
        already loaded.

    Raises:
      ModuleNotFoundError: If `path` does not point to a module or if `name` is
        specified and dose not match the directory name of `path`.

    Returns:
      The module or `None` if it was not found.
    """
    assert notfound in ("error", "ignore")

    import importlib.util
    import inspect
    import pathlib
    import sys

    # Resolve relative path.
    path = pathlib.Path(path).expanduser()
    if not path.is_absolute():
        for info in inspect.stack():
            if info.filename == __file__:
                continue
            break
        script = info.filename
        root = pathlib.Path(script).parent
        path = (root / path).resolve()

    # Skip if the module is already loaded.
    name = name or path.name
    if name in sys.modules and not reload:
        return sys.modules[name]

    # Verify path name against user input.
    if name and path.name != name:
        if notfound == "ignore":
            return None
        raise ModuleNotFoundError(f"Path name {path.name} does not match {name}")

    # Try to find the module.
    for finder in sys.meta_path:
        if not hasattr(finder, "find_spec"):
            continue
        spec = finder.find_spec(name, [str(path.parent)])
        if spec is not None:
            break
    else:
        if notfound == "ignore":
            return None
        raise ModuleNotFoundError(f"No module named {name}", name=name)

    # Import the module.
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
