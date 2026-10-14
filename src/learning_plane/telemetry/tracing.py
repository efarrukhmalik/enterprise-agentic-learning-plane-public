from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from learning_plane.storage import SQLiteStore


class LocalTracer:
    """OTel-compatible local evidence with redacted payloads and causal IDs."""

    def __init__(self, store: SQLiteStore, output: str | Path) -> None:
        self.store = store
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def digest(value: Any) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

    @contextmanager
    def span(
        self,
        name: str,
        *,
        tenant_id: str,
        trace_id: str,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        span_id = uuid4().hex[:16]
        started = datetime.now(UTC)
        start_clock = perf_counter()
        record: dict[str, Any] = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "tenant_id": tenant_id,
            "name": name,
            "started_at": started.isoformat(),
            "status": "OK",
            "attributes": attributes or {},
            "events": [],
        }
        try:
            yield record
        except Exception as exc:
            record["status"] = "ERROR"
            record["events"].append({"name": "exception", "type": type(exc).__name__})
            raise
        finally:
            record["ended_at"] = datetime.now(UTC).isoformat()
            record["duration_ms"] = round((perf_counter() - start_clock) * 1000, 3)
            self.store.save_span(record)
            with self.output.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")

    def trace_tree(self, tenant_id: str, trace_id: str) -> list[dict[str, Any]]:
        return self.store.spans(tenant_id, trace_id)
