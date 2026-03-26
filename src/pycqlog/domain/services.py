from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pycqlog.domain.models import QsoDraft


class QsoValidationError(ValueError):
    pass


@dataclass(slots=True)
class ValidationResult:
    warnings: list[str]


class BandModeResolver:
    def resolve_band(self, freq: Decimal) -> str:
        mhz = float(freq)
        if 1.8 <= mhz < 2.0:
            return "160m"
        if 3.5 <= mhz < 4.0:
            return "80m"
        if 7.0 <= mhz < 7.3:
            return "40m"
        if 10.1 <= mhz < 10.15:
            return "30m"
        if 14.0 <= mhz < 14.35:
            return "20m"
        if 18.068 <= mhz < 18.168:
            return "17m"
        if 21.0 <= mhz < 21.45:
            return "15m"
        if 24.89 <= mhz < 24.99:
            return "12m"
        if 28.0 <= mhz < 29.7:
            return "10m"
        if 50.0 <= mhz < 54.0:
            return "6m"
        if 144.0 <= mhz < 148.0:
            return "2m"
        return "unknown"


class QsoNormalizer:
    def normalize(self, draft: QsoDraft) -> QsoDraft:
        return QsoDraft(
            callsign=draft.callsign.strip().upper(),
            qso_date=draft.qso_date,
            time_on=draft.time_on,
            freq=Decimal(str(draft.freq)),
            mode=draft.mode.strip().upper(),
            rst_sent=draft.rst_sent.strip(),
            rst_recv=draft.rst_recv.strip(),
            operator=draft.operator.strip().upper(),
            station_callsign=draft.station_callsign.strip().upper(),
            notes=draft.notes.strip(),
            source=draft.source.strip().lower() or "manual",
            band=draft.band,
            created_at=draft.created_at,
        )


class QsoEnrichmentService:
    def __init__(self, band_mode_resolver: BandModeResolver) -> None:
        self._band_mode_resolver = band_mode_resolver

    def enrich(self, draft: QsoDraft) -> QsoDraft:
        band = self._band_mode_resolver.resolve_band(draft.freq)
        return QsoDraft(
            callsign=draft.callsign,
            qso_date=draft.qso_date,
            time_on=draft.time_on,
            freq=draft.freq,
            mode=draft.mode,
            rst_sent=draft.rst_sent,
            rst_recv=draft.rst_recv,
            operator=draft.operator,
            station_callsign=draft.station_callsign,
            notes=draft.notes,
            source=draft.source,
            band=band,
            created_at=draft.created_at,
        )


class QsoValidationService:
    def validate(self, draft: QsoDraft) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not draft.callsign:
            errors.append("Callsign is required.")

        if draft.freq <= 0:
            errors.append("Frequency must be greater than zero.")

        if not draft.mode:
            errors.append("Mode is required.")

        if draft.band == "unknown":
            warnings.append("Frequency is outside the mapped amateur bands.")

        if errors:
            raise QsoValidationError("\n".join(errors))

        return ValidationResult(warnings=warnings)
