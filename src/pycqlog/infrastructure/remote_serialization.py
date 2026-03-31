from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pycqlog.application.dto import CallbookData, DashboardStats, StatsSlice
from pycqlog.domain.models import Logbook, LogbookDraft, Qso, QsoDraft, StationProfile, StationProfileDraft


def serialize_qso(qso: Qso) -> dict[str, object]:
    return {
        "id": qso.id,
        "callsign": qso.callsign,
        "qso_date": qso.qso_date.isoformat(),
        "time_on": qso.time_on.strftime("%H:%M:%S"),
        "freq": str(qso.freq),
        "mode": qso.mode,
        "band": qso.band,
        "logbook_id": qso.logbook_id,
        "rst_sent": qso.rst_sent,
        "rst_recv": qso.rst_recv,
        "operator": qso.operator,
        "station_callsign": qso.station_callsign,
        "notes": qso.notes,
        "source": qso.source,
        "created_at": qso.created_at.isoformat(),
    }


def deserialize_qso(payload: dict[str, object]) -> Qso:
    return Qso(
        id=int(payload["id"]),
        callsign=str(payload["callsign"]),
        qso_date=date.fromisoformat(str(payload["qso_date"])),
        time_on=_parse_time(str(payload["time_on"])),
        freq=Decimal(str(payload["freq"])),
        mode=str(payload["mode"]),
        band=str(payload["band"]),
        logbook_id=int(payload["logbook_id"]),
        rst_sent=str(payload.get("rst_sent") or ""),
        rst_recv=str(payload.get("rst_recv") or ""),
        operator=str(payload.get("operator") or ""),
        station_callsign=str(payload.get("station_callsign") or ""),
        notes=str(payload.get("notes") or ""),
        source=str(payload.get("source") or "manual"),
        created_at=_parse_datetime(str(payload.get("created_at") or datetime.utcnow().isoformat())),
    )


def serialize_qso_draft(draft: QsoDraft) -> dict[str, object]:
    return {
        "callsign": draft.callsign,
        "qso_date": draft.qso_date.isoformat(),
        "time_on": draft.time_on.strftime("%H:%M:%S"),
        "freq": str(draft.freq),
        "mode": draft.mode,
        "rst_sent": draft.rst_sent,
        "rst_recv": draft.rst_recv,
        "operator": draft.operator,
        "station_callsign": draft.station_callsign,
        "notes": draft.notes,
        "source": draft.source,
        "band": draft.band,
        "logbook_id": draft.logbook_id,
        "created_at": draft.created_at.isoformat(),
    }


def deserialize_qso_draft(payload: dict[str, object]) -> QsoDraft:
    logbook_raw = payload.get("logbook_id")
    return QsoDraft(
        callsign=str(payload["callsign"]),
        qso_date=date.fromisoformat(str(payload["qso_date"])),
        time_on=_parse_time(str(payload["time_on"])),
        freq=Decimal(str(payload["freq"])),
        mode=str(payload["mode"]),
        rst_sent=str(payload.get("rst_sent") or ""),
        rst_recv=str(payload.get("rst_recv") or ""),
        operator=str(payload.get("operator") or ""),
        station_callsign=str(payload.get("station_callsign") or ""),
        notes=str(payload.get("notes") or ""),
        source=str(payload.get("source") or "manual"),
        band=str(payload.get("band") or ""),
        logbook_id=int(logbook_raw) if logbook_raw not in (None, "") else None,
        created_at=_parse_datetime(str(payload.get("created_at") or datetime.utcnow().isoformat())),
    )


def serialize_logbook(logbook: Logbook) -> dict[str, object]:
    return {
        "id": logbook.id,
        "name": logbook.name,
        "description": logbook.description,
        "operator_profile_id": logbook.operator_profile_id,
        "station_profile_id": logbook.station_profile_id,
        "operator_callsign": logbook.operator_callsign,
        "station_callsign": logbook.station_callsign,
        "qso_count": logbook.qso_count,
        "created_at": logbook.created_at.isoformat(),
    }


def deserialize_logbook(payload: dict[str, object]) -> Logbook:
    return Logbook(
        id=int(payload["id"]),
        name=str(payload["name"]),
        description=str(payload.get("description") or ""),
        operator_profile_id=int(payload["operator_profile_id"]) if payload.get("operator_profile_id") not in (None, "") else None,
        station_profile_id=int(payload["station_profile_id"]) if payload.get("station_profile_id") not in (None, "") else None,
        operator_callsign=str(payload.get("operator_callsign") or ""),
        station_callsign=str(payload.get("station_callsign") or ""),
        qso_count=int(payload.get("qso_count") or 0),
        created_at=_parse_datetime(str(payload.get("created_at") or datetime.utcnow().isoformat())),
    )


def serialize_logbook_draft(draft: LogbookDraft) -> dict[str, object]:
    return {
        "name": draft.name,
        "description": draft.description,
        "operator_profile_id": draft.operator_profile_id,
        "station_profile_id": draft.station_profile_id,
    }


def deserialize_logbook_draft(payload: dict[str, object]) -> LogbookDraft:
    return LogbookDraft(
        name=str(payload["name"]),
        description=str(payload.get("description") or ""),
        operator_profile_id=int(payload["operator_profile_id"]) if payload.get("operator_profile_id") not in (None, "") else None,
        station_profile_id=int(payload["station_profile_id"]) if payload.get("station_profile_id") not in (None, "") else None,
    )


def serialize_station_profile(profile: StationProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "name": profile.name,
        "profile_type": profile.profile_type,
        "callsign": profile.callsign,
        "qth": profile.qth,
        "locator": profile.locator,
        "power": profile.power,
        "antenna": profile.antenna,
        "notes": profile.notes,
        "created_at": profile.created_at.isoformat(),
    }


def deserialize_station_profile(payload: dict[str, object]) -> StationProfile:
    return StationProfile(
        id=int(payload["id"]),
        name=str(payload["name"]),
        profile_type=str(payload.get("profile_type") or "both"),
        callsign=str(payload.get("callsign") or ""),
        qth=str(payload.get("qth") or ""),
        locator=str(payload.get("locator") or ""),
        power=str(payload.get("power") or ""),
        antenna=str(payload.get("antenna") or ""),
        notes=str(payload.get("notes") or ""),
        created_at=_parse_datetime(str(payload.get("created_at") or datetime.utcnow().isoformat())),
    )


def serialize_station_profile_draft(draft: StationProfileDraft) -> dict[str, object]:
    return {
        "name": draft.name,
        "profile_type": draft.profile_type,
        "callsign": draft.callsign,
        "qth": draft.qth,
        "locator": draft.locator,
        "power": draft.power,
        "antenna": draft.antenna,
        "notes": draft.notes,
    }


def deserialize_station_profile_draft(payload: dict[str, object]) -> StationProfileDraft:
    return StationProfileDraft(
        name=str(payload["name"]),
        profile_type=str(payload.get("profile_type") or "both"),
        callsign=str(payload.get("callsign") or ""),
        qth=str(payload.get("qth") or ""),
        locator=str(payload.get("locator") or ""),
        power=str(payload.get("power") or ""),
        antenna=str(payload.get("antenna") or ""),
        notes=str(payload.get("notes") or ""),
    )


def serialize_callbook(data: CallbookData | None) -> dict[str, object] | None:
    if data is None:
        return None
    return {
        "callsign": data.callsign,
        "name": data.name,
        "qth": data.qth,
        "locator": data.locator,
        "country": data.country,
        "dxcc": data.dxcc,
    }


def deserialize_callbook(payload: dict[str, object] | None) -> CallbookData | None:
    if payload is None:
        return None
    return CallbookData(
        callsign=str(payload.get("callsign") or ""),
        name=str(payload.get("name") or ""),
        qth=str(payload.get("qth") or ""),
        locator=str(payload.get("locator") or ""),
        country=str(payload.get("country") or ""),
        dxcc=int(payload["dxcc"]) if payload.get("dxcc") not in (None, "") else None,
    )


def serialize_dashboard(stats: DashboardStats) -> dict[str, object]:
    return {
        "total_qsos": stats.total_qsos,
        "unique_callsigns": stats.unique_callsigns,
        "active_bands": stats.active_bands,
        "active_modes": stats.active_modes,
        "logbook_name": stats.logbook_name,
        "period_label": stats.period_label,
        "dxcc_entities": stats.dxcc_entities,
        "waz_zones": stats.waz_zones,
        "wpx_prefixes": stats.wpx_prefixes,
        "top_callsigns": [serialize_stats_slice(item) for item in stats.top_callsigns],
        "by_band": [serialize_stats_slice(item) for item in stats.by_band],
        "by_mode": [serialize_stats_slice(item) for item in stats.by_mode],
        "by_day": [serialize_stats_slice(item) for item in stats.by_day],
        "by_month": [serialize_stats_slice(item) for item in stats.by_month],
        "by_hour": [serialize_stats_slice(item) for item in stats.by_hour],
    }


def deserialize_dashboard(payload: dict[str, object]) -> DashboardStats:
    return DashboardStats(
        total_qsos=int(payload.get("total_qsos") or 0),
        unique_callsigns=int(payload.get("unique_callsigns") or 0),
        active_bands=int(payload.get("active_bands") or 0),
        active_modes=int(payload.get("active_modes") or 0),
        logbook_name=str(payload.get("logbook_name") or ""),
        period_label=str(payload.get("period_label") or ""),
        dxcc_entities=int(payload.get("dxcc_entities") or 0),
        waz_zones=int(payload.get("waz_zones") or 0),
        wpx_prefixes=int(payload.get("wpx_prefixes") or 0),
        top_callsigns=[deserialize_stats_slice(item) for item in payload.get("top_callsigns", [])],
        by_band=[deserialize_stats_slice(item) for item in payload.get("by_band", [])],
        by_mode=[deserialize_stats_slice(item) for item in payload.get("by_mode", [])],
        by_day=[deserialize_stats_slice(item) for item in payload.get("by_day", [])],
        by_month=[deserialize_stats_slice(item) for item in payload.get("by_month", [])],
        by_hour=[deserialize_stats_slice(item) for item in payload.get("by_hour", [])],
    )


def serialize_stats_slice(item: StatsSlice) -> dict[str, object]:
    return {"label": item.label, "value": item.value}


def deserialize_stats_slice(payload: dict[str, object]) -> StatsSlice:
    return StatsSlice(label=str(payload.get("label") or ""), value=int(payload.get("value") or 0))


def _parse_time(raw: str) -> time:
    value = raw.strip()
    if len(value) == 5:
        value = f"{value}:00"
    return time.fromisoformat(value)


def _parse_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw)
