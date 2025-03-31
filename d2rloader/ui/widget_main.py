from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QTabWidget,
    QWidget,
)

from d2rloader.core.state import D2RLoaderState
from d2rloader.ui.widget_main_table import D2RLoaderTableWidget


class MainTabsWidget(QTabWidget):
    refresh: Signal = Signal()

    def __init__(self, d2rloader: D2RLoaderState, parent: QWidget | None = None):
        """Initialize the MainTabsWidget."""
        super().__init__(parent)
        self.d2rloader: D2RLoaderState = d2rloader
        self.d2rloader_table: D2RLoaderTableWidget = D2RLoaderTableWidget(d2rloader)
        # self.setTabBarAutoHide(True)
        self.addTab(self.d2rloader_table, "D2RLoader")

        self.d2rloader.plugins.hook.d2rloader_main_tabbar(
            d2rloader=d2rloader, tabbar=self
        )
