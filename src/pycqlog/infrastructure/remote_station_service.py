from __future__ import annotations

from dataclasses import dataclass

from pycqlog.infrastructure.remote_client import RemoteApiClient


@dataclass(slots=True)
class RemoteServiceProcessResult:
    saved_callsigns: list[str]
    upload_results: list[tuple[str, bool, str]]


class RemoteStationService:
    def __init__(self, host: str, port: int, auth_code: str = "") -> None:
        self._client = RemoteApiClient(host, port, auth_code)
        self._summary: dict[str, object] = {
            "listener_ready": False,
            "listener_detail": "",
            "clublog_ready": False,
            "clublog_detail": "",
            "pending": 0,
            "stats": {"received": 0, "saved": 0, "uploaded": 0, "failed": 0},
            "active_logbook": None,
        }
        self._events: list[dict[str, str]] = []
        self._last_event_count = 0

    def start(self) -> None:
        self.process_once()

    def stop(self) -> None:
        return

    def reconfigure(self) -> None:
        self.process_once()

    def process_once(self) -> RemoteServiceProcessResult:
        payload = self._client.get("/summary")
        self._summary = payload.get("summary", self._summary)
        self._events = payload.get("events", self._events)
        changed = len(self._events) != self._last_event_count
        self._last_event_count = len(self._events)
        return RemoteServiceProcessResult(saved_callsigns=["*"] if changed else [], upload_results=[])

    def clear_history(self) -> None:
        self._client.post("/actions/clear-history")
        self.process_once()

    def events(self) -> list[dict[str, str]]:
        return list(self._events)

    def stats(self) -> dict[str, int]:
        return dict(self._summary.get("stats", {}))

    def listener_status(self) -> tuple[bool, str]:
        return bool(self._summary.get("listener_ready")), str(self._summary.get("listener_detail") or "")

    def clublog_status(self) -> tuple[bool, str]:
        return bool(self._summary.get("clublog_ready")), str(self._summary.get("clublog_detail") or "")

    def pending_upload_count(self) -> int:
        return int(self._summary.get("pending") or 0)

    def inject_test_logged_qso(self) -> None:
        self._client.post("/actions/test-udp")
        self.process_once()

    def enqueue_test_clublog_upload(self) -> tuple[bool, str]:
        payload = self._client.post("/actions/test-clublog")
        self.process_once()
        return bool(payload.get("queued")), str(payload.get("detail") or "")

    def retry_pending_uploads(self) -> int:
        payload = self._client.post("/actions/retry-pending")
        self.process_once()
        return int(payload.get("count") or 0)

    def enqueue_uploads(self, adif_text: str, source: str) -> list[str]:
        payload = self._client.post("/actions/enqueue-upload", {"adif_text": adif_text, "source": source})
        self.process_once()
        return [str(item) for item in payload.get("services", [])]

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
        payload = self._client.post(
            "/actions/enqueue-clublog-update",
            {
                "old_callsign": old_callsign,
                "old_qso_date": old_qso_date,
                "old_time_on": old_time_on,
                "old_band": old_band,
                "new_adif_text": new_adif_text,
                "source": source,
            },
        )
        self.process_once()
        return [str(item) for item in payload.get("services", [])]

    def enqueue_clublog_delete(
        self,
        *,
        callsign: str,
        qso_date: str,
        time_on: str,
        band: str,
        source: str,
    ) -> bool:
        payload = self._client.post(
            "/actions/enqueue-clublog-delete",
            {
                "callsign": callsign,
                "qso_date": qso_date,
                "time_on": time_on,
                "band": band,
                "source": source,
            },
        )
        self.process_once()
        return bool(payload.get("queued"))
