from __future__ import annotations

import functools
import warnings
from typing import Final, cast

from loguru import logger
from PySide6.QtCore import QProcess, Qt, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from d2rloader.core.state import D2RLoaderState
from d2rloader.models.account import Account, AuthMethod, Region
from d2rloader.ui.dialog_account import AccountDialogWidget
from d2rloader.ui.utils import create_margins, show_error_dialog


class D2RLoaderTableWidget(QWidget):
    _columns: Final = [
        "Account",
        "Auth Method",
        "Region",
        "Launch Parameters",
        "Run Time",
        "Actions",
    ]
    _items: int = 0
    _process: QProcess | None = None
    _processes: dict[str, tuple[bool, int]] = {}

    def __init__(self, d2rloader: D2RLoaderState):
        super().__init__()
        self.d2rloader: D2RLoaderState = d2rloader

        self.table: QTableWidget = self.create_table()
        self.toolbar: QWidget = self.create_toolbar()

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.toolbar)
        layout.setContentsMargins(create_margins(2, 2, 5, 5))
        self.setLayout(layout)

        self.create_table_entries()
        self.find_active_instances()

    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(len(self._columns))
        table.setHorizontalHeaderLabels(self._columns)
        table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.hideColumn(4)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.itemChanged.connect(self.change_parameters)
        table.itemDoubleClicked.connect(self.double_clicked_row)
        return table

    def create_toolbar(self):
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(create_margins(0, 0, 0, 0))

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_entry)
        clone_button = QPushButton("Clone")
        clone_button.clicked.connect(self.clone_entry)
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_entry)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_entry)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(add_button)
        toolbar_layout.addWidget(clone_button)
        toolbar_layout.addWidget(edit_button)
        toolbar_layout.addWidget(delete_button)

        toolbar_widget.setLayout(toolbar_layout)
        return toolbar_widget

    @Slot()
    def edit_entry(self) -> None:
        if len(self.table.selectedIndexes()) == 0:
            return

        row_index = self.table.selectedIndexes()[0].row()
        edit_dialog = AccountDialogWidget(
            self, self.d2rloader, self.d2rloader.accounts.get(row_index)
        )

        if edit_dialog.exec():
            self.table.removeRow(row_index)
            self.create_row(row_index, edit_dialog.data)
            self.d2rloader.accounts.add(edit_dialog.data, row_index)
            self.table.selectRow(row_index)

    @Slot()
    def add_entry(self):
        add_dialog = AccountDialogWidget(self, self.d2rloader)

        if add_dialog.exec():
            self.add_row(add_dialog.data)
            self.d2rloader.accounts.add(add_dialog.data)

    @Slot()
    def clone_entry(self):
        if len(self.table.selectedIndexes()) == 0:
            return

        row_index = self.table.selectedIndexes()[0].row()

        cloned_idx = self.d2rloader.accounts.clone(row_index)
        if cloned_idx is None:
            logger.error(f"Couldn't clone account with row_index {row_index}")
            return

        self.add_row(self.d2rloader.accounts.get(cloned_idx))

    @Slot()
    def delete_entry(self):
        if len(self.table.selectedIndexes()) == 0:
            return

        row_index = self.table.selectedIndexes()[0].row()
        self.table.removeRow(row_index)
        self._items -= 1
        self.d2rloader.accounts.delete(row_index)

    def double_clicked_row(self, _: QTableWidgetItem):
        self.edit_entry()

    def create_table_entries(self, data: list[Account] | None = None):
        data = self.d2rloader.accounts.data if not data else data

        for item in data:
            self.add_row(item)

    def create_row(self, row: int, item: Account | None = None):
        if item is None:
            return

        account_item = QTableWidgetItem(item.displayname)
        account_item.setFlags(account_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        auth_item = QTableWidgetItem()
        auth_item.setFlags(auth_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        auth_combobox = QComboBox()
        auth_combobox.addItem(AuthMethod.Token.name, AuthMethod.Token)
        auth_combobox.addItem(AuthMethod.Password.name, AuthMethod.Password)
        idx = auth_combobox.findData(item.auth_method)
        auth_combobox.setCurrentIndex(idx)
        auth_combobox.currentTextChanged.connect(self.change_auth_method)

        region_item = QTableWidgetItem()
        region_item.setFlags(region_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        region_combobox = QComboBox()
        region_combobox.setFrame(True)
        region_combobox.addItem(Region.Europe.name, Region.Europe)
        region_combobox.addItem(Region.Americas.name, Region.Americas)
        region_combobox.addItem(Region.Asia.name, Region.Asia)
        idx = region_combobox.findData(item.region)
        region_combobox.setCurrentIndex(idx)
        region_combobox.currentTextChanged.connect(self.change_region)

        parameters_item = QTableWidgetItem(item.params if item.params else "")
        parameters_item.setFlags(
            parameters_item.flags()
            & ~Qt.ItemFlag.ItemIsEditable
            & ~Qt.ItemFlag.ItemIsSelectable
        )

        runtime_item = QTableWidgetItem(f"{item.runtime:.2f}")
        runtime_item.setFlags(runtime_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        action_item = QTableWidgetItem()
        action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        start_stop_btn = QPushButton("Start")
        start_stop_btn.setCheckable(True)
        start_stop_btn.setFlat(True)
        start_stop_btn.clicked.connect(
            functools.partial(self.clicked_start_stop_button, row, start_stop_btn)
        )

        self.table.insertRow(row)

        self.table.setItem(row, 0, account_item)
        self.table.setItem(row, 1, auth_item)
        self.table.setCellWidget(row, 1, auth_combobox)
        self.table.setItem(row, 2, region_item)
        self.table.setCellWidget(row, 2, region_combobox)
        self.table.setItem(row, 3, parameters_item)
        self.table.setItem(row, 4, runtime_item)
        self.table.setItem(row, 5, action_item)
        self.table.setCellWidget(row, 5, start_stop_btn)

    def add_row(self, item: Account | None = None):
        self.create_row(self._items, item)
        self._items += 1

    def reload_table(self):
        self.table.setRowCount(0)
        self._items = 0
        self.create_table_entries()

    def clicked_start_stop_button(self, row_index: int, button: QPushButton | None):
        account = self.d2rloader.accounts.get(row_index)
        if account is None:
            logger.error(f"Accout not found for row_index {row_index}")
            return

        if button is not None:
            if button.text() != "Running":
                self.process_start(account, button)
            else:
                self.process_kill(account, button)

        self.table.selectRow(row_index)

    def change_buttons_state(self, activeButton: QPushButton, new_state: str = "start"):
        if new_state == "start":
            activeButton.setDisabled(False)
            activeButton.setChecked(False)
            activeButton.setText("Start")
        else:
            activeButton.setDisabled(True)

        for row in range(self.table.rowCount()):
            button = cast(QPushButton, self.table.cellWidget(row, 5))
            if button == activeButton or button.text() == "Running":
                continue

            if new_state == "stop":
                button.setDisabled(True)
            else:
                button.setDisabled(False)
                button.setChecked(False)

    @Slot()
    def change_auth_method(self, activated: str | None = None):
        method = AuthMethod.from_name(activated or "")
        if activated is None or method is None:
            return

        row_index = self.table.selectedIndexes()[0].row()
        self.d2rloader.accounts.update(row_index, auth_method=method)

    @Slot()
    def change_region(self, activated: str | None = None):
        reg = Region.from_name(activated or "")
        if activated is None or reg is None:
            return

        row_index = self.table.selectedIndexes()[0].row()
        self.d2rloader.accounts.update(row_index, region=reg)

    def change_parameters(self, item: QTableWidgetItem):
        if self._columns[item.column()] == "Launch Parameters":
            account = self.d2rloader.accounts.get(item.row())
            if account is not None and account.params != item.text():
                self.d2rloader.accounts.update(item.row(), params=item.text())

    def find_active_instances(self):
        if self.d2rloader.process_manager is None:
            logger.error("ProcessManager not registered!")
            return

        instances = self.d2rloader.process_manager.find_active_instances(
            self.d2rloader.accounts.data
        )
        for i in instances.items():
            self._processes[i[1].id] = (True, i[0])

        for idx, account in enumerate(self.d2rloader.accounts.data):
            if account.id in self._processes.keys():
                button = cast(QPushButton, self.table.cellWidget(idx, 5))
                if button.text() == "Running":
                    continue
                button.setText("Running")

    def process_start(self, account: Account, button: QPushButton):
        if self.d2rloader.process_manager is None:
            logger.error("ProcessManager not registered!")
            return

        # try to disconnect previous signals before adding a new one
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.d2rloader.process_manager.process_finished.disconnect()
                self.d2rloader.process_manager.process_error.disconnect()
        except Exception:
            pass

        self.change_buttons_state(button, "stop")
        button.setText("Starting...")
        button.setDisabled(True)

        logger.info(
            f"Starting D2R.exe - {account.displayname} ({account.region.value})"
        )
        self.d2rloader.process_manager.process_finished.connect(
            functools.partial(self.process_finished, button)
        )
        self.d2rloader.process_manager.process_error.connect(
            functools.partial(self.process_error, button)
        )
        self.d2rloader.process_manager.start(account)

    def process_kill(self, account: Account, button: QPushButton):
        pid = None
        try:
            pid = self._processes[account.id][1]
        except KeyError:
            pass

        if pid is None or self.d2rloader.process_manager is None:
            logger.error("Stopping D2R.exe failed - PID not found!")
        else:
            logger.info(
                f"Stopping D2R.exe with PID {self._processes[account.id][1]} - {account.displayname} ({account.region})"
            )
            try:
                self.d2rloader.process_manager.kill(pid)
            except Exception:
                logger.error(f"Couldn't kill pid {pid}")

        del self._processes[account.id]
        self.change_buttons_state(button, "start")

    @Slot()
    def process_finished(
        self, button: QPushButton, logged_in: bool, account: Account | None, pid: int
    ):
        if not account:
            button.setText("Start")
            button.setDisabled(False)
            self.change_buttons_state(button, "start")
            return

        logger.info(f"Started profile {account.displayname} with pid {pid}")
        self.change_buttons_state(button, "start")
        button.setText("Running")
        button.setDisabled(False)

        self._processes[account.id] = (logged_in, pid)

    @Slot()
    def process_error(self, button: QPushButton, account: Account, msg: str):
        show_error_dialog(self, msg)
        self.change_buttons_state(button, "start")
