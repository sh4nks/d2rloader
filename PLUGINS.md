# D2RLoader's Plugin API

Yes, there even exists a Plugin API for this loader!

## Hooks

If more hooks are required for your plugin, feel free to create a new issue!
At the moment there are 3 hooks implemented:

- ``d2rloader_mainwindow_plugin_menu(d2rloader: "D2RLoaderState", parent: QObject, menu: QMenuBar)``

    Hook for adding a new entry to the QMenu item.

- ``d2rloader_main_tabbar(d2rloader: "D2RLoaderState", tabbar: QTabWidget)``

    Hook for extending the main tabbar

- ``d2rloader_info_tabbar(d2rloader: "D2RLoaderState", tabbar: QTabWidget)``

    Hook for extending the info tabbar


# How To

First you gotta select your plugins directory. For this go to "File -> Settings -> Advanced Settings"
By default it will be next to the ``_internal`` directory but it wont exist - so create it!

Then, create inside the ``plugins`` directory a new directory and inside this directory create a "package" directory:
```
d2rloader-plugin-example (Folder)
- plugin.json (File - REQUIRED)
- example_plugin (Folder - REQUIRED)
-- __init__.py (define your hooks here)
-- ... other python files or sub-packages
```

File: ``plugin.json``
```json
{
    "name": "Example Plugin",
    "license": "",
    "author": "",
    "required_d2rloader_version": "1.3.0",
    "package": "example_plugin" // Must match the name of your package directory
}
```

File: ``__init__.py``
```python
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMenuBar, QTabWidget
from d2rloader.core.state import D2RLoaderState
from d2rloader.core.plugins.markers import hookimpl
from d2rloader.ui.utils import create_action


@hookimpl
def d2rloader_mainwindow_plugin_menu(d2rloader: D2RLoaderState, parent: QObject, menu: QMenuBar):
    example_plugin_menu = menu.addMenu("Example Plugin")
    example_plugin_menu.addAction(create_action(parent, "Test", None))

@hookimpl
def d2rloader_main_tabbar(d2rloader: D2RLoaderState, tabbar: QTabWidget):
    example_plugin_tab = ExamplePluginTab()
    tabbar.addTab(example_plugin_tab, "Example Plugin Tab")
```

## Packaging

Now this part is a bit tricky. D2RLoader includes the complete Python Standard Library and then some (look at the pyproject.toml to see which dependencies are used).

If your plugin requires a dependency that is not provided by D2RLoader you can "vendor" it.

I have successfully used [vendoring](https://github.com/pradyunsg/vendoring) for this.

Example ``pyproject.toml`` for a plugin with vendoring:
```toml
[project]
name = "d2rloader-plugin-example"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = []
requires-python = ">=3.12"
dependencies = [
    "d2rloader @ git+https://github.com/sh4nks/d2rloader@dev",
    "pyautogui",
    "pygetwindow",
    "keyboard",
]

[dependency-groups]
dev = [
    "vendoring>=1.2.0",
]
build = ["hatch"]


[project.scripts]
d2rloader-plugin-example = "example_plugin:main"

[project.entry-points."d2rloader.plugins"]
example_plugin = "example_plugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.vendoring]
destination = "example_plugin/_vendor/"
requirements = "example_plugin/_vendor/vendor.txt"
namespace = "example_plugin._vendor"

protected-files = ["__init__.py", "README.rst", "vendor.txt", "LICENSE.txt"]
patches-dir = "tools/vendoring/patches"

[tool.vendoring.transformations]
substitute = [
  # pyrect is dependency of a dependency
  { match='pyrect', replace="example_plugin._vendor.pyrect" },
]

[tool.vendoring.license.fallback-urls]
PyGetWindow = "https://github.com/asweigart/PyGetWindow/blob/master/LICENSE.txt"

[tool.hatch.build.targets.wheel]
packages = ["example_plugin"]

[tool.hatch.metadata]
allow-direct-references = true

[tool.basedpyright]
include = ["example_plugin"]
exclude = ["**/node_modules", "**/__pycache__"]
defineConstant = { DEBUG = true }
reportIgnoreCommentWithoutRule = false
reportMissingImports = "error"
reportMissingTypeStubs = false
reportUnusedCallResult = false
reportUnannotatedClassAttribute = false
reportAny = false
reportExplicitAny = false
```

Now run ``vendoring sync`` to synchronize the dependencies.

## Linux

If you have installed D2RLoader with your package manager, you can create a installable version of your plugin and set the appropriate entrypoint ``d2rloader.plugins``. D2RLoader will now find your plugin. You don't need to vendor anything this way (Year of the Linux Desktop?).
