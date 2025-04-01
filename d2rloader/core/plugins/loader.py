import json
import os

from loguru import logger
from pluggy import PluginManager

from d2rloader.core.plugins import hookspec
from d2rloader.core.plugins.imptools import import_path


class PluginError(Exception):
    pass


class PluginFilesystemLoader:
    def __init__(self, manager: PluginManager, path: str | None = None):
        self.manager: PluginManager = manager
        self.loaded_plugins: list[str] = []

        if path is None or not os.path.exists(path):
            logger.info(
                "Not loading any plugins as the plugin path is not defined or does not exist"
            )
        else:
            logger.info(f"Loading plugins from: {path}")
            self.load_plugins(path)

    def load_plugins(self, path: str):
        for item in os.listdir(path):
            plugin_path = os.path.join(path, item)
            plugin_info_path = os.path.join(plugin_path, "plugin.json")

            # plugin already loaded
            if plugin_info_path in self.loaded_plugins:
                continue

            plugin_package_path = self._validate_plugin(plugin_path, plugin_info_path)
            # plugin not valid - no plugin package path returned
            if plugin_package_path is None:
                continue

            plugin = import_path(plugin_package_path)
            # plugin already registered or is blocked
            if (
                plugin is None
                or self.manager.get_plugin(item) is not None
                or self.manager.is_blocked(item)
            ):
                continue

            self.loaded_plugins.append(plugin_info_path)
            logger.debug(f"Loaded plugin '{item}'")
            self.manager.register(plugin)

    def _validate_plugin(self, plugin_path: str, plugin_info_path: str):
        if not os.path.exists(plugin_info_path):
            logger.error(
                f"Plugin metadata 'plugin.json' doesn't exist for plugin {plugin_info_path}"
            )
            return None

        plugin_info: dict[str, str] | None = None
        with open(plugin_info_path) as fd:
            plugin_info = json.load(fd)

        if not plugin_info:
            logger.error(
                f"Couldn't load plugin.json metadata for plugin {plugin_info_path}"
            )
            return None

        plugin_package: str | None = None
        try:
            plugin_package = plugin_info["package"]
        except KeyError:
            pass

        if not plugin_package:
            logger.error(
                f"Couldn't get 'package' from plugin.json for plugin {plugin_info_path}"
            )
            return None

        plugin_package_path = os.path.join(plugin_path, plugin_package)
        if not os.path.exists(plugin_package_path):
            logger.error(
                f"Plugin package path doesn't exist on filesystem: {plugin_package_path}"
            )
            return None

        if not os.path.exists(os.path.join(plugin_package_path, "__init__.py")):
            logger.error(
                "Plugin package is not a valid Python module - __init__.py is missing!"
            )
            return None

        return plugin_package_path


def register_plugins(path: str | None = None):
    pm = PluginManager("d2rloader")
    pm.add_hookspecs(hookspec)
    pm.load_setuptools_entrypoints("d2rloader.plugins")

    if path is not None and os.path.exists(path):
        filesystem_loader = PluginFilesystemLoader(pm, path)
        filesystem_loader.load_plugins(path)
    return pm
