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

from pycqlog.application.dto import SaveStationProfileCommand, StationProfileListItem
from pycqlog.localization import LocalizationService


class StationProfilesDialog(QDialog):
    def __init__(self, localization: LocalizationService, profiles_loader, profile_saver, profile_deleter, parent=None) -> None:
        super().__init__(parent)
        self._localization = localization
        self._profiles_loader = profiles_loader
        self._profile_saver = profile_saver
        self._profile_deleter = profile_deleter
        self._current_profile_id: int | None = None
        self._build_ui()
        self._load_profiles()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("profiles.title"))
        self.resize(860, 560)
        root = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            [
                self._localization.t("profiles.name"),
                self._localization.t("profiles.type"),
                self._localization.t("label.callsign"),
            ]
        )
        self.table.itemSelectionChanged.connect(self._load_selected_profile)
        root.addWidget(self.table)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.profile_type_combo = QComboBox()
        self.profile_type_combo.addItem(self._localization.t("profiles.type_both"), "both")
        self.profile_type_combo.addItem(self._localization.t("profiles.type_operator"), "operator")
        self.profile_type_combo.addItem(self._localization.t("profiles.type_station"), "station")
        self.callsign_input = QLineEdit()
        self.qth_input = QLineEdit()
        self.locator_input = QLineEdit()
        self.power_input = QLineEdit()
        self.antenna_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(90)
        form.addRow(QLabel(self._localization.t("profiles.name")), self.name_input)
        form.addRow(QLabel(self._localization.t("profiles.type")), self.profile_type_combo)
        form.addRow(QLabel(self._localization.t("label.callsign")), self.callsign_input)
        form.addRow(QLabel(self._localization.t("profiles.qth")), self.qth_input)
        form.addRow(QLabel(self._localization.t("profiles.locator")), self.locator_input)
        form.addRow(QLabel(self._localization.t("profiles.power")), self.power_input)
        form.addRow(QLabel(self._localization.t("profiles.antenna")), self.antenna_input)
        form.addRow(QLabel(self._localization.t("label.notes")), self.notes_input)
        root.addLayout(form)

        action_row = QHBoxLayout()
        self.new_button = QPushButton(self._localization.t("button.new_profile"))
        self.new_button.clicked.connect(self._reset_form)
        action_row.addWidget(self.new_button)
        self.delete_button = QPushButton(self._localization.t("button.delete_profile"))
        self.delete_button.clicked.connect(self._delete_profile)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        root.addLayout(action_row)

        self.help_label = QLabel(self._localization.t("profiles.help"))
        self.help_label.setWordWrap(True)
        root.addWidget(self.help_label)

        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton(
            self._localization.t("button.save_profile"),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.close_button = self.button_box.addButton(
            self._localization.t("button.close"),
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        self.save_button.clicked.connect(self._save_profile)
        self.close_button.clicked.connect(self.reject)
        root.addWidget(self.button_box)

    def _load_profiles(self) -> None:
        self._profiles = self._profiles_loader.execute()
        self.table.setRowCount(len(self._profiles))
        for row, item in enumerate(self._profiles):
            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, QTableWidgetItem(self._profile_type_label(item.profile_type)))
            self.table.setItem(row, 2, QTableWidgetItem(item.callsign))
        self.table.resizeColumnsToContents()

    def _profile_type_label(self, profile_type: str) -> str:
        return self._localization.t(f"profiles.type_{profile_type}")

    def _load_selected_profile(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._profiles):
            return
        item = self._profiles[row]
        self._current_profile_id = item.profile_id
        self.name_input.setText(item.name)
        self.profile_type_combo.setCurrentIndex(max(0, self.profile_type_combo.findData(item.profile_type)))
        self.callsign_input.setText(item.callsign)
        self.qth_input.setText(item.qth)
        self.locator_input.setText(item.locator)
        self.power_input.setText(item.power)
        self.antenna_input.setText(item.antenna)
        self.notes_input.setPlainText(item.notes)

    def _reset_form(self) -> None:
        self._current_profile_id = None
        self.table.clearSelection()
        self.name_input.clear()
        self.profile_type_combo.setCurrentIndex(0)
        self.callsign_input.clear()
        self.qth_input.clear()
        self.locator_input.clear()
        self.power_input.clear()
        self.antenna_input.clear()
        self.notes_input.clear()
        self.name_input.setFocus()

    def _save_profile(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                self._localization.t("message.invalid_data_title"),
                self._localization.t("profiles.name_required"),
            )
            return
        self._profile_saver.execute(
            SaveStationProfileCommand(
                profile_id=self._current_profile_id,
                name=self.name_input.text(),
                profile_type=str(self.profile_type_combo.currentData()),
                callsign=self.callsign_input.text(),
                qth=self.qth_input.text(),
                locator=self.locator_input.text(),
                power=self.power_input.text(),
                antenna=self.antenna_input.text(),
                notes=self.notes_input.toPlainText(),
            )
        )
        self._load_profiles()
        self._reset_form()

    def _delete_profile(self) -> None:
        if self._current_profile_id is None:
            return
        answer = QMessageBox.question(
            self,
            self._localization.t("profiles.delete_title"),
            self._localization.t("profiles.delete_body"),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._profile_deleter.execute(self._current_profile_id)
        self._load_profiles()
        self._reset_form()
