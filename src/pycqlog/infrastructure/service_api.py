from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse
from urllib.parse import urlparse

from pycqlog.infrastructure.app_logging import get_logger
from pycqlog.infrastructure.remote_serialization import (
    deserialize_logbook_draft,
    deserialize_qso_draft,
    deserialize_station_profile_draft,
    serialize_callbook,
    serialize_dashboard,
    serialize_logbook,
    serialize_qso,
    serialize_station_profile,
)
from pycqlog.infrastructure.station_service import StationService


logger = get_logger("service_api")


class ServiceApiServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        service: StationService,
        app_context,
        auth_code: str,
    ) -> None:
        super().__init__(server_address, ServiceApiRequestHandler)
        self.station_service = service
        self.app_context = app_context
        self.auth_code = auth_code.strip()


class ServiceApiRequestHandler(BaseHTTPRequestHandler):
    server: ServiceApiServer

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        query = self._query_params()
        if path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        if not self._require_auth():
            return
        if path == "/summary":
            self._send_json(
                HTTPStatus.OK,
                {
                    "summary": self.server.station_service.summary(),
                    "events": self.server.station_service.events(),
                },
            )
            return
        if path == "/events":
            self._send_json(HTTPStatus.OK, {"events": self.server.station_service.events()})
            return
        if path == "/api/qsos/all":
            items = self.server.app_context.list_recent_qsos._repository.list_all()
            self._send_json(HTTPStatus.OK, {"qsos": [serialize_qso(item) for item in items]})
            return
        if path == "/api/qsos/recent":
            limit = int(query.get("limit", "50") or "50")
            items = self.server.app_context.list_recent_qsos.execute(limit=limit)
            self._send_json(HTTPStatus.OK, {"qsos": [serialize_qso(item) for item in self.server.app_context.list_recent_qsos._repository.list_recent(limit=limit)]})
            return
        if path == "/api/qsos/search":
            limit = int(query.get("limit", "50") or "50")
            callsign = query.get("callsign", "")
            items = self.server.app_context.search_qsos.execute(callsign, limit=limit)
            self._send_json(
                HTTPStatus.OK,
                {
                    "qsos": [
                        serialize_qso(self.server.app_context.search_qsos._repository.get_by_id(item.qso_id))
                        for item in items
                        if self.server.app_context.search_qsos._repository.get_by_id(item.qso_id) is not None
                    ]
                },
            )
            return
        if path.startswith("/api/qsos/") and path.count("/") == 3:
            qso_id = int(path.rsplit("/", 1)[-1])
            item = self.server.app_context.get_qso_detail.execute(qso_id)
            if item is None:
                self._send_json(HTTPStatus.OK, {"qso": None})
                return
            repository_item = self.server.app_context.get_qso_detail._repository.get_by_id(qso_id)
            self._send_json(HTTPStatus.OK, {"qso": serialize_qso(repository_item) if repository_item else None})
            return
        if path.startswith("/api/history/"):
            callsign = path.rsplit("/", 1)[-1]
            limit = int(query.get("limit", "10") or "10")
            items = self.server.app_context.get_callsign_history.execute(callsign, limit=limit)
            self._send_json(
                HTTPStatus.OK,
                {
                    "qsos": [
                        serialize_qso(self.server.app_context.get_qso_detail._repository.get_by_id(item.qso_id))
                        for item in items
                        if self.server.app_context.get_qso_detail._repository.get_by_id(item.qso_id) is not None
                    ]
                },
            )
            return
        if path == "/api/dashboard":
            period_raw = query.get("period_days", "").strip()
            period_days = int(period_raw) if period_raw else None
            stats = self.server.app_context.get_dashboard_stats.execute(period_days=period_days)
            self._send_json(HTTPStatus.OK, {"stats": serialize_dashboard(stats)})
            return
        if path == "/api/logbooks":
            items = self.server.app_context.list_logbooks.execute()
            self._send_json(
                HTTPStatus.OK,
                {"logbooks": [serialize_logbook(self.server.app_context.list_logbooks._repository.get_logbook(item.logbook_id)) for item in items]},
            )
            return
        if path == "/api/logbooks/active":
            item = self.server.app_context.get_active_logbook.execute()
            logbook = self.server.app_context.get_active_logbook._repository.get_logbook(item.logbook_id)
            self._send_json(HTTPStatus.OK, {"logbook": serialize_logbook(logbook) if logbook else None})
            return
        if path.startswith("/api/logbooks/") and path.count("/") == 3:
            logbook_id = int(path.rsplit("/", 1)[-1])
            logbook = self.server.app_context.list_logbooks._repository.get_logbook(logbook_id)
            self._send_json(HTTPStatus.OK, {"logbook": serialize_logbook(logbook) if logbook else None})
            return
        if path == "/api/profiles":
            items = self.server.app_context.list_station_profiles.execute()
            self._send_json(
                HTTPStatus.OK,
                {
                    "profiles": [
                        serialize_station_profile(self.server.app_context.list_station_profiles._repository.get_station_profile(item.profile_id))
                        for item in items
                    ]
                },
            )
            return
        if path.startswith("/api/profiles/") and path.count("/") == 3:
            profile_id = int(path.rsplit("/", 1)[-1])
            profile = self.server.app_context.list_station_profiles._repository.get_station_profile(profile_id)
            self._send_json(HTTPStatus.OK, {"profile": serialize_station_profile(profile) if profile else None})
            return
        if path == "/api/callbook":
            callsign = query.get("callsign", "")
            item = self.server.app_context.fetch_callbook_info.execute(callsign)
            self._send_json(HTTPStatus.OK, {"callbook": serialize_callbook(item)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._require_auth():
            return
        data = self._read_json()
        if path == "/actions/test-udp":
            self.server.station_service.inject_test_logged_qso()
            self._send_json(HTTPStatus.OK, {"queued": True})
            return
        if path == "/actions/test-clublog":
            queued, detail = self.server.station_service.enqueue_test_clublog_upload()
            self._send_json(HTTPStatus.OK, {"queued": queued, "detail": detail})
            return
        if path == "/actions/retry-pending":
            count = self.server.station_service.retry_pending_uploads()
            self._send_json(HTTPStatus.OK, {"count": count})
            return
        if path == "/actions/clear-history":
            self.server.station_service.clear_history()
            self._send_json(HTTPStatus.OK, {"cleared": True})
            return
        if path == "/actions/enqueue-upload":
            queued = self.server.station_service.enqueue_uploads(
                adif_text=str(data.get("adif_text") or ""),
                source=str(data.get("source") or "manual"),
            )
            self._send_json(HTTPStatus.OK, {"services": queued})
            return
        if path == "/actions/enqueue-clublog-delete":
            queued = self.server.station_service.enqueue_clublog_delete(
                callsign=str(data.get("callsign") or ""),
                qso_date=str(data.get("qso_date") or ""),
                time_on=str(data.get("time_on") or ""),
                band=str(data.get("band") or ""),
                source=str(data.get("source") or "manual"),
            )
            self._send_json(HTTPStatus.OK, {"queued": queued})
            return
        if path == "/actions/enqueue-clublog-update":
            queued = self.server.station_service.enqueue_clublog_update(
                old_callsign=str(data.get("old_callsign") or ""),
                old_qso_date=str(data.get("old_qso_date") or ""),
                old_time_on=str(data.get("old_time_on") or ""),
                old_band=str(data.get("old_band") or ""),
                new_adif_text=str(data.get("new_adif_text") or ""),
                source=str(data.get("source") or "manual"),
            )
            self._send_json(HTTPStatus.OK, {"services": queued})
            return
        if path == "/api/qsos/save":
            draft = deserialize_qso_draft(data.get("draft") or {})
            qso_id = data.get("qso_id")
            if qso_id not in (None, ""):
                item = self.server.app_context.list_recent_qsos._repository.update(int(qso_id), draft)
            else:
                item = self.server.app_context.list_recent_qsos._repository.save(draft)
            self._send_json(HTTPStatus.OK, {"qso": serialize_qso(item) if item else None})
            return
        if path.startswith("/api/qsos/") and path.endswith("/update"):
            qso_id = int(path.split("/")[-2])
            draft = deserialize_qso_draft(data.get("draft") or {})
            item = self.server.app_context.list_recent_qsos._repository.update(qso_id, draft)
            self._send_json(HTTPStatus.OK, {"qso": serialize_qso(item) if item else None})
            return
        if path == "/api/qsos/find-duplicate":
            draft = deserialize_qso_draft(data.get("draft") or {})
            item = self.server.app_context.list_recent_qsos._repository.find_duplicate(draft)
            self._send_json(HTTPStatus.OK, {"qso": serialize_qso(item) if item else None})
            return
        if path == "/api/logbooks/save":
            draft = deserialize_logbook_draft(data.get("draft") or {})
            item = self.server.app_context.list_logbooks._repository.save_logbook(draft, data.get("logbook_id"))
            self._send_json(HTTPStatus.OK, {"logbook": serialize_logbook(item)})
            return
        if path.startswith("/api/logbooks/") and path.endswith("/activate"):
            logbook_id = int(path.split("/")[-2])
            item = self.server.app_context.set_active_logbook.execute(logbook_id)
            logbook = self.server.app_context.list_logbooks._repository.get_logbook(item.logbook_id)
            self._send_json(HTTPStatus.OK, {"logbook": serialize_logbook(logbook) if logbook else None})
            return
        if path == "/api/profiles/save":
            draft = deserialize_station_profile_draft(data.get("draft") or {})
            item = self.server.app_context.list_station_profiles._repository.save_station_profile(draft, data.get("profile_id"))
            self._send_json(HTTPStatus.OK, {"profile": serialize_station_profile(item)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._require_auth():
            return
        if path.startswith("/api/qsos/") and path.count("/") == 3:
            qso_id = int(path.rsplit("/", 1)[-1])
            deleted = self.server.app_context.delete_qso.execute(qso_id)
            self._send_json(HTTPStatus.OK, {"deleted": deleted})
            return
        if path.startswith("/api/logbooks/") and path.count("/") == 3:
            logbook_id = int(path.rsplit("/", 1)[-1])
            deleted = self.server.app_context.delete_logbook.execute(logbook_id)
            self._send_json(HTTPStatus.OK, {"deleted": deleted})
            return
        if path.startswith("/api/profiles/") and path.count("/") == 3:
            profile_id = int(path.rsplit("/", 1)[-1])
            deleted = self.server.app_context.delete_station_profile.execute(profile_id)
            self._send_json(HTTPStatus.OK, {"deleted": deleted})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def log_message(self, format: str, *args) -> None:
        logger.info("Service API request. client=%s detail=%s", self.client_address[0], format % args)

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _query_params(self) -> dict[str, str]:
        parsed = urlparse(self.path)
        params = parse.parse_qs(parsed.query)
        return {key: values[-1] for key, values in params.items() if values}

    def _require_auth(self) -> bool:
        expected = self.server.auth_code.strip()
        if not expected:
            return True
        provided = self.headers.get("X-PyCQLog-Auth", "").strip()
        if provided == expected:
            return True
        logger.warning(
            "Service API unauthorized request. client=%s path=%s",
            self.client_address[0],
            self.path,
        )
        self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
        return False
