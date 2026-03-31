from __future__ import annotations

import json
from datetime import date, time
from decimal import Decimal
from urllib import error, parse, request

from pycqlog.application.dto import CallbookData, DashboardStats
from pycqlog.application.ports import CallbookPort, LogbookRepository, QsoRepository, StationProfileRepository
from pycqlog.domain.models import Logbook, LogbookDraft, Qso, QsoDraft, StationProfile, StationProfileDraft
from pycqlog.infrastructure.app_logging import get_logger
from pycqlog.infrastructure.remote_serialization import (
    deserialize_callbook,
    deserialize_dashboard,
    deserialize_logbook,
    deserialize_logbook_draft,
    deserialize_qso,
    deserialize_qso_draft,
    deserialize_station_profile,
    deserialize_station_profile_draft,
    serialize_logbook_draft,
    serialize_qso_draft,
    serialize_station_profile_draft,
)


logger = get_logger("remote_client")


class RemoteApiError(RuntimeError):
    pass


class RemoteApiClient:
    def __init__(self, host: str, port: int, auth_code: str = "") -> None:
        self._base_url = f"http://{host}:{port}"
        self._auth_code = auth_code.strip()

    def get(self, path: str, query: dict[str, str] | None = None) -> dict[str, object]:
        url = self._base_url + path
        if query:
            url += "?" + parse.urlencode(query)
        req = request.Request(url, method="GET")
        return self._request(req)

    def post(self, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        encoded = json.dumps(payload or {}, ensure_ascii=True).encode("utf-8")
        req = request.Request(self._base_url + path, data=encoded, method="POST")
        req.add_header("Content-Type", "application/json")
        return self._request(req)

    def delete(self, path: str) -> dict[str, object]:
        req = request.Request(self._base_url + path, method="DELETE")
        return self._request(req)

    def _request(self, req: request.Request) -> dict[str, object]:
        req.add_header("User-Agent", "PyCQLog-RemoteUI/0.1.0")
        if self._auth_code:
            req.add_header("X-PyCQLog-Auth", self._auth_code)
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8", errors="ignore")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise RemoteApiError(f"HTTP {exc.code}: {body[:200] or exc.reason}") from exc
        except error.URLError as exc:
            raise RemoteApiError(str(exc)) from exc
        if not body.strip():
            return {}
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RemoteApiError("Invalid JSON from remote service") from exc
        if not isinstance(payload, dict):
            raise RemoteApiError("Invalid payload from remote service")
        return payload


class RemoteQsoRepository(QsoRepository):
    def __init__(self, client: RemoteApiClient) -> None:
        self._client = client

    def save(self, draft: QsoDraft) -> Qso:
        payload = self._client.post("/api/qsos/save", {"draft": serialize_qso_draft(draft)})
        return deserialize_qso(payload["qso"])

    def list_all(self) -> list[Qso]:
        payload = self._client.get("/api/qsos/all")
        return [deserialize_qso(item) for item in payload.get("qsos", [])]

    def list_recent(self, limit: int = 50) -> list[Qso]:
        payload = self._client.get("/api/qsos/recent", {"limit": str(limit)})
        return [deserialize_qso(item) for item in payload.get("qsos", [])]

    def get_by_id(self, qso_id: int) -> Qso | None:
        payload = self._client.get(f"/api/qsos/{qso_id}")
        qso_payload = payload.get("qso")
        if qso_payload is None:
            return None
        return deserialize_qso(qso_payload)

    def update(self, qso_id: int, draft: QsoDraft) -> Qso | None:
        payload = self._client.post(f"/api/qsos/{qso_id}/update", {"draft": serialize_qso_draft(draft)})
        qso_payload = payload.get("qso")
        if qso_payload is None:
            return None
        return deserialize_qso(qso_payload)

    def delete(self, qso_id: int) -> bool:
        payload = self._client.delete(f"/api/qsos/{qso_id}")
        return bool(payload.get("deleted"))

    def search(self, callsign: str, limit: int = 50) -> list[Qso]:
        payload = self._client.get("/api/qsos/search", {"callsign": callsign, "limit": str(limit)})
        return [deserialize_qso(item) for item in payload.get("qsos", [])]

    def find_duplicate(self, draft: QsoDraft) -> Qso | None:
        payload = self._client.post("/api/qsos/find-duplicate", {"draft": serialize_qso_draft(draft)})
        qso_payload = payload.get("qso")
        if qso_payload is None:
            return None
        return deserialize_qso(qso_payload)


class RemoteLogbookRepository(LogbookRepository):
    def __init__(self, client: RemoteApiClient) -> None:
        self._client = client

    def ensure_default_logbook(self) -> Logbook:
        payload = self._client.get("/api/logbooks/active")
        return deserialize_logbook(payload["logbook"])

    def list_logbooks(self) -> list[Logbook]:
        payload = self._client.get("/api/logbooks")
        return [deserialize_logbook(item) for item in payload.get("logbooks", [])]

    def get_logbook(self, logbook_id: int) -> Logbook | None:
        payload = self._client.get(f"/api/logbooks/{logbook_id}")
        logbook_payload = payload.get("logbook")
        if logbook_payload is None:
            return None
        return deserialize_logbook(logbook_payload)

    def save_logbook(self, draft: LogbookDraft, logbook_id: int | None = None) -> Logbook:
        payload = self._client.post(
            "/api/logbooks/save",
            {"draft": serialize_logbook_draft(draft), "logbook_id": logbook_id},
        )
        return deserialize_logbook(payload["logbook"])

    def delete_logbook(self, logbook_id: int) -> bool:
        payload = self._client.delete(f"/api/logbooks/{logbook_id}")
        return bool(payload.get("deleted"))

    def get_active_logbook(self) -> Logbook:
        payload = self._client.get("/api/logbooks/active")
        return deserialize_logbook(payload["logbook"])

    def set_active_logbook(self, logbook_id: int) -> Logbook:
        payload = self._client.post(f"/api/logbooks/{logbook_id}/activate")
        return deserialize_logbook(payload["logbook"])


class RemoteStationProfileRepository(StationProfileRepository):
    def __init__(self, client: RemoteApiClient) -> None:
        self._client = client

    def list_station_profiles(self) -> list[StationProfile]:
        payload = self._client.get("/api/profiles")
        return [deserialize_station_profile(item) for item in payload.get("profiles", [])]

    def get_station_profile(self, profile_id: int) -> StationProfile | None:
        payload = self._client.get(f"/api/profiles/{profile_id}")
        profile_payload = payload.get("profile")
        if profile_payload is None:
            return None
        return deserialize_station_profile(profile_payload)

    def save_station_profile(self, draft: StationProfileDraft, profile_id: int | None = None) -> StationProfile:
        payload = self._client.post(
            "/api/profiles/save",
            {"draft": serialize_station_profile_draft(draft), "profile_id": profile_id},
        )
        return deserialize_station_profile(payload["profile"])

    def delete_station_profile(self, profile_id: int) -> bool:
        payload = self._client.delete(f"/api/profiles/{profile_id}")
        return bool(payload.get("deleted"))


class RemoteCallbookProvider(CallbookPort):
    def __init__(self, client: RemoteApiClient) -> None:
        self._client = client

    def lookup(self, callsign: str) -> CallbookData | None:
        payload = self._client.get("/api/callbook", {"callsign": callsign})
        return deserialize_callbook(payload.get("callbook"))


class RemoteDashboardLoader:
    def __init__(self, client: RemoteApiClient) -> None:
        self._client = client

    def execute(self, period_days: int | None = None) -> DashboardStats:
        query = {}
        if period_days is not None:
            query["period_days"] = str(period_days)
        payload = self._client.get("/api/dashboard", query)
        return deserialize_dashboard(payload["stats"])
