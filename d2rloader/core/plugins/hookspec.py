from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from d2rloader.core.state import D2RLoaderState

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QMenuBar,
    QTabWidget,
)

from .markers import hookspec

# types are removed here to prevent those nasty cyclic import errors
# 'state' always implies the D2RLoaderState


@hookspec
def d2rloader_mainwindow_plugin_menu(
    d2rloader: "D2RLoaderState", parent: QObject, menu: QMenuBar
):
    """Hook for adding a new entry to the QMenu item.

    A new Section 'Plugins' will be created if it doesn't exist and you plugin will be
    placed in it
    """
    pass


@hookspec
def d2rloader_table_context_menu(d2rloader: "D2RLoaderState", table, item):
    """Hook for extending the right click menu in the accounts table

    NOT IMPLEMENTED YET
    """
    pass


@hookspec
def d2rloader_table_right_button_menu(d2rloader: "D2RLoaderState", widget):
    """Hook for extending the right aligned button menu"""
    pass


@hookspec
def d2rloader_table_left_button_menu(d2rloader: "D2RLoaderState", widget):
    """Hook for extending the left aligned button menu"""
    pass


@hookspec
def d2rloader_main_tabbar(d2rloader: "D2RLoaderState", tabbar: QTabWidget):
    """Hook for extending the main tabbar"""
    pass


@hookspec
def d2rloader_info_tabbar(d2rloader: "D2RLoaderState", tabbar: QTabWidget):
    """Hook for extending the info tabbar"""
    pass
