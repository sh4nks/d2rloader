from loguru import logger
from d2rloader.core.core import D2RLoaderState
from d2rloader.ui.main import D2RLoaderUI


class D2RLoader:
    def __init__(self):
        self.state: D2RLoaderState = D2RLoaderState()
        self.ui: D2RLoaderUI = D2RLoaderUI(self.state)

    def run(self):
        logger.debug(f"{self.state}")
        self.ui.run()


def main():
    app = D2RLoader()
    app.run()
