from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import DurableRecord, RecordStatus


class SearchIndexError(RuntimeError):
    pass


_STATUS_RANK = {
    RecordStatus.LOCKED: 0,
    RecordStatus.OPEN: 1,
    RecordStatus.QUARANTINE: 2,
    RecordStatus.SUPERSEDED: 3,
    RecordStatus.DROP: 4,
}


@dataclass(frozen=True)
class SearchHit:
    record_id: str
    entity_id: str
    status: RecordStatus
    record_type: str
    text: str
    source_id: str
    authority: str
    score: float


class SearchIndex:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def rebuild(self, records: Iterable[DurableRecord]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute("DROP TABLE IF EXISTS records_fts")
                connection.execute("DROP TABLE IF EXISTS records")
                connection.execute(
                    """
                    CREATE TABLE records (
                        record_id TEXT PRIMARY KEY,
                        entity_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        record_type TEXT NOT NULL,
                        text TEXT NOT NULL,
                        source_id TEXT NOT NULL,
                        authority TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE VIRTUAL TABLE records_fts USING fts5(record_id UNINDEXED, entity_id, text)"
                )
                for record in sorted(records, key=lambda item: (item.created_at, item.record_id)):
                    connection.execute(
                        "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            record.record_id,
                            record.entity_id,
                            record.status.value,
                            record.record_type,
                            record.text,
                            record.source.source_id,
                            record.source.authority,
                            record.created_at.isoformat(),
                        ),
                    )
                    connection.execute(
                        "INSERT INTO records_fts(record_id, entity_id, text) VALUES (?, ?, ?)",
                        (record.record_id, record.entity_id, record.text),
                    )
                connection.commit()
        except sqlite3.Error as exc:
            raise SearchIndexError("INDEX_REBUILD_FAILED") from exc

    @staticmethod
    def _status_clause(statuses: set[RecordStatus] | None) -> tuple[str, tuple[str, ...]]:
        if not statuses:
            return "", ()
        values = tuple(sorted(status.value for status in statuses))
        placeholders = ",".join("?" for _ in values)
        return f" AND status IN ({placeholders})", values

    @staticmethod
    def _hit(row: tuple[object, ...], score: float) -> SearchHit:
        return SearchHit(
            record_id=str(row[0]),
            entity_id=str(row[1]),
            status=RecordStatus(str(row[2])),
            record_type=str(row[3]),
            text=str(row[4]),
            source_id=str(row[5]),
            authority=str(row[6]),
            score=float(score),
        )

    @staticmethod
    def _sort(hits: list[SearchHit]) -> tuple[SearchHit, ...]:
        hits.sort(key=lambda hit: (_STATUS_RANK[hit.status], hit.score, hit.record_id))
        return tuple(hits)

    def search(
        self,
        query: str,
        *,
        statuses: set[RecordStatus] | None = None,
    ) -> tuple[SearchHit, ...]:
        text = str(query).strip()
        if not text:
            return ()
        if not self.db_path.exists():
            raise SearchIndexError("INDEX_MISSING")

        status_clause, status_values = self._status_clause(statuses)
        try:
            with sqlite3.connect(self.db_path) as connection:
                exact_sql = (
                    "SELECT record_id, entity_id, status, record_type, text, source_id, authority "
                    "FROM records WHERE (record_id = ? OR entity_id = ?)" + status_clause
                )
                exact_rows = connection.execute(exact_sql, (text, text, *status_values)).fetchall()
                if exact_rows:
                    exact_hits = [self._hit(tuple(row), -1000.0 if row[0] == text else -900.0) for row in exact_rows]
                    return self._sort(exact_hits)

                phrase = '"' + text.replace('"', '""') + '"'
                fts_sql = (
                    "SELECT r.record_id, r.entity_id, r.status, r.record_type, r.text, r.source_id, r.authority, "
                    "bm25(records_fts) "
                    "FROM records_fts JOIN records r ON r.record_id = records_fts.record_id "
                    "WHERE records_fts MATCH ?"
                )
                params: tuple[object, ...] = (phrase,)
                if statuses:
                    values = tuple(sorted(status.value for status in statuses))
                    placeholders = ",".join("?" for _ in values)
                    fts_sql += f" AND r.status IN ({placeholders})"
                    params = (phrase, *values)
                rows = connection.execute(fts_sql, params).fetchall()
        except sqlite3.Error as exc:
            raise SearchIndexError("INDEX_SEARCH_FAILED") from exc

        hits = [self._hit(tuple(row[:7]), float(row[7])) for row in rows]
        return self._sort(hits)
