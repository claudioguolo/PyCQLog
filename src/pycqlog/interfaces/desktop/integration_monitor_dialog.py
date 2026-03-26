from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialogButtonBox,
    QDialog,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pycqlog.localization import LocalizationService


class IntegrationMonitorDialog(QDialog):
    def __init__(self, localization: LocalizationService, parent=None) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("integrations.monitor_title"))
        self.resize(920, 560)
        root = QVBoxLayout(self)

        summary_grid = QGridLayout()
        self.listener_value = self._summary_card(summary_grid, 0, 0, self._localization.t("integrations.monitor_listener"))
        self.clublog_value = self._summary_card(summary_grid, 0, 1, self._localization.t("integrations.monitor_clublog"))
        self.received_value = self._summary_card(summary_grid, 1, 0, self._localization.t("integrations.monitor_received"))
        self.saved_value = self._summary_card(summary_grid, 1, 1, self._localization.t("integrations.monitor_saved"))
        self.uploaded_value = self._summary_card(summary_grid, 2, 0, self._localization.t("integrations.monitor_uploaded"))
        self.failed_value = self._summary_card(summary_grid, 2, 1, self._localization.t("integrations.monitor_failed"))
        self.pending_value = self._summary_card(summary_grid, 3, 0, self._localization.t("integrations.monitor_pending"))
        root.addLayout(summary_grid)

        button_row = QHBoxLayout()
        self.test_udp_button = QPushButton(self._localization.t("integrations.monitor_test_udp"))
        button_row.addWidget(self.test_udp_button)
        self.test_clublog_button = QPushButton(self._localization.t("integrations.monitor_test_clublog"))
        button_row.addWidget(self.test_clublog_button)
        self.retry_button = QPushButton(self._localization.t("integrations.monitor_retry_pending"))
        button_row.addWidget(self.retry_button)
        self.clear_button = QPushButton(self._localization.t("integrations.monitor_clear"))
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        root.addLayout(button_row)

        self.events_table = QTableWidget(0, 4)
        self.events_table.setHorizontalHeaderLabels(
            [
                self._localization.t("integrations.monitor_time"),
                self._localization.t("integrations.monitor_source"),
                self._localization.t("integrations.monitor_event"),
                self._localization.t("integrations.monitor_detail"),
            ]
        )
        self.events_table.verticalHeader().setVisible(False)
        self.events_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.events_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.events_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.events_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.events_table)

    def _summary_card(self, layout: QGridLayout, row: int, column: int, title: str) -> QLabel:
        container = QWidget()
        box = QVBoxLayout(container)
        title_label = QLabel(title)
        title_label.setObjectName("dashboardCardTitle")
        value_label = QLabel("-")
        value_label.setObjectName("dashboardCardValue")
        box.addWidget(title_label)
        box.addWidget(value_label)
        container.setObjectName("dashboardCard")
        layout.addWidget(container, row, column)
        return value_label

    def update_summary(self, summary: dict[str, str]) -> None:
        self.listener_value.setText(summary.get("listener", "-"))
        self.clublog_value.setText(summary.get("clublog", "-"))
        self.received_value.setText(summary.get("received", "0"))
        self.saved_value.setText(summary.get("saved", "0"))
        self.uploaded_value.setText(summary.get("uploaded", "0"))
        self.failed_value.setText(summary.get("failed", "0"))
        self.pending_value.setText(summary.get("pending", "0"))

    def set_events(self, entries: list[dict[str, str]]) -> None:
        self.events_table.setRowCount(len(entries))
        for row, item in enumerate(entries):
            self.events_table.setItem(row, 0, QTableWidgetItem(item.get("time", "")))
            self.events_table.setItem(row, 1, QTableWidgetItem(item.get("source", "")))
            self.events_table.setItem(row, 2, QTableWidgetItem(item.get("event", "")))
            self.events_table.setItem(row, 3, QTableWidgetItem(item.get("detail", "")))
        self.events_table.resizeRowsToContents()
