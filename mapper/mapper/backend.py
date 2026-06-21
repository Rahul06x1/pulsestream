"""BigQuery sink: streaming-inserts validated events into the raw_stream table."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery


def to_row(event: dict[str, Any]) -> dict[str, Any]:
    """Shape a normalized event into a BigQuery row."""
    return {
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "wiki": event["wiki"],
        "title": event.get("title"),
        "user": event.get("user"),
        "occurred_at": event.get("occurred_at"),
        "bot": bool(event.get("bot", False)),
        "payload": event,
    }


def insert_event(table_ref: str, event: dict[str, Any], client: bigquery.Client | None = None) -> None:
    """Insert a single event. Raises RuntimeError on a BigQuery insert error."""
    bq = client or bigquery.Client()
    errors = bq.insert_rows_json(table_ref, [to_row(event)])
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
