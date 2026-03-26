from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from pycqlog.localization import LocalizationService


class AdifSettingsDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        operator_callsign: str,
        station_callsign: str,
        export_prefix: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui(operator_callsign, station_callsign, export_prefix)

    def _build_ui(self, operator_callsign: str, station_callsign: str, export_prefix: str) -> None:
        self.setWindowTitle(self._localization.t("adif.settings_title"))
        root = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.operator_input = QLineEdit(operator_callsign)
        self.station_input = QLineEdit(station_callsign)
        self.export_prefix_input = QLineEdit(export_prefix)
        self.export_prefix_input.setPlaceholderText(self._localization.t("adif.export_prefix_placeholder"))
        form_layout.addRow(QLabel(self._localization.t("settings.operator_callsign")), self.operator_input)
        form_layout.addRow(QLabel(self._localization.t("settings.station_callsign")), self.station_input)
        form_layout.addRow(QLabel(self._localization.t("adif.export_prefix")), self.export_prefix_input)
        root.addLayout(form_layout)

        self.help_label = QLabel(self._localization.t("adif.settings_help"))
        self.help_label.setWordWrap(True)
        root.addWidget(self.help_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            self._localization.t("button.save_settings")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._localization.t("button.cancel")
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

    def operator_callsign(self) -> str:
        return self.operator_input.text().strip().upper()

    def station_callsign(self) -> str:
        return self.station_input.text().strip().upper()

    def export_prefix(self) -> str:
        value = self.export_prefix_input.text().strip()
        return value or "pycqlog_export"
