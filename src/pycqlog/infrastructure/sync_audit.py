from __future__ import annotations

import re
from typing import Any

from pycqlog.infrastructure.app_logging import get_logger, register_logger_file


_ADIF_FIELD_RE = re.compile(r"<([A-Z0-9_]+):(\d+)(?::[^>]*)?>([^<]*)", re.IGNORECASE)


def _sanitize(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("|", "/")


def _normalize_time(value: str) -> str:
    raw = value.strip()
    if not raw:
        return "-"
    if len(raw) >= 4 and raw.isdigit():
        return f"{raw[0:2]}:{raw[2:4]}"
    return raw


def parse_adif_summary(adif_text: str) -> dict[str, str]:
    summary = {
        "callsign": "-",
        "qso_date": "-",
        "time_on": "-",
        "band": "-",
        "mode": "-",
    }
    for match in _ADIF_FIELD_RE.finditer(adif_text):
        field = match.group(1).upper()
        raw_length = match.group(2)
        value = match.group(3)
        try:
            size = int(raw_length)
        except ValueError:
            continue
        trimmed = value[:size].strip()
        if field == "CALL":
            summary["callsign"] = trimmed.upper() or "-"
        elif field == "QSO_DATE":
            summary["qso_date"] = trimmed or "-"
        elif field == "TIME_ON":
            summary["time_on"] = _normalize_time(trimmed)
        elif field == "BAND":
            summary["band"] = trimmed.upper() or "-"
        elif field == "MODE":
            summary["mode"] = trimmed.upper() or "-"
    return summary


def sync_logger(destination: str):
    normalized = destination.strip().lower().replace(" ", "_")
    register_logger_file(f"pycqlog.sync.{normalized}", f"sync_{normalized}.log")
    return get_logger(f"sync.{normalized}")


def audit_sync_event(
    destination: str,
    *,
    state: str,
    job_id: str,
    action: str,
    detail: str = "",
    adif_text: str = "",
    callsign: str = "",
    qso_date: str = "",
    time_on: str = "",
    band: str = "",
    mode: str = "",
    endpoint: str = "",
    attempts: int | str = "",
) -> None:
    summary = parse_adif_summary(adif_text) if adif_text else {}
    record = {
        "state": state,
        "job_id": job_id,
        "action": action,
        "callsign": callsign or summary.get("callsign", "-"),
        "qso_date": qso_date or summary.get("qso_date", "-"),
        "time_on": time_on or summary.get("time_on", "-"),
        "band": band or summary.get("band", "-"),
        "mode": mode or summary.get("mode", "-"),
        "attempts": attempts if attempts != "" else "-",
        "endpoint": endpoint,
        "detail": detail,
    }
    line = " | ".join(f"{key}={_sanitize(value)}" for key, value in record.items())
    sync_logger(destination).info(line)
