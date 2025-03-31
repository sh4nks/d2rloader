from PySide6.QtCore import QMargins, QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox, QSizePolicy, QWidget


def class_name(o: QWidget):
    return str(o.metaObject().className())


def init_widget(w: QWidget, name: str, tooltip: str | None = None) -> None:
    """Init a widget for the gallery, give it a tooltip showing the
    class name"""
    w.setObjectName(name)
    w.setToolTip(tooltip or class_name(w))


def create_margins(
    left: int | None = None,
    right: int | None = None,
    top: int | None = None,
    bottom: int | None = None,
):
    margin = QMargins()
    if left is not None:
        margin.setLeft(left)

    if right is not None:
        margin.setRight(right)

    if top is not None:
        margin.setTop(top)

    if bottom is not None:
        margin.setBottom(bottom)

    return margin


def create_action(parent: QObject, text: str, slot: object) -> QAction:
    """Helper function to save typing when populating menus    with action."""
    action = QAction(text, parent)
    action.triggered.connect(slot)
    return action


def create_toolbar_spacer():
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return spacer


def show_error_dialog(w: QWidget, msg: str) -> None:
    QMessageBox.critical(
        w,
        "Error",
        (f"<center>{msg}</center>"),
        QMessageBox.StandardButton.Ok,
    )
