from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QSplitter,
)

from pycqlog.application.dto import QsoListItem, SaveQsoCommand
from pycqlog.application.dto import AdifExportFilter
from pycqlog.application.use_cases import (
    DeleteLogbookUseCase,
    DeleteQsoUseCase,
    DeleteStationProfileUseCase,
    ExportAdifUseCase,
    GetActiveLogbookUseCase,
    GetDashboardStatsUseCase,
    GetCallsignHistoryUseCase,
    GetQsoDetailUseCase,
    ImportAdifUseCase,
    ListLogbooksUseCase,
    ListRecentQsosUseCase,
    ListStationProfilesUseCase,
    SaveLogbookUseCase,
    SaveQsoUseCase,
    SaveStationProfileUseCase,
    SearchQsosUseCase,
    SetActiveLogbookUseCase,
    FetchCallbookInfoUseCase,
)
from pycqlog.domain.services import QsoValidationError
from pycqlog.infrastructure.adif_export import AdifExporter
from pycqlog.infrastructure.app_logging import configure_app_logging, current_log_file, get_logger
from pycqlog.infrastructure.remote_station_service import RemoteStationService
from pycqlog.infrastructure.settings import JsonSettingsStore, UI_SETTINGS_KEYS
from pycqlog.infrastructure.station_service import StationService
from pycqlog.interfaces.desktop.adif_preview_dialog import AdifPreviewDialog
from pycqlog.interfaces.desktop.adif_settings_dialog import AdifSettingsDialog
from pycqlog.interfaces.desktop.dashboard_dialog import DashboardDialog
from pycqlog.interfaces.desktop.dashboard_settings_dialog import DashboardSettingsDialog
from pycqlog.interfaces.desktop.directories_dialog import DirectoriesDialog
from pycqlog.interfaces.desktop.export_adif_dialog import ExportAdifDialog
from pycqlog.interfaces.desktop.integration_settings_dialog import IntegrationSettingsDialog
from pycqlog.interfaces.desktop.integration_monitor_dialog import IntegrationMonitorDialog
from pycqlog.interfaces.desktop.logbooks_dialog import LogbooksDialog
from pycqlog.interfaces.desktop.station_profiles_dialog import StationProfilesDialog
from pycqlog.localization import LocalizationService
from pycqlog.themes import build_stylesheet, resolve_theme
from pycqlog.ui_colors import color_for_band, color_for_mode, contrasting_text_color


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value: int) -> None:
        super().__init__(str(value))
        self._numeric_value = value

    def __lt__(self, other: object) -> bool:
        if isinstance(other, NumericTableWidgetItem):
            return self._numeric_value < other._numeric_value
        if isinstance(other, QTableWidgetItem):
            try:
                return self._numeric_value < int(other.text())
            except ValueError:
                return super().__lt__(other)
        return NotImplemented


class ProportionalTableWidget(QTableWidget):
    def __init__(self, rows: int, columns: int, column_weights: list[int]) -> None:
        super().__init__(rows, columns)
        self._column_weights = column_weights
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.apply_proportional_widths()

    def apply_proportional_widths(self) -> None:
        if not self._column_weights or len(self._column_weights) != self.columnCount():
            return
        available_width = max(0, self.viewport().width())
        if available_width <= 0:
            return
        total_weight = sum(self._column_weights)
        widths = [max(32, (available_width * weight) // total_weight) for weight in self._column_weights]
        overflow = sum(widths) - available_width
        if overflow > 0:
            for index in range(len(widths) - 1, -1, -1):
                reducible = widths[index] - 32
                if reducible <= 0:
                    continue
                reduction = min(reducible, overflow)
                widths[index] -= reduction
                overflow -= reduction
                if overflow <= 0:
                    break
        elif overflow < 0:
            widths[-1] += -overflow
        for column, width in enumerate(widths):
            self.setColumnWidth(column, width)


class MainWindow(QMainWindow):
    _CONTENT_MIN_WIDTH = 760

    def __init__(
        self,
        save_qso: SaveQsoUseCase,
        list_recent_qsos: ListRecentQsosUseCase,
        get_qso_detail: GetQsoDetailUseCase,
        delete_qso: DeleteQsoUseCase,
        search_qsos: SearchQsosUseCase,
        get_callsign_history: GetCallsignHistoryUseCase,
        get_dashboard_stats: GetDashboardStatsUseCase,
        import_adif: ImportAdifUseCase,
        export_adif: ExportAdifUseCase,
        list_logbooks: ListLogbooksUseCase,
        get_active_logbook: GetActiveLogbookUseCase,
        save_logbook: SaveLogbookUseCase,
        delete_logbook: DeleteLogbookUseCase,
        set_active_logbook: SetActiveLogbookUseCase,
        list_station_profiles: ListStationProfilesUseCase,
        save_station_profile: SaveStationProfileUseCase,
        delete_station_profile: DeleteStationProfileUseCase,
        fetch_callbook_info: FetchCallbookInfoUseCase,
        localization: LocalizationService,
        ui_settings_store: JsonSettingsStore,
        daemon_settings_store: JsonSettingsStore,
        data_dir: Path,
        config_dir: Path,
    ) -> None:
        super().__init__()
        self._save_qso_use_case = save_qso
        self._list_recent_qsos_use_case = list_recent_qsos
        self._get_qso_detail_use_case = get_qso_detail
        self._delete_qso_use_case = delete_qso
        self._search_qsos_use_case = search_qsos
        self._get_callsign_history_use_case = get_callsign_history
        self._get_dashboard_stats_use_case = get_dashboard_stats
        self._import_adif_use_case = import_adif
        self._export_adif_use_case = export_adif
        self._list_logbooks_use_case = list_logbooks
        self._get_active_logbook_use_case = get_active_logbook
        self._save_logbook_use_case = save_logbook
        self._delete_logbook_use_case = delete_logbook
        self._set_active_logbook_use_case = set_active_logbook
        self._list_station_profiles_use_case = list_station_profiles
        self._save_station_profile_use_case = save_station_profile
        self._delete_station_profile_use_case = delete_station_profile
        self._fetch_callbook_info_use_case = fetch_callbook_info
        self._localization = localization
        self._ui_settings_store = ui_settings_store
        self._daemon_settings_store = daemon_settings_store
        self._active_data_dir = data_dir
        self._config_dir = config_dir
        self._logger = get_logger("ui.main_window")
        self._editing_qso_id: int | None = None
        self._current_status_key = "status.ready_first"
        self._current_status_params: dict[str, object] = {}
        self._last_history_callsign = ""
        self._last_history_count = 0
        self._loaded_qso_items: list[QsoListItem] = []
        self._active_band_filters: set[str] = set()
        self._active_mode_filters: set[str] = set()
        self._band_filter_buttons: dict[str, QPushButton] = {}
        self._mode_filter_buttons: dict[str, QPushButton] = {}
        self._data_dir = self._daemon_settings_store.get_string("data_dir", str(self._active_data_dir))
        self._log_dir = self._daemon_settings_store.get_string("log_dir", self._data_dir)
        self._theme_name = self._ui_settings_store.get_string("theme", "system")
        self._remote_service_enabled = False
        self._remote_service_host = "127.0.0.1"
        self._remote_service_port = 8746
        self._remote_service_auth_code = ""
        self._theme_stylesheet = ""
        self._dashboard_dialog: DashboardDialog | None = None
        self._integration_monitor_dialog: IntegrationMonitorDialog | None = None
        self._adif_exporter = AdifExporter()
        self._build_ui()
        self._station_service = self._create_station_service()
        self._load_logbook_options()
        self._apply_translations()
        self._apply_saved_defaults()
        self._station_service.start()
        self._integration_timer = QTimer(self)
        self._integration_timer.setInterval(1200)
        self._integration_timer.timeout.connect(self._poll_integrations)
        self._integration_timer.start()
        self._load_recent_qsos()
        self._logger.info(
            "Main window initialized. data_dir=%s log_dir=%s log_file=%s remote_service_enabled=%s remote_service=%s:%s",
            self._data_dir,
            self._log_dir,
            current_log_file(),
            self._remote_service_enabled,
            self._remote_service_host,
            self._remote_service_port,
        )

    def _build_ui(self) -> None:
        self.resize(956, 538)
        self.setMinimumSize(760, 490)
        self._build_menu()

        central = QWidget(self)
        central.setMinimumWidth(self._CONTENT_MIN_WIDTH)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        top_bar = QFrame()
        top_bar.setObjectName("workspaceCard")
        top_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_bar_root = QHBoxLayout(top_bar)
        top_bar_root.setContentsMargins(14, 12, 14, 12)
        top_bar_root.setSpacing(10)

        hero_block = QVBoxLayout()
        hero_block.setSpacing(2)
        self.operation_badge_label = QLabel()
        self.operation_badge_label.setObjectName("consoleBadge")
        hero_block.addWidget(self.operation_badge_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.header_label = QLabel()
        self.header_label.setObjectName("headerLabel")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hero_block.addWidget(self.header_label)

        self.console_hint_label = QLabel()
        self.console_hint_label.setObjectName("mutedLabel")
        self.console_hint_label.setWordWrap(True)
        hero_block.addWidget(self.console_hint_label)
        top_bar_root.addLayout(hero_block, 4)

        self.top_logbook_title = QLabel()
        self.top_logbook_title.setObjectName("summaryCardTitle")
        self.top_logbook_value = QLabel()
        self.top_logbook_value.setObjectName("summaryCardValue")
        top_bar_root.addWidget(self._build_summary_card(self.top_logbook_title, self.top_logbook_value), 2)

        self.top_integrations_title = QLabel()
        self.top_integrations_title.setObjectName("summaryCardTitle")
        self.top_integrations_value = QLabel()
        self.top_integrations_value.setObjectName("summaryCardValue")
        top_bar_root.addWidget(self._build_summary_card(self.top_integrations_title, self.top_integrations_value), 2)

        self.top_pending_title = QLabel()
        self.top_pending_title.setObjectName("summaryCardTitle")
        self.top_pending_value = QLabel()
        self.top_pending_value.setObjectName("summaryCardValue")
        top_bar_root.addWidget(self._build_summary_card(self.top_pending_title, self.top_pending_value), 1)

        root.addWidget(top_bar)

        entry_card = QFrame()
        entry_card.setObjectName("entryBarCard")
        entry_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        entry_root = QVBoxLayout(entry_card)
        entry_root.setContentsMargins(12, 10, 12, 10)
        entry_root.setSpacing(6)

        entry_header_row = QHBoxLayout()
        entry_header_row.setSpacing(8)
        self.entry_header_label = QLabel()
        self.entry_header_label.setObjectName("sectionLabel")
        entry_header_row.addWidget(self.entry_header_label)

        self.entry_hint_label = QLabel()
        self.entry_hint_label.setObjectName("mutedLabel")
        self.entry_hint_label.setWordWrap(True)
        entry_header_row.addWidget(self.entry_hint_label, 1)
        entry_root.addLayout(entry_header_row)

        self._entry_field_labels: dict[str, QLabel] = {}
        capture_row = QHBoxLayout()
        capture_row.setSpacing(8)

        self.callsign_input = QLineEdit()
        self.callsign_input.setObjectName("callsignHeroInput")
        self.callsign_input.setMaxLength(10)
        self.callsign_input.editingFinished.connect(self._refresh_history_from_form)
        capture_row.addWidget(self._build_entry_field("callsign", self.callsign_input, min_width=138, max_width=168), 3)

        self.date_input = QLineEdit()
        self.date_input.setText(date.today().isoformat())
        capture_row.addWidget(self._build_entry_field("date", self.date_input, min_width=112), 2)

        self.time_input = QLineEdit()
        self.time_input.setText(datetime.now().strftime("%H:%M"))
        capture_row.addWidget(self._build_entry_field("time", self.time_input, min_width=84), 1)

        self.freq_input = QLineEdit()
        capture_row.addWidget(self._build_entry_field("frequency_mhz", self.freq_input, min_width=106), 2)

        self.mode_input = QLineEdit()
        capture_row.addWidget(self._build_entry_field("mode", self.mode_input, min_width=92), 1)

        self.rst_sent_input = QLineEdit()
        capture_row.addWidget(self._build_entry_field("rst_sent", self.rst_sent_input, min_width=70), 1)

        self.rst_recv_input = QLineEdit()
        capture_row.addWidget(self._build_entry_field("rst_recv", self.rst_recv_input, min_width=70), 1)

        self.operator_input = QLineEdit()
        self.station_callsign_input = QLineEdit()

        self.save_button = QPushButton()
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._save_qso)
        capture_row.addWidget(self._build_action_field(self.save_button), 1)

        self.clear_button = QPushButton()
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self._reset_form)
        capture_row.addWidget(self._build_action_field(self.clear_button), 1)
        entry_root.addLayout(capture_row)

        notes_row = QHBoxLayout()
        notes_row.setSpacing(8)
        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(42)
        self.notes_input.setMaximumHeight(56)
        notes_row.addWidget(self._build_entry_field("notes", self.notes_input), 1)
        entry_root.addLayout(notes_row)
        root.addWidget(entry_card)

        center_panel = QWidget()
        center_panel.setMinimumWidth(440)
        center_root = QVBoxLayout(center_panel)
        center_root.setContentsMargins(0, 0, 0, 0)
        center_root.setSpacing(10)

        list_card = QFrame()
        list_card.setObjectName("workspaceCard")
        list_root = QVBoxLayout(list_card)
        list_root.setContentsMargins(14, 12, 14, 12)
        list_root.setSpacing(8)

        list_header_row = QHBoxLayout()
        list_header_col = QVBoxLayout()
        list_header_col.setSpacing(2)
        self.recent_header = QLabel()
        self.recent_header.setObjectName("sectionLabel")
        list_header_col.addWidget(self.recent_header)

        self.recent_summary_label = QLabel()
        self.recent_summary_label.setObjectName("mutedLabel")
        list_header_col.addWidget(self.recent_summary_label)
        list_header_row.addLayout(list_header_col, 1)

        header_actions = QHBoxLayout()
        header_actions.setSpacing(8)
        self.edit_button = QPushButton()
        self.edit_button.setObjectName("secondaryButton")
        self.edit_button.clicked.connect(self._load_selected_qso)
        self.edit_button.setEnabled(False)
        header_actions.addWidget(self.edit_button)

        self.delete_button = QPushButton()
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self._delete_selected_qso)
        self.delete_button.setEnabled(False)
        header_actions.addWidget(self.delete_button)
        list_header_row.addLayout(header_actions)
        list_root.addLayout(list_header_row)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.quick_filters_label = QLabel()
        self.quick_filters_label.setObjectName("filterLabel")
        search_row.addWidget(self.quick_filters_label)

        self.band_filters_row = QHBoxLayout()
        self.band_filters_row.setSpacing(6)
        self.band_filters_label = QLabel()
        self.band_filters_label.setObjectName("inlineFilterLabel")
        self.band_filters_row.addWidget(self.band_filters_label)
        self.band_filters_host = QWidget()
        self.band_filters_host.setLayout(self.band_filters_row)
        search_row.addWidget(self.band_filters_host)

        self.mode_filters_row = QHBoxLayout()
        self.mode_filters_row.setSpacing(6)
        self.mode_filters_label = QLabel()
        self.mode_filters_label.setObjectName("inlineFilterLabel")
        self.mode_filters_row.addWidget(self.mode_filters_label)
        self.mode_filters_host = QWidget()
        self.mode_filters_host.setLayout(self.mode_filters_row)
        search_row.addWidget(self.mode_filters_host)

        self.clear_filters_button = QPushButton()
        self.clear_filters_button.setObjectName("quickFilterChip")
        self.clear_filters_button.clicked.connect(self._clear_quick_filters)
        search_row.addWidget(self.clear_filters_button)

        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._search_qsos)
        search_row.addWidget(self.search_input, 1)

        self.search_button = QPushButton()
        self.search_button.setObjectName("secondaryButton")
        self.search_button.clicked.connect(self._search_qsos)
        search_row.addWidget(self.search_button)
        list_root.addLayout(search_row)

        self.qso_table = ProportionalTableWidget(0, 6, [10, 24, 18, 12, 12, 12])
        self.qso_table.setObjectName("denseTable")
        self.qso_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.qso_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.qso_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.qso_table.setAlternatingRowColors(True)
        self.qso_table.setSortingEnabled(True)
        self.qso_table.verticalHeader().setVisible(False)
        self.qso_table.horizontalHeader().setHighlightSections(False)
        self.qso_table.itemSelectionChanged.connect(self._handle_selection_changed)
        list_root.addWidget(self.qso_table, 1)
        center_root.addWidget(list_card, 1)

        history_card = QFrame()
        history_card.setObjectName("workspaceCard")
        history_card.setMinimumWidth(280)
        history_root = QVBoxLayout(history_card)
        history_root.setContentsMargins(14, 12, 14, 12)
        history_root.setSpacing(8)

        self.history_header = QLabel()
        self.history_header.setObjectName("sectionLabel")
        history_root.addWidget(self.history_header)

        self.history_summary_label = QLabel()
        self.history_summary_label.setWordWrap(True)
        self.history_summary_label.setObjectName("mutedLabel")
        history_root.addWidget(self.history_summary_label)

        self.history_table = ProportionalTableWidget(0, 6, [10, 20, 12, 12, 12, 14])
        self.history_table.setObjectName("denseTable")
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setHighlightSections(False)
        history_root.addWidget(self.history_table, 1)

        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        body_splitter.addWidget(center_panel)
        body_splitter.addWidget(history_card)
        body_splitter.setStretchFactor(0, 4)
        body_splitter.setStretchFactor(1, 3)
        body_splitter.setSizes([620, 320])
        root.addWidget(body_splitter, 1)

        footer_bar = QFrame()
        footer_bar.setObjectName("footerStatusBar")
        footer_root = QHBoxLayout(footer_bar)
        footer_root.setContentsMargins(8, 6, 8, 6)
        footer_root.setSpacing(10)

        self.footer_logbook_label = QLabel()
        self.footer_logbook_label.setObjectName("footerMeta")
        footer_root.addWidget(self.footer_logbook_label)

        self.footer_integrations_label = QLabel()
        self.footer_integrations_label.setObjectName("footerMeta")
        footer_root.addWidget(self.footer_integrations_label)

        self.footer_pending_label = QLabel()
        self.footer_pending_label.setObjectName("footerMeta")
        footer_root.addWidget(self.footer_pending_label)

        footer_root.addStretch(1)

        self.status_label = QLabel()
        self.status_label.setObjectName("footerStatus")
        self.status_label.setWordWrap(True)
        footer_root.addWidget(self.status_label, 2)
        root.addWidget(footer_bar)

        self.setCentralWidget(central)

    def _build_summary_card(self, title_label: QLabel, value_label: QLabel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("summaryCard")
        frame.setMinimumWidth(150)
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        self.app_menu = menu_bar.addMenu("")
        self.dashboard_menu = menu_bar.addMenu("")
        self.settings_menu = menu_bar.addMenu("")
        self.help_menu = menu_bar.addMenu("")
        self.language_menu = self.settings_menu.addMenu("")
        self.theme_menu = self.settings_menu.addMenu("")
        self.dashboard_settings_menu = self.settings_menu.addMenu("")
        self.integration_menu = self.settings_menu.addMenu("")
        self.adif_menu = self.settings_menu.addMenu("")

        self.exit_action = QAction(self)
        self.exit_action.triggered.connect(self.close)
        self.directories_action = QAction(self)
        self.directories_action.triggered.connect(self._open_settings_dialog)
        self.open_dashboard_action = QAction(self)
        self.open_dashboard_action.triggered.connect(self._open_dashboard)
        self.dashboard_colors_action = QAction(self)
        self.dashboard_colors_action.triggered.connect(self._open_dashboard_settings_dialog)
        self.import_adif_action = QAction(self)
        self.import_adif_action.triggered.connect(self._import_adif)
        self.export_adif_action = QAction(self)
        self.export_adif_action.triggered.connect(self._export_adif)
        self.export_lotw_action = QAction(self)
        self.export_lotw_action.triggered.connect(self._export_lotw_tqsl)
        self.adif_preferences_action = QAction(self)
        self.adif_preferences_action.triggered.connect(self._open_adif_settings_dialog)
        self.manage_logbooks_action = QAction(self)
        self.manage_logbooks_action.triggered.connect(self._open_logbooks_dialog)
        self.manage_profiles_action = QAction(self)
        self.manage_profiles_action.triggered.connect(self._open_station_profiles_dialog)
        self.integration_settings_action = QAction(self)
        self.integration_settings_action.triggered.connect(self._open_integration_settings_dialog)
        self.integration_monitor_action = QAction(self)
        self.integration_monitor_action.triggered.connect(self._open_integration_monitor_dialog)
        self.dashboard_menu.addAction(self.open_dashboard_action)
        self.settings_menu.addAction(self.directories_action)
        self.settings_menu.addAction(self.manage_logbooks_action)
        self.settings_menu.addAction(self.manage_profiles_action)
        self.dashboard_settings_menu.addAction(self.dashboard_colors_action)
        self.integration_menu.addAction(self.integration_settings_action)
        self.integration_menu.addAction(self.integration_monitor_action)
        self.adif_menu.addAction(self.adif_preferences_action)
        self.adif_menu.addSeparator()
        self.adif_menu.addAction(self.import_adif_action)
        self.adif_menu.addAction(self.export_adif_action)
        self.adif_menu.addAction(self.export_lotw_action)
        self.app_menu.addAction(self.exit_action)

        self.about_action = QAction(self)
        self.about_action.triggered.connect(self._show_about)
        self.help_menu.addAction(self.about_action)

        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        self.language_actions: dict[str, QAction] = {}
        for language in self._localization.available_languages():
            action = QAction(self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, code=language: self._change_language(code)
            )
            self.language_action_group.addAction(action)
            self.language_menu.addAction(action)
            self.language_actions[language] = action

        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for theme in ("system", "light", "dark"):
            action = QAction(self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, value=theme: self._change_theme(value)
            )
            self.theme_action_group.addAction(action)
            self.theme_menu.addAction(action)
            self.theme_actions[theme] = action

    def _build_entry_field(
        self,
        key: str,
        field: QWidget,
        min_width: int | None = None,
        max_width: int | None = None,
    ) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label = QLabel()
        label.setObjectName("fieldHeroLabel")
        layout.addWidget(label)
        if min_width is not None:
            field.setMinimumWidth(min_width)
        if max_width is not None:
            field.setMaximumWidth(max_width)
        layout.addWidget(field)
        self._entry_field_labels[key] = label
        return wrapper

    def _build_action_field(self, button: QPushButton) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        spacer = QLabel(" ")
        spacer.setObjectName("fieldHeroLabel")
        layout.addWidget(spacer)
        button.setMinimumWidth(104)
        layout.addWidget(button)
        return wrapper

    def _apply_translations(self) -> None:
        self.setWindowTitle(self._app_window_title())
        self.operation_badge_label.setText(self._t("section.operation_console"))
        self.header_label.setText(self._t("section.manual_entry"))
        self.console_hint_label.setText(self._t("section.operation_console_hint"))
        self.entry_header_label.setText(self._t("section.qso_capture"))
        self.entry_hint_label.setText(self._t("section.qso_capture_hint"))
        self.recent_header.setText(self._t("section.recent_qsos"))
        self.history_header.setText(self._t("section.callsign_history"))
        self.top_logbook_title.setText(self._t("summary.logbook"))
        self.top_integrations_title.setText(self._t("summary.integrations"))
        self.top_pending_title.setText(self._t("summary.pending"))

        compact_labels = {
            "callsign": self._t("label.callsign"),
            "date": self._t("label.date"),
            "time": self._t("label.time"),
            "frequency_mhz": self._t("label.frequency_mhz"),
            "mode": self._t("label.mode"),
            "rst_sent": self._t("label.rst_sent"),
            "rst_recv": self._t("label.rst_recv"),
            "operator": self._t("label.operator"),
            "station": self._t("label.station"),
            "notes": self._t("label.notes"),
        }
        for key, text in compact_labels.items():
            label = self._entry_field_labels.get(key)
            if label is not None:
                label.setText(text)

        self.callsign_input.setPlaceholderText(self._t("placeholder.callsign"))
        self.date_input.setPlaceholderText(self._t("placeholder.date"))
        self.time_input.setPlaceholderText(self._t("placeholder.time"))
        self.freq_input.setPlaceholderText(self._t("placeholder.frequency"))
        self.mode_input.setPlaceholderText(self._t("placeholder.mode"))
        self.rst_sent_input.setPlaceholderText(self._t("placeholder.rst"))
        self.rst_recv_input.setPlaceholderText(self._t("placeholder.rst"))
        self.operator_input.setPlaceholderText(self._t("placeholder.operator"))
        self.station_callsign_input.setPlaceholderText(self._t("placeholder.station"))
        self.notes_input.setPlaceholderText(self._t("placeholder.notes"))
        self.search_input.setPlaceholderText(self._t("placeholder.search_callsign"))
        self.quick_filters_label.setText(self._t("section.quick_filters"))
        self.band_filters_label.setText(self._t("filter.band"))
        self.mode_filters_label.setText(self._t("filter.mode"))
        self.clear_filters_button.setText(self._t("filter.clear"))
        self.save_button.setText(
            self._t("button.update_qso") if self._editing_qso_id is not None else self._t("button.save_qso")
        )
        self.clear_button.setText(self._t("button.new_qso"))
        self.search_button.setText(self._t("button.search"))
        self.edit_button.setText(self._t("button.edit_selected"))
        self.delete_button.setText(self._t("button.delete_selected"))

        self.recent_summary_label.setText(self._t("summary.visible_qsos", count=len(self._loaded_qso_items)))
        self.qso_table.setHorizontalHeaderLabels(
            [
                self._t("table.recent.id"),
                self._t("table.recent.callsign"),
                self._t("table.recent.date"),
                self._t("table.recent.time"),
                self._t("table.recent.band"),
                self._t("table.recent.mode"),
            ]
        )
        self.history_table.setHorizontalHeaderLabels(
            [
                self._t("table.history.id"),
                self._t("table.history.date"),
                self._t("table.history.time"),
                self._t("table.history.band"),
                self._t("table.history.mode"),
                self._t("table.history.rst"),
            ]
        )

        self.app_menu.setTitle(self._t("menu.app"))
        self.dashboard_menu.setTitle(self._t("menu.dashboard"))
        self.settings_menu.setTitle(self._t("menu.settings"))
        self.language_menu.setTitle(self._t("menu.language"))
        self.theme_menu.setTitle(self._t("menu.theme"))
        self.dashboard_settings_menu.setTitle(self._t("menu.dashboard"))
        self.integration_menu.setTitle(self._t("menu.integrations"))
        self.adif_menu.setTitle(self._t("menu.adif"))
        self.help_menu.setTitle(self._t("menu.help"))
        self.open_dashboard_action.setText(self._t("menu.dashboard_open"))
        self.directories_action.setText(self._t("menu.directories"))
        self.manage_logbooks_action.setText(self._t("menu.logbooks"))
        self.manage_profiles_action.setText(self._t("menu.station_profiles"))
        self.dashboard_colors_action.setText(self._t("dashboard.settings_menu"))
        self.integration_settings_action.setText(self._t("menu.integration_settings"))
        self.integration_monitor_action.setText(self._t("menu.integration_monitor"))
        self.adif_preferences_action.setText(self._t("menu.adif_preferences"))
        self.import_adif_action.setText(self._t("menu.import_adif"))
        self.export_adif_action.setText(self._t("menu.export_adif"))
        self.export_lotw_action.setText(self._t("menu.export_lotw"))
        self.exit_action.setText(self._t("menu.exit"))
        self.about_action.setText(self._t("menu.about"))
        for language, action in self.language_actions.items():
            action.setText(self._t(f"language.{language}"))
            action.setChecked(language == self._localization.language)
        for theme, action in self.theme_actions.items():
            action.setText(self._t(f"theme.{theme}"))
            action.setChecked(theme == self._theme_name)

        self._apply_theme()
        self._refresh_status_label()
        self._refresh_quick_filter_labels()
        self._refresh_operational_summary()
        if self._last_history_callsign:
            self._refresh_history(self._last_history_callsign)
        else:
            self._clear_history()

    def _app_window_title(self) -> str:
        try:
            from pycqlog import __version__

            version_text = __version__
        except ImportError:
            version_text = "0.1.0"
        return f"{self._t('app.title')} by PY9MT v{version_text}"

    def _t(self, key: str, **kwargs: object) -> str:
        return self._localization.t(key, **kwargs)

    def _change_language(self, language: str) -> None:
        self._localization.set_language(language)
        self._ui_settings_store.set_language(language)
        self._apply_translations()

    def _change_theme(self, theme: str) -> None:
        self._theme_name = theme
        self._ui_settings_store.set_string("theme", theme)
        self._apply_translations()

    def _apply_saved_defaults(self) -> None:
        operator_callsign = self._daemon_settings_store.get_string("operator_callsign", "")
        station_callsign = self._daemon_settings_store.get_string("station_callsign", "")
        active_logbook = self._get_active_logbook_use_case.execute()
        if active_logbook.operator_callsign:
            operator_callsign = active_logbook.operator_callsign
        if active_logbook.station_callsign:
            station_callsign = active_logbook.station_callsign
        if operator_callsign and not self.operator_input.text().strip():
            self.operator_input.setText(operator_callsign)
        if station_callsign and not self.station_callsign_input.text().strip():
            self.station_callsign_input.setText(station_callsign)

    def _load_logbook_options(self) -> None:
        self._refresh_operational_summary()

    def _open_logbooks_dialog(self) -> None:
        dialog = LogbooksDialog(
            localization=self._localization,
            logbooks_loader=self._list_logbooks_use_case,
            logbook_saver=self._save_logbook_use_case,
            logbook_deleter=self._delete_logbook_use_case,
            profiles_loader=self._list_station_profiles_use_case,
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        dialog.exec()
        self._load_logbook_options()

    def _open_station_profiles_dialog(self) -> None:
        dialog = StationProfilesDialog(
            localization=self._localization,
            profiles_loader=self._list_station_profiles_use_case,
            profile_saver=self._save_station_profile_use_case,
            profile_deleter=self._delete_station_profile_use_case,
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        dialog.exec()
        self._apply_saved_defaults()

    def _open_integration_settings_dialog(self) -> None:
        dialog = IntegrationSettingsDialog(
            localization=self._localization,
            settings={**self._daemon_settings_store.load(), **self._ui_settings_store.load()},
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        values = dialog.values()
        ui_values = {key: value for key, value in values.items() if key in UI_SETTINGS_KEYS}
        daemon_values = {key: value for key, value in values.items() if key not in UI_SETTINGS_KEYS or key == "service_auth_code"}
        if ui_values:
            self._ui_settings_store.update_many(ui_values)
        if daemon_values:
            self._daemon_settings_store.update_many(daemon_values)
        self._reload_station_service()
        self._refresh_integration_monitor()
        self._show_info("settings.saved_title", "settings.saved_body")

    def _create_station_service(self):
        self._remote_service_enabled = self._ui_settings_store.get_string("service_remote_enabled", "false") == "true"
        self._remote_service_host = self._ui_settings_store.get_string("service_remote_host", "127.0.0.1") or "127.0.0.1"
        self._remote_service_port = int(self._ui_settings_store.get_string("service_remote_port", "8746") or "8746")
        self._remote_service_auth_code = self._ui_settings_store.get_string("service_auth_code", "")
        if self._remote_service_enabled:
            return RemoteStationService(
                self._remote_service_host,
                self._remote_service_port,
                self._remote_service_auth_code,
            )
        return StationService(
            settings_store=self._daemon_settings_store,
            save_qso_use_case=self._save_qso_use_case,
            get_active_logbook_use_case=self._get_active_logbook_use_case,
            queue_path=self._config_dir / "clublog_queue.json",
            operator_callsign_getter=lambda: self.operator_input.text(),
            station_callsign_getter=lambda: self.station_callsign_input.text(),
        )

    def _reload_station_service(self) -> None:
        self._station_service.stop()
        self._station_service = self._create_station_service()
        self._station_service.start()
        self._logger.info(
            "Station service reloaded. remote_service_enabled=%s remote_service=%s:%s",
            self._remote_service_enabled,
            self._remote_service_host,
            self._remote_service_port,
        )

    def _open_integration_monitor_dialog(self) -> None:
        if self._integration_monitor_dialog is None:
            self._integration_monitor_dialog = IntegrationMonitorDialog(self._localization, parent=self)
            self._integration_monitor_dialog.finished.connect(self._clear_integration_monitor_dialog)
            self._integration_monitor_dialog.setStyleSheet(self._theme_stylesheet)
            self._integration_monitor_dialog.test_udp_button.clicked.connect(self._run_integration_udp_test)
            self._integration_monitor_dialog.test_clublog_button.clicked.connect(self._run_integration_clublog_test)
            self._integration_monitor_dialog.retry_button.clicked.connect(self._retry_pending_integrations)
            self._integration_monitor_dialog.clear_button.clicked.connect(self._clear_integration_monitor_history)
            self._refresh_integration_monitor()
            self._integration_monitor_dialog.show()
            return
        self._refresh_integration_monitor()
        self._integration_monitor_dialog.raise_()
        self._integration_monitor_dialog.activateWindow()

    def _clear_integration_monitor_dialog(self) -> None:
        self._integration_monitor_dialog = None

    def _run_integration_udp_test(self) -> None:
        self._logger.info("Manual action: integration UDP test requested.")
        self._station_service.inject_test_logged_qso()
        self._refresh_integration_monitor()

    def _run_integration_clublog_test(self) -> None:
        self._logger.info("Manual action: Club Log test requested.")
        queued, detail = self._station_service.enqueue_test_clublog_upload()
        self._refresh_integration_monitor()
        status_key = "status.clublog_queued" if queued else "status.clublog_upload_failed"
        self._set_status(status_key, detail=detail)

    def _retry_pending_integrations(self) -> None:
        count = self._station_service.retry_pending_uploads()
        self._logger.info("Manual action: retry pending integrations. count=%s", count)
        self._refresh_integration_monitor()

    def _clear_integration_monitor_history(self) -> None:
        self._logger.info("Manual action: integration monitor history cleared.")
        self._station_service.clear_history()
        self._refresh_integration_monitor()

    def _open_settings_dialog(self) -> None:
        self._logger.info("Opening directories dialog.")
        dialog = DirectoriesDialog(
            localization=self._localization,
            data_dir=self._daemon_settings_store.get_string("data_dir", str(self._active_data_dir)),
            log_dir=self._daemon_settings_store.get_string("log_dir", self._data_dir),
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        self._daemon_settings_store.update_many(
            {
                "data_dir": dialog.data_dir(),
                "log_dir": dialog.log_dir(),
            }
        )
        self._data_dir = dialog.data_dir()
        self._log_dir = dialog.log_dir()
        log_file = configure_app_logging(self._log_dir or self._data_dir or str(self._active_data_dir))
        self._logger = get_logger("ui.main_window")
        self._logger.info(
            "Directories updated. data_dir=%s log_dir=%s log_file=%s",
            self._data_dir,
            self._log_dir,
            log_file,
        )
        self._show_info("settings.saved_title", "settings.saved_body")

    def _apply_theme(self) -> None:
        qt_app = QApplication.instance()
        if qt_app is None:
            return
        _, palette = resolve_theme(self._theme_name, qt_app)
        self._theme_stylesheet = build_stylesheet(palette)
        self.setStyleSheet(self._theme_stylesheet)

    def _show_about(self) -> None:
        self._logger.info("Opening About dialog.")
        try:
            from pycqlog import __version__
            ver = __version__
        except ImportError:
            try:
                from importlib.metadata import version
                ver = version("pycqlog")
            except Exception:
                ver = "0.1.0"
                
        body = self._t("about.body") + f"\n\nVersion: {ver}"
        self._show_message_box(
            QMessageBox.Icon.Information,
            self._t("about.title"),
            body,
        )

    def _poll_integrations(self) -> None:
        result = self._station_service.process_once()
        if result.saved_callsigns:
            self._load_recent_qsos()
            latest = result.saved_callsigns[-1]
            if latest != "*":
                self._refresh_history(latest)
            elif self._last_history_callsign:
                self._refresh_history(self._last_history_callsign)
            self._refresh_dashboard_if_open()
        for service_name, success, detail in result.upload_results:
            self._logger.info("Integration result. service=%s success=%s detail=%s", service_name, success, detail)
            key = "status.clublog_upload_ok" if success else "status.clublog_upload_failed"
            self._set_status(key, detail=f"[{service_name}] {detail}")
        self._refresh_integration_monitor()
        self._refresh_operational_summary()

    def _open_dashboard(self) -> None:
        self._logger.info("Opening dashboard dialog.")
        if self._dashboard_dialog is None:
            self._dashboard_dialog = DashboardDialog(
                self._localization,
                stats_loader=self._get_dashboard_stats_use_case.execute,
                chart_preferences_loader=self._dashboard_chart_preferences,
                parent=self,
            )
            self._dashboard_dialog.finished.connect(self._clear_dashboard_dialog)
            self._dashboard_dialog.setStyleSheet(self._theme_stylesheet)
            self._dashboard_dialog.show()
            return
        self._dashboard_dialog.refresh()
        self._dashboard_dialog.raise_()
        self._dashboard_dialog.activateWindow()

    def _open_dashboard_settings_dialog(self) -> None:
        self._logger.info("Opening dashboard settings dialog.")
        dialog = DashboardSettingsDialog(
            localization=self._localization,
            use_band_colors=self._dashboard_chart_preferences()["use_band_colors"],
            use_mode_colors=self._dashboard_chart_preferences()["use_mode_colors"],
            colorize_tables=self._dashboard_chart_preferences()["colorize_tables"],
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._ui_settings_store.update_many(
            {
                "dashboard_use_band_colors": "true" if dialog.use_band_colors() else "false",
                "dashboard_use_mode_colors": "true" if dialog.use_mode_colors() else "false",
                "dashboard_colorize_tables": "true" if dialog.colorize_tables() else "false",
            }
        )
        self._load_recent_qsos()
        if self._last_history_callsign:
            self._refresh_history(self._last_history_callsign)
        self._refresh_dashboard_if_open()
        self._show_info("settings.saved_title", "settings.saved_body")

    def _clear_dashboard_dialog(self) -> None:
        self._dashboard_dialog = None

    def _dashboard_chart_preferences(self) -> dict[str, bool]:
        return {
            "use_band_colors": self._ui_settings_store.get_string("dashboard_use_band_colors", "true") == "true",
            "use_mode_colors": self._ui_settings_store.get_string("dashboard_use_mode_colors", "true") == "true",
            "colorize_tables": self._ui_settings_store.get_string("dashboard_colorize_tables", "true") == "true",
        }

    def _open_adif_settings_dialog(self) -> None:
        self._logger.info("Opening ADIF settings dialog.")
        dialog = AdifSettingsDialog(
            localization=self._localization,
            operator_callsign=self._daemon_settings_store.get_string("operator_callsign", ""),
            station_callsign=self._daemon_settings_store.get_string("station_callsign", ""),
            export_prefix=self._daemon_settings_store.get_string("adif_export_prefix", "pycqlog_export"),
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._daemon_settings_store.update_many(
            {
                "operator_callsign": dialog.operator_callsign(),
                "station_callsign": dialog.station_callsign(),
                "adif_export_prefix": dialog.export_prefix(),
            }
        )
        self._apply_saved_defaults()
        self._show_info("settings.saved_title", "settings.saved_body")

    def _import_adif(self) -> None:
        self._logger.info("Manual action: import ADIF requested.")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("adif.dialog_title"),
            self._log_dir or self._data_dir or str(self._active_data_dir),
            "ADIF (*.adi *.adif);;All files (*)",
        )
        if not file_path:
            self._logger.info("ADIF import canceled by user.")
            return

        self._log_dir = str(Path(file_path).expanduser().parent)
        self._daemon_settings_store.set_string("log_dir", self._log_dir)

        preview = self._import_adif_use_case.preview(Path(file_path))
        self._logger.info("ADIF preview loaded. file=%s records=%s", file_path, len(preview.records))
        dialog = AdifPreviewDialog(self._localization, preview, parent=self)
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            self._logger.info("ADIF import preview canceled. file=%s", file_path)
            return

        result = self._import_adif_use_case.execute(
            Path(file_path),
            selected_record_numbers=dialog.selected_record_numbers(),
            overrides=dialog.edited_values(),
        )
        self._load_recent_qsos()
        self._logger.info(
            "ADIF import finished. file=%s imported=%s skipped=%s failed=%s",
            file_path,
            result.imported_count,
            result.skipped_count,
            result.failed_count,
        )
        self._set_status(
            "status.adif_imported",
            imported=result.imported_count,
            skipped=result.skipped_count,
            failed=result.failed_count,
        )
        body = self._t(
            "adif.import_result",
            imported=result.imported_count,
            skipped=result.skipped_count,
            failed=result.failed_count,
        )
        if result.errors:
            body = body + "\n\n" + "\n".join(result.errors[:5])
        self._show_message_box(
            QMessageBox.Icon.Information,
            self._t("adif.import_title"),
            body,
        )
        self._refresh_dashboard_if_open()

    def _export_adif(self) -> None:
        self._logger.info("Manual action: export ADIF requested.")
        filter_dialog = ExportAdifDialog(self._localization, parent=self)
        filter_dialog.setStyleSheet(self._theme_stylesheet)
        if filter_dialog.exec() != filter_dialog.DialogCode.Accepted:
            self._logger.info("ADIF export canceled by user.")
            return
        try:
            export_filter = filter_dialog.export_filter()
        except ValueError as exc:
            self._logger.warning("ADIF export filter invalid. detail=%s", exc)
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.invalid_data_title"),
                str(exc),
            )
            return

        default_dir = Path(self._log_dir or self._data_dir or str(self._active_data_dir))
        export_prefix = self._daemon_settings_store.get_string("adif_export_prefix", "pycqlog_export")
        default_name = f"{export_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.adi"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("adif.export_dialog_title"),
            str(default_dir / default_name),
            "ADIF (*.adi *.adif);;All files (*)",
        )
        if not file_path:
            self._logger.info("ADIF export save dialog canceled.")
            return
        result = self._export_adif_use_case.execute(Path(file_path), filters=export_filter)
        self._log_dir = str(Path(file_path).expanduser().parent)
        self._daemon_settings_store.set_string("log_dir", self._log_dir)
        self._logger.info(
            "ADIF export finished. file=%s exported=%s",
            file_path,
            result.exported_count,
        )
        self._set_status("status.adif_exported", exported=result.exported_count)
        self._show_message_box(
            QMessageBox.Icon.Information,
            self._t("adif.export_title"),
            self._t(
                "adif.export_result",
                exported=result.exported_count,
                destination=result.destination,
            ),
        )

    def _export_lotw_tqsl(self) -> None:
        from pycqlog.interfaces.desktop.export_adif_dialog import ExportAdifDialog
        dialog = ExportAdifDialog(self._localization, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        export_filter = dialog.filter_values()
        default_dir = self._active_data_dir
        default_fname = "lotw_export.tq8"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar arquivo TQ8 (LoTW)",
            str(default_dir / default_fname),
            "LoTW Signed Files (*.tq8);;Todos os arquivos (*)",
        )
        if not file_path:
            return
            
        import tempfile
        import os
        from pycqlog.infrastructure.lotw import TqslRunner
        
        fd, temp_adif = tempfile.mkstemp(suffix=".adi", text=True)
        os.close(fd)
        temp_adif_path = Path(temp_adif)
        
        try:
            result = self._export_adif_use_case.execute(temp_adif_path, filters=export_filter)
            if not result.success:
                self._show_message_box(QMessageBox.Icon.Warning, "ADIF Export Failed", str(result))
                return
                
            if result.exported_count == 0:
                self._show_message_box(QMessageBox.Icon.Information, "ADIF Export", "Nenhum QSO correspondente.")
                return
                
            runner = TqslRunner(
                executable_path=self._daemon_settings_store.get_string("integration_lotw_tqsl_path", "tqsl"),
                station_location=self._daemon_settings_store.get_string("integration_lotw_station_location", "")
            )
            success, detail = runner.build_tq8(temp_adif_path, Path(file_path))
            
            if success:
                self._show_message_box(
                    QMessageBox.Icon.Information, 
                    "LoTW TQSL", 
                    f"{result.exported_count} QSOs processados.\n\n{detail}"
                )
            else:
                self._show_message_box(QMessageBox.Icon.Warning, "LoTW TQSL Error", detail)
        finally:
            try:
                os.unlink(temp_adif_path)
            except OSError:
                pass

    def _save_qso(self) -> None:
        self._logger.info("Manual action: save QSO requested. editing_qso_id=%s", self._editing_qso_id)
        existing_detail = (
            self._get_qso_detail_use_case.execute(self._editing_qso_id)
            if self._editing_qso_id is not None
            else None
        )
        try:
            command = SaveQsoCommand(
                callsign=self.callsign_input.text(),
                qso_date=date.fromisoformat(self.date_input.text().strip()),
                time_on=datetime.strptime(self.time_input.text().strip(), "%H:%M").time(),
                freq=Decimal(self.freq_input.text().strip()),
                mode=self.mode_input.text(),
                rst_sent=self.rst_sent_input.text(),
                rst_recv=self.rst_recv_input.text(),
                operator=self.operator_input.text(),
                station_callsign=self.station_callsign_input.text(),
                notes=self.notes_input.toPlainText(),
                source="manual",
                qso_id=self._editing_qso_id,
            )
        except ValueError as exc:
            self._logger.warning("QSO save failed due to invalid value. detail=%s", exc)
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.invalid_data_title"),
                str(exc),
            )
            return
        except InvalidOperation:
            self._logger.warning("QSO save failed due to invalid frequency.")
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.invalid_data_title"),
                self._t("message.invalid_frequency"),
            )
            return

        is_new_qso = self._editing_qso_id is None
        try:
            result = self._save_qso_use_case.execute(command)
        except QsoValidationError as exc:
            self._logger.warning("QSO save failed validation. detail=%s", exc)
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.validation_error_title"),
                str(exc),
            )
            return

        action_key = "action.updated" if self._editing_qso_id is not None else "action.saved"
        self._logger.info(
            "QSO save succeeded. qso_id=%s callsign=%s band=%s mode=%s is_new=%s",
            result.qso_id,
            result.callsign,
            result.band,
            result.mode,
            is_new_qso,
        )
        warning_text = ""
        if result.warnings:
            warning_text = " " + "; ".join(result.warnings)

        self._set_status(
            "status.saved",
            qso_id=result.qso_id,
            action=self._t(action_key),
            callsign=result.callsign,
            band=result.band,
            mode=result.mode,
            warnings=warning_text,
        )
        self._show_info(
            "message.qso_saved_title",
            "message.qso_saved_body",
            qso_id=result.qso_id,
            action=self._t(action_key),
            callsign=result.callsign,
            band=result.band,
        )
        self._reset_form()
        self._load_recent_qsos()
        self._refresh_history(result.callsign)
        self._refresh_dashboard_if_open()
        if is_new_qso:
            adif_text = self._build_adif_record_text(
                callsign=result.callsign,
                qso_date=command.qso_date,
                time_on=command.time_on,
                freq=command.freq,
                band=result.band,
                mode=result.mode,
                rst_sent=command.rst_sent,
                rst_recv=command.rst_recv,
                operator=command.operator,
                station_callsign=command.station_callsign,
                notes=command.notes,
                source="manual",
                logbook_id=result.logbook_id,
                qso_id=result.qso_id,
            )
            enqueued_services = self._station_service.enqueue_uploads(adif_text, source="manual")
            if enqueued_services:
                self._logger.info("Manual QSO queued for integrations. services=%s callsign=%s", ",".join(enqueued_services), result.callsign)
            self._refresh_integration_monitor()
        elif existing_detail is not None:
            new_adif_text = self._build_adif_record_text(
                callsign=result.callsign,
                qso_date=command.qso_date,
                time_on=command.time_on,
                freq=command.freq,
                band=result.band,
                mode=result.mode,
                rst_sent=command.rst_sent,
                rst_recv=command.rst_recv,
                operator=command.operator,
                station_callsign=command.station_callsign,
                notes=command.notes,
                source="manual",
                logbook_id=result.logbook_id,
                qso_id=result.qso_id,
            )
            queued_actions = self._station_service.enqueue_clublog_update(
                old_callsign=existing_detail.callsign,
                old_qso_date=existing_detail.qso_date.isoformat(),
                old_time_on=existing_detail.time_on.strftime("%H:%M"),
                old_band=existing_detail.band,
                new_adif_text=new_adif_text,
                source="manual",
            )
            if queued_actions:
                self._logger.info(
                    "Manual QSO update queued for Club Log. actions=%s callsign=%s",
                    ",".join(queued_actions),
                    result.callsign,
                )
                self._refresh_integration_monitor()

    def _load_recent_qsos(self) -> None:
        items = self._list_recent_qsos_use_case.execute(limit=20)
        self._logger.debug("Recent QSOs loaded. count=%s", len(items))
        self.search_input.clear()
        self._set_visible_qso_items(items)

    def _search_qsos(self) -> None:
        items = self._search_qsos_use_case.execute(self.search_input.text(), limit=50)
        self._logger.info("QSO search executed. term=%s count=%s", self.search_input.text().strip(), len(items))
        self._set_visible_qso_items(items)
        self._set_status("status.search_loaded", count=len(items))

    def _set_visible_qso_items(self, items: list[QsoListItem]) -> None:
        self._loaded_qso_items = items
        self.recent_summary_label.setText(self._t("summary.visible_qsos", count=len(items)))
        self._sync_quick_filter_options(items)
        self._populate_table(self._filtered_qso_items())

    def _filtered_qso_items(self) -> list[QsoListItem]:
        return [item for item in self._loaded_qso_items if self._matches_quick_filters(item)]

    def _matches_quick_filters(self, item: QsoListItem) -> bool:
        band_match = not self._active_band_filters or item.band in self._active_band_filters
        mode_match = not self._active_mode_filters or item.mode in self._active_mode_filters
        return band_match and mode_match

    def _sync_quick_filter_options(self, items: list[QsoListItem]) -> None:
        available_bands = {item.band for item in items if item.band}
        available_modes = {item.mode for item in items if item.mode}
        self._active_band_filters &= available_bands
        self._active_mode_filters &= available_modes
        self._rebuild_filter_buttons(
            self.band_filters_row,
            self.band_filters_label,
            self._band_filter_buttons,
            sorted(available_bands),
            self._active_band_filters,
            self._toggle_band_filter,
        )
        self._rebuild_filter_buttons(
            self.mode_filters_row,
            self.mode_filters_label,
            self._mode_filter_buttons,
            sorted(available_modes),
            self._active_mode_filters,
            self._toggle_mode_filter,
        )
        self._refresh_quick_filter_labels()

    def _rebuild_filter_buttons(
        self,
        layout: QHBoxLayout,
        label: QLabel,
        button_map: dict[str, QPushButton],
        values: list[str],
        active_filters: set[str],
        toggle_handler,
    ) -> None:
        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        button_map.clear()
        insert_at = 1
        for value in values:
            button = QPushButton(value)
            button.setObjectName("quickFilterChip")
            button.setCheckable(True)
            button.setChecked(value in active_filters)
            button.clicked.connect(lambda checked=False, selected=value: toggle_handler(selected))
            layout.insertWidget(insert_at, button)
            button_map[value] = button
            insert_at += 1
        label.setVisible(bool(values))
        layout.parentWidget().setVisible(bool(values))
        self.clear_filters_button.setVisible(bool(values))

    def _toggle_band_filter(self, band: str) -> None:
        if band in self._active_band_filters:
            self._active_band_filters.remove(band)
        else:
            self._active_band_filters.add(band)
        self._refresh_quick_filter_labels()
        self._populate_table(self._filtered_qso_items())

    def _toggle_mode_filter(self, mode: str) -> None:
        if mode in self._active_mode_filters:
            self._active_mode_filters.remove(mode)
        else:
            self._active_mode_filters.add(mode)
        self._refresh_quick_filter_labels()
        self._populate_table(self._filtered_qso_items())

    def _clear_quick_filters(self) -> None:
        if not self._active_band_filters and not self._active_mode_filters:
            return
        self._active_band_filters.clear()
        self._active_mode_filters.clear()
        for button in self._band_filter_buttons.values():
            button.setChecked(False)
        for button in self._mode_filter_buttons.values():
            button.setChecked(False)
        self._refresh_quick_filter_labels()
        self._populate_table(self._filtered_qso_items())

    def _refresh_quick_filter_labels(self) -> None:
        band_suffix = ""
        mode_suffix = ""
        if self._active_band_filters:
            band_suffix = f": {','.join(sorted(self._active_band_filters))}"
        if self._active_mode_filters:
            mode_suffix = f": {','.join(sorted(self._active_mode_filters))}"
        self.band_filters_label.setText(self._t("filter.band") + band_suffix)
        self.mode_filters_label.setText(self._t("filter.mode") + mode_suffix)
        has_any_filters = bool(self._active_band_filters or self._active_mode_filters)
        self.clear_filters_button.setEnabled(has_any_filters)

    def _populate_table(self, items: list[QsoListItem]) -> None:
        self.recent_summary_label.setText(self._t("summary.visible_qsos", count=len(items)))
        self.qso_table.setSortingEnabled(False)
        self.qso_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            self._set_table_item(row_index, 0, item.qso_id)
            self._set_table_item(row_index, 1, item.callsign)
            self._set_table_item(row_index, 2, item.qso_date.isoformat())
            self._set_table_item(row_index, 3, item.time_on.strftime("%H:%M"))
            self._set_table_item(row_index, 4, item.band)
            self._set_table_item(row_index, 5, item.mode)
            self._apply_qso_row_colors(row_index, item.band, item.mode)
        self.qso_table.apply_proportional_widths()
        self.qso_table.setSortingEnabled(True)
        self._handle_selection_changed()

    def _handle_selection_changed(self) -> None:
        has_selection = self._selected_qso_id() is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _selected_qso_id(self) -> int | None:
        selected_items = self.qso_table.selectedItems()
        if not selected_items:
            return None
        try:
            return int(selected_items[0].text())
        except ValueError:
            return None

    def _load_selected_qso(self) -> None:
        qso_id = self._selected_qso_id()
        if qso_id is None:
            return
        self._logger.info("Loading selected QSO. qso_id=%s", qso_id)
        detail = self._get_qso_detail_use_case.execute(qso_id)
        if detail is None:
            self._logger.warning("Selected QSO not found. qso_id=%s", qso_id)
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.qso_not_found_title"),
                self._t("message.qso_not_found_body", qso_id=qso_id),
            )
            self._load_recent_qsos()
            return

        self._editing_qso_id = detail.qso_id
        self.callsign_input.setText(detail.callsign)
        self.date_input.setText(detail.qso_date.isoformat())
        self.time_input.setText(detail.time_on.strftime("%H:%M"))
        self.freq_input.setText(str(detail.freq))
        self.mode_input.setText(detail.mode)
        self.rst_sent_input.setText(detail.rst_sent)
        self.rst_recv_input.setText(detail.rst_recv)
        self.operator_input.setText(detail.operator)
        self.station_callsign_input.setText(detail.station_callsign)
        self.notes_input.setPlainText(detail.notes)
        self.save_button.setText(self._t("button.update_qso"))
        self._set_status("status.editing", qso_id=detail.qso_id, callsign=detail.callsign)
        self._refresh_history(detail.callsign)
        self.callsign_input.setFocus()

    def _delete_selected_qso(self) -> None:
        qso_id = self._selected_qso_id()
        if qso_id is None:
            return
        self._logger.info("Delete selected QSO requested. qso_id=%s", qso_id)
        existing_detail = self._get_qso_detail_use_case.execute(qso_id)
        answer = self._show_question(
            self._t("message.delete_title"),
            self._t("message.delete_body", qso_id=qso_id),
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._logger.info("QSO delete canceled by user. qso_id=%s", qso_id)
            return
        deleted = self._delete_qso_use_case.execute(qso_id)
        if not deleted:
            self._logger.warning("QSO delete failed. qso_id=%s", qso_id)
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.delete_failed_title"),
                self._t("message.delete_failed_body", qso_id=qso_id),
            )
            return
        self._logger.info("QSO deleted. qso_id=%s", qso_id)
        if self._editing_qso_id == qso_id:
            self._reset_form()
        self._load_recent_qsos()
        self._set_status("status.deleted", qso_id=qso_id)
        self._refresh_history_from_form()
        self._refresh_dashboard_if_open()
        if existing_detail is not None and self._station_service.enqueue_clublog_delete(
            callsign=existing_detail.callsign,
            qso_date=existing_detail.qso_date.isoformat(),
            time_on=existing_detail.time_on.strftime("%H:%M"),
            band=existing_detail.band,
            source="manual",
        ):
            self._logger.info("Manual QSO delete queued for Club Log. callsign=%s qso_id=%s", existing_detail.callsign, qso_id)
            self._refresh_integration_monitor()

    def _set_table_item(self, row: int, column: int, value: int | str) -> None:
        if column == 0:
            item = NumericTableWidgetItem(int(value))
        else:
            item = QTableWidgetItem(str(value))
        self.qso_table.setItem(row, column, item)

    def _apply_qso_row_colors(self, row: int, band: str, mode: str) -> None:
        if not self._dashboard_chart_preferences()["colorize_tables"]:
            return
        self._apply_cell_color(self.qso_table.item(row, 4), color_for_band(band), bool(band))
        self._apply_cell_color(self.qso_table.item(row, 5), color_for_mode(mode), bool(mode))

    def _reset_form(self) -> None:
        self._logger.debug("QSO form reset.")
        self._editing_qso_id = None
        self.callsign_input.clear()
        self.freq_input.clear()
        self.mode_input.clear()
        self.rst_sent_input.clear()
        self.rst_recv_input.clear()
        self.operator_input.clear()
        self.station_callsign_input.clear()
        self.notes_input.clear()
        self.save_button.setText(self._t("button.save_qso"))
        self._set_status("status.ready_next")
        self._clear_history()
        self._apply_saved_defaults()
        self.callsign_input.setFocus()

    def _refresh_history_from_form(self) -> None:
        callsign = self.callsign_input.text()
        self._refresh_history(callsign)
        self._perform_callbook_lookup(callsign)

    def _perform_callbook_lookup(self, callsign: str) -> None:
        if not callsign.strip():
            return
        if self._editing_qso_id is not None:
            return
            
        self._logger.info("Callbook lookup requested. callsign=%s", callsign.strip().upper())
        info = self._fetch_callbook_info_use_case.execute(callsign)
        if info:
            self._logger.info("Callbook lookup succeeded. callsign=%s", callsign.strip().upper())
            current_notes = self.notes_input.toPlainText()
            notes_parts = []
            if info.name and f"Name: {info.name}" not in current_notes:
                notes_parts.append(f"Name: {info.name}")
            if info.qth and f"QTH: {info.qth}" not in current_notes:
                notes_parts.append(f"QTH: {info.qth}")
            if info.locator and f"Grid: {info.locator}" not in current_notes:
                notes_parts.append(f"Grid: {info.locator}")
            if info.country and f"Country: {info.country}" not in current_notes:
                notes_parts.append(f"Country: {info.country}")
                
            if notes_parts:
                new_notes = " | ".join(notes_parts)
                if current_notes:
                    self.notes_input.setPlainText(f"{current_notes}\\n{new_notes}")
                else:
                    self.notes_input.setPlainText(new_notes)

    def _refresh_history(self, callsign: str) -> None:
        normalized = callsign.strip().upper()
        self._last_history_callsign = normalized
        if not normalized:
            self._clear_history()
            return
        items = self._get_callsign_history_use_case.execute(normalized, limit=10)
        self._last_history_count = len(items)
        self.history_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            self._set_history_item(row_index, 0, str(item.qso_id))
            self._set_history_item(row_index, 1, item.qso_date.isoformat())
            self._set_history_item(row_index, 2, item.time_on.strftime("%H:%M"))
            self._set_history_item(row_index, 3, item.band)
            self._set_history_item(row_index, 4, item.mode)
            self._set_history_item(row_index, 5, f"{item.rst_sent}/{item.rst_recv}".strip("/"))
            if self._dashboard_chart_preferences()["colorize_tables"]:
                self._apply_cell_color(self.history_table.item(row_index, 3), color_for_band(item.band), bool(item.band))
                self._apply_cell_color(self.history_table.item(row_index, 4), color_for_mode(item.mode), bool(item.mode))
        self.history_table.apply_proportional_widths()
        if items:
            self.history_summary_label.setText(
                self._t("status.history_found", count=len(items), callsign=normalized)
            )
        else:
            self.history_summary_label.setText(self._t("status.history_empty", callsign=normalized))
        self._refresh_operational_summary()

    def _set_history_item(self, row: int, column: int, value: str) -> None:
        self.history_table.setItem(row, column, QTableWidgetItem(value))

    def _apply_cell_color(self, item: QTableWidgetItem | None, color: str, enabled: bool) -> None:
        if item is None:
            return
        if not enabled:
            item.setBackground(QColor())
            item.setForeground(QColor())
            return
        item.setBackground(QColor(color))
        item.setForeground(QColor(contrasting_text_color(color)))

    def _clear_history(self) -> None:
        self._last_history_callsign = ""
        self._last_history_count = 0
        self.history_table.setRowCount(0)
        self.history_summary_label.setText(self._t("status.history_prompt"))
        self._refresh_operational_summary()

    def _set_status(self, key: str, **params: object) -> None:
        self._current_status_key = key
        self._current_status_params = params
        self._logger.debug("Status updated. key=%s params=%s", key, params)
        self._refresh_status_label()

    def _refresh_status_label(self) -> None:
        self.status_label.setText(self._t(self._current_status_key, **self._current_status_params))
        self._refresh_operational_summary()

    def _refresh_operational_summary(self) -> None:
        try:
            active_logbook = self._get_active_logbook_use_case.execute()
            self.top_logbook_value.setText(active_logbook.name)
            self.footer_logbook_label.setText(
                self._t("summary.logbook_footer", name=active_logbook.name, count=active_logbook.qso_count)
            )
        except Exception:
            self.top_logbook_value.setText("--")
            self.footer_logbook_label.setText("--")

        listener_ready, listener_detail = self._station_service.listener_status()
        clublog_ready, clublog_detail = self._station_service.clublog_status()
        pending_count = self._station_service.pending_upload_count()
        integration_parts = []
        integration_parts.append(
            self._t("summary.integration_listener_on")
            if listener_ready
            else self._t("summary.integration_listener_off")
        )
        integration_parts.append(
            self._t("summary.integration_cloud_on")
            if clublog_ready
            else self._t("summary.integration_cloud_off")
        )
        self.top_integrations_value.setText(" / ".join(integration_parts))
        self.footer_integrations_label.setText(
            self._t(
                "summary.integrations_footer",
                listener=listener_detail or (
                    self._t("integrations.monitor_on") if listener_ready else self._t("integrations.monitor_off")
                ),
                cloud=clublog_detail or (
                    self._t("integrations.monitor_on") if clublog_ready else self._t("integrations.monitor_off")
                ),
            )
        )
        self.top_pending_value.setText(str(pending_count))
        self.footer_pending_label.setText(self._t("summary.pending_footer", pending=pending_count))

    def _show_info(self, title_key: str, body_key: str, **kwargs: object) -> None:
        self._show_message_box(
            QMessageBox.Icon.Information,
            self._t(title_key),
            self._t(body_key, **kwargs),
        )

    def _refresh_dashboard_if_open(self) -> None:
        if self._dashboard_dialog is not None:
            self._dashboard_dialog.refresh()

    def _show_question(self, title: str, text: str) -> QMessageBox.StandardButton:
        self._logger.debug("Question dialog opened. title=%s text=%s", title, text)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setStyleSheet(self._theme_stylesheet)
        return box.exec()

    def _show_message_box(
        self,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
    ) -> QMessageBox.StandardButton:
        level = "warning" if icon == QMessageBox.Icon.Warning else "info"
        getattr(self._logger, level)("Message dialog shown. title=%s text=%s", title, text)
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(self._theme_stylesheet)
        return box.exec()

    def _refresh_integration_monitor(self) -> None:
        if self._integration_monitor_dialog is None:
            return
        listener_ready, listener_detail = self._station_service.listener_status()
        clublog_ready, clublog_detail = self._station_service.clublog_status()
        stats = self._station_service.stats()
        self._integration_monitor_dialog.update_summary(
            {
                "listener": (
                    f"{self._t('integrations.monitor_on')} ({listener_detail})"
                    if listener_ready and listener_detail
                    else listener_detail or (self._t("integrations.monitor_on") if listener_ready else self._t("integrations.monitor_off"))
                ),
                "clublog": (
                    self._t("integrations.monitor_on")
                    if clublog_ready and not clublog_detail
                    else clublog_detail or self._t("integrations.monitor_off")
                ),
                "received": str(stats["received"]),
                "saved": str(stats["saved"]),
                "uploaded": str(stats["uploaded"]),
                "failed": str(stats["failed"]),
                "pending": str(self._station_service.pending_upload_count()),
            }
        )
        self._integration_monitor_dialog.set_events(list(reversed(self._station_service.events())))

    def _build_adif_record_text(
        self,
        *,
        callsign: str,
        qso_date: date,
        time_on,
        freq: Decimal,
        band: str,
        mode: str,
        rst_sent: str,
        rst_recv: str,
        operator: str,
        station_callsign: str,
        notes: str,
        source: str,
        logbook_id: int,
        qso_id: int,
    ) -> str:
        from pycqlog.domain.models import Qso

        qso = Qso(
            id=qso_id,
            callsign=callsign,
            qso_date=qso_date,
            time_on=time_on,
            freq=freq,
            mode=mode,
            band=band,
            logbook_id=logbook_id,
            rst_sent=rst_sent,
            rst_recv=rst_recv,
            operator=operator,
            station_callsign=station_callsign,
            notes=notes,
            source=source,
        )
        return self._adif_exporter.build_record(qso)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._logger.info("Application closing.")
        self._integration_timer.stop()
        self._station_service.stop()
        super().closeEvent(event)
