import os
from pathlib import Path

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
from pycqlog.infrastructure.adif import AdifParser
from pycqlog.infrastructure.callbook import HamQTHCallbookProvider, QrzCallbookProvider
from pycqlog.infrastructure.adif_export import AdifExporter
from pycqlog.infrastructure.repositories import SQLiteQsoRepository
from pycqlog.infrastructure.settings import JsonSettingsStore
from pycqlog.interfaces.desktop.app import DesktopApplication
from pycqlog.localization import LocalizationService


def _env_value(primary: str, legacy: str) -> str | None:
    return os.environ.get(primary) or os.environ.get(legacy)


def _ensure_dir(preferred: Path, fallback: Path) -> Path:
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _resolve_config_dir() -> Path:
    env_dir = _env_value("PYCQLOG_CONFIG_DIR", "PY4LOG_CONFIG_DIR")
    if env_dir:
        return _ensure_dir(Path(env_dir).expanduser(), Path.cwd() / ".pycqlog_config")
    return _ensure_dir(Path.home() / ".config" / "pycqlog", Path.cwd() / ".pycqlog_config")


def _resolve_default_data_dir() -> Path:
    env_dir = _env_value("PYCQLOG_DATA_DIR", "PY4LOG_DATA_DIR")
    if env_dir:
        return _ensure_dir(Path(env_dir).expanduser(), Path.cwd() / ".pycqlog_data")
    return _ensure_dir(Path.home() / ".local" / "share" / "pycqlog", Path.cwd() / ".pycqlog_data")


def _resolve_data_dir(settings_store: JsonSettingsStore) -> Path:
    env_dir = _env_value("PYCQLOG_DATA_DIR", "PY4LOG_DATA_DIR")
    if env_dir:
        return _ensure_dir(Path(env_dir).expanduser(), Path.cwd() / ".pycqlog_data")

    configured = settings_store.get_string("data_dir", "").strip()
    if configured:
        return _ensure_dir(Path(configured).expanduser(), Path.cwd() / ".pycqlog_data")

    return _resolve_default_data_dir()


def build_desktop_app() -> DesktopApplication:
    config_dir = _resolve_config_dir()
    settings_store = JsonSettingsStore(config_dir / "settings.json")
    default_language = "pt-BR" if os.environ.get("LANG", "").lower().startswith("pt_br") else "en"
    localization = LocalizationService(settings_store.get_language(default_language))
    data_dir = _resolve_data_dir(settings_store)
    active_logbook_id = int(settings_store.get_string("active_logbook_id", "1") or "1")
    repository = SQLiteQsoRepository(data_dir / "pycqlog.db", active_logbook_id=active_logbook_id)
    repository.ensure_default_logbook()

    save_qso = SaveQsoUseCase(repository=repository)
    list_recent_qsos = ListRecentQsosUseCase(repository=repository)
    get_qso_detail = GetQsoDetailUseCase(repository=repository)
    delete_qso = DeleteQsoUseCase(repository=repository)
    search_qsos = SearchQsosUseCase(repository=repository)
    get_callsign_history = GetCallsignHistoryUseCase(repository=repository)
    get_dashboard_stats = GetDashboardStatsUseCase(repository=repository, logbook_repository=repository)
    import_adif = ImportAdifUseCase(
        save_qso=save_qso,
        parser=AdifParser(),
        repository=repository,
    )
    export_adif = ExportAdifUseCase(
        repository=repository,
        exporter=AdifExporter(),
    )
    list_logbooks = ListLogbooksUseCase(repository=repository)
    get_active_logbook = GetActiveLogbookUseCase(repository=repository)
    save_logbook = SaveLogbookUseCase(repository=repository)
    delete_logbook = DeleteLogbookUseCase(repository=repository)
    set_active_logbook = SetActiveLogbookUseCase(repository=repository)
    list_station_profiles = ListStationProfilesUseCase(repository=repository)
    save_station_profile = SaveStationProfileUseCase(repository=repository)
    delete_station_profile = DeleteStationProfileUseCase(repository=repository)
    
    # callbook_provider = HamQTHCallbookProvider() # Disabled by request
    callbook_provider = QrzCallbookProvider(
        username=settings_store.get_string("integration_qrz_username", ""),
        password=settings_store.get_string("integration_qrz_password", "")
    )
    fetch_callbook_info = FetchCallbookInfoUseCase(port=callbook_provider)

    return DesktopApplication(
        save_qso=save_qso,
        list_recent_qsos=list_recent_qsos,
        get_qso_detail=get_qso_detail,
        delete_qso=delete_qso,
        search_qsos=search_qsos,
        get_callsign_history=get_callsign_history,
        get_dashboard_stats=get_dashboard_stats,
        import_adif=import_adif,
        export_adif=export_adif,
        list_logbooks=list_logbooks,
        get_active_logbook=get_active_logbook,
        save_logbook=save_logbook,
        delete_logbook=delete_logbook,
        set_active_logbook=set_active_logbook,
        list_station_profiles=list_station_profiles,
        save_station_profile=save_station_profile,
        delete_station_profile=delete_station_profile,
        fetch_callbook_info=fetch_callbook_info,
        localization=localization,
        settings_store=settings_store,
        data_dir=data_dir,
        config_dir=config_dir,
    )
