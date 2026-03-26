from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from pycqlog.application.use_cases import (
    DeleteLogbookUseCase,
    DeleteQsoUseCase,
    DeleteStationProfileUseCase,
    ExportAdifUseCase,
    GetActiveLogbookUseCase,
    GetCallsignHistoryUseCase,
    GetDashboardStatsUseCase,
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
from pycqlog.infrastructure.settings import JsonSettingsStore
from pycqlog.interfaces.desktop.main_window import MainWindow
from pycqlog.localization import LocalizationService


class DesktopApplication:
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
        self._save_qso = save_qso
        self._list_recent_qsos = list_recent_qsos
        self._get_qso_detail = get_qso_detail
        self._delete_qso = delete_qso
        self._search_qsos = search_qsos
        self._get_callsign_history = get_callsign_history
        self._get_dashboard_stats = get_dashboard_stats
        self._import_adif = import_adif
        self._export_adif = export_adif
        self._list_logbooks = list_logbooks
        self._get_active_logbook = get_active_logbook
        self._save_logbook = save_logbook
        self._delete_logbook = delete_logbook
        self._set_active_logbook = set_active_logbook
        self._list_station_profiles = list_station_profiles
        self._save_station_profile = save_station_profile
        self._delete_station_profile = delete_station_profile
        self._fetch_callbook_info = fetch_callbook_info
        self._localization = localization
        self._settings_store = settings_store
        self._data_dir = data_dir
        self._config_dir = config_dir

    def run(self) -> int:
        qt_app = QApplication(sys.argv)
        window = MainWindow(
            save_qso=self._save_qso,
            list_recent_qsos=self._list_recent_qsos,
            get_qso_detail=self._get_qso_detail,
            delete_qso=self._delete_qso,
            search_qsos=self._search_qsos,
            get_callsign_history=self._get_callsign_history,
            get_dashboard_stats=self._get_dashboard_stats,
            import_adif=self._import_adif,
            export_adif=self._export_adif,
            list_logbooks=self._list_logbooks,
            get_active_logbook=self._get_active_logbook,
            save_logbook=self._save_logbook,
            delete_logbook=self._delete_logbook,
            set_active_logbook=self._set_active_logbook,
            list_station_profiles=self._list_station_profiles,
            save_station_profile=self._save_station_profile,
            delete_station_profile=self._delete_station_profile,
            fetch_callbook_info=self._fetch_callbook_info,
            localization=self._localization,
            settings_store=self._settings_store,
            data_dir=self._data_dir,
            config_dir=self._config_dir,
        )
        window.show()
        return qt_app.exec()
