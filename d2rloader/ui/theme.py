from PySide6.QtCore import Slot

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QStyleFactory,
)

from d2rloader.ui.utils.utils import init_widget


def style_names() -> list[str]:
    """Return a list of styles, default platform style first"""
    default_style_name = QApplication.style().objectName().lower()
    result: list[str] = []
    for style in QStyleFactory.keys():
        if style.lower() == default_style_name:
            result.insert(0, style)
        else:
            result.append(style)
    return result


class D2RStyleWidget(QHBoxLayout):
    def __init__(self):
        super().__init__()

        _style_combobox = QComboBox()
        init_widget(_style_combobox, "styleComboBox")
        _style_combobox.addItems(style_names())

        style_label = QLabel("Style:")
        init_widget(style_label, "style_label")
        style_label.setBuddy(_style_combobox)

        _ = _style_combobox.textActivated.connect(self.change_style)

        self.addWidget(style_label)
        self.addWidget(_style_combobox)

    @Slot()
    def change_style(self, style_name: str | None = None):
        if style_name is not None:
            QApplication.setStyle(QStyleFactory.create(style_name))
