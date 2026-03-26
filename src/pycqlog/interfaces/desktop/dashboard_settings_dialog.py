from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from pycqlog.localization import LocalizationService


class DashboardSettingsDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        use_band_colors: bool,
        use_mode_colors: bool,
        colorize_tables: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui(use_band_colors, use_mode_colors, colorize_tables)

    def _build_ui(self, use_band_colors: bool, use_mode_colors: bool, colorize_tables: bool) -> None:
        self.setWindowTitle(self._localization.t("dashboard.settings_title"))
        root = QVBoxLayout(self)

        self.band_colors_checkbox = QCheckBox(self._localization.t("dashboard.settings_band_colors"))
        self.band_colors_checkbox.setChecked(use_band_colors)
        root.addWidget(self.band_colors_checkbox)

        self.mode_colors_checkbox = QCheckBox(self._localization.t("dashboard.settings_mode_colors"))
        self.mode_colors_checkbox.setChecked(use_mode_colors)
        root.addWidget(self.mode_colors_checkbox)

        self.colorize_tables_checkbox = QCheckBox(self._localization.t("dashboard.settings_table_colors"))
        self.colorize_tables_checkbox.setChecked(colorize_tables)
        root.addWidget(self.colorize_tables_checkbox)

        self.help_label = QLabel(self._localization.t("dashboard.settings_help"))
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

    def use_band_colors(self) -> bool:
        return self.band_colors_checkbox.isChecked()

    def use_mode_colors(self) -> bool:
        return self.mode_colors_checkbox.isChecked()

    def colorize_tables(self) -> bool:
        return self.colorize_tables_checkbox.isChecked()
