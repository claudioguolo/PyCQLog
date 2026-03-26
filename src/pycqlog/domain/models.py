from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal


@dataclass(slots=True)
class StationProfileDraft:
    name: str
    profile_type: str = "both"
    callsign: str = ""
    qth: str = ""
    locator: str = ""
    power: str = ""
    antenna: str = ""
    notes: str = ""


@dataclass(slots=True)
class StationProfile:
    id: int
    name: str
    profile_type: str = "both"
    callsign: str = ""
    qth: str = ""
    locator: str = ""
    power: str = ""
    antenna: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class LogbookDraft:
    name: str
    description: str = ""
    operator_profile_id: int | None = None
    station_profile_id: int | None = None


@dataclass(slots=True)
class Logbook:
    id: int
    name: str
    description: str = ""
    operator_profile_id: int | None = None
    station_profile_id: int | None = None
    operator_callsign: str = ""
    station_callsign: str = ""
    qso_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class QsoDraft:
    callsign: str
    qso_date: date
    time_on: time
    freq: Decimal
    mode: str
    rst_sent: str = ""
    rst_recv: str = ""
    operator: str = ""
    station_callsign: str = ""
    notes: str = ""
    source: str = "manual"
    band: str = ""
    logbook_id: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Qso:
    id: int
    callsign: str
    qso_date: date
    time_on: time
    freq: Decimal
    mode: str
    band: str
    logbook_id: int
    rst_sent: str = ""
    rst_recv: str = ""
    operator: str = ""
    station_callsign: str = ""
    notes: str = ""
    source: str = "manual"
    created_at: datetime = field(default_factory=datetime.utcnow)
