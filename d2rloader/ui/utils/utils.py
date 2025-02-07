from PySide6.QtWidgets import QWidget


def class_name(o: QWidget):
    return str(o.metaObject().className())


def init_widget(w: QWidget, name: str) -> None:
    """Init a widget for the gallery, give it a tooltip showing the
    class name"""
    w.setObjectName(name)
    w.setToolTip(class_name(w))
