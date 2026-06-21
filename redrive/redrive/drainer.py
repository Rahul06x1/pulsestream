"""Drain the dead-letter subscription.

For each dead-lettered message we make one more attempt to insert it into BigQuery. If it
still fails (e.g. permanently invalid), we quarantine it to a `dead_letters` table so it
is never lost, then ack. This bounds retries and keeps the DLQ from growing forever.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Callable

from .logger import get_logger

log = get_logger("pulsestream-redrive")


def _quarantine_row(reason: str, raw: str) -> dict[str, Any]:
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "raw": raw,
    }


def drain(
    subscriber,
    subscription_path: str,
    reinsert: Callable[[dict], None],
    quarantine: Callable[[dict], None],
    max_messages: int = 100,
) -> dict[str, int]:
    """Pull up to `max_messages`, retry insertion, quarantine failures, ack everything.

    `reinsert` inserts a decoded event into BigQuery; `quarantine` writes a quarantine row.
    Both are injected so the function is fully unit-testable.
    """
    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": max_messages}
    )
    received = list(response.received_messages)
    stats = {"pulled": len(received), "reinserted": 0, "quarantined": 0}
    ack_ids = []

    for msg in received:
        raw = base64.b64decode(msg.message.data).decode("utf-8") if isinstance(
            msg.message.data, (bytes, bytearray)
        ) else msg.message.data
        try:
            event = json.loads(raw)
            reinsert(event)
            stats["reinserted"] += 1
        except Exception as exc:  # noqa: BLE001 - persist instead of losing the message
            log.error("reinsert failed; quarantining", extra={"context": {"error": str(exc)}})
            quarantine(_quarantine_row(str(exc), raw))
            stats["quarantined"] += 1
        ack_ids.append(msg.ack_id)

    if ack_ids:
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})

    log.info("drain complete", extra={"context": stats})
    return stats
