"""PulseStream redrive entry point (Cloud Run job).

Runs once per invocation (Scheduler-triggered or manual), drains the dead-letter
subscription, and exits. Idempotent: anything it cannot re-insert is quarantined.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from google.cloud import bigquery, pubsub_v1

from redrive.drainer import drain
from redrive.logger import get_logger

log = get_logger("pulsestream-redrive")

PROJECT_ID = os.environ.get("GCP_PROJECT", "")
DLQ_SUBSCRIPTION = os.environ.get("DLQ_SUBSCRIPTION", "events-dlq-sub")
DATASET = os.environ.get("BQ_DATASET", "events")
RAW_TABLE = os.environ.get("BQ_TABLE", "raw_stream")
QUARANTINE_TABLE = os.environ.get("QUARANTINE_TABLE", "dead_letters")


def main() -> int:
    subscriber = pubsub_v1.SubscriberClient()
    bq = bigquery.Client()
    sub_path = subscriber.subscription_path(PROJECT_ID, DLQ_SUBSCRIPTION)
    raw_ref = f"{PROJECT_ID}.{DATASET}.{RAW_TABLE}"
    quarantine_ref = f"{PROJECT_ID}.{DATASET}.{QUARANTINE_TABLE}"

    def reinsert(event: dict) -> None:
        row = {
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
        errors = bq.insert_rows_json(raw_ref, [row])
        if errors:
            raise RuntimeError(f"reinsert failed: {errors}")

    def quarantine(row: dict) -> None:
        errors = bq.insert_rows_json(quarantine_ref, [row])
        if errors:
            raise RuntimeError(f"quarantine failed: {errors}")

    stats = drain(subscriber, sub_path, reinsert, quarantine)
    log.info("redrive finished", extra={"context": stats})
    return 0


if __name__ == "__main__":
    sys.exit(main())
