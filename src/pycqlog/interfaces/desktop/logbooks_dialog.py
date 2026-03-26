from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from pycqlog.application.dto import SaveLogbookCommand
from pycqlog.localization import LocalizationService


class LogbooksDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        logbooks_loader,
        logbook_saver,
        logbook_deleter,
        profiles_loader,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._logbooks_loader = logbooks_loader
        self._logbook_saver = logbook_saver
        self._logbook_deleter = logbook_deleter
        self._profiles_loader = profiles_loader
        self._current_logbook_id: int | None = None
        self._profile_choices = []
        self._build_ui()
        self._load_profiles()
        self._load_logbooks()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("logbooks.title"))
        self.resize(920, 580)
        root = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            [
                self._localization.t("logbooks.name"),
                self._localization.t("settings.operator_callsign"),
                self._localization.t("settings.station_callsign"),
                self._localization.t("logbooks.qso_count"),
            ]
        )
        self.table.itemSelectionChanged.connect(self._load_selected_logbook)
        root.addWidget(self.table)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(70)
        self.operator_combo = QComboBox()
        self.station_combo = QComboBox()
        form.addRow(QLabel(self._localization.t("logbooks.name")), self.name_input)
        form.addRow(QLabel(self._localization.t("logbooks.description")), self.description_input)
        form.addRow(QLabel(self._localization.t("logbooks.operator_profile")), self.operator_combo)
        form.addRow(QLabel(self._localization.t("logbooks.station_profile")), self.station_combo)
        root.addLayout(form)

        action_row = QHBoxLayout()
        self.new_button = QPushButton(self._localization.t("button.new_logbook"))
        self.new_button.clicked.connect(self._reset_form)
        action_row.addWidget(self.new_button)
        self.delete_button = QPushButton(self._localization.t("button.delete_logbook"))
        self.delete_button.clicked.connect(self._delete_logbook)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        root.addLayout(action_row)

        self.help_label = QLabel(self._localization.t("logbooks.help"))
        self.help_label.setWordWrap(True)
        root.addWidget(self.help_label)

        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton(
            self._localization.t("button.save_logbook"),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.close_button = self.button_box.addButton(
            self._localization.t("button.close"),
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        self.save_button.clicked.connect(self._save_logbook)
        self.close_button.clicked.connect(self.reject)
        root.addWidget(self.button_box)

    def _load_profiles(self) -> None:
        self._profile_choices = self._profiles_loader.execute()
        self.operator_combo.clear()
        self.station_combo.clear()
        self.operator_combo.addItem(self._localization.t("logbooks.no_profile"), None)
        self.station_combo.addItem(self._localization.t("logbooks.no_profile"), None)
        for item in self._profile_choices:
            self.operator_combo.addItem(f"{item.name} ({item.callsign})".strip(), item.profile_id)
            self.station_combo.addItem(f"{item.name} ({item.callsign})".strip(), item.profile_id)

    def _load_logbooks(self) -> None:
        self._logbooks = self._logbooks_loader.execute()
        self.table.setRowCount(len(self._logbooks))
        for row, item in enumerate(self._logbooks):
            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, QTableWidgetItem(item.operator_callsign))
            self.table.setItem(row, 2, QTableWidgetItem(item.station_callsign))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.qso_count)))
        self.table.resizeColumnsToContents()

    def _load_selected_logbook(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._logbooks):
            return
        item = self._logbooks[row]
        self._current_logbook_id = item.logbook_id
        self.name_input.setText(item.name)
        self.description_input.setPlainText(item.description)
        self.operator_combo.setCurrentIndex(max(0, self.operator_combo.findData(item.operator_profile_id)))
        self.station_combo.setCurrentIndex(max(0, self.station_combo.findData(item.station_profile_id)))

    def _reset_form(self) -> None:
        self._current_logbook_id = None
        self.table.clearSelection()
        self.name_input.clear()
        self.description_input.clear()
        self.operator_combo.setCurrentIndex(0)
        self.station_combo.setCurrentIndex(0)
        self.name_input.setFocus()

    def _save_logbook(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                self._localization.t("message.invalid_data_title"),
                self._localization.t("logbooks.name_required"),
            )
            return
        self._logbook_saver.execute(
            SaveLogbookCommand(
                logbook_id=self._current_logbook_id,
                name=self.name_input.text(),
                description=self.description_input.toPlainText(),
                operator_profile_id=self.operator_combo.currentData(),
                station_profile_id=self.station_combo.currentData(),
            )
        )
        self._load_logbooks()
        self._reset_form()

    def _delete_logbook(self) -> None:
        if self._current_logbook_id is None:
            return
        answer = QMessageBox.question(
            self,
            self._localization.t("logbooks.delete_title"),
            self._localization.t("logbooks.delete_body"),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = self._logbook_deleter.execute(self._current_logbook_id)
        if not deleted:
            QMessageBox.warning(
                self,
                self._localization.t("logbooks.delete_blocked_title"),
                self._localization.t("logbooks.delete_blocked_body"),
            )
            return
        self._load_logbooks()
        self._reset_form()
