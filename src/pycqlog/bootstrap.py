import os
import secrets
from dataclasses import dataclass
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
from pycqlog.infrastructure.app_logging import configure_app_logging, get_logger
from pycqlog.infrastructure.remote_client import (
    RemoteApiClient,
    RemoteCallbookProvider,
    RemoteLogbookRepository,
    RemoteQsoRepository,
    RemoteStationProfileRepository,
)
from pycqlog.infrastructure.repositories import SQLiteQsoRepository
from pycqlog.infrastructure.settings import JsonSettingsStore, filter_settings_for_profile
from pycqlog.infrastructure.station_service import StationService
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


def _normalize_legacy_project_path(raw_path: str) -> str:
    value = raw_path.strip()
    if not value:
        return ""
    return value.replace("/py4log/", "/pycqlog/")


def _resolve_log_dir(settings_store: JsonSettingsStore, data_dir: Path) -> Path:
    configured = settings_store.get_string("log_dir", "").strip()
    if configured:
        normalized = _normalize_legacy_project_path(configured)
        if normalized != configured:
            settings_store.set_string("log_dir", normalized)
        return _ensure_dir(Path(normalized).expanduser(), data_dir)
    return _ensure_dir(data_dir, Path.cwd() / ".pycqlog_data")


def _settings_filename(profile: str) -> str:
    return "pycqlog_daemon.conf" if profile == "daemon" else "pycqlog_ui.conf"


def _resolve_settings_store(config_dir: Path, profile: str = "ui") -> JsonSettingsStore:
    conf_path = config_dir / _settings_filename(profile)
    legacy_json_path = config_dir / "settings.json"
    store = JsonSettingsStore(conf_path)
    if conf_path.exists():
        filtered = filter_settings_for_profile(store.load(), profile)
        if filtered != store.load():
            store.save(filtered)
        _ensure_service_security_defaults(store, profile)
        return store
    if legacy_json_path.exists():
        legacy_store = JsonSettingsStore(legacy_json_path)
        legacy_data = legacy_store.load()
        if legacy_data:
            flat = {key: str(value) for key, value in legacy_data.items() if isinstance(key, str)}
            store.save(filter_settings_for_profile(flat, profile))
    _ensure_service_security_defaults(store, profile)
    return store


def _ensure_service_security_defaults(settings_store: JsonSettingsStore, profile: str) -> None:
    updates: dict[str, str] = {}
    if profile == "ui":
        if not settings_store.get_string("service_remote_enabled", "").strip():
            updates["service_remote_enabled"] = "false"
        if not settings_store.get_string("service_remote_host", "").strip():
            updates["service_remote_host"] = "127.0.0.1"
        if not settings_store.get_string("service_remote_port", "").strip():
            updates["service_remote_port"] = "8746"
    else:
        if not settings_store.get_string("service_bind_host", "").strip():
            updates["service_bind_host"] = "127.0.0.1"
        if not settings_store.get_string("service_bind_port", "").strip():
            updates["service_bind_port"] = "8746"
    if not settings_store.get_string("service_auth_code", "").strip():
        updates["service_auth_code"] = secrets.token_urlsafe(24)
    if updates:
        settings_store.update_many(updates)


@dataclass(slots=True)
class AppContext:
    save_qso: SaveQsoUseCase
    list_recent_qsos: ListRecentQsosUseCase
    get_qso_detail: GetQsoDetailUseCase
    delete_qso: DeleteQsoUseCase
    search_qsos: SearchQsosUseCase
    get_callsign_history: GetCallsignHistoryUseCase
    get_dashboard_stats: GetDashboardStatsUseCase
    import_adif: ImportAdifUseCase
    export_adif: ExportAdifUseCase
    list_logbooks: ListLogbooksUseCase
    get_active_logbook: GetActiveLogbookUseCase
    save_logbook: SaveLogbookUseCase
    delete_logbook: DeleteLogbookUseCase
    set_active_logbook: SetActiveLogbookUseCase
    list_station_profiles: ListStationProfilesUseCase
    save_station_profile: SaveStationProfileUseCase
    delete_station_profile: DeleteStationProfileUseCase
    fetch_callbook_info: FetchCallbookInfoUseCase
    localization: LocalizationService
    settings_store: JsonSettingsStore
    ui_settings_store: JsonSettingsStore
    daemon_settings_store: JsonSettingsStore
    data_dir: Path
    config_dir: Path


def build_app_context(*, allow_remote: bool = True, settings_profile: str | None = None) -> AppContext:
    config_dir = _resolve_config_dir()
    ui_settings_store = _resolve_settings_store(config_dir, profile="ui")
    daemon_settings_store = _resolve_settings_store(config_dir, profile="daemon")
    profile = settings_profile or ("ui" if allow_remote else "daemon")
    settings_store = _resolve_settings_store(config_dir, profile=profile)
    default_language = "pt-BR" if os.environ.get("LANG", "").lower().startswith("pt_br") else "en"
    localization = LocalizationService(ui_settings_store.get_language(default_language))
    data_dir = _resolve_data_dir(settings_store)
    log_dir = _resolve_log_dir(settings_store, data_dir)
    log_file = configure_app_logging(log_dir)
    logger = get_logger("bootstrap")
    remote_enabled = allow_remote and settings_store.get_string("service_remote_enabled", "false") == "true"
    logger.info(
        "Starting PyCQLog. config_dir=%s data_dir=%s log_dir=%s log_file=%s remote_enabled=%s",
        config_dir,
        data_dir,
        log_dir,
        log_file,
        remote_enabled,
    )
    if remote_enabled:
        remote_host = settings_store.get_string("service_remote_host", "127.0.0.1") or "127.0.0.1"
        remote_port = int(settings_store.get_string("service_remote_port", "8746") or "8746")
        remote_auth_code = settings_store.get_string("service_auth_code", "")
        client = RemoteApiClient(remote_host, remote_port, remote_auth_code)
        repository = RemoteQsoRepository(client)
        logbook_repository = RemoteLogbookRepository(client)
        station_profile_repository = RemoteStationProfileRepository(client)
        callbook_provider = RemoteCallbookProvider(client)
    else:
        active_logbook_id = int(settings_store.get_string("active_logbook_id", "1") or "1")
        repository = SQLiteQsoRepository(data_dir / "pycqlog.db", active_logbook_id=active_logbook_id)
        repository.ensure_default_logbook()
        logbook_repository = repository
        station_profile_repository = repository

    save_qso = SaveQsoUseCase(repository=repository)
    list_recent_qsos = ListRecentQsosUseCase(repository=repository)
    get_qso_detail = GetQsoDetailUseCase(repository=repository)
    delete_qso = DeleteQsoUseCase(repository=repository)
    search_qsos = SearchQsosUseCase(repository=repository)
    get_callsign_history = GetCallsignHistoryUseCase(repository=repository)
    get_dashboard_stats = GetDashboardStatsUseCase(repository=repository, logbook_repository=logbook_repository)
    import_adif = ImportAdifUseCase(
        save_qso=save_qso,
        parser=AdifParser(),
        repository=repository,
    )
    export_adif = ExportAdifUseCase(
        repository=repository,
        exporter=AdifExporter(),
    )
    list_logbooks = ListLogbooksUseCase(repository=logbook_repository)
    get_active_logbook = GetActiveLogbookUseCase(repository=logbook_repository)
    save_logbook = SaveLogbookUseCase(repository=logbook_repository)
    delete_logbook = DeleteLogbookUseCase(repository=logbook_repository)
    set_active_logbook = SetActiveLogbookUseCase(repository=logbook_repository)
    list_station_profiles = ListStationProfilesUseCase(repository=station_profile_repository)
    save_station_profile = SaveStationProfileUseCase(repository=station_profile_repository)
    delete_station_profile = DeleteStationProfileUseCase(repository=station_profile_repository)

    if not remote_enabled:
        # callbook_provider = HamQTHCallbookProvider() # Disabled by request
        callbook_provider = QrzCallbookProvider(
            username=settings_store.get_string("integration_qrz_username", ""),
            password=settings_store.get_string("integration_qrz_password", "")
        )
    fetch_callbook_info = FetchCallbookInfoUseCase(port=callbook_provider)

    return AppContext(
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
        ui_settings_store=ui_settings_store,
        daemon_settings_store=daemon_settings_store,
        data_dir=data_dir,
        config_dir=config_dir,
    )


def build_desktop_app() -> DesktopApplication:
    config_dir = _resolve_config_dir()
    ui_settings_store = _resolve_settings_store(config_dir, profile="ui")
    remote_enabled = ui_settings_store.get_string("service_remote_enabled", "false") == "true"
    context = build_app_context(
        allow_remote=remote_enabled,
        settings_profile="ui" if remote_enabled else "daemon",
    )
    return DesktopApplication(
        save_qso=context.save_qso,
        list_recent_qsos=context.list_recent_qsos,
        get_qso_detail=context.get_qso_detail,
        delete_qso=context.delete_qso,
        search_qsos=context.search_qsos,
        get_callsign_history=context.get_callsign_history,
        get_dashboard_stats=context.get_dashboard_stats,
        import_adif=context.import_adif,
        export_adif=context.export_adif,
        list_logbooks=context.list_logbooks,
        get_active_logbook=context.get_active_logbook,
        save_logbook=context.save_logbook,
        delete_logbook=context.delete_logbook,
        set_active_logbook=context.set_active_logbook,
        list_station_profiles=context.list_station_profiles,
        save_station_profile=context.save_station_profile,
        delete_station_profile=context.delete_station_profile,
        fetch_callbook_info=context.fetch_callbook_info,
        localization=context.localization,
        ui_settings_store=context.ui_settings_store,
        daemon_settings_store=context.daemon_settings_store,
        data_dir=context.data_dir,
        config_dir=context.config_dir,
    )


def build_station_service(
    *,
    operator_callsign_getter=None,
    station_callsign_getter=None,
) -> StationService:
    context = build_app_context(allow_remote=False)
    return StationService(
        settings_store=context.settings_store,
        save_qso_use_case=context.save_qso,
        get_active_logbook_use_case=context.get_active_logbook,
        queue_path=context.config_dir / "clublog_queue.json",
        operator_callsign_getter=operator_callsign_getter,
        station_callsign_getter=station_callsign_getter,
    )
