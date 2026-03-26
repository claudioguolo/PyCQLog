from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from pycqlog.application.dto import AdifExportFilter
from pycqlog.localization import LocalizationService


class ExportAdifDialog(QDialog):
    def __init__(self, localization: LocalizationService, parent=None) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("adif.export_filters_title"))
        root = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.callsign_input = QLineEdit()
        self.date_from_input = QLineEdit()
        self.date_to_input = QLineEdit()
        self.band_input = QLineEdit()
        self.mode_input = QLineEdit()
        self.form_layout.addRow(QLabel(self._localization.t("label.callsign")), self.callsign_input)
        self.form_layout.addRow(QLabel(self._localization.t("adif.export_date_from")), self.date_from_input)
        self.form_layout.addRow(QLabel(self._localization.t("adif.export_date_to")), self.date_to_input)
        self.form_layout.addRow(QLabel(self._localization.t("adif.export_band")), self.band_input)
        self.form_layout.addRow(QLabel(self._localization.t("label.mode")), self.mode_input)
        root.addLayout(self.form_layout)

        self.help_label = QLabel(self._localization.t("adif.export_filters_help"))
        self.help_label.setWordWrap(True)
        root.addWidget(self.help_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            self._localization.t("adif.export_choose_file")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._localization.t("button.cancel")
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

        self.date_from_input.setPlaceholderText("AAAA-MM-DD / YYYY-MM-DD")
        self.date_to_input.setPlaceholderText("AAAA-MM-DD / YYYY-MM-DD")
        self.band_input.setPlaceholderText("20m")
        self.mode_input.setPlaceholderText("FT8")

    def export_filter(self) -> AdifExportFilter:
        return AdifExportFilter(
            callsign=self.callsign_input.text().strip(),
            date_from=self._parse_date(self.date_from_input.text().strip()),
            date_to=self._parse_date(self.date_to_input.text().strip()),
            band=self.band_input.text().strip(),
            mode=self.mode_input.text().strip(),
        )

    def _parse_date(self, value: str) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)
