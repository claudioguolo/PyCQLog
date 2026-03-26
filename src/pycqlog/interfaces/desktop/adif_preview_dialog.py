from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pycqlog.application.dto import AdifPreviewResult
from pycqlog.localization import LocalizationService


class AdifPreviewDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        preview: AdifPreviewResult,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._preview = preview
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("adif.preview_title"))
        self.resize(860, 480)

        root = QVBoxLayout(self)

        summary = self._localization.t(
            "adif.preview_summary",
            total=self._preview.total_count,
            ready=self._preview.ready_count,
            skipped=self._preview.skipped_count,
            failed=self._preview.failed_count,
        )
        self.summary_label = QLabel(summary)
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        actions_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(self._localization.t("adif.filter_all"), "all")
        self.filter_combo.addItem(self._localization.t("adif.filter_ready"), "ready")
        self.filter_combo.addItem(self._localization.t("adif.filter_skipped"), "skipped")
        self.filter_combo.addItem(self._localization.t("adif.filter_failed"), "failed")
        self.filter_combo.currentIndexChanged.connect(self._apply_status_filter)
        actions_layout.addWidget(QLabel(self._localization.t("adif.filter_label")))
        actions_layout.addWidget(self.filter_combo)

        self.select_ready_button = QPushButton(self._localization.t("adif.select_ready"))
        self.select_ready_button.clicked.connect(self._select_ready_rows)
        actions_layout.addWidget(self.select_ready_button)

        self.clear_selection_button = QPushButton(self._localization.t("adif.clear_selection"))
        self.clear_selection_button.clicked.connect(self._clear_selection)
        actions_layout.addWidget(self.clear_selection_button)
        actions_layout.addStretch()
        root.addLayout(actions_layout)

        self.table = QTableWidget(len(self._preview.entries), 8)
        self.table.setHorizontalHeaderLabels(
            [
                self._localization.t("adif.preview_import"),
                "#",
                self._localization.t("table.recent.callsign"),
                self._localization.t("table.recent.date"),
                self._localization.t("table.recent.time"),
                self._localization.t("label.frequency_mhz"),
                self._localization.t("table.recent.mode"),
                self._localization.t("adif.preview_status"),
            ]
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        for row, entry in enumerate(self._preview.entries[:]):
            select_item = QTableWidgetItem()
            if entry.status != "skipped":
                select_item.setFlags(select_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                select_item.setCheckState(Qt.CheckState.Checked if entry.selected else Qt.CheckState.Unchecked)
            else:
                select_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 0, select_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(entry.record_number)))
            self.table.setItem(row, 2, self._editable_item(entry.callsign, entry.status))
            self.table.setItem(row, 3, self._editable_item(entry.qso_date, entry.status))
            self.table.setItem(row, 4, self._editable_item(entry.time_on, entry.status))
            self.table.setItem(row, 5, self._editable_item(entry.freq, entry.status))
            self.table.setItem(row, 6, self._editable_item(entry.mode, entry.status))
            status_text = entry.status
            if entry.message:
                status_text = f"{entry.status}: {entry.message}"
            self.table.setItem(row, 7, QTableWidgetItem(status_text))
        self.table.resizeColumnsToContents()
        root.addWidget(self.table)
        self._apply_status_filter()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            self._localization.t("adif.preview_confirm")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._localization.t("button.cancel")
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

    def selected_record_numbers(self) -> set[int]:
        selected: set[int] = set()
        for row, entry in enumerate(self._preview.entries):
            if entry.status == "skipped":
                continue
            item = self.table.item(row, 0)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                selected.add(entry.record_number)
        return selected

    def edited_values(self) -> dict[int, dict[str, str]]:
        values: dict[int, dict[str, str]] = {}
        for row, entry in enumerate(self._preview.entries):
            values[entry.record_number] = {
                "callsign": self._table_text(row, 2),
                "qso_date": self._table_text(row, 3),
                "time_on": self._table_text(row, 4),
                "freq": self._table_text(row, 5),
                "mode": self._table_text(row, 6),
            }
        return values

    def _editable_item(self, text: str, status: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if status == "skipped":
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _table_text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        return item.text().strip() if item is not None else ""

    def _set_selection_for_rows(self, statuses: set[str], checked: Qt.CheckState) -> None:
        for row, entry in enumerate(self._preview.entries):
            if entry.status not in statuses:
                continue
            item = self.table.item(row, 0)
            if item is None:
                continue
            if not item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                continue
            item.setCheckState(checked)

    def _select_ready_rows(self) -> None:
        self._set_selection_for_rows({"ready", "failed"}, Qt.CheckState.Unchecked)
        self._set_selection_for_rows({"ready"}, Qt.CheckState.Checked)

    def _clear_selection(self) -> None:
        self._set_selection_for_rows({"ready", "failed"}, Qt.CheckState.Unchecked)

    def _apply_status_filter(self) -> None:
        selected_status = self.filter_combo.currentData()
        for row, entry in enumerate(self._preview.entries):
            should_show = selected_status in (None, "all") or entry.status == selected_status
            self.table.setRowHidden(row, not should_show)
