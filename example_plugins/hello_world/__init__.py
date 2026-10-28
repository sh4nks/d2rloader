from d2rloader.core.plugins.filesystem import FilesystemPlugin as FilesystemPlugin
from loguru import logger
from pluggy import HookimplMarker

impl = HookimplMarker("d2rloader")


@impl
def d2rloader_example_hook(state):
    logger.info(f"logged state from hello world: {state}")
