from PySide6.QtWidgets import QMessageBox, QWidget


def class_name(o: QWidget):
    return str(o.metaObject().className())


def init_widget(w: QWidget, name: str) -> None:
    """Init a widget for the gallery, give it a tooltip showing the
    class name"""
    w.setObjectName(name)
    w.setToolTip(class_name(w))

def show_error_dialog(w: QWidget, msg: str) -> None:
    QMessageBox.critical(
        w,
        "Error",
        (
            "<center>"
            f"{msg}"
            "</center>"
        ),
        QMessageBox.StandardButton.Ok,
    )
