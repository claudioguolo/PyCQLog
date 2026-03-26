from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pycqlog.application.dto import (
    ActiveLogbookSummary,
    AdifExportFilter,
    AdifExportResult,
    AdifImportResult,
    AdifPreviewEntry,
    AdifPreviewResult,
    CallbookData,
    CallsignHistoryEntry,
    DashboardStats,
    LogbookListItem,
    QsoDetail,
    QsoListItem,
    SaveLogbookCommand,
    SaveQsoCommand,
    SaveQsoResult,
    SaveStationProfileCommand,
    StationProfileListItem,
    StatsSlice,
)
from pycqlog.application.ports import CallbookPort, LogbookRepository, QsoRepository, StationProfileRepository
from pycqlog.domain.awards import resolve_awards
from pycqlog.domain.models import LogbookDraft, QsoDraft, StationProfileDraft
from pycqlog.domain.services import (
    BandModeResolver,
    QsoEnrichmentService,
    QsoNormalizer,
    QsoValidationService,
)
from pycqlog.infrastructure.adif import AdifParser
from pycqlog.infrastructure.adif_export import AdifExporter


class SaveQsoUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository
        self._normalizer = QsoNormalizer()
        self._enrichment_service = QsoEnrichmentService(BandModeResolver())
        self._validator = QsoValidationService()

    def execute(self, command: SaveQsoCommand) -> SaveQsoResult:
        draft = QsoDraft(
            callsign=command.callsign,
            qso_date=command.qso_date,
            time_on=command.time_on,
            freq=command.freq,
            mode=command.mode,
            rst_sent=command.rst_sent,
            rst_recv=command.rst_recv,
            operator=command.operator,
            station_callsign=command.station_callsign,
            notes=command.notes,
            source=command.source,
        )
        normalized = self._normalizer.normalize(draft)
        enriched = self._enrichment_service.enrich(normalized)
        validation = self._validator.validate(enriched)
        if command.qso_id is None:
            qso = self._repository.save(enriched)
        else:
            qso = self._repository.update(command.qso_id, enriched)
            if qso is None:
                raise ValueError(f"QSO {command.qso_id} not found.")

        return SaveQsoResult(
            qso_id=qso.id,
            callsign=qso.callsign,
            band=qso.band,
            mode=qso.mode,
            logbook_id=qso.logbook_id,
            warnings=validation.warnings,
        )


class ListRecentQsosUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository

    def execute(self, limit: int = 50) -> list[QsoListItem]:
        return [self._to_qso_list_item(item) for item in self._repository.list_recent(limit=limit)]

    def _to_qso_list_item(self, item) -> QsoListItem:
        return QsoListItem(
            qso_id=item.id,
            callsign=item.callsign,
            qso_date=item.qso_date,
            time_on=item.time_on,
            freq=item.freq,
            band=item.band,
            mode=item.mode,
            logbook_id=item.logbook_id,
        )


class SearchQsosUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository

    def execute(self, callsign: str, limit: int = 50) -> list[QsoListItem]:
        return [
            QsoListItem(
                qso_id=item.id,
                callsign=item.callsign,
                qso_date=item.qso_date,
                time_on=item.time_on,
                freq=item.freq,
                band=item.band,
                mode=item.mode,
                logbook_id=item.logbook_id,
            )
            for item in self._repository.search(callsign=callsign, limit=limit)
        ]


class GetQsoDetailUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository

    def execute(self, qso_id: int) -> QsoDetail | None:
        qso = self._repository.get_by_id(qso_id)
        if qso is None:
            return None

        return QsoDetail(
            qso_id=qso.id,
            callsign=qso.callsign,
            qso_date=qso.qso_date,
            time_on=qso.time_on,
            freq=qso.freq,
            mode=qso.mode,
            band=qso.band,
            logbook_id=qso.logbook_id,
            rst_sent=qso.rst_sent,
            rst_recv=qso.rst_recv,
            operator=qso.operator,
            station_callsign=qso.station_callsign,
            notes=qso.notes,
            source=qso.source,
        )


class DeleteQsoUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository

    def execute(self, qso_id: int) -> bool:
        return self._repository.delete(qso_id)


class GetCallsignHistoryUseCase:
    def __init__(self, repository: QsoRepository) -> None:
        self._repository = repository

    def execute(self, callsign: str, limit: int = 10) -> list[CallsignHistoryEntry]:
        items = self._repository.search(callsign=callsign, limit=limit)
        exact = [item for item in items if item.callsign == callsign.strip().upper()]
        return [
            CallsignHistoryEntry(
                qso_id=item.id,
                callsign=item.callsign,
                qso_date=item.qso_date,
                time_on=item.time_on,
                freq=item.freq,
                mode=item.mode,
                band=item.band,
                logbook_id=item.logbook_id,
                rst_sent=item.rst_sent,
                rst_recv=item.rst_recv,
            )
            for item in exact
        ]


class ListLogbooksUseCase:
    def __init__(self, repository: LogbookRepository) -> None:
        self._repository = repository

    def execute(self) -> list[LogbookListItem]:
        return [
            LogbookListItem(
                logbook_id=item.id,
                name=item.name,
                description=item.description,
                operator_profile_id=item.operator_profile_id,
                station_profile_id=item.station_profile_id,
                operator_callsign=item.operator_callsign,
                station_callsign=item.station_callsign,
                qso_count=item.qso_count,
            )
            for item in self._repository.list_logbooks()
        ]


class GetActiveLogbookUseCase:
    def __init__(self, repository: LogbookRepository) -> None:
        self._repository = repository

    def execute(self) -> ActiveLogbookSummary:
        item = self._repository.get_active_logbook()
        return ActiveLogbookSummary(
            logbook_id=item.id,
            name=item.name,
            description=item.description,
            operator_profile_id=item.operator_profile_id,
            station_profile_id=item.station_profile_id,
            operator_callsign=item.operator_callsign,
            station_callsign=item.station_callsign,
            qso_count=item.qso_count,
        )


class SaveLogbookUseCase:
    def __init__(self, repository: LogbookRepository) -> None:
        self._repository = repository

    def execute(self, command: SaveLogbookCommand) -> LogbookListItem:
        item = self._repository.save_logbook(
            LogbookDraft(
                name=command.name,
                description=command.description,
                operator_profile_id=command.operator_profile_id,
                station_profile_id=command.station_profile_id,
            ),
            logbook_id=command.logbook_id,
        )
        return LogbookListItem(
            logbook_id=item.id,
            name=item.name,
            description=item.description,
            operator_profile_id=item.operator_profile_id,
            station_profile_id=item.station_profile_id,
            operator_callsign=item.operator_callsign,
            station_callsign=item.station_callsign,
            qso_count=item.qso_count,
        )


class DeleteLogbookUseCase:
    def __init__(self, repository: LogbookRepository) -> None:
        self._repository = repository

    def execute(self, logbook_id: int) -> bool:
        return self._repository.delete_logbook(logbook_id)


class SetActiveLogbookUseCase:
    def __init__(self, repository: LogbookRepository) -> None:
        self._repository = repository

    def execute(self, logbook_id: int) -> ActiveLogbookSummary:
        item = self._repository.set_active_logbook(logbook_id)
        return ActiveLogbookSummary(
            logbook_id=item.id,
            name=item.name,
            description=item.description,
            operator_profile_id=item.operator_profile_id,
            station_profile_id=item.station_profile_id,
            operator_callsign=item.operator_callsign,
            station_callsign=item.station_callsign,
            qso_count=item.qso_count,
        )


class ListStationProfilesUseCase:
    def __init__(self, repository: StationProfileRepository) -> None:
        self._repository = repository

    def execute(self) -> list[StationProfileListItem]:
        return [
            StationProfileListItem(
                profile_id=item.id,
                name=item.name,
                profile_type=item.profile_type,
                callsign=item.callsign,
                qth=item.qth,
                locator=item.locator,
                power=item.power,
                antenna=item.antenna,
                notes=item.notes,
            )
            for item in self._repository.list_station_profiles()
        ]


class SaveStationProfileUseCase:
    def __init__(self, repository: StationProfileRepository) -> None:
        self._repository = repository

    def execute(self, command: SaveStationProfileCommand) -> StationProfileListItem:
        item = self._repository.save_station_profile(
            StationProfileDraft(
                name=command.name,
                profile_type=command.profile_type,
                callsign=command.callsign,
                qth=command.qth,
                locator=command.locator,
                power=command.power,
                antenna=command.antenna,
                notes=command.notes,
            ),
            profile_id=command.profile_id,
        )
        return StationProfileListItem(
            profile_id=item.id,
            name=item.name,
            profile_type=item.profile_type,
            callsign=item.callsign,
            qth=item.qth,
            locator=item.locator,
            power=item.power,
            antenna=item.antenna,
            notes=item.notes,
        )


class DeleteStationProfileUseCase:
    def __init__(self, repository: StationProfileRepository) -> None:
        self._repository = repository

    def execute(self, profile_id: int) -> bool:
        return self._repository.delete_station_profile(profile_id)


class GetDashboardStatsUseCase:
    def __init__(self, repository: QsoRepository, logbook_repository: LogbookRepository) -> None:
        self._repository = repository
        self._logbook_repository = logbook_repository

    def execute(self, period_days: int | None = None) -> DashboardStats:
        qsos = self._repository.list_all()
        if period_days is not None and qsos:
            max_date = max(qso.qso_date for qso in qsos)
            date_from = max_date.fromordinal(max_date.toordinal() - period_days + 1)
            qsos = [qso for qso in qsos if qso.qso_date >= date_from]
        callsign_counter = Counter(qso.callsign for qso in qsos)
        band_counter = Counter(qso.band for qso in qsos if qso.band)
        mode_counter = Counter(qso.mode for qso in qsos if qso.mode)
        day_counter = Counter(qso.qso_date.isoformat() for qso in qsos)
        month_counter = Counter(qso.qso_date.strftime("%Y-%m") for qso in qsos)
        hour_counter = Counter(qso.time_on.strftime("%H:00") for qso in qsos)

        award_infos = [resolve_awards(qso.callsign) for qso in qsos]
        dxcc_entities = {info.entity for info in award_infos if info.entity}
        waz_zones = {info.cq_zone for info in award_infos if info.cq_zone is not None}
        wpx_prefixes = {info.wpx_prefix for info in award_infos if info.wpx_prefix}
        active_logbook = self._logbook_repository.get_active_logbook()

        return DashboardStats(
            total_qsos=len(qsos),
            unique_callsigns=len(callsign_counter),
            active_bands=len(band_counter),
            active_modes=len(mode_counter),
            logbook_name=active_logbook.name,
            period_label="all" if period_days is None else f"{period_days}d",
            dxcc_entities=len(dxcc_entities),
            waz_zones=len(waz_zones),
            wpx_prefixes=len(wpx_prefixes),
            top_callsigns=self._to_slices(callsign_counter, limit=8),
            by_band=self._to_slices(band_counter, limit=8),
            by_mode=self._to_slices(mode_counter, limit=8),
            by_day=self._to_slices(day_counter, limit=10, sort_by_label=True),
            by_month=self._to_slices(month_counter, limit=12, sort_by_label=True),
            by_hour=self._to_slices(hour_counter, limit=24, sort_by_label=True),
        )

    def _to_slices(
        self,
        counter: Counter[str],
        limit: int,
        sort_by_label: bool = False,
    ) -> list[StatsSlice]:
        items = list(counter.items())
        if sort_by_label:
            items.sort(key=lambda item: item[0])
        else:
            items.sort(key=lambda item: (-item[1], item[0]))
        return [StatsSlice(label=label, value=value) for label, value in items[:limit]]


class ImportAdifUseCase:
    def __init__(
        self,
        save_qso: SaveQsoUseCase,
        parser: AdifParser,
        repository: QsoRepository,
    ) -> None:
        self._save_qso = save_qso
        self._parser = parser
        self._repository = repository
        self._last_records = []

    def execute(
        self,
        path: Path,
        selected_record_numbers: set[int] | None = None,
        overrides: dict[int, dict[str, str]] | None = None,
    ) -> AdifImportResult:
        preview = self.preview(path)
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        errors: list[str] = []
        for entry in preview.entries:
            if selected_record_numbers is not None and entry.record_number not in selected_record_numbers:
                if entry.status != "skipped":
                    skipped_count += 1
                continue
            if entry.status == "skipped":
                skipped_count += 1
                continue
            try:
                command = self._build_command(
                    entry.record_number,
                    self._last_records[entry.record_number - 1],
                    overrides.get(entry.record_number) if overrides else None,
                )
                if self._is_duplicate(command):
                    skipped_count += 1
                    continue
                self._save_qso.execute(command)
                imported_count += 1
            except (ValueError, InvalidOperation) as exc:
                failed_count += 1
                errors.append(f"Record {entry.record_number}: {exc}")

        return AdifImportResult(
            imported_count=imported_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            errors=errors[:20],
        )

    def preview(self, path: Path) -> AdifPreviewResult:
        content = path.read_text(encoding="utf-8", errors="ignore")
        records = self._parser.parse(content)
        self._last_records = records

        entries: list[AdifPreviewEntry] = []
        ready_count = 0
        skipped_count = 0
        failed_count = 0
        seen_keys: set[tuple[str, str, str, str, str]] = set()

        for index, record in enumerate(records, start=1):
            try:
                command = self._build_command(index, record)
                duplicate = self._is_duplicate(command)
                batch_key = self._duplicate_key(command)
                if batch_key in seen_keys:
                    duplicate = True
                else:
                    seen_keys.add(batch_key)
                status = "skipped" if duplicate else "ready"
                if duplicate:
                    skipped_count += 1
                else:
                    ready_count += 1
                entries.append(
                    AdifPreviewEntry(
                        record_number=index,
                        callsign=command.callsign.strip().upper(),
                        qso_date=command.qso_date.isoformat(),
                        time_on=command.time_on.strftime("%H:%M:%S"),
                        freq=str(command.freq),
                        mode=command.mode.strip().upper(),
                        status=status,
                        selected=not duplicate,
                        message="Duplicate QSO." if duplicate else "",
                    )
                )
            except (ValueError, InvalidOperation) as exc:
                failed_count += 1
                entries.append(
                    AdifPreviewEntry(
                        record_number=index,
                        callsign=record.get("CALL"),
                        qso_date=record.get("QSO_DATE"),
                        time_on=record.get("TIME_ON"),
                        freq=record.get("FREQ"),
                        mode=self._resolve_mode(record),
                        status="failed",
                        selected=False,
                        message=str(exc),
                    )
                )

        return AdifPreviewResult(
            total_count=len(records),
            ready_count=ready_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            entries=entries,
        )

    def _build_command(self, index: int, record, override: dict[str, str] | None = None) -> SaveQsoCommand:
        override = override or {}
        return SaveQsoCommand(
            callsign=override.get("callsign") or record.get("CALL"),
            qso_date=self._parse_date((override.get("qso_date") or record.get("QSO_DATE")).replace("-", "")),
            time_on=self._parse_time((override.get("time_on") or record.get("TIME_ON")).replace(":", "")),
            freq=Decimal(override.get("freq") or record.get("FREQ")),
            mode=override.get("mode") or self._resolve_mode(record),
            rst_sent=record.get("RST_SENT"),
            rst_recv=record.get("RST_RCVD"),
            operator=record.get("OPERATOR"),
            station_callsign=record.get("STATION_CALLSIGN"),
            notes=self._build_notes(record),
            source="adif_import",
        )

    def _parse_date(self, value: str) -> date:
        if len(value) != 8:
            raise ValueError("Invalid QSO_DATE.")
        return datetime.strptime(value, "%Y%m%d").date()

    def _parse_time(self, value: str) -> time:
        if len(value) < 4:
            raise ValueError("Invalid TIME_ON.")
        normalized = value[:6].ljust(6, "0")
        return datetime.strptime(normalized, "%H%M%S").time()

    def _resolve_mode(self, record) -> str:
        submode = record.get("SUBMODE")
        mode = record.get("MODE")
        return submode or mode

    def _build_notes(self, record) -> str:
        parts: list[str] = []
        comment = record.get("COMMENT")
        if comment:
            parts.append(comment)
        name = record.get("NAME")
        if name:
            parts.append(f"Name: {name}")
        qth = record.get("QTH")
        if qth:
            parts.append(f"QTH: {qth}")
        return " | ".join(parts)

    def _is_duplicate(self, command: SaveQsoCommand) -> bool:
        draft = QsoDraft(
            callsign=command.callsign.strip().upper(),
            qso_date=command.qso_date,
            time_on=command.time_on,
            freq=Decimal(str(command.freq)),
            mode=command.mode.strip().upper(),
            rst_sent=command.rst_sent,
            rst_recv=command.rst_recv,
            operator=command.operator,
            station_callsign=command.station_callsign,
            notes=command.notes,
            source=command.source,
        )
        return self._repository.find_duplicate(draft) is not None

    def _duplicate_key(self, command: SaveQsoCommand) -> tuple[str, str, str, str, str]:
        return (
            command.callsign.strip().upper(),
            command.qso_date.isoformat(),
            command.time_on.isoformat(),
            str(Decimal(str(command.freq))),
            command.mode.strip().upper(),
        )


class ExportAdifUseCase:
    def __init__(self, repository: QsoRepository, exporter: AdifExporter) -> None:
        self._repository = repository
        self._exporter = exporter

    def execute(self, destination: Path, filters: AdifExportFilter | None = None) -> AdifExportResult:
        qsos = self._repository.list_all()
        if filters is not None:
            qsos = self._apply_filters(qsos, filters)
        exported_count = self._exporter.export(qsos, destination)
        return AdifExportResult(
            exported_count=exported_count,
            destination=str(destination),
        )

    def _apply_filters(self, qsos, filters: AdifExportFilter):
        callsign = filters.callsign.strip().upper()
        band = filters.band.strip().lower()
        mode = filters.mode.strip().upper()
        filtered = []
        for qso in qsos:
            if callsign and callsign not in qso.callsign.upper():
                continue
            if filters.date_from is not None and qso.qso_date < filters.date_from:
                continue
            if filters.date_to is not None and qso.qso_date > filters.date_to:
                continue
            if band and qso.band.lower() != band:
                continue
            if mode and qso.mode.upper() != mode:
                continue
            filtered.append(qso)
        return filtered

class FetchCallbookInfoUseCase:
    def __init__(self, port: CallbookPort) -> None:
        self._port = port

    def execute(self, callsign: str) -> CallbookData | None:
        return self._port.lookup(callsign)
