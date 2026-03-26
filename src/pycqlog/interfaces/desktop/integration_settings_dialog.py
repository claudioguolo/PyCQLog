from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QTabWidget,
    QWidget,
)

from pycqlog.localization import LocalizationService


class IntegrationSettingsDialog(QDialog):
    def __init__(self, localization: LocalizationService, settings: dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui(settings)

    def _build_ui(self, settings: dict[str, str]) -> None:
        self.setWindowTitle(self._localization.t("integrations.title"))
        self.resize(650, 560)
        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Tab 1: Local / WSJT
        wsjt_tab = QWidget()
        wsjt_layout = QVBoxLayout(wsjt_tab)
        self.wsjt_enabled = QCheckBox(self._localization.t("integrations.wsjt_enabled"))
        self.wsjt_enabled.setChecked(settings.get("integration_wsjt_enabled", "false") == "true")
        wsjt_layout.addWidget(self.wsjt_enabled)

        wsjt_form = QFormLayout()
        self.wsjt_host = QLineEdit(settings.get("integration_wsjt_host", "127.0.0.1"))
        self.wsjt_port = QSpinBox()
        self.wsjt_port.setRange(1024, 65535)
        self.wsjt_port.setValue(int(settings.get("integration_wsjt_port", "2237") or "2237"))
        wsjt_form.addRow(QLabel(self._localization.t("integrations.wsjt_host")), self.wsjt_host)
        wsjt_form.addRow(QLabel(self._localization.t("integrations.wsjt_port")), self.wsjt_port)
        wsjt_layout.addLayout(wsjt_form)
        wsjt_layout.addStretch(1)
        self.tabs.addTab(wsjt_tab, self._localization.t("integrations.tab_local"))

        # Tab 2: QRZ.com
        qrz_tab = QWidget()
        qrz_layout = QVBoxLayout(qrz_tab)
        
        self.qrz_enabled = QCheckBox(self._localization.t("integrations.qrz_enabled"))
        self.qrz_enabled.setChecked(settings.get("integration_qrz_enabled", "false") == "true")
        qrz_layout.addWidget(self.qrz_enabled)

        self.qrz_upload_udp = QCheckBox(self._localization.t("integrations.qrz_upload_udp"))
        self.qrz_upload_udp.setChecked(settings.get("integration_qrz_upload_udp", "true") == "true")
        qrz_layout.addWidget(self.qrz_upload_udp)

        self.qrz_upload_manual = QCheckBox(self._localization.t("integrations.qrz_upload_manual"))
        self.qrz_upload_manual.setChecked(settings.get("integration_qrz_upload_manual", "false") == "true")
        qrz_layout.addWidget(self.qrz_upload_manual)

        qrz_form = QFormLayout()
        self.qrz_username = QLineEdit(settings.get("integration_qrz_username", ""))
        self.qrz_password = QLineEdit(settings.get("integration_qrz_password", ""))
        self.qrz_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.qrz_api_key = QLineEdit(settings.get("integration_qrz_api_key", ""))
        qrz_form.addRow(QLabel(self._localization.t("integrations.qrz_username")), self.qrz_username)
        qrz_form.addRow(QLabel(self._localization.t("integrations.qrz_password")), self.qrz_password)
        qrz_form.addRow(QLabel(self._localization.t("integrations.qrz_api_key")), self.qrz_api_key)
        qrz_layout.addLayout(qrz_form)
        qrz_layout.addStretch(1)
        self.tabs.addTab(qrz_tab, self._localization.t("integrations.tab_qrz"))

        # Tab 3: Club Log
        clublog_tab = QWidget()
        clublog_layout = QVBoxLayout(clublog_tab)
        
        self.clublog_enabled = QCheckBox(self._localization.t("integrations.clublog_enabled"))
        self.clublog_enabled.setChecked(settings.get("integration_clublog_enabled", "false") == "true")
        clublog_layout.addWidget(self.clublog_enabled)

        self.clublog_upload_udp = QCheckBox(self._localization.t("integrations.clublog_upload_udp"))
        self.clublog_upload_udp.setChecked(settings.get("integration_clublog_upload_udp", "true") == "true")
        clublog_layout.addWidget(self.clublog_upload_udp)

        self.clublog_upload_manual = QCheckBox(self._localization.t("integrations.clublog_upload_manual"))
        self.clublog_upload_manual.setChecked(settings.get("integration_clublog_upload_manual", "false") == "true")
        clublog_layout.addWidget(self.clublog_upload_manual)

        clublog_form = QFormLayout()
        self.clublog_email = QLineEdit(settings.get("integration_clublog_email", ""))
        self.clublog_password = QLineEdit(settings.get("integration_clublog_password", ""))
        self.clublog_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.clublog_callsign = QLineEdit(settings.get("integration_clublog_callsign", ""))
        self.clublog_api_key = QLineEdit(settings.get("integration_clublog_api_key", ""))
        self.clublog_endpoint = QLineEdit(settings.get("integration_clublog_endpoint", "https://clublog.org/realtime.php"))
        self.clublog_interval = QSpinBox()
        self.clublog_interval.setRange(5, 600)
        self.clublog_interval.setValue(int(settings.get("integration_clublog_interval", "30") or "30"))
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_email")), self.clublog_email)
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_password")), self.clublog_password)
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_callsign")), self.clublog_callsign)
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_api_key")), self.clublog_api_key)
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_endpoint")), self.clublog_endpoint)
        clublog_form.addRow(QLabel(self._localization.t("integrations.clublog_interval")), self.clublog_interval)
        clublog_layout.addLayout(clublog_form)
        clublog_layout.addStretch(1)
        self.tabs.addTab(clublog_tab, self._localization.t("integrations.tab_clublog"))

        # Tab 4: LoTW
        lotw_tab = QWidget()
        lotw_layout = QVBoxLayout(lotw_tab)
        lotw_form = QFormLayout()
        
        self.lotw_tqsl_path = QLineEdit(settings.get("integration_lotw_tqsl_path", "tqsl"))
        self.lotw_station_location = QLineEdit(settings.get("integration_lotw_station_location", ""))
        
        lotw_form.addRow(QLabel(self._localization.t("integrations.lotw_tqsl_path")), self.lotw_tqsl_path)
        lotw_form.addRow(QLabel(self._localization.t("integrations.lotw_station_location")), self.lotw_station_location)
        lotw_layout.addLayout(lotw_form)
        lotw_layout.addStretch(1)
        self.tabs.addTab(lotw_tab, self._localization.t("integrations.tab_lotw"))

        # Help message below tabs
        self.help_label = QLabel(self._localization.t("integrations.help"))
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

    def values(self) -> dict[str, str]:
        return {
            "integration_wsjt_enabled": "true" if self.wsjt_enabled.isChecked() else "false",
            "integration_wsjt_host": self.wsjt_host.text().strip() or "127.0.0.1",
            "integration_wsjt_port": str(self.wsjt_port.value()),
            "integration_clublog_enabled": "true" if self.clublog_enabled.isChecked() else "false",
            "integration_clublog_upload_udp": "true" if self.clublog_upload_udp.isChecked() else "false",
            "integration_clublog_upload_manual": "true" if self.clublog_upload_manual.isChecked() else "false",
            "integration_clublog_email": self.clublog_email.text().strip(),
            "integration_clublog_password": self.clublog_password.text().strip(),
            "integration_clublog_callsign": self.clublog_callsign.text().strip().upper(),
            "integration_clublog_api_key": self.clublog_api_key.text().strip(),
            "integration_clublog_endpoint": self.clublog_endpoint.text().strip() or "https://clublog.org/realtime.php",
            "integration_clublog_interval": str(self.clublog_interval.value()),
            "integration_qrz_enabled": "true" if self.qrz_enabled.isChecked() else "false",
            "integration_qrz_upload_udp": "true" if self.qrz_upload_udp.isChecked() else "false",
            "integration_qrz_upload_manual": "true" if self.qrz_upload_manual.isChecked() else "false",
            "integration_qrz_username": self.qrz_username.text().strip(),
            "integration_qrz_password": self.qrz_password.text().strip(),
            "integration_qrz_api_key": self.qrz_api_key.text().strip(),
            "integration_lotw_tqsl_path": self.lotw_tqsl_path.text().strip() or "tqsl",
            "integration_lotw_station_location": self.lotw_station_location.text().strip(),
        }
