import os

import imptools
from loguru import logger
from pluggy import PluginManager

from d2rloader.core.plugins import spec


class PluginError(Exception):
    pass


class PluginFilesystemLoader:
    def __init__(self, manager: PluginManager, path: str | None = None):
        self.manager: PluginManager = manager

        if path is None or not os.path.exists(path):
            logger.info(
                "Not loading any plugins as the plugin path is not defined or does not exist"
            )
        else:
            self.load_plugins(path)

    def load_plugins(self, path: str):
        logger.info(f"Loading plugins from: {path}")

        for item in os.listdir(path):
            if os.path.isdir(os.path.join(path, item)) and os.path.exists(
                os.path.join(path, item, "__init__.py")
            ):
                PLUGIN_PATH = os.path.realpath(os.path.join(path, item))
                plugin = imptools.import_path(PLUGIN_PATH)

                if (
                    plugin is None
                    or self.manager.get_plugin(item) is not None
                    or self.manager.is_blocked(item)
                ):
                    continue

                logger.debug(f"Loaded plugin '{item}'")
                self.manager.register(plugin)


def register_plugins(path: str | None = None):
    pm = PluginManager("d2rloader")
    pm.add_hookspecs(spec)
    pm.load_setuptools_entrypoints("d2rloader.plugins")

    if path is not None and os.path.exists(path):
        filesystem_loader = PluginFilesystemLoader(pm, path)
        filesystem_loader.load_plugins(path)
    return pm
