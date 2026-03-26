from __future__ import annotations

import sqlite3
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from pycqlog.domain.models import (
    Logbook,
    LogbookDraft,
    Qso,
    QsoDraft,
    StationProfile,
    StationProfileDraft,
)


class InMemoryQsoRepository:
    def __init__(self, active_logbook_id: int | None = None) -> None:
        self._items: list[Qso] = []
        self._profiles: list[StationProfile] = []
        self._logbooks: list[Logbook] = [
            Logbook(
                id=1,
                name="Main Logbook",
                description="Default logbook",
                qso_count=0,
            )
        ]
        self._active_logbook_id = active_logbook_id or 1
        self._next_qso_id = 1
        self._next_profile_id = 1
        self._next_logbook_id = 2

    def ensure_default_logbook(self) -> Logbook:
        return self.get_active_logbook()

    def list_logbooks(self) -> list[Logbook]:
        return [self._decorate_logbook(item) for item in self._logbooks]

    def get_logbook(self, logbook_id: int) -> Logbook | None:
        for item in self._logbooks:
            if item.id == logbook_id:
                return self._decorate_logbook(item)
        return None

    def save_logbook(self, draft: LogbookDraft, logbook_id: int | None = None) -> Logbook:
        if logbook_id is None:
            logbook = Logbook(
                id=self._next_logbook_id,
                name=draft.name.strip(),
                description=draft.description.strip(),
                operator_profile_id=draft.operator_profile_id,
                station_profile_id=draft.station_profile_id,
            )
            self._next_logbook_id += 1
            self._logbooks.append(logbook)
            return self._decorate_logbook(logbook)

        for index, item in enumerate(self._logbooks):
            if item.id == logbook_id:
                updated = Logbook(
                    id=item.id,
                    name=draft.name.strip(),
                    description=draft.description.strip(),
                    operator_profile_id=draft.operator_profile_id,
                    station_profile_id=draft.station_profile_id,
                    created_at=item.created_at,
                )
                self._logbooks[index] = updated
                return self._decorate_logbook(updated)
        raise ValueError(f"Logbook {logbook_id} not found.")

    def delete_logbook(self, logbook_id: int) -> bool:
        if len(self._logbooks) <= 1:
            return False
        before = len(self._logbooks)
        self._logbooks = [item for item in self._logbooks if item.id != logbook_id]
        if len(self._logbooks) == before:
            return False
        self._items = [item for item in self._items if item.logbook_id != logbook_id]
        if self._active_logbook_id == logbook_id:
            self._active_logbook_id = self._logbooks[0].id
        return True

    def get_active_logbook(self) -> Logbook:
        logbook = self.get_logbook(self._active_logbook_id)
        if logbook is None:
            self._active_logbook_id = self._logbooks[0].id
            return self._decorate_logbook(self._logbooks[0])
        return logbook

    def set_active_logbook(self, logbook_id: int) -> Logbook:
        logbook = self.get_logbook(logbook_id)
        if logbook is None:
            raise ValueError(f"Logbook {logbook_id} not found.")
        self._active_logbook_id = logbook_id
        return logbook

    def list_station_profiles(self) -> list[StationProfile]:
        return list(self._profiles)

    def get_station_profile(self, profile_id: int) -> StationProfile | None:
        for item in self._profiles:
            if item.id == profile_id:
                return item
        return None

    def save_station_profile(
        self,
        draft: StationProfileDraft,
        profile_id: int | None = None,
    ) -> StationProfile:
        if profile_id is None:
            profile = StationProfile(
                id=self._next_profile_id,
                name=draft.name.strip(),
                profile_type=draft.profile_type,
                callsign=draft.callsign.strip().upper(),
                qth=draft.qth.strip(),
                locator=draft.locator.strip().upper(),
                power=draft.power.strip(),
                antenna=draft.antenna.strip(),
                notes=draft.notes.strip(),
            )
            self._next_profile_id += 1
            self._profiles.append(profile)
            return profile

        for index, item in enumerate(self._profiles):
            if item.id == profile_id:
                updated = StationProfile(
                    id=item.id,
                    name=draft.name.strip(),
                    profile_type=draft.profile_type,
                    callsign=draft.callsign.strip().upper(),
                    qth=draft.qth.strip(),
                    locator=draft.locator.strip().upper(),
                    power=draft.power.strip(),
                    antenna=draft.antenna.strip(),
                    notes=draft.notes.strip(),
                    created_at=item.created_at,
                )
                self._profiles[index] = updated
                return updated
        raise ValueError(f"Station profile {profile_id} not found.")

    def delete_station_profile(self, profile_id: int) -> bool:
        before = len(self._profiles)
        self._profiles = [item for item in self._profiles if item.id != profile_id]
        if len(self._profiles) == before:
            return False
        self._logbooks = [
            Logbook(
                id=item.id,
                name=item.name,
                description=item.description,
                operator_profile_id=None if item.operator_profile_id == profile_id else item.operator_profile_id,
                station_profile_id=None if item.station_profile_id == profile_id else item.station_profile_id,
                created_at=item.created_at,
            )
            for item in self._logbooks
        ]
        return True

    def save(self, draft: QsoDraft) -> Qso:
        qso = Qso(
            id=self._next_qso_id,
            callsign=draft.callsign,
            qso_date=draft.qso_date,
            time_on=draft.time_on,
            freq=draft.freq,
            mode=draft.mode,
            band=draft.band,
            logbook_id=draft.logbook_id or self._active_logbook_id,
            rst_sent=draft.rst_sent,
            rst_recv=draft.rst_recv,
            operator=draft.operator,
            station_callsign=draft.station_callsign,
            notes=draft.notes,
            source=draft.source,
            created_at=draft.created_at,
        )
        self._items.append(qso)
        self._next_qso_id += 1
        return qso

    def list_all(self) -> list[Qso]:
        return sorted(
            [item for item in self._items if item.logbook_id == self._active_logbook_id],
            key=lambda item: (item.qso_date, item.time_on, item.id),
        )

    def list_recent(self, limit: int = 50) -> list[Qso]:
        items = sorted(
            [item for item in self._items if item.logbook_id == self._active_logbook_id],
            key=lambda item: item.id,
            reverse=True,
        )
        return items[:limit]

    def get_by_id(self, qso_id: int) -> Qso | None:
        for item in self._items:
            if item.id == qso_id and item.logbook_id == self._active_logbook_id:
                return item
        return None

    def update(self, qso_id: int, draft: QsoDraft) -> Qso | None:
        for index, item in enumerate(self._items):
            if item.id == qso_id and item.logbook_id == self._active_logbook_id:
                updated = Qso(
                    id=qso_id,
                    callsign=draft.callsign,
                    qso_date=draft.qso_date,
                    time_on=draft.time_on,
                    freq=draft.freq,
                    mode=draft.mode,
                    band=draft.band,
                    logbook_id=item.logbook_id,
                    rst_sent=draft.rst_sent,
                    rst_recv=draft.rst_recv,
                    operator=draft.operator,
                    station_callsign=draft.station_callsign,
                    notes=draft.notes,
                    source=draft.source,
                    created_at=item.created_at,
                )
                self._items[index] = updated
                return updated
        return None

    def delete(self, qso_id: int) -> bool:
        before = len(self._items)
        self._items = [
            item for item in self._items if not (item.id == qso_id and item.logbook_id == self._active_logbook_id)
        ]
        return len(self._items) != before

    def search(self, callsign: str, limit: int = 50) -> list[Qso]:
        term = callsign.strip().upper()
        items = sorted(
            [item for item in self._items if item.logbook_id == self._active_logbook_id],
            key=lambda item: item.id,
            reverse=True,
        )
        if not term:
            return items[:limit]
        return [item for item in items if term in item.callsign][:limit]

    def find_duplicate(self, draft: QsoDraft) -> Qso | None:
        logbook_id = draft.logbook_id or self._active_logbook_id
        for item in self._items:
            if (
                item.logbook_id == logbook_id
                and item.callsign == draft.callsign
                and item.qso_date == draft.qso_date
                and item.time_on == draft.time_on
                and item.freq == draft.freq
                and item.mode == draft.mode
            ):
                return item
        return None

    def _decorate_logbook(self, logbook: Logbook) -> Logbook:
        operator = self.get_station_profile(logbook.operator_profile_id) if logbook.operator_profile_id else None
        station = self.get_station_profile(logbook.station_profile_id) if logbook.station_profile_id else None
        qso_count = len([item for item in self._items if item.logbook_id == logbook.id])
        return Logbook(
            id=logbook.id,
            name=logbook.name,
            description=logbook.description,
            operator_profile_id=logbook.operator_profile_id,
            station_profile_id=logbook.station_profile_id,
            operator_callsign=operator.callsign if operator else "",
            station_callsign=station.callsign if station else "",
            qso_count=qso_count,
            created_at=logbook.created_at,
        )


class SQLiteQsoRepository:
    def __init__(self, database_path: Path, active_logbook_id: int | None = None) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_logbook_id = active_logbook_id or 1
        self._initialize()
        self._active_logbook_id = self.get_active_logbook().id

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS station_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    profile_type TEXT NOT NULL DEFAULT 'both',
                    callsign TEXT NOT NULL DEFAULT '',
                    qth TEXT NOT NULL DEFAULT '',
                    locator TEXT NOT NULL DEFAULT '',
                    power TEXT NOT NULL DEFAULT '',
                    antenna TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS logbooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    operator_profile_id INTEGER,
                    station_profile_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(operator_profile_id) REFERENCES station_profiles(id) ON DELETE SET NULL,
                    FOREIGN KEY(station_profile_id) REFERENCES station_profiles(id) ON DELETE SET NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS qsos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    logbook_id INTEGER NOT NULL DEFAULT 1,
                    callsign TEXT NOT NULL,
                    qso_date TEXT NOT NULL,
                    time_on TEXT NOT NULL,
                    freq TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    band TEXT NOT NULL,
                    rst_sent TEXT NOT NULL DEFAULT '',
                    rst_recv TEXT NOT NULL DEFAULT '',
                    operator TEXT NOT NULL DEFAULT '',
                    station_callsign TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'manual',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(logbook_id) REFERENCES logbooks(id) ON DELETE CASCADE
                )
                """
            )
            self._migrate_existing_schema(connection)
            self._ensure_default_logbook_row(connection)

    def _migrate_existing_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(qsos)").fetchall()
        }
        if "logbook_id" not in columns:
            connection.execute("ALTER TABLE qsos ADD COLUMN logbook_id INTEGER NOT NULL DEFAULT 1")

    def _ensure_default_logbook_row(self, connection: sqlite3.Connection) -> None:
        row = connection.execute("SELECT id FROM logbooks ORDER BY id ASC LIMIT 1").fetchone()
        if row is None:
            created_at = datetime.utcnow().isoformat()
            connection.execute(
                """
                INSERT INTO logbooks (id, name, description, operator_profile_id, station_profile_id, created_at)
                VALUES (1, ?, ?, NULL, NULL, ?)
                """,
                ("Main Logbook", "Default logbook", created_at),
            )

    def ensure_default_logbook(self) -> Logbook:
        return self.get_active_logbook()

    def list_logbooks(self) -> list[Logbook]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    l.id,
                    l.name,
                    l.description,
                    l.operator_profile_id,
                    l.station_profile_id,
                    l.created_at,
                    COALESCE(op.callsign, '') AS operator_callsign,
                    COALESCE(sp.callsign, '') AS station_callsign,
                    COALESCE(q.qso_count, 0) AS qso_count
                FROM logbooks l
                LEFT JOIN station_profiles op ON op.id = l.operator_profile_id
                LEFT JOIN station_profiles sp ON sp.id = l.station_profile_id
                LEFT JOIN (
                    SELECT logbook_id, COUNT(*) AS qso_count
                    FROM qsos
                    GROUP BY logbook_id
                ) q ON q.logbook_id = l.id
                ORDER BY l.name ASC, l.id ASC
                """
            ).fetchall()
        return [self._row_to_logbook(row) for row in rows]

    def get_logbook(self, logbook_id: int) -> Logbook | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    l.id,
                    l.name,
                    l.description,
                    l.operator_profile_id,
                    l.station_profile_id,
                    l.created_at,
                    COALESCE(op.callsign, '') AS operator_callsign,
                    COALESCE(sp.callsign, '') AS station_callsign,
                    COALESCE(q.qso_count, 0) AS qso_count
                FROM logbooks l
                LEFT JOIN station_profiles op ON op.id = l.operator_profile_id
                LEFT JOIN station_profiles sp ON sp.id = l.station_profile_id
                LEFT JOIN (
                    SELECT logbook_id, COUNT(*) AS qso_count
                    FROM qsos
                    GROUP BY logbook_id
                ) q ON q.logbook_id = l.id
                WHERE l.id = ?
                """,
                (logbook_id,),
            ).fetchone()
        return self._row_to_logbook(row) if row is not None else None

    def save_logbook(self, draft: LogbookDraft, logbook_id: int | None = None) -> Logbook:
        name = draft.name.strip()
        description = draft.description.strip()
        with self._connect() as connection:
            if logbook_id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO logbooks (
                        name,
                        description,
                        operator_profile_id,
                        station_profile_id,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        description,
                        draft.operator_profile_id,
                        draft.station_profile_id,
                        datetime.utcnow().isoformat(),
                    ),
                )
                logbook_id = int(cursor.lastrowid)
            else:
                connection.execute(
                    """
                    UPDATE logbooks
                    SET
                        name = ?,
                        description = ?,
                        operator_profile_id = ?,
                        station_profile_id = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        description,
                        draft.operator_profile_id,
                        draft.station_profile_id,
                        logbook_id,
                    ),
                )
        logbook = self.get_logbook(logbook_id)
        if logbook is None:
            raise ValueError(f"Logbook {logbook_id} not found.")
        return logbook

    def delete_logbook(self, logbook_id: int) -> bool:
        with self._connect() as connection:
            count_row = connection.execute("SELECT COUNT(*) AS total FROM logbooks").fetchone()
            if count_row is not None and int(count_row["total"]) <= 1:
                return False
            cursor = connection.execute("DELETE FROM logbooks WHERE id = ?", (logbook_id,))
            deleted = cursor.rowcount > 0
            if deleted and self._active_logbook_id == logbook_id:
                next_row = connection.execute("SELECT id FROM logbooks ORDER BY name ASC, id ASC LIMIT 1").fetchone()
                if next_row is not None:
                    self._active_logbook_id = int(next_row["id"])
        return deleted

    def get_active_logbook(self) -> Logbook:
        logbook = self.get_logbook(self._active_logbook_id)
        if logbook is None:
            logbooks = self.list_logbooks()
            if not logbooks:
                raise ValueError("No logbooks available.")
            self._active_logbook_id = logbooks[0].id
            return logbooks[0]
        return logbook

    def set_active_logbook(self, logbook_id: int) -> Logbook:
        logbook = self.get_logbook(logbook_id)
        if logbook is None:
            raise ValueError(f"Logbook {logbook_id} not found.")
        self._active_logbook_id = logbook_id
        return logbook

    def list_station_profiles(self) -> list[StationProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    profile_type,
                    callsign,
                    qth,
                    locator,
                    power,
                    antenna,
                    notes,
                    created_at
                FROM station_profiles
                ORDER BY name ASC, id ASC
                """
            ).fetchall()
        return [self._row_to_profile(row) for row in rows]

    def get_station_profile(self, profile_id: int) -> StationProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    profile_type,
                    callsign,
                    qth,
                    locator,
                    power,
                    antenna,
                    notes,
                    created_at
                FROM station_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()
        return self._row_to_profile(row) if row is not None else None

    def save_station_profile(
        self,
        draft: StationProfileDraft,
        profile_id: int | None = None,
    ) -> StationProfile:
        name = draft.name.strip()
        with self._connect() as connection:
            if profile_id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO station_profiles (
                        name,
                        profile_type,
                        callsign,
                        qth,
                        locator,
                        power,
                        antenna,
                        notes,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        draft.profile_type,
                        draft.callsign.strip().upper(),
                        draft.qth.strip(),
                        draft.locator.strip().upper(),
                        draft.power.strip(),
                        draft.antenna.strip(),
                        draft.notes.strip(),
                        datetime.utcnow().isoformat(),
                    ),
                )
                profile_id = int(cursor.lastrowid)
            else:
                connection.execute(
                    """
                    UPDATE station_profiles
                    SET
                        name = ?,
                        profile_type = ?,
                        callsign = ?,
                        qth = ?,
                        locator = ?,
                        power = ?,
                        antenna = ?,
                        notes = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        draft.profile_type,
                        draft.callsign.strip().upper(),
                        draft.qth.strip(),
                        draft.locator.strip().upper(),
                        draft.power.strip(),
                        draft.antenna.strip(),
                        draft.notes.strip(),
                        profile_id,
                    ),
                )
        profile = self.get_station_profile(profile_id)
        if profile is None:
            raise ValueError(f"Station profile {profile_id} not found.")
        return profile

    def delete_station_profile(self, profile_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM station_profiles WHERE id = ?", (profile_id,))
        return cursor.rowcount > 0

    def save(self, draft: QsoDraft) -> Qso:
        logbook_id = draft.logbook_id or self._active_logbook_id
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO qsos (
                    logbook_id,
                    callsign,
                    qso_date,
                    time_on,
                    freq,
                    mode,
                    band,
                    rst_sent,
                    rst_recv,
                    operator,
                    station_callsign,
                    notes,
                    source,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    logbook_id,
                    draft.callsign,
                    draft.qso_date.isoformat(),
                    draft.time_on.isoformat(),
                    str(draft.freq),
                    draft.mode,
                    draft.band,
                    draft.rst_sent,
                    draft.rst_recv,
                    draft.operator,
                    draft.station_callsign,
                    draft.notes,
                    draft.source,
                    draft.created_at.isoformat(),
                ),
            )
            qso_id = int(cursor.lastrowid)

        return Qso(
            id=qso_id,
            callsign=draft.callsign,
            qso_date=draft.qso_date,
            time_on=draft.time_on,
            freq=draft.freq,
            mode=draft.mode,
            band=draft.band,
            logbook_id=logbook_id,
            rst_sent=draft.rst_sent,
            rst_recv=draft.rst_recv,
            operator=draft.operator,
            station_callsign=draft.station_callsign,
            notes=draft.notes,
            source=draft.source,
            created_at=draft.created_at,
        )

    def list_all(self) -> list[Qso]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    logbook_id,
                    callsign,
                    qso_date,
                    time_on,
                    freq,
                    mode,
                    band,
                    rst_sent,
                    rst_recv,
                    operator,
                    station_callsign,
                    notes,
                    source,
                    created_at
                FROM qsos
                WHERE logbook_id = ?
                ORDER BY qso_date ASC, time_on ASC, id ASC
                """,
                (self._active_logbook_id,),
            ).fetchall()
        return [self._row_to_qso(row) for row in rows]

    def get_by_id(self, qso_id: int) -> Qso | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    logbook_id,
                    callsign,
                    qso_date,
                    time_on,
                    freq,
                    mode,
                    band,
                    rst_sent,
                    rst_recv,
                    operator,
                    station_callsign,
                    notes,
                    source,
                    created_at
                FROM qsos
                WHERE id = ? AND logbook_id = ?
                """,
                (qso_id, self._active_logbook_id),
            ).fetchone()
        return self._row_to_qso(row) if row is not None else None

    def update(self, qso_id: int, draft: QsoDraft) -> Qso | None:
        existing = self.get_by_id(qso_id)
        if existing is None:
            return None

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE qsos
                SET
                    callsign = ?,
                    qso_date = ?,
                    time_on = ?,
                    freq = ?,
                    mode = ?,
                    band = ?,
                    rst_sent = ?,
                    rst_recv = ?,
                    operator = ?,
                    station_callsign = ?,
                    notes = ?,
                    source = ?
                WHERE id = ? AND logbook_id = ?
                """,
                (
                    draft.callsign,
                    draft.qso_date.isoformat(),
                    draft.time_on.isoformat(),
                    str(draft.freq),
                    draft.mode,
                    draft.band,
                    draft.rst_sent,
                    draft.rst_recv,
                    draft.operator,
                    draft.station_callsign,
                    draft.notes,
                    draft.source,
                    qso_id,
                    self._active_logbook_id,
                ),
            )

        return Qso(
            id=qso_id,
            callsign=draft.callsign,
            qso_date=draft.qso_date,
            time_on=draft.time_on,
            freq=draft.freq,
            mode=draft.mode,
            band=draft.band,
            logbook_id=existing.logbook_id,
            rst_sent=draft.rst_sent,
            rst_recv=draft.rst_recv,
            operator=draft.operator,
            station_callsign=draft.station_callsign,
            notes=draft.notes,
            source=draft.source,
            created_at=existing.created_at,
        )

    def delete(self, qso_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM qsos WHERE id = ? AND logbook_id = ?",
                (qso_id, self._active_logbook_id),
            )
        return cursor.rowcount > 0

    def search(self, callsign: str, limit: int = 50) -> list[Qso]:
        term = callsign.strip().upper()
        with self._connect() as connection:
            if term:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        logbook_id,
                        callsign,
                        qso_date,
                        time_on,
                        freq,
                        mode,
                        band,
                        rst_sent,
                        rst_recv,
                        operator,
                        station_callsign,
                        notes,
                        source,
                        created_at
                    FROM qsos
                    WHERE logbook_id = ? AND callsign LIKE ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (self._active_logbook_id, f"%{term}%", limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        logbook_id,
                        callsign,
                        qso_date,
                        time_on,
                        freq,
                        mode,
                        band,
                        rst_sent,
                        rst_recv,
                        operator,
                        station_callsign,
                        notes,
                        source,
                        created_at
                    FROM qsos
                    WHERE logbook_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (self._active_logbook_id, limit),
                ).fetchall()
        return [self._row_to_qso(row) for row in rows]

    def find_duplicate(self, draft: QsoDraft) -> Qso | None:
        logbook_id = draft.logbook_id or self._active_logbook_id
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    logbook_id,
                    callsign,
                    qso_date,
                    time_on,
                    freq,
                    mode,
                    band,
                    rst_sent,
                    rst_recv,
                    operator,
                    station_callsign,
                    notes,
                    source,
                    created_at
                FROM qsos
                WHERE
                    logbook_id = ?
                    AND callsign = ?
                    AND qso_date = ?
                    AND time_on = ?
                    AND freq = ?
                    AND mode = ?
                LIMIT 1
                """,
                (
                    logbook_id,
                    draft.callsign,
                    draft.qso_date.isoformat(),
                    draft.time_on.isoformat(),
                    str(draft.freq),
                    draft.mode,
                ),
            ).fetchone()
        return self._row_to_qso(row) if row is not None else None

    def list_recent(self, limit: int = 50) -> list[Qso]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    logbook_id,
                    callsign,
                    qso_date,
                    time_on,
                    freq,
                    mode,
                    band,
                    rst_sent,
                    rst_recv,
                    operator,
                    station_callsign,
                    notes,
                    source,
                    created_at
                FROM qsos
                WHERE logbook_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (self._active_logbook_id, limit),
            ).fetchall()
        return [self._row_to_qso(row) for row in rows]

    def _row_to_qso(self, row: sqlite3.Row) -> Qso:
        return Qso(
            id=int(row["id"]),
            logbook_id=int(row["logbook_id"]),
            callsign=str(row["callsign"]),
            qso_date=date.fromisoformat(str(row["qso_date"])),
            time_on=time.fromisoformat(str(row["time_on"])),
            freq=Decimal(str(row["freq"])),
            mode=str(row["mode"]),
            band=str(row["band"]),
            rst_sent=str(row["rst_sent"]),
            rst_recv=str(row["rst_recv"]),
            operator=str(row["operator"]),
            station_callsign=str(row["station_callsign"]),
            notes=str(row["notes"]),
            source=str(row["source"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    def _row_to_profile(self, row: sqlite3.Row) -> StationProfile:
        return StationProfile(
            id=int(row["id"]),
            name=str(row["name"]),
            profile_type=str(row["profile_type"]),
            callsign=str(row["callsign"]),
            qth=str(row["qth"]),
            locator=str(row["locator"]),
            power=str(row["power"]),
            antenna=str(row["antenna"]),
            notes=str(row["notes"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    def _row_to_logbook(self, row: sqlite3.Row) -> Logbook:
        return Logbook(
            id=int(row["id"]),
            name=str(row["name"]),
            description=str(row["description"]),
            operator_profile_id=int(row["operator_profile_id"]) if row["operator_profile_id"] is not None else None,
            station_profile_id=int(row["station_profile_id"]) if row["station_profile_id"] is not None else None,
            operator_callsign=str(row["operator_callsign"]),
            station_callsign=str(row["station_callsign"]),
            qso_count=int(row["qso_count"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
