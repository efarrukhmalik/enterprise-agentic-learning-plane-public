from __future__ import annotations

from hashlib import sha256
from typing import Any

from learning_plane.storage import SQLiteStore


class LocalEventPipeline:
    """SQLite-backed at-least-once event pipeline with idempotent analytical sink."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def publish(self, tenant_id: str, event: dict[str, Any]) -> str:
        event_id = (
            event.get("event_id")
            or sha256(f"{tenant_id}:{sorted(event.items())}".encode()).hexdigest()[:24]
        )
        self.store.enqueue(event_id, tenant_id, {**event, "event_id": event_id})
        return event_id

    def process(self, tenant_id: str) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []
        for event in self.store.pending_events(tenant_id):
            record = {
                "event_id": event["event_id"],
                "kind": event.get("kind", "unknown"),
                "run_id": event.get("run_id"),
                "latency_ms": event.get("latency_ms", 0),
                "error": bool(event.get("error", False)),
                "estimated_cost_units": event.get("token_cost_units", 0),
                "sink": "local_sqlite_analytics",
                "cloud_mapping": "Pub/Sub -> Cloud Run worker -> BigQuery",
            }
            self.store.complete_event(event["event_id"], tenant_id, record)
            processed.append(record)
        return processed


class CloudAdapterUnavailable(RuntimeError):
    pass


class PubSubPublisher:
    def publish(self, *_: Any, **__: Any) -> None:
        raise CloudAdapterUnavailable(
            "Google Pub/Sub adapter is configuration-only in the offline demo; "
            "install cloud extras and provide explicit credentials to implement a live call."
        )


class BigQuerySink:
    def write(self, *_: Any, **__: Any) -> None:
        raise CloudAdapterUnavailable(
            "BigQuery adapter is disabled by default; the local analytical sink is active."
        )


class VertexModelProvider:
    def invoke(self, *_: Any, **__: Any) -> None:
        raise CloudAdapterUnavailable(
            "Vertex AI provider is disabled by default; no paid model call was attempted."
        )
