import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path

from pycqlog.application.dto import (
    AdifExportFilter,
    SaveLogbookCommand,
    SaveQsoCommand,
    SaveStationProfileCommand,
)
from pycqlog.application.use_cases import (
    GetActiveLogbookUseCase,
    DeleteQsoUseCase,
    ExportAdifUseCase,
    GetDashboardStatsUseCase,
    GetCallsignHistoryUseCase,
    GetQsoDetailUseCase,
    ListLogbooksUseCase,
    ListRecentQsosUseCase,
    SaveLogbookUseCase,
    SaveQsoUseCase,
    SaveStationProfileUseCase,
    SearchQsosUseCase,
    SetActiveLogbookUseCase,
)
from pycqlog.bootstrap import _resolve_settings_store
from pycqlog.domain.awards import extract_wpx_prefix, resolve_awards
from pycqlog.infrastructure.adif_export import AdifExporter
from pycqlog.infrastructure.app_logging import configure_app_logging
from pycqlog.infrastructure.integrations import ClubLogConfig, IntegrationManager, build_clublog_payload
from pycqlog.infrastructure.repositories import InMemoryQsoRepository, SQLiteQsoRepository
from pycqlog.infrastructure.settings import JsonSettingsStore
from pycqlog.infrastructure.station_service import StationService
from pycqlog.infrastructure.sync_audit import audit_sync_event, parse_adif_summary


def test_save_qso_normalizes_and_resolves_band() -> None:
    use_case = SaveQsoUseCase(repository=InMemoryQsoRepository())

    result = use_case.execute(
        SaveQsoCommand(
            callsign=" py2abc ",
            qso_date=date(2026, 3, 26),
            time_on=time(12, 15),
            freq=Decimal("14.074"),
            mode=" ft8 ",
        )
    )

    assert result.qso_id == 1
    assert result.callsign == "PY2ABC"
    assert result.band == "20m"
    assert result.mode == "FT8"


def test_list_recent_qsos_returns_latest_first() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    list_use_case = ListRecentQsosUseCase(repository=repository)

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2AAA",
            qso_date=date(2026, 3, 26),
            time_on=time(10, 0),
            freq=Decimal("7.074"),
            mode="FT8",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2BBB",
            qso_date=date(2026, 3, 26),
            time_on=time(10, 5),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )

    items = list_use_case.execute(limit=10)

    assert [item.callsign for item in items] == ["PY2BBB", "PY2AAA"]


def test_sqlite_repository_persists_qsos(tmp_path: Path) -> None:
    repository = SQLiteQsoRepository(tmp_path / "pycqlog.db")
    use_case = SaveQsoUseCase(repository=repository)
    list_use_case = ListRecentQsosUseCase(repository=repository)

    result = use_case.execute(
        SaveQsoCommand(
            callsign="PY2SQL",
            qso_date=date(2026, 3, 26),
            time_on=time(18, 30),
            freq=Decimal("21.074"),
            mode="FT8",
        )
    )

    items = list_use_case.execute(limit=10)

    assert result.qso_id == 1
    assert len(items) == 1
    assert items[0].callsign == "PY2SQL"


def test_update_and_get_qso_detail() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    get_use_case = GetQsoDetailUseCase(repository=repository)

    created = save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2OLD",
            qso_date=date(2026, 3, 26),
            time_on=time(9, 0),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )

    updated = save_use_case.execute(
        SaveQsoCommand(
            qso_id=created.qso_id,
            callsign="PY2NEW",
            qso_date=date(2026, 3, 26),
            time_on=time(9, 5),
            freq=Decimal("14.250"),
            mode="SSB",
            notes="Updated contact",
        )
    )
    detail = get_use_case.execute(created.qso_id)

    assert updated.qso_id == created.qso_id
    assert detail is not None
    assert detail.callsign == "PY2NEW"
    assert detail.mode == "SSB"
    assert detail.band == "20m"
    assert detail.notes == "Updated contact"


def test_search_and_delete_qso() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    search_use_case = SearchQsosUseCase(repository=repository)
    delete_use_case = DeleteQsoUseCase(repository=repository)

    created = save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2SEARCH",
            qso_date=date(2026, 3, 26),
            time_on=time(11, 0),
            freq=Decimal("28.074"),
            mode="FT8",
        )
    )

    items = search_use_case.execute("search", limit=10)
    deleted = delete_use_case.execute(created.qso_id)
    after_delete = search_use_case.execute("PY2SEARCH", limit=10)

    assert len(items) == 1
    assert items[0].callsign == "PY2SEARCH"
    assert deleted is True
    assert after_delete == []


def test_callsign_history_returns_only_exact_match() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    history_use_case = GetCallsignHistoryUseCase(repository=repository)

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2HIST",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 0),
            freq=Decimal("14.074"),
            mode="FT8",
            rst_sent="59",
            rst_recv="57",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2HIST/P",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 5),
            freq=Decimal("7.074"),
            mode="FT8",
        )
    )

    items = history_use_case.execute("py2hist", limit=10)

    assert len(items) == 1
    assert items[0].callsign == "PY2HIST"
    assert items[0].rst_sent == "59"


def test_export_adif_writes_saved_qsos(tmp_path: Path) -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    export_use_case = ExportAdifUseCase(repository=repository, exporter=AdifExporter())

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2EXP",
            qso_date=date(2026, 3, 26),
            time_on=time(13, 45),
            freq=Decimal("14.074"),
            mode="FT8",
            rst_sent="59",
            rst_recv="57",
            operator="PY9MT",
            station_callsign="PY9MT",
            notes="Export test",
        )
    )

    destination = tmp_path / "export.adi"
    result = export_use_case.execute(destination)
    content = destination.read_text(encoding="utf-8")

    assert result.exported_count == 1
    assert destination.exists()
    assert "<PROGRAMID:7>PyCQLog" in content
    assert "<CALL:6>PY2EXP" in content
    assert "<COMMENT:11>Export test" in content


def test_export_adif_applies_filters(tmp_path: Path) -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    export_use_case = ExportAdifUseCase(repository=repository, exporter=AdifExporter())

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2AAA",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 0),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2BBB",
            qso_date=date(2026, 3, 27),
            time_on=time(9, 0),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )

    destination = tmp_path / "filtered_export.adi"
    result = export_use_case.execute(
        destination,
        filters=AdifExportFilter(callsign="PY2BBB", date_from=date(2026, 3, 27), mode="CW"),
    )
    content = destination.read_text(encoding="utf-8")

    assert result.exported_count == 1
    assert "<CALL:6>PY2BBB" in content
    assert "<MODE:2>CW" in content
    assert "PY2AAA" not in content


def test_award_resolver_handles_operating_prefix_and_wpx() -> None:
    hawaii = resolve_awards("KH6/PY2ABC")
    brazil = resolve_awards("PY2XYZ/P")

    assert hawaii.entity == "Hawaii"
    assert hawaii.cq_zone == 31
    assert hawaii.wpx_prefix == "PY2ABC"
    assert brazil.entity == "Brazil"
    assert brazil.cq_zone == 11
    assert extract_wpx_prefix("PY2XYZ/P") == "PY2XYZ"


def test_award_resolver_matches_curated_prefixes() -> None:
    info = resolve_awards("ZZ9PX")

    assert info.entity == "Brazil"
    assert info.reliable is True


def test_integration_manager_validates_and_filters_sources(tmp_path: Path) -> None:
    settings = JsonSettingsStore(tmp_path / "settings.json")
    settings.update_many(
        {
            "integration_clublog_enabled": "true",
            "integration_clublog_email": "radio@example.com",
            "integration_clublog_password": "app-pass",
            "integration_clublog_callsign": "PY9MT",
            "integration_clublog_api_key": "secret",
            "integration_clublog_endpoint": "https://clublog.org/realtime.php",
            "integration_clublog_delete_endpoint": "https://clublog.org/delete.php",
            "integration_clublog_upload_udp": "true",
            "integration_clublog_upload_manual": "false",
        }
    )
    manager = IntegrationManager(settings, tmp_path / "queue.json")

    ready, detail = manager.validate_clublog_config()

    assert ready is True
    assert detail == "Club Log ready"
    assert manager.should_upload_source("udp") is True
    assert manager.should_upload_source("manual") is False
    assert "Club Log" not in manager.enqueue_uploads("<CALL:5>PY9MT<EOR>", source="manual")
    assert "Club Log" in manager.enqueue_uploads("<CALL:5>PY9MT<EOR>", source="udp")


def test_integration_manager_accepts_local_clublog_mock_without_real_credentials(tmp_path: Path) -> None:
    settings = JsonSettingsStore(tmp_path / "settings.json")
    settings.update_many(
        {
            "integration_clublog_enabled": "true",
            "integration_clublog_email": "",
            "integration_clublog_password": "",
            "integration_clublog_callsign": "PY9MT",
            "integration_clublog_api_key": "",
            "integration_clublog_endpoint": "http://127.0.0.1:8000/clublog/upload",
            "integration_clublog_delete_endpoint": "http://127.0.0.1:8000/clublog/delete",
            "integration_clublog_upload_udp": "true",
            "integration_clublog_upload_manual": "true",
        }
    )
    manager = IntegrationManager(settings, tmp_path / "queue.json")

    ready, detail = manager.validate_clublog_config()

    assert ready is True
    assert detail == "Club Log ready"
    assert "Club Log" in manager.enqueue_uploads("<CALL:5>PY9MT<EOR>", source="manual")


def test_build_clublog_payload_adds_mock_defaults_for_local_endpoint() -> None:
    config = ClubLogConfig(
        enabled=True,
        email="",
        password="",
        callsign="PY9MT",
        api_key="",
        endpoint="http://localhost:8000/clublog/upload",
        delete_endpoint="http://localhost:8000/clublog/delete",
        interval_seconds=5,
    )

    payload = build_clublog_payload(config, "<CALL:5>PY9MT<EOR>")

    assert payload["email"] == "mock@example.com"
    assert payload["password"] == "mock-password"
    assert payload["callsign"] == "PY9MT"
    assert payload["api"] == "mock-api-key"
    assert payload["api_key"] == "mock-api-key"
    assert payload["source"] == "pycqlog"
    assert payload["format"] == "adif_realtime"


def test_integration_manager_does_not_retry_pending_jobs_automatically_on_startup(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(
        json.dumps(
            [
                {
                    "job_id": "pending-1",
                    "config": {
                        "enabled": True,
                        "email": "radio@example.com",
                        "password": "app-pass",
                        "callsign": "PY9MT",
                        "api_key": "secret",
                        "endpoint": "https://clublog.org/realtime.php",
                        "delete_endpoint": "https://clublog.org/delete.php",
                        "interval_seconds": 10,
                    },
                    "adif_text": "<CALL:5>PY9MT<EOR>",
                    "created_at": "2026-03-31T15:00:00",
                    "signature": "sig-1",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    settings = JsonSettingsStore(tmp_path / "settings.json")

    manager = IntegrationManager(settings, queue_path)

    assert manager.pending_upload_count() == 1
    assert manager.poll_upload_results() == []


def test_retry_pending_uploads_removes_stale_local_jobs(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(
        json.dumps(
            [
                {
                    "job_id": "pending-local",
                    "config": {
                        "enabled": True,
                        "email": "",
                        "password": "",
                        "callsign": "PY9MT",
                        "api_key": "",
                        "endpoint": "http://127.0.0.1:8000/",
                        "delete_endpoint": "http://127.0.0.1:8000/delete",
                        "interval_seconds": 10,
                    },
                    "adif_text": "<CALL:5>PY9MT<EOR>",
                    "created_at": "2026-03-31T15:00:00",
                    "signature": "sig-local",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    settings = JsonSettingsStore(tmp_path / "settings.json")

    manager = IntegrationManager(settings, queue_path)
    retried = manager.retry_pending_uploads()

    assert retried == 0
    assert manager.pending_upload_count() == 0


def test_integration_manager_blocks_new_enqueue_during_clublog_cooldown(tmp_path: Path) -> None:
    settings = JsonSettingsStore(tmp_path / "settings.json")
    settings.update_many(
        {
            "integration_clublog_enabled": "true",
            "integration_clublog_email": "radio@example.com",
            "integration_clublog_password": "app-pass",
            "integration_clublog_callsign": "PY9MT",
            "integration_clublog_api_key": "secret",
            "integration_clublog_endpoint": "https://clublog.org/realtime.php",
            "integration_clublog_delete_endpoint": "https://clublog.org/delete.php",
            "integration_clublog_upload_udp": "true",
            "integration_clublog_upload_manual": "true",
            "integration_clublog_cooldown_until": "2099-01-01T00:00:00",
        }
    )
    manager = IntegrationManager(settings, tmp_path / "queue.json")

    assert manager.clublog_status()[0] is False
    assert manager.enqueue_uploads("<CALL:5>PY9MT<EOR>", source="manual") == []


def test_integration_manager_can_enqueue_clublog_delete(tmp_path: Path) -> None:
    settings = JsonSettingsStore(tmp_path / "settings.json")
    settings.update_many(
        {
            "integration_clublog_enabled": "true",
            "integration_clublog_email": "radio@example.com",
            "integration_clublog_password": "app-pass",
            "integration_clublog_callsign": "PY9MT",
            "integration_clublog_api_key": "secret",
            "integration_clublog_endpoint": "https://clublog.org/realtime.php",
            "integration_clublog_delete_endpoint": "https://clublog.org/delete.php",
            "integration_clublog_upload_manual": "true",
        }
    )
    manager = IntegrationManager(settings, tmp_path / "queue.json")

    queued = manager.enqueue_clublog_delete(
        callsign="PY2ABC",
        qso_date="2026-03-31",
        time_on="15:24",
        band="10m",
        source="manual",
    )

    assert queued is True
    assert manager.pending_upload_count() == 1


def test_sync_audit_writes_destination_specific_log_file(tmp_path: Path) -> None:
    configure_app_logging(tmp_path)

    audit_sync_event(
        "clublog",
        state="queued",
        job_id="job-1",
        action="insert",
        adif_text="<CALL:6>PY2ABC<QSO_DATE:8>20260331<TIME_ON:6>152400<BAND:3>20m<MODE:3>FT8<EOR>",
        detail="Queued for Club Log upload",
        endpoint="https://clublog.org/realtime.php",
    )

    sync_log = tmp_path / "logs" / "sync_clublog.log"

    assert sync_log.exists()
    content = sync_log.read_text(encoding="utf-8")
    assert "state=queued" in content
    assert "job_id=job-1" in content
    assert "callsign=PY2ABC" in content
    assert "qso_date=20260331" in content
    assert "time_on=15:24" in content


def test_parse_adif_summary_extracts_identity_fields() -> None:
    summary = parse_adif_summary(
        "<CALL:6>PY2ABC<QSO_DATE:8>20260331<TIME_ON:6>152400<BAND:3>20m<MODE:3>FT8<EOR>"
    )

    assert summary == {
        "callsign": "PY2ABC",
        "qso_date": "20260331",
        "time_on": "15:24",
        "band": "20M",
        "mode": "FT8",
    }


def test_station_service_processes_udp_event_and_updates_stats(tmp_path: Path) -> None:
    repository = InMemoryQsoRepository()
    settings = JsonSettingsStore(tmp_path / "settings.json")
    settings.update_many(
        {
            "integration_wsjt_enabled": "true",
            "integration_clublog_enabled": "false",
            "integration_qrz_enabled": "false",
        }
    )
    service = StationService(
        settings_store=settings,
        save_qso_use_case=SaveQsoUseCase(repository=repository),
        get_active_logbook_use_case=GetActiveLogbookUseCase(repository=repository),
        queue_path=tmp_path / "queue.json",
    )

    service.start()
    try:
        service.inject_test_logged_qso()
        result = service.process_once()
    finally:
        service.stop()

    recent = ListRecentQsosUseCase(repository=repository).execute(limit=10)

    assert result.saved_callsigns == ["PY0TEST"]
    assert recent[0].callsign == "PY0TEST"
    assert service.stats()["received"] == 1
    assert service.stats()["saved"] == 1
    assert any(event["event"] == "QSO saved" for event in service.events())


def test_settings_store_writes_ini_with_sections_and_comments(tmp_path: Path) -> None:
    store = JsonSettingsStore(tmp_path / "pycqlog.conf")
    store.update_many(
        {
            "language": "pt-BR",
            "data_dir": "/tmp/data",
            "integration_wsjt_enabled": "true",
            "integration_clublog_endpoint": "https://clublog.org/realtime.php",
        }
    )

    content = (tmp_path / "pycqlog.conf").read_text(encoding="utf-8")

    assert "# PyCQLog configuration file" in content
    assert "[ui]" in content
    assert "language = pt-BR" in content
    assert "[paths]" in content
    assert "data_dir = /tmp/data" in content
    assert "[wsjt]" in content
    assert "integration_wsjt_enabled = true" in content
    assert "[clublog]" in content


def test_bootstrap_migrates_legacy_json_to_pycqlog_conf(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    legacy = config_dir / "settings.json"
    legacy.write_text(
        json.dumps(
            {
                "language": "pt-BR",
                "theme": "system",
                "integration_wsjt_enabled": "true",
            }
        ),
        encoding="utf-8",
    )

    store = _resolve_settings_store(config_dir)

    assert store.get_string("language", "") == "pt-BR"
    conf_path = config_dir / "pycqlog.conf"
    assert conf_path.exists()
    content = conf_path.read_text(encoding="utf-8")
    assert "[ui]" in content
    assert "[wsjt]" in content


def test_dashboard_stats_aggregates_repository_data() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    dashboard_use_case = GetDashboardStatsUseCase(repository=repository, logbook_repository=repository)

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2AAA",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 0),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2AAA",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 15),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2BBB",
            qso_date=date(2026, 3, 27),
            time_on=time(9, 0),
            freq=Decimal("21.200"),
            mode="SSB",
        )
    )

    stats = dashboard_use_case.execute()

    assert stats.total_qsos == 3
    assert stats.unique_callsigns == 2
    assert stats.active_bands == 3
    assert stats.active_modes == 3
    assert stats.top_callsigns[0].label == "PY2AAA"
    assert stats.top_callsigns[0].value == 2


def test_dashboard_stats_filters_by_period() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    dashboard_use_case = GetDashboardStatsUseCase(repository=repository, logbook_repository=repository)

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2OLD",
            qso_date=date(2026, 3, 1),
            time_on=time(8, 0),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2NEW",
            qso_date=date(2026, 3, 26),
            time_on=time(9, 0),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )

    stats = dashboard_use_case.execute(period_days=7)

    assert stats.total_qsos == 1
    assert stats.unique_callsigns == 1
    assert stats.top_callsigns[0].label == "PY2NEW"


def test_dashboard_stats_includes_month_and_hour_views() -> None:
    repository = InMemoryQsoRepository()
    save_use_case = SaveQsoUseCase(repository=repository)
    dashboard_use_case = GetDashboardStatsUseCase(repository=repository, logbook_repository=repository)


def test_logbooks_scope_qsos_and_active_selection() -> None:
    repository = InMemoryQsoRepository()
    save_logbook_use_case = SaveLogbookUseCase(repository=repository)
    set_active_use_case = SetActiveLogbookUseCase(repository=repository)
    list_logbooks_use_case = ListLogbooksUseCase(repository=repository)
    active_logbook_use_case = GetActiveLogbookUseCase(repository=repository)
    save_qso_use_case = SaveQsoUseCase(repository=repository)
    list_recent_use_case = ListRecentQsosUseCase(repository=repository)

    portable = save_logbook_use_case.execute(
        SaveLogbookCommand(name="Portable", description="Field operation")
    )
    set_active_use_case.execute(portable.logbook_id)
    save_qso_use_case.execute(
        SaveQsoCommand(
            callsign="PY2PORT",
            qso_date=date(2026, 3, 26),
            time_on=time(10, 0),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    set_active_use_case.execute(1)
    save_qso_use_case.execute(
        SaveQsoCommand(
            callsign="PY2MAIN",
            qso_date=date(2026, 3, 26),
            time_on=time(10, 5),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )

    main_items = list_recent_use_case.execute(limit=10)
    logbooks = list_logbooks_use_case.execute()
    active = active_logbook_use_case.execute()

    assert active.logbook_id == 1
    assert [item.callsign for item in main_items] == ["PY2MAIN"]
    assert any(item.name == "Portable" and item.qso_count == 1 for item in logbooks)


def test_station_profiles_can_be_linked_to_logbook_defaults() -> None:
    repository = InMemoryQsoRepository()
    save_profile_use_case = SaveStationProfileUseCase(repository=repository)
    save_logbook_use_case = SaveLogbookUseCase(repository=repository)
    set_active_use_case = SetActiveLogbookUseCase(repository=repository)
    active_logbook_use_case = GetActiveLogbookUseCase(repository=repository)

    operator = save_profile_use_case.execute(
        SaveStationProfileCommand(name="Operador Base", profile_type="operator", callsign="PY9MT")
    )
    station = save_profile_use_case.execute(
        SaveStationProfileCommand(name="Estacao Base", profile_type="station", callsign="PY9MT")
    )
    logbook = save_logbook_use_case.execute(
        SaveLogbookCommand(
            name="Contest",
            operator_profile_id=operator.profile_id,
            station_profile_id=station.profile_id,
        )
    )
    active = set_active_use_case.execute(logbook.logbook_id)
    summary = active_logbook_use_case.execute()

    assert active.operator_callsign == "PY9MT"
    assert active.station_callsign == "PY9MT"
    assert summary.operator_profile_id == operator.profile_id


def test_dashboard_stats_include_logbook_and_award_counters() -> None:
    repository = InMemoryQsoRepository()
    save_qso_use_case = SaveQsoUseCase(repository=repository)
    dashboard_use_case = GetDashboardStatsUseCase(repository=repository, logbook_repository=repository)

    save_qso_use_case.execute(
        SaveQsoCommand(
            callsign="PY2AAA",
            qso_date=date(2026, 3, 26),
            time_on=time(8, 0),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    save_qso_use_case.execute(
        SaveQsoCommand(
            callsign="K1ABC",
            qso_date=date(2026, 3, 26),
            time_on=time(9, 0),
            freq=Decimal("21.074"),
            mode="FT8",
        )
    )

    stats = dashboard_use_case.execute()

    assert stats.logbook_name == "Main Logbook"
    assert stats.dxcc_entities >= 2
    assert stats.waz_zones >= 2
    assert stats.wpx_prefixes >= 2

    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2JAN",
            qso_date=date(2026, 1, 15),
            time_on=time(8, 30),
            freq=Decimal("14.074"),
            mode="FT8",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2FEB",
            qso_date=date(2026, 2, 10),
            time_on=time(8, 45),
            freq=Decimal("7.040"),
            mode="CW",
        )
    )
    save_use_case.execute(
        SaveQsoCommand(
            callsign="PY2FEB2",
            qso_date=date(2026, 2, 11),
            time_on=time(21, 5),
            freq=Decimal("21.300"),
            mode="SSB",
        )
    )

    stats = dashboard_use_case.execute()

    assert ("2026-01", 1) in [(item.label, item.value) for item in stats.by_month]
    assert ("2026-02", 2) in [(item.label, item.value) for item in stats.by_month]
    assert ("08:00", 2) in [(item.label, item.value) for item in stats.by_hour]
    assert ("21:00", 1) in [(item.label, item.value) for item in stats.by_hour]
