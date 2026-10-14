from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_runs_tenant ON runs(tenant_id, correlation_id);
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    decision_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS idempotent_writes (
    tenant_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, idempotency_key)
);
CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id, started_at);
CREATE TABLE IF NOT EXISTS variants (
    variant_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS releases (
    release_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    status TEXT NOT NULL,
    version TEXT NOT NULL,
    prior_version TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT
);
CREATE TABLE IF NOT EXISTS analytics (
    record_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class SQLiteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def save_run(self, request: Any, result: Any) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO runs
                (run_id, tenant_id, principal_id, correlation_id, status, result_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result.run_id,
                    request.tenant_id,
                    request.principal_id,
                    request.correlation_id,
                    result.status,
                    result.model_dump_json(),
                ),
            )

    def get_run(self, tenant_id: str, run_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT result_json FROM runs WHERE tenant_id = ? AND run_id = ?",
                (tenant_id, run_id),
            ).fetchone()
        return json.loads(row["result_json"]) if row else None

    def save_approval(self, decision: Any) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (decision.approval_id, decision.tenant_id, decision.model_dump_json()),
            )

    def get_approval(self, tenant_id: str, approval_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT decision_json FROM approvals WHERE tenant_id = ? AND approval_id = ?",
                (tenant_id, approval_id),
            ).fetchone()
        return json.loads(row["decision_json"]) if row else None

    def put_idempotent(self, tenant_id: str, key: str, result: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT result_json FROM idempotent_writes
                WHERE tenant_id = ? AND idempotency_key = ?""",
                (tenant_id, key),
            ).fetchone()
            if row:
                return json.loads(row["result_json"])
            connection.execute(
                "INSERT INTO idempotent_writes VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (tenant_id, key, json.dumps(result, sort_keys=True)),
            )
        return result

    def save_span(self, span: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO spans
                (span_id, trace_id, parent_span_id, tenant_id,
                 name, payload_json, started_at, ended_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    span["span_id"],
                    span["trace_id"],
                    span.get("parent_span_id"),
                    span["tenant_id"],
                    span["name"],
                    json.dumps(span, sort_keys=True),
                    span["started_at"],
                    span["ended_at"],
                ),
            )

    def spans(self, tenant_id: str, trace_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT payload_json FROM spans
                WHERE tenant_id = ? AND trace_id = ? ORDER BY started_at""",
                (tenant_id, trace_id),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def save_variant(self, manifest: Any) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO variants VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (manifest.variant_id, manifest.content_hash, manifest.model_dump_json()),
            )

    def save_release(self, release: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO releases
                (release_id, tenant_id, status, version, prior_version, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    release["release_id"],
                    release["tenant_id"],
                    release["status"],
                    release["version"],
                    release.get("prior_version"),
                    json.dumps(release, sort_keys=True),
                ),
            )

    def releases(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM releases WHERE tenant_id = ? ORDER BY created_at",
                (tenant_id,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def enqueue(self, event_id: str, tenant_id: str, payload: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO events VALUES (?, ?, 'pending', ?, CURRENT_TIMESTAMP, NULL)",
                (event_id, tenant_id, json.dumps(payload, sort_keys=True)),
            )

    def pending_events(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT event_id, payload_json FROM events
                WHERE tenant_id = ? AND status = 'pending'""",
                (tenant_id,),
            ).fetchall()
        return [{"event_id": r["event_id"], **json.loads(r["payload_json"])} for r in rows]

    def complete_event(self, event_id: str, tenant_id: str, record: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """UPDATE events SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                WHERE event_id = ? AND tenant_id = ?""",
                (event_id, tenant_id),
            )
            connection.execute(
                "INSERT OR IGNORE INTO analytics VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (event_id, tenant_id, json.dumps(record, sort_keys=True)),
            )

    def analytics(self, tenant_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM analytics WHERE tenant_id = ? ORDER BY created_at",
                (tenant_id,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]
