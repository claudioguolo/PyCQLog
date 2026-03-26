from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pycqlog.localization import LocalizationService
from pycqlog.themes import THEME_CHOICES


class SettingsDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        current_language: str,
        current_theme: str,
        operator_callsign: str,
        station_callsign: str,
        data_dir: str,
        log_dir: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui(
            current_language,
            current_theme,
            operator_callsign,
            station_callsign,
            data_dir,
            log_dir,
        )
        self._apply_translations()

    def _build_ui(
        self,
        current_language: str,
        current_theme: str,
        operator_callsign: str,
        station_callsign: str,
        data_dir: str,
        log_dir: str,
    ) -> None:
        root = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.language_combo = QComboBox()
        for language in self._localization.available_languages():
            self.language_combo.addItem(self._localization.t(f"language.{language}"), language)
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.theme_combo = QComboBox()
        for theme in THEME_CHOICES:
            self.theme_combo.addItem("", theme)
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.operator_input = QLineEdit(operator_callsign)
        self.station_input = QLineEdit(station_callsign)
        self.data_dir_input = QLineEdit(data_dir)
        self.data_dir_button = QPushButton()
        self.data_dir_button.clicked.connect(self._choose_data_dir)
        self.log_dir_input = QLineEdit(log_dir)
        self.log_dir_button = QPushButton()
        self.log_dir_button.clicked.connect(self._choose_log_dir)
        data_dir_row = QHBoxLayout()
        data_dir_row.setContentsMargins(0, 0, 0, 0)
        data_dir_row.addWidget(self.data_dir_input, 1)
        data_dir_row.addWidget(self.data_dir_button)
        log_dir_row = QHBoxLayout()
        log_dir_row.setContentsMargins(0, 0, 0, 0)
        log_dir_row.addWidget(self.log_dir_input, 1)
        log_dir_row.addWidget(self.log_dir_button)

        self.form_layout.addRow("", self.language_combo)
        self.form_layout.addRow("", self.theme_combo)
        self.form_layout.addRow("", self.operator_input)
        self.form_layout.addRow("", self.station_input)
        self.form_layout.addRow("", data_dir_row)
        self.form_layout.addRow("", log_dir_row)
        root.addLayout(self.form_layout)

        self.notice_label = QLabel()
        self.notice_label.setWordWrap(True)
        root.addWidget(self.notice_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

    def _apply_translations(self) -> None:
        self.setWindowTitle(self._localization.t("settings.title"))
        labels = [
            self._localization.t("settings.language"),
            self._localization.t("settings.theme"),
            self._localization.t("settings.operator_callsign"),
            self._localization.t("settings.station_callsign"),
            self._localization.t("settings.data_dir"),
            self._localization.t("settings.log_dir"),
        ]
        for row, text in enumerate(labels):
            label_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            if label_item is not None and label_item.widget() is not None:
                label_item.widget().deleteLater()
            self.form_layout.setWidget(row, QFormLayout.ItemRole.LabelRole, QLabel(text))

        for index in range(self.theme_combo.count()):
            theme = str(self.theme_combo.itemData(index))
            self.theme_combo.setItemText(index, self._localization.t(f"theme.{theme}"))

        self.data_dir_input.setPlaceholderText(self._localization.t("settings.data_dir_help"))
        self.data_dir_button.setText(self._localization.t("settings.choose_directory"))
        self.log_dir_input.setPlaceholderText(self._localization.t("settings.log_dir_help"))
        self.log_dir_button.setText(self._localization.t("settings.choose_directory"))
        self.notice_label.setText(self._localization.t("settings.restart_notice"))
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            self._localization.t("button.save_settings")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._localization.t("button.cancel")
        )

    def selected_language(self) -> str:
        return str(self.language_combo.currentData())

    def operator_callsign(self) -> str:
        return self.operator_input.text().strip().upper()

    def theme(self) -> str:
        return str(self.theme_combo.currentData())

    def station_callsign(self) -> str:
        return self.station_input.text().strip().upper()

    def data_dir(self) -> str:
        value = self.data_dir_input.text().strip()
        return str(Path(value).expanduser()) if value else ""

    def log_dir(self) -> str:
        value = self.log_dir_input.text().strip()
        return str(Path(value).expanduser()) if value else ""

    def accept(self) -> None:
        for selected_dir, title_key, body_key in (
            (self.data_dir(), "settings.invalid_data_dir_title", "settings.invalid_data_dir_body"),
            (self.log_dir(), "settings.invalid_log_dir_title", "settings.invalid_log_dir_body"),
        ):
            if not selected_dir:
                continue
            try:
                Path(selected_dir).mkdir(parents=True, exist_ok=True)
            except OSError:
                QMessageBox.warning(
                    self,
                    self._localization.t(title_key),
                    self._localization.t(body_key),
                )
                return
        super().accept()

    def _choose_data_dir(self) -> None:
        start_dir = self.data_dir() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._localization.t("settings.directory_dialog_title"),
            start_dir,
        )
        if chosen:
            self.data_dir_input.setText(chosen)

    def _choose_log_dir(self) -> None:
        start_dir = self.log_dir() or self.data_dir() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._localization.t("settings.log_dir_dialog_title"),
            start_dir,
        )
        if chosen:
            self.log_dir_input.setText(chosen)
