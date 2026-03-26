from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pycqlog.application.dto import DashboardStats, StatsSlice
from pycqlog.localization import LocalizationService


BAND_COLORS = {
    "160m": "#8b5e3c",
    "80m": "#b35c44",
    "40m": "#d97757",
    "20m": "#f4a261",
    "15m": "#e9c46a",
    "10m": "#2a9d8f",
    "6m": "#3a86ff",
}

MODE_COLORS = {
    "FT8": "#3a86ff",
    "CW": "#e9c46a",
    "SSB": "#d97757",
    "AM": "#f4a261",
    "FM": "#2a9d8f",
    "RTTY": "#9b5de5",
}

DEFAULT_SERIES_COLORS = ["#d97757", "#e9c46a", "#2a9d8f", "#3a86ff", "#9b5de5", "#f4a261"]


class DashboardChart(QWidget):
    def __init__(self, title: str, slices: list[StatsSlice], color_key: str = "", parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self._slices = slices
        self._color_key = color_key
        self.setMinimumHeight(220)

    def set_data(self, title: str, slices: list[StatsSlice], color_key: str = "") -> None:
        self._title = title
        self._slices = slices
        self._color_key = color_key
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)
        painter.setPen(QColor("#7a8896"))
        painter.drawText(rect.left(), rect.top() + 12, self._title)
        if not self._slices:
            painter.drawText(rect.adjusted(0, 30, 0, 0), Qt.AlignmentFlag.AlignCenter, "No data")
            return

        chart_rect = rect.adjusted(0, 30, 0, 0)
        max_value = max(item.value for item in self._slices) or 1
        row_height = max(18, chart_rect.height() // max(len(self._slices), 1))
        bar_area_width = max(120, chart_rect.width() - 140)
        for index, item in enumerate(self._slices):
            y = chart_rect.top() + index * row_height
            label_rect = QRectF(chart_rect.left(), y, 90, row_height - 4)
            bar_bg = QRectF(chart_rect.left() + 96, y + 2, bar_area_width, row_height - 8)
            bar_width = (item.value / max_value) * bar_area_width
            bar_fg = QRectF(bar_bg.left(), bar_bg.top(), bar_width, bar_bg.height())
            painter.setPen(QColor("#95a2af"))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, item.label)
            painter.setPen(QPen(QColor("#3b4654")))
            painter.setBrush(QColor("#2f3945"))
            painter.drawRoundedRect(bar_bg, 4, 4)
            painter.setBrush(QColor(self._bar_color(item.label, index)))
            painter.drawRoundedRect(bar_fg, 4, 4)
            painter.setPen(QColor("#dfe7ee"))
            painter.drawText(
                QRectF(bar_bg.right() + 8, y, 32, row_height - 4),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(item.value),
            )

    def _bar_color(self, label: str, index: int) -> str:
        if self._color_key == "band":
            return BAND_COLORS.get(label, DEFAULT_SERIES_COLORS[index % len(DEFAULT_SERIES_COLORS)])
        if self._color_key == "mode":
            return MODE_COLORS.get(label.upper(), DEFAULT_SERIES_COLORS[index % len(DEFAULT_SERIES_COLORS)])
        return DEFAULT_SERIES_COLORS[index % len(DEFAULT_SERIES_COLORS)]


class DashboardDialog(QDialog):
    def __init__(self, localization: LocalizationService, stats_loader, chart_preferences_loader, parent=None) -> None:
        super().__init__(parent)
        self._localization = localization
        self._stats_loader = stats_loader
        self._chart_preferences_loader = chart_preferences_loader
        self._stats = self._stats_loader(None)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._localization.t("dashboard.title"))
        self.resize(980, 720)

        root = QVBoxLayout(self)
        self.logbook_label = QLabel()
        self.logbook_label.setObjectName("filterLabel")
        root.addWidget(self.logbook_label)

        controls_row = QHBoxLayout()
        self.period_label = QLabel(self._localization.t("dashboard.period"))
        self.period_combo = QComboBox()
        self.period_combo.addItem(self._localization.t("dashboard.period_all"), None)
        self.period_combo.addItem(self._localization.t("dashboard.period_7d"), 7)
        self.period_combo.addItem(self._localization.t("dashboard.period_30d"), 30)
        self.period_combo.addItem(self._localization.t("dashboard.period_365d"), 365)
        self.period_combo.currentIndexChanged.connect(self._refresh_from_filter)
        controls_row.addWidget(self.period_label)
        controls_row.addWidget(self.period_combo)
        controls_row.addStretch(1)
        root.addLayout(controls_row)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(12)
        summary_grid.setVerticalSpacing(12)

        self.summary_total = self._summary_card(
            self._localization.t("dashboard.total_qsos"),
            str(self._stats.total_qsos),
        )
        self.summary_callsigns = self._summary_card(
            self._localization.t("dashboard.unique_callsigns"),
            str(self._stats.unique_callsigns),
        )
        self.summary_bands = self._summary_card(
            self._localization.t("dashboard.active_bands"),
            str(self._stats.active_bands),
        )
        self.summary_modes = self._summary_card(
            self._localization.t("dashboard.active_modes"),
            str(self._stats.active_modes),
        )
        self.summary_dxcc = self._summary_card(
            self._localization.t("dashboard.dxcc_entities"),
            str(self._stats.dxcc_entities),
        )
        self.summary_waz = self._summary_card(
            self._localization.t("dashboard.waz_zones"),
            str(self._stats.waz_zones),
        )
        self.summary_wpx = self._summary_card(
            self._localization.t("dashboard.wpx_prefixes"),
            str(self._stats.wpx_prefixes),
        )

        summary_grid.addWidget(self.summary_total, 0, 0)
        summary_grid.addWidget(self.summary_callsigns, 0, 1)
        summary_grid.addWidget(self.summary_bands, 1, 0)
        summary_grid.addWidget(self.summary_modes, 1, 1)
        summary_grid.addWidget(self.summary_dxcc, 2, 0)
        summary_grid.addWidget(self.summary_waz, 2, 1)
        summary_grid.addWidget(self.summary_wpx, 3, 0, 1, 2)
        root.addLayout(summary_grid)

        charts_grid = QGridLayout()
        charts_grid.setHorizontalSpacing(12)
        charts_grid.setVerticalSpacing(12)
        preferences = self._chart_preferences_loader()
        self.band_chart = DashboardChart(
            self._localization.t("dashboard.chart_bands"),
            self._stats.by_band,
            "band" if preferences["use_band_colors"] else "",
        )
        self.mode_chart = DashboardChart(
            self._localization.t("dashboard.chart_modes"),
            self._stats.by_mode,
            "mode" if preferences["use_mode_colors"] else "",
        )
        self.day_chart = DashboardChart(self._localization.t("dashboard.chart_days"), self._stats.by_day)
        self.month_chart = DashboardChart(self._localization.t("dashboard.chart_months"), self._stats.by_month)
        self.hour_chart = DashboardChart(self._localization.t("dashboard.chart_hours"), self._stats.by_hour)
        charts_grid.addWidget(self.band_chart, 0, 0)
        charts_grid.addWidget(self.mode_chart, 0, 1)
        charts_grid.addWidget(self.day_chart, 1, 0)
        charts_grid.addWidget(self.month_chart, 1, 1)
        charts_grid.addWidget(self.hour_chart, 2, 0, 1, 2)
        root.addLayout(charts_grid)

        self.top_callsigns_label = QLabel(self._localization.t("dashboard.top_callsigns"))
        self.top_callsigns_label.setObjectName("sectionLabel")
        root.addWidget(self.top_callsigns_label)

        self.top_callsigns_table = QTableWidget(len(self._stats.top_callsigns), 2)
        self.top_callsigns_table.setHorizontalHeaderLabels(
            [
                self._localization.t("table.recent.callsign"),
                self._localization.t("dashboard.contacts"),
            ]
        )
        self.top_callsigns_table.verticalHeader().setVisible(False)
        self.top_callsigns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row, item in enumerate(self._stats.top_callsigns):
            self.top_callsigns_table.setItem(row, 0, QTableWidgetItem(item.label))
            self.top_callsigns_table.setItem(row, 1, QTableWidgetItem(str(item.value)))
        root.addWidget(self.top_callsigns_table)

    def refresh(self) -> None:
        self._refresh_from_filter()

    def _refresh_from_filter(self) -> None:
        self._stats = self._stats_loader(self.period_combo.currentData())
        preferences = self._chart_preferences_loader()
        self.logbook_label.setText(
            self._localization.t("dashboard.active_logbook", name=self._stats.logbook_name or "-")
        )
        self._set_summary_value(self.summary_total, str(self._stats.total_qsos))
        self._set_summary_value(self.summary_callsigns, str(self._stats.unique_callsigns))
        self._set_summary_value(self.summary_bands, str(self._stats.active_bands))
        self._set_summary_value(self.summary_modes, str(self._stats.active_modes))
        self._set_summary_value(self.summary_dxcc, str(self._stats.dxcc_entities))
        self._set_summary_value(self.summary_waz, str(self._stats.waz_zones))
        self._set_summary_value(self.summary_wpx, str(self._stats.wpx_prefixes))
        self.band_chart.set_data(
            self._localization.t("dashboard.chart_bands"),
            self._stats.by_band,
            "band" if preferences["use_band_colors"] else "",
        )
        self.mode_chart.set_data(
            self._localization.t("dashboard.chart_modes"),
            self._stats.by_mode,
            "mode" if preferences["use_mode_colors"] else "",
        )
        self.day_chart.set_data(self._localization.t("dashboard.chart_days"), self._stats.by_day)
        self.month_chart.set_data(self._localization.t("dashboard.chart_months"), self._stats.by_month)
        self.hour_chart.set_data(self._localization.t("dashboard.chart_hours"), self._stats.by_hour)
        self.top_callsigns_table.setRowCount(len(self._stats.top_callsigns))
        for row, item in enumerate(self._stats.top_callsigns):
            self.top_callsigns_table.setItem(row, 0, QTableWidgetItem(item.label))
            self.top_callsigns_table.setItem(row, 1, QTableWidgetItem(str(item.value)))
        self.top_callsigns_table.resizeColumnsToContents()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._refresh_from_filter()

    def _summary_card(self, title: str, value: str) -> QWidget:
        container = QWidget()
        container.setObjectName("dashboardCard")
        layout = QVBoxLayout(container)
        title_label = QLabel(title)
        title_label.setObjectName("dashboardCardTitle")
        value_label = QLabel(value)
        value_label.setObjectName("dashboardCardValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return container

    def _set_summary_value(self, container: QWidget, value: str) -> None:
        value_label = container.findChild(QLabel, "dashboardCardValue")
        if value_label is not None:
            value_label.setText(value)
