from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Callable

from pycqlog.application.dto import SaveQsoCommand
from pycqlog.application.use_cases import GetActiveLogbookUseCase, SaveQsoUseCase
from pycqlog.domain.services import QsoValidationError
from pycqlog.infrastructure.adif import AdifParser
from pycqlog.infrastructure.app_logging import get_logger
from pycqlog.infrastructure.integrations import IntegrationManager, LoggedAdifEvent
from pycqlog.infrastructure.settings import JsonSettingsStore


logger = get_logger("station_service")


@dataclass(slots=True)
class IntegrationEventRecord:
    time: str
    source: str
    event: str
    detail: str


@dataclass(slots=True)
class IntegrationStatsRecord:
    received: int = 0
    saved: int = 0
    uploaded: int = 0
    failed: int = 0


@dataclass(slots=True)
class StationServiceProcessResult:
    saved_callsigns: list[str]
    upload_results: list[tuple[str, bool, str]]


class StationService:
    def __init__(
        self,
        *,
        settings_store: JsonSettingsStore,
        save_qso_use_case: SaveQsoUseCase,
        get_active_logbook_use_case: GetActiveLogbookUseCase | None,
        queue_path,
        operator_callsign_getter: Callable[[], str] | None = None,
        station_callsign_getter: Callable[[], str] | None = None,
    ) -> None:
        self._settings_store = settings_store
        self._save_qso_use_case = save_qso_use_case
        self._get_active_logbook_use_case = get_active_logbook_use_case
        self._integration_manager = IntegrationManager(settings_store, queue_path)
        self._adif_parser = AdifParser()
        self._operator_callsign_getter = operator_callsign_getter or (lambda: "")
        self._station_callsign_getter = station_callsign_getter or (lambda: "")
        self._events: list[IntegrationEventRecord] = []
        self._stats = IntegrationStatsRecord()
        self._lock = threading.Lock()

    def start(self) -> None:
        self._integration_manager.start()
        logger.info("Station service started.")

    def stop(self) -> None:
        self._integration_manager.stop()
        logger.info("Station service stopped.")

    def process_once(self) -> StationServiceProcessResult:
        saved_callsigns: list[str] = []
        for msg in self._integration_manager.poll_debug_messages():
            self._append_event("WSJT-UDP", "Debug / Raw Packet", msg)
        for event in self._integration_manager.poll_logged_qsos():
            callsign = self._handle_logged_adif_event(event)
            if callsign:
                saved_callsigns.append(callsign)
        upload_results = self._integration_manager.poll_upload_results()
        for service_name, success, detail in upload_results:
            logger.info("Integration result. service=%s success=%s detail=%s", service_name, success, detail)
            if success:
                with self._lock:
                    self._stats.uploaded += 1
                self._append_event(service_name, "Upload succeeded", detail)
            else:
                with self._lock:
                    self._stats.failed += 1
                self._append_event(service_name, "Upload failed", detail)
        return StationServiceProcessResult(saved_callsigns=saved_callsigns, upload_results=upload_results)

    def run_forever(self, *, poll_interval_seconds: float = 1.0, stop_event: threading.Event | None = None) -> None:
        self.start()
        try:
            while stop_event is None or not stop_event.is_set():
                self.process_once()
                time.sleep(poll_interval_seconds)
        finally:
            self.stop()

    def reconfigure(self) -> None:
        self._integration_manager.reconfigure()

    def clear_history(self) -> None:
        with self._lock:
            self._events.clear()
            self._stats = IntegrationStatsRecord()
        logger.info("Station service history cleared.")

    def events(self) -> list[dict[str, str]]:
        with self._lock:
            return [asdict(item) for item in self._events]

    def stats(self) -> dict[str, int]:
        with self._lock:
            return asdict(self._stats)

    def listener_status(self) -> tuple[bool, str]:
        return self._integration_manager.listener_status()

    def clublog_status(self) -> tuple[bool, str]:
        return self._integration_manager.clublog_status()

    def pending_upload_count(self) -> int:
        return self._integration_manager.pending_upload_count()

    def summary(self) -> dict[str, object]:
        listener_ready, listener_detail = self.listener_status()
        clublog_ready, clublog_detail = self.clublog_status()
        active_logbook = None
        if self._get_active_logbook_use_case is not None:
            try:
                item = self._get_active_logbook_use_case.execute()
                active_logbook = {"name": item.name, "qso_count": item.qso_count}
            except Exception:
                active_logbook = None
        return {
            "listener_ready": listener_ready,
            "listener_detail": listener_detail,
            "clublog_ready": clublog_ready,
            "clublog_detail": clublog_detail,
            "pending": self.pending_upload_count(),
            "stats": self.stats(),
            "active_logbook": active_logbook,
        }

    def inject_test_logged_qso(self) -> None:
        self._integration_manager.inject_test_logged_qso()
        self._append_event("PyCQLog", "UDP test queued", "Synthetic UDP QSO queued for processing")

    def enqueue_test_clublog_upload(self) -> tuple[bool, str]:
        result = self._integration_manager.enqueue_test_clublog_upload()
        queued, detail = result
        self._append_event("Club Log", "Club Log test queued" if queued else "Club Log test failed", detail)
        return result

    def retry_pending_uploads(self) -> int:
        count = self._integration_manager.retry_pending_uploads()
        self._append_event("Cloud Sync", "Retry pending uploads", str(count))
        return count

    def enqueue_uploads(self, adif_text: str, source: str) -> list[str]:
        queued = self._integration_manager.enqueue_uploads(adif_text, source)
        for service_name in queued:
            self._append_event(service_name, "Upload queued", source)
        return queued

    def enqueue_clublog_update(
        self,
        *,
        old_callsign: str,
        old_qso_date: str,
        old_time_on: str,
        old_band: str,
        new_adif_text: str,
        source: str,
    ) -> list[str]:
        queued = self._integration_manager.enqueue_clublog_update(
            old_callsign=old_callsign,
            old_qso_date=old_qso_date,
            old_time_on=old_time_on,
            old_band=old_band,
            new_adif_text=new_adif_text,
            source=source,
        )
        for item in queued:
            self._append_event("Club Log", "Upload queued", item)
        return queued

    def enqueue_clublog_delete(
        self,
        *,
        callsign: str,
        qso_date: str,
        time_on: str,
        band: str,
        source: str,
    ) -> bool:
        queued = self._integration_manager.enqueue_clublog_delete(
            callsign=callsign,
            qso_date=qso_date,
            time_on=time_on,
            band=band,
            source=source,
        )
        if queued:
            self._append_event("Club Log", "Upload queued", f"delete {callsign}")
        return queued

    def _handle_logged_adif_event(self, event: LoggedAdifEvent) -> str | None:
        logger.info("Integration ADIF received. source=%s adif_preview=%s", event.source_app, event.adif_text[:160])
        with self._lock:
            self._stats.received += 1
        self._append_event(event.source_app, "Received ADIF", event.adif_text[:140])
        records = self._adif_parser.parse(event.adif_text)
        if not records:
            logger.warning("Integration ADIF parse failed. source=%s", event.source_app)
            with self._lock:
                self._stats.failed += 1
            self._append_event(event.source_app, "ADIF parse failed", event.adif_text[:140])
            return None
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
                operator=record.get("OPERATOR") or self._operator_callsign_getter(),
                station_callsign=record.get("STATION_CALLSIGN") or self._station_callsign_getter(),
                notes=record.get("COMMENT"),
                source=self._integration_source(event.source_app),
            )
            result = self._save_qso_use_case.execute(command)
        except (ValueError, InvalidOperation, QsoValidationError) as exc:
            logger.warning("Integration QSO save failed. source=%s detail=%s", event.source_app, exc)
            with self._lock:
                self._stats.failed += 1
            self._append_event(event.source_app, "Save failed", str(exc))
            return None

        with self._lock:
            self._stats.saved += 1
        logger.info(
            "Integration QSO saved. source=%s callsign=%s band=%s mode=%s",
            event.source_app,
            result.callsign,
            result.band,
            result.mode,
        )
        self._append_event(event.source_app, "QSO saved", f"{result.callsign} {result.band} {result.mode}")
        enqueued_services = self._integration_manager.enqueue_uploads(event.adif_text, source="udp")
        for service_name in enqueued_services:
            self._append_event(service_name, "Upload queued", result.callsign)
        return result.callsign

    def _append_event(self, source: str, event_name: str, detail: str) -> None:
        logger.info("Station service event. source=%s event=%s detail=%s", source, event_name, detail)
        with self._lock:
            self._events.append(
                IntegrationEventRecord(
                    time=datetime.now().strftime("%H:%M:%S"),
                    source=source,
                    event=event_name,
                    detail=detail,
                )
            )
            self._events = self._events[-200:]

    def _parse_integration_time(self, value: str) -> datetime.time:
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


def station_service_summary_json(service: StationService) -> bytes:
    return json.dumps(
        {
            "summary": service.summary(),
            "events": service.events(),
        },
        ensure_ascii=True,
    ).encode("utf-8")
