from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget


def class_name(o: QWidget):
    return str(o.metaObject().className())


def init_widget(w: QWidget, name: str, tooltip: str | None = None) -> None:
    """Init a widget for the gallery, give it a tooltip showing the
    class name"""
    w.setObjectName(name)
    w.setToolTip(tooltip or class_name(w))


def create_action(parent: QObject, text: str, menu: QMenu, slot: object) -> QAction:
    """Helper function to save typing when populating menus
    with action.
    """
    action = QAction(text, parent)
    menu.addAction(action)
    action.triggered.connect(slot)
    return action


def show_error_dialog(w: QWidget, msg: str) -> None:
    QMessageBox.critical(
        w,
        "Error",
        (f"<center>{msg}</center>"),
        QMessageBox.StandardButton.Ok,
    )
