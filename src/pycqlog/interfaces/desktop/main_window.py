from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFileDialog,
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
from pycqlog.infrastructure.adif import AdifParser
from pycqlog.infrastructure.adif_export import AdifExporter
from pycqlog.infrastructure.integrations import IntegrationManager, LoggedAdifEvent
from pycqlog.infrastructure.settings import JsonSettingsStore
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


class MainWindow(QMainWindow):
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
        settings_store: JsonSettingsStore,
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
        self._settings_store = settings_store
        self._active_data_dir = data_dir
        self._config_dir = config_dir
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
        self._data_dir = self._settings_store.get_string("data_dir", str(self._active_data_dir))
        self._log_dir = self._settings_store.get_string("log_dir", self._data_dir)
        self._theme_name = self._settings_store.get_string("theme", "system")
        self._theme_stylesheet = ""
        self._dashboard_dialog: DashboardDialog | None = None
        self._integration_monitor_dialog: IntegrationMonitorDialog | None = None
        self._suppress_logbook_change = False
        self._adif_parser = AdifParser()
        self._adif_exporter = AdifExporter()
        self._integration_manager = IntegrationManager(settings_store, config_dir / "clublog_queue.json")
        self._integration_events: list[dict[str, str]] = []
        self._integration_stats = {
            "received": 0,
            "saved": 0,
            "uploaded": 0,
            "failed": 0,
        }
        self._build_ui()
        self._load_logbook_options()
        self._apply_translations()
        self._apply_saved_defaults()
        self._integration_manager.start()
        self._integration_timer = QTimer(self)
        self._integration_timer.setInterval(1200)
        self._integration_timer.timeout.connect(self._poll_integrations)
        self._integration_timer.start()
        self._load_recent_qsos()

    def _build_ui(self) -> None:
        self.resize(1220, 680)
        self._build_menu()

        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        form_panel = QWidget()
        form_root = QVBoxLayout(form_panel)
        form_root.setContentsMargins(0, 0, 0, 0)
        form_root.setSpacing(16)

        self.header_label = QLabel()
        self.header_label.setObjectName("headerLabel")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form_root.addWidget(self.header_label)

        logbook_row = QHBoxLayout()
        self.active_logbook_label = QLabel()
        logbook_row.addWidget(self.active_logbook_label)
        self.active_logbook_combo = QComboBox()
        self.active_logbook_combo.currentIndexChanged.connect(self._handle_active_logbook_change)
        logbook_row.addWidget(self.active_logbook_combo, 1)
        self.manage_logbooks_button = QPushButton()
        self.manage_logbooks_button.clicked.connect(self._open_logbooks_dialog)
        logbook_row.addWidget(self.manage_logbooks_button)
        form_root.addLayout(logbook_row)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)
        self.form_labels: list[QLabel] = []

        self.callsign_input = QLineEdit()
        self.callsign_input.editingFinished.connect(self._refresh_history_from_form)
        self._add_form_row(self.callsign_input)

        self.date_input = QLineEdit()
        self.date_input.setText(date.today().isoformat())
        self._add_form_row(self.date_input)

        self.time_input = QLineEdit()
        self.time_input.setText(datetime.now().strftime("%H:%M"))
        self._add_form_row(self.time_input)

        self.freq_input = QLineEdit()
        self._add_form_row(self.freq_input)

        self.mode_input = QLineEdit()
        self._add_form_row(self.mode_input)

        self.rst_sent_input = QLineEdit()
        self._add_form_row(self.rst_sent_input)

        self.rst_recv_input = QLineEdit()
        self._add_form_row(self.rst_recv_input)

        self.operator_input = QLineEdit()
        self._add_form_row(self.operator_input)

        self.station_callsign_input = QLineEdit()
        self._add_form_row(self.station_callsign_input)

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(120)
        self._add_form_row(self.notes_input)

        form_root.addLayout(self.form_layout)

        button_row = QHBoxLayout()
        self.save_button = QPushButton()
        self.save_button.clicked.connect(self._save_qso)
        button_row.addWidget(self.save_button)

        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self._reset_form)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        form_root.addLayout(button_row)

        self.status_label = QLabel()
        form_root.addWidget(self.status_label)

        root.addWidget(form_panel, 3)

        list_panel = QWidget()
        list_root = QVBoxLayout(list_panel)
        list_root.setContentsMargins(0, 0, 0, 0)
        list_root.setSpacing(12)

        self.recent_header = QLabel()
        self.recent_header.setObjectName("sectionLabel")
        list_root.addWidget(self.recent_header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._search_qsos)
        search_row.addWidget(self.search_input)

        self.search_button = QPushButton()
        self.search_button.clicked.connect(self._search_qsos)
        search_row.addWidget(self.search_button)

        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self._load_recent_qsos)
        search_row.addWidget(self.refresh_button)
        list_root.addLayout(search_row)

        self.quick_filters_label = QLabel()
        self.quick_filters_label.setObjectName("filterLabel")
        list_root.addWidget(self.quick_filters_label)

        self.band_filters_row = QHBoxLayout()
        self.band_filters_label = QLabel()
        self.band_filters_row.addWidget(self.band_filters_label)
        self.band_filters_row.addStretch(1)
        list_root.addLayout(self.band_filters_row)

        self.mode_filters_row = QHBoxLayout()
        self.mode_filters_label = QLabel()
        self.mode_filters_row.addWidget(self.mode_filters_label)
        self.mode_filters_row.addStretch(1)
        list_root.addLayout(self.mode_filters_row)

        self.clear_filters_button = QPushButton()
        self.clear_filters_button.setObjectName("quickFilterChip")
        self.clear_filters_button.clicked.connect(self._clear_quick_filters)
        list_root.addWidget(self.clear_filters_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.qso_table = QTableWidget(0, 6)
        self.qso_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.qso_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.qso_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.qso_table.verticalHeader().setVisible(False)
        self.qso_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.qso_table.horizontalHeader().setHighlightSections(False)
        self.qso_table.itemSelectionChanged.connect(self._handle_selection_changed)
        list_root.addWidget(self.qso_table)

        action_row = QHBoxLayout()
        self.edit_button = QPushButton()
        self.edit_button.clicked.connect(self._load_selected_qso)
        self.edit_button.setEnabled(False)
        action_row.addWidget(self.edit_button)

        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self._delete_selected_qso)
        self.delete_button.setEnabled(False)
        action_row.addWidget(self.delete_button)
        action_row.addStretch(1)
        list_root.addLayout(action_row)

        root.addWidget(list_panel, 2)

        history_panel = QWidget()
        history_root = QVBoxLayout(history_panel)
        history_root.setContentsMargins(0, 0, 0, 0)
        history_root.setSpacing(12)

        self.history_header = QLabel()
        self.history_header.setObjectName("sectionLabel")
        history_root.addWidget(self.history_header)

        self.history_summary_label = QLabel()
        self.history_summary_label.setWordWrap(True)
        history_root.addWidget(self.history_summary_label)

        self.history_table = QTableWidget(0, 6)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setHighlightSections(False)
        history_root.addWidget(self.history_table)

        root.addWidget(history_panel, 2)

        self.setCentralWidget(central)

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

    def _add_form_row(self, field: QWidget) -> None:
        label = QLabel()
        self.form_labels.append(label)
        self.form_layout.addRow(label, field)

    def _apply_translations(self) -> None:
        self.setWindowTitle(self._t("app.title"))
        self.header_label.setText(self._t("section.manual_entry"))
        self.active_logbook_label.setText(self._t("logbooks.active"))
        self.recent_header.setText(self._t("section.recent_qsos"))
        self.history_header.setText(self._t("section.callsign_history"))

        labels = [
            self._t("label.callsign"),
            self._t("label.date"),
            self._t("label.time"),
            self._t("label.frequency_mhz"),
            self._t("label.mode"),
            self._t("label.rst_sent"),
            self._t("label.rst_recv"),
            self._t("label.operator"),
            self._t("label.station"),
            self._t("label.notes"),
        ]
        for label_widget, text in zip(self.form_labels, labels, strict=False):
            label_widget.setText(text)

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
        self.manage_logbooks_button.setText(self._t("button.manage_logbooks"))

        self.save_button.setText(
            self._t("button.update_qso") if self._editing_qso_id is not None else self._t("button.save_qso")
        )
        self.clear_button.setText(self._t("button.new_qso"))
        self.search_button.setText(self._t("button.search"))
        self.refresh_button.setText(self._t("button.show_recent"))
        self.edit_button.setText(self._t("button.edit_selected"))
        self.delete_button.setText(self._t("button.delete_selected"))

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
        if self._last_history_callsign:
            self._refresh_history(self._last_history_callsign)
        else:
            self._clear_history()

    def _t(self, key: str, **kwargs: object) -> str:
        return self._localization.t(key, **kwargs)

    def _change_language(self, language: str) -> None:
        self._localization.set_language(language)
        self._settings_store.set_language(language)
        self._apply_translations()

    def _change_theme(self, theme: str) -> None:
        self._theme_name = theme
        self._settings_store.set_string("theme", theme)
        self._apply_translations()

    def _apply_saved_defaults(self) -> None:
        operator_callsign = self._settings_store.get_string("operator_callsign", "")
        station_callsign = self._settings_store.get_string("station_callsign", "")
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
        active = self._get_active_logbook_use_case.execute()
        logbooks = self._list_logbooks_use_case.execute()
        self._suppress_logbook_change = True
        self.active_logbook_combo.clear()
        for item in logbooks:
            self.active_logbook_combo.addItem(item.name, item.logbook_id)
        index = max(0, self.active_logbook_combo.findData(active.logbook_id))
        self.active_logbook_combo.setCurrentIndex(index)
        self._suppress_logbook_change = False

    def _handle_active_logbook_change(self) -> None:
        if self._suppress_logbook_change:
            return
        logbook_id = self.active_logbook_combo.currentData()
        if logbook_id is None:
            return
        active = self._set_active_logbook_use_case.execute(int(logbook_id))
        self._settings_store.set_string("active_logbook_id", str(active.logbook_id))
        self._editing_qso_id = None
        self.operator_input.clear()
        self.station_callsign_input.clear()
        self._apply_saved_defaults()
        self._load_recent_qsos()
        self._clear_history()
        self._refresh_dashboard_if_open()
        self._set_status("status.logbook_changed", name=active.name)

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
        self._handle_active_logbook_change()

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
            settings=self._settings_store.load(),
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._settings_store.update_many(dialog.values())
        self._integration_manager.reconfigure()
        self._refresh_integration_monitor()
        self._show_info("settings.saved_title", "settings.saved_body")

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
        self._integration_manager.inject_test_logged_qso()
        self._append_integration_event(
            "PyCQLog",
            self._t("integrations.event_test_udp"),
            self._t("integrations.test_udp_detail"),
        )
        self._refresh_integration_monitor()

    def _run_integration_clublog_test(self) -> None:
        queued, detail = self._integration_manager.enqueue_test_clublog_upload()
        event_key = "integrations.event_test_clublog" if queued else "integrations.event_test_clublog_failed"
        self._append_integration_event("Club Log", self._t(event_key), detail)
        self._refresh_integration_monitor()
        status_key = "status.clublog_queued" if queued else "status.clublog_upload_failed"
        self._set_status(status_key, detail=detail)

    def _retry_pending_integrations(self) -> None:
        count = self._integration_manager.retry_pending_uploads()
        self._append_integration_event("Club Log", self._t("integrations.event_retry_pending"), str(count))
        self._refresh_integration_monitor()

    def _clear_integration_monitor_history(self) -> None:
        self._integration_events.clear()
        self._integration_stats = {
            "received": 0,
            "saved": 0,
            "uploaded": 0,
            "failed": 0,
        }
        self._refresh_integration_monitor()

    def _open_settings_dialog(self) -> None:
        dialog = DirectoriesDialog(
            localization=self._localization,
            data_dir=self._settings_store.get_string("data_dir", str(self._active_data_dir)),
            log_dir=self._settings_store.get_string("log_dir", self._data_dir),
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        self._settings_store.update_many(
            {
                "data_dir": dialog.data_dir(),
                "log_dir": dialog.log_dir(),
            }
        )
        self._data_dir = dialog.data_dir()
        self._log_dir = dialog.log_dir()
        self._show_info("settings.saved_title", "settings.saved_body")

    def _apply_theme(self) -> None:
        qt_app = QApplication.instance()
        if qt_app is None:
            return
        _, palette = resolve_theme(self._theme_name, qt_app)
        self._theme_stylesheet = build_stylesheet(palette)
        self.setStyleSheet(self._theme_stylesheet)

    def _show_about(self) -> None:
        self._show_message_box(
            QMessageBox.Icon.Information,
            self._t("about.title"),
            self._t("about.body"),
        )

    def _poll_integrations(self) -> None:
        for event in self._integration_manager.poll_logged_qsos():
            self._handle_logged_adif_event(event)
        for service_name, success, detail in self._integration_manager.poll_upload_results():
            key = "status.clublog_upload_ok" if success else "status.clublog_upload_failed"
            if success:
                self._integration_stats["uploaded"] += 1
                self._append_integration_event(service_name, self._t("integrations.event_uploaded"), detail)
            else:
                self._integration_stats["failed"] += 1
                self._append_integration_event(service_name, self._t("integrations.event_upload_failed"), detail)
            self._set_status(key, detail=f"[{service_name}] {detail}")
        self._refresh_integration_monitor()

    def _open_dashboard(self) -> None:
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
        self._settings_store.update_many(
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
            "use_band_colors": self._settings_store.get_string("dashboard_use_band_colors", "true") == "true",
            "use_mode_colors": self._settings_store.get_string("dashboard_use_mode_colors", "true") == "true",
            "colorize_tables": self._settings_store.get_string("dashboard_colorize_tables", "true") == "true",
        }

    def _open_adif_settings_dialog(self) -> None:
        dialog = AdifSettingsDialog(
            localization=self._localization,
            operator_callsign=self._settings_store.get_string("operator_callsign", ""),
            station_callsign=self._settings_store.get_string("station_callsign", ""),
            export_prefix=self._settings_store.get_string("adif_export_prefix", "pycqlog_export"),
            parent=self,
        )
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self._settings_store.update_many(
            {
                "operator_callsign": dialog.operator_callsign(),
                "station_callsign": dialog.station_callsign(),
                "adif_export_prefix": dialog.export_prefix(),
            }
        )
        self._apply_saved_defaults()
        self._show_info("settings.saved_title", "settings.saved_body")

    def _import_adif(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("adif.dialog_title"),
            self._log_dir or self._data_dir or str(self._active_data_dir),
            "ADIF (*.adi *.adif);;All files (*)",
        )
        if not file_path:
            return

        self._log_dir = str(Path(file_path).expanduser().parent)
        self._settings_store.set_string("log_dir", self._log_dir)

        preview = self._import_adif_use_case.preview(Path(file_path))
        dialog = AdifPreviewDialog(self._localization, preview, parent=self)
        dialog.setStyleSheet(self._theme_stylesheet)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        result = self._import_adif_use_case.execute(
            Path(file_path),
            selected_record_numbers=dialog.selected_record_numbers(),
            overrides=dialog.edited_values(),
        )
        self._load_recent_qsos()
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

    def _handle_logged_adif_event(self, event: LoggedAdifEvent) -> None:
        self._integration_stats["received"] += 1
        self._append_integration_event(event.source_app, self._t("integrations.event_received"), event.adif_text[:140])
        records = self._adif_parser.parse(event.adif_text)
        if not records:
            self._integration_stats["failed"] += 1
            self._append_integration_event(event.source_app, self._t("integrations.event_parse_failed"), event.adif_text[:140])
            self._set_status("status.integration_parse_failed", source=event.source_app)
            return
        record = records[0]
        try:
            command = SaveQsoCommand(
                callsign=record.get("CALL"),
                qso_date=datetime.strptime(record.get("QSO_DATE"), "%Y%m%d").date(),
                time_on=self._parse_integration_time(record.get("TIME_ON")),
                freq=Decimal(record.get("FREQ")),
                mode=record.get("SUBMODE") or record.get("MODE"),
                rst_sent=record.get("RST_SENT"),
                rst_recv=record.get("RST_RCVD"),
                operator=record.get("OPERATOR") or self.operator_input.text(),
                station_callsign=record.get("STATION_CALLSIGN") or self.station_callsign_input.text(),
                notes=record.get("COMMENT"),
                source=self._integration_source(event.source_app),
            )
            result = self._save_qso_use_case.execute(command)
        except (ValueError, InvalidOperation, QsoValidationError) as exc:
            self._integration_stats["failed"] += 1
            self._append_integration_event(event.source_app, self._t("integrations.event_save_failed"), str(exc))
            self._set_status("status.integration_save_failed", source=event.source_app, detail=str(exc))
            return

        self._integration_stats["saved"] += 1
        self._append_integration_event(
            event.source_app,
            self._t("integrations.event_saved"),
            f"{result.callsign} {result.band} {result.mode}",
        )
        self._load_recent_qsos()
        self._refresh_history(result.callsign)
        self._refresh_dashboard_if_open()
        self._set_status(
            "status.integration_logged",
            source=event.source_app,
            callsign=result.callsign,
            band=result.band,
            mode=result.mode,
        )
        enqueued_services = self._integration_manager.enqueue_uploads(event.adif_text, source="udp")
        for svc in enqueued_services:
            self._append_integration_event(svc, self._t("integrations.event_queued"), result.callsign)
        self._refresh_integration_monitor()

    def _parse_integration_time(self, value: str):
        normalized = value.strip().replace(":", "")
        if len(normalized) < 4:
            raise ValueError("Invalid TIME_ON from integration.")
        normalized = normalized[:6].ljust(6, "0")
        return datetime.strptime(normalized, "%H%M%S").time()

    def _integration_source(self, source_app: str) -> str:
        upper = source_app.upper()
        if "JTDX" in upper:
            return "jtdx_udp"
        if "WSJT" in upper:
            return "wsjtx_udp"
        return "udp_integration"

    def _export_adif(self) -> None:
        filter_dialog = ExportAdifDialog(self._localization, parent=self)
        filter_dialog.setStyleSheet(self._theme_stylesheet)
        if filter_dialog.exec() != filter_dialog.DialogCode.Accepted:
            return
        try:
            export_filter = filter_dialog.export_filter()
        except ValueError as exc:
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.invalid_data_title"),
                str(exc),
            )
            return

        default_dir = Path(self._log_dir or self._data_dir or str(self._active_data_dir))
        export_prefix = self._settings_store.get_string("adif_export_prefix", "pycqlog_export")
        default_name = f"{export_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.adi"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("adif.export_dialog_title"),
            str(default_dir / default_name),
            "ADIF (*.adi *.adif);;All files (*)",
        )
        if not file_path:
            return
        result = self._export_adif_use_case.execute(Path(file_path), filters=export_filter)
        self._log_dir = str(Path(file_path).expanduser().parent)
        self._settings_store.set_string("log_dir", self._log_dir)
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
                executable_path=self._settings_store.get_string("integration_lotw_tqsl_path", "tqsl"),
                station_location=self._settings_store.get_string("integration_lotw_station_location", "")
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
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.invalid_data_title"),
                str(exc),
            )
            return
        except InvalidOperation:
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
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.validation_error_title"),
                str(exc),
            )
            return

        action_key = "action.updated" if self._editing_qso_id is not None else "action.saved"
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
            enqueued_services = self._integration_manager.enqueue_uploads(adif_text, source="manual")
            for svc in enqueued_services:
                self._append_integration_event(svc, self._t("integrations.event_queued"), result.callsign)
            self._refresh_integration_monitor()

    def _load_recent_qsos(self) -> None:
        items = self._list_recent_qsos_use_case.execute(limit=20)
        self.search_input.clear()
        self._set_visible_qso_items(items)

    def _search_qsos(self) -> None:
        items = self._search_qsos_use_case.execute(self.search_input.text(), limit=50)
        self._set_visible_qso_items(items)
        self._set_status("status.search_loaded", count=len(items))

    def _set_visible_qso_items(self, items: list[QsoListItem]) -> None:
        self._loaded_qso_items = items
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
        while layout.count() > 2:
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
            band_suffix = f" ({', '.join(sorted(self._active_band_filters))})"
        if self._active_mode_filters:
            mode_suffix = f" ({', '.join(sorted(self._active_mode_filters))})"
        self.band_filters_label.setText(self._t("filter.band") + band_suffix)
        self.mode_filters_label.setText(self._t("filter.mode") + mode_suffix)
        has_any_filters = bool(self._active_band_filters or self._active_mode_filters)
        self.clear_filters_button.setEnabled(has_any_filters)

    def _populate_table(self, items: list[QsoListItem]) -> None:
        self.qso_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            self._set_table_item(row_index, 0, str(item.qso_id))
            self._set_table_item(row_index, 1, item.callsign)
            self._set_table_item(row_index, 2, item.qso_date.isoformat())
            self._set_table_item(row_index, 3, item.time_on.strftime("%H:%M"))
            self._set_table_item(row_index, 4, item.band)
            self._set_table_item(row_index, 5, item.mode)
            self._apply_qso_row_colors(row_index, item.band, item.mode)
        self.qso_table.resizeColumnsToContents()
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
        detail = self._get_qso_detail_use_case.execute(qso_id)
        if detail is None:
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
        answer = self._show_question(
            self._t("message.delete_title"),
            self._t("message.delete_body", qso_id=qso_id),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted = self._delete_qso_use_case.execute(qso_id)
        if not deleted:
            self._show_message_box(
                QMessageBox.Icon.Warning,
                self._t("message.delete_failed_title"),
                self._t("message.delete_failed_body", qso_id=qso_id),
            )
            return
        if self._editing_qso_id == qso_id:
            self._reset_form()
        self._load_recent_qsos()
        self._set_status("status.deleted", qso_id=qso_id)
        self._refresh_history_from_form()
        self._refresh_dashboard_if_open()

    def _set_table_item(self, row: int, column: int, value: str) -> None:
        self.qso_table.setItem(row, column, QTableWidgetItem(value))

    def _apply_qso_row_colors(self, row: int, band: str, mode: str) -> None:
        if not self._dashboard_chart_preferences()["colorize_tables"]:
            return
        self._apply_cell_color(self.qso_table.item(row, 4), color_for_band(band), bool(band))
        self._apply_cell_color(self.qso_table.item(row, 5), color_for_mode(mode), bool(mode))

    def _reset_form(self) -> None:
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
            
        info = self._fetch_callbook_info_use_case.execute(callsign)
        if info:
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
        if items:
            self.history_summary_label.setText(
                self._t("status.history_found", count=len(items), callsign=normalized)
            )
        else:
            self.history_summary_label.setText(self._t("status.history_empty", callsign=normalized))
        self.history_table.resizeColumnsToContents()

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

    def _set_status(self, key: str, **params: object) -> None:
        self._current_status_key = key
        self._current_status_params = params
        self._refresh_status_label()

    def _refresh_status_label(self) -> None:
        self.status_label.setText(self._t(self._current_status_key, **self._current_status_params))

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
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(self._theme_stylesheet)
        return box.exec()

    def _append_integration_event(self, source: str, event_name: str, detail: str) -> None:
        self._integration_events.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "source": source,
                "event": event_name,
                "detail": detail,
            }
        )
        self._integration_events = self._integration_events[-200:]

    def _refresh_integration_monitor(self) -> None:
        if self._integration_monitor_dialog is None:
            return
        listener_ready, listener_detail = self._integration_manager.listener_status()
        clublog_ready, clublog_detail = self._integration_manager.clublog_status()
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
                "received": str(self._integration_stats["received"]),
                "saved": str(self._integration_stats["saved"]),
                "uploaded": str(self._integration_stats["uploaded"]),
                "failed": str(self._integration_stats["failed"]),
                "pending": str(self._integration_manager.pending_upload_count()),
            }
        )
        self._integration_monitor_dialog.set_events(list(reversed(self._integration_events)))

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
        self._integration_timer.stop()
        self._integration_manager.stop()
        super().closeEvent(event)
