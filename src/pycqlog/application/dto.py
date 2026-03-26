from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal

@dataclass(slots=True)
class CallbookData:
    callsign: str
    name: str = ""
    qth: str = ""
    locator: str = ""
    country: str = ""
    dxcc: int | None = None
@dataclass(slots=True)
class SaveQsoCommand:
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
    qso_id: int | None = None


@dataclass(slots=True)
class SaveQsoResult:
    qso_id: int
    callsign: str
    band: str
    mode: str
    logbook_id: int
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class QsoListItem:
    qso_id: int
    callsign: str
    qso_date: date
    time_on: time
    freq: Decimal
    band: str
    mode: str
    logbook_id: int


@dataclass(slots=True)
class QsoDetail:
    qso_id: int
    callsign: str
    qso_date: date
    time_on: time
    freq: Decimal
    mode: str
    band: str
    logbook_id: int
    rst_sent: str
    rst_recv: str
    operator: str
    station_callsign: str
    notes: str
    source: str


@dataclass(slots=True)
class CallsignHistoryEntry:
    qso_id: int
    callsign: str
    qso_date: date
    time_on: time
    freq: Decimal
    mode: str
    band: str
    logbook_id: int
    rst_sent: str
    rst_recv: str


@dataclass(slots=True)
class StationProfileListItem:
    profile_id: int
    name: str
    profile_type: str
    callsign: str
    qth: str
    locator: str
    power: str
    antenna: str
    notes: str


@dataclass(slots=True)
class LogbookListItem:
    logbook_id: int
    name: str
    description: str
    operator_profile_id: int | None
    station_profile_id: int | None
    operator_callsign: str
    station_callsign: str
    qso_count: int


@dataclass(slots=True)
class ActiveLogbookSummary:
    logbook_id: int
    name: str
    description: str
    operator_profile_id: int | None
    station_profile_id: int | None
    operator_callsign: str
    station_callsign: str
    qso_count: int


@dataclass(slots=True)
class SaveStationProfileCommand:
    name: str
    profile_type: str = "both"
    callsign: str = ""
    qth: str = ""
    locator: str = ""
    power: str = ""
    antenna: str = ""
    notes: str = ""
    profile_id: int | None = None


@dataclass(slots=True)
class SaveLogbookCommand:
    name: str
    description: str = ""
    operator_profile_id: int | None = None
    station_profile_id: int | None = None
    logbook_id: int | None = None


@dataclass(slots=True)
class AdifImportResult:
    imported_count: int
    skipped_count: int
    failed_count: int
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AdifExportFilter:
    callsign: str = ""
    date_from: date | None = None
    date_to: date | None = None
    band: str = ""
    mode: str = ""


@dataclass(slots=True)
class AdifExportResult:
    exported_count: int
    destination: str


@dataclass(slots=True)
class AdifPreviewEntry:
    record_number: int
    callsign: str
    qso_date: str
    time_on: str
    freq: str
    mode: str
    status: str
    selected: bool = False
    message: str = ""


@dataclass(slots=True)
class AdifPreviewResult:
    total_count: int
    ready_count: int
    skipped_count: int
    failed_count: int
    entries: list[AdifPreviewEntry] = field(default_factory=list)


@dataclass(slots=True)
class StatsSlice:
    label: str
    value: int


@dataclass(slots=True)
class DashboardStats:
    total_qsos: int
    unique_callsigns: int
    active_bands: int
    active_modes: int
    logbook_name: str = ""
    period_label: str = ""
    dxcc_entities: int = 0
    waz_zones: int = 0
    wpx_prefixes: int = 0
    top_callsigns: list[StatsSlice] = field(default_factory=list)
    by_band: list[StatsSlice] = field(default_factory=list)
    by_mode: list[StatsSlice] = field(default_factory=list)
    by_day: list[StatsSlice] = field(default_factory=list)
    by_month: list[StatsSlice] = field(default_factory=list)
    by_hour: list[StatsSlice] = field(default_factory=list)
