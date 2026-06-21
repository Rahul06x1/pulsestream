"""Normalize a raw Wikimedia recentchange event into the PulseStream contract.

Wikimedia EventStreams docs: https://stream.wikimedia.org/?doc
Each event is a JSON object with fields like `id`, `type`, `title`, `user`, `bot`,
`wiki`, `timestamp` (epoch seconds) and a `meta` object (`meta.id`, `meta.dt`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw recentchange event to the normalized event schema."""
    meta = raw.get("meta") or {}

    occurred_at = meta.get("dt")
    if not occurred_at and raw.get("timestamp") is not None:
        occurred_at = datetime.fromtimestamp(int(raw["timestamp"]), tz=timezone.utc).isoformat()

    event_id = str(meta.get("id") or raw.get("id") or "")

    return {
        "event_id": event_id,
        "event_type": raw.get("type", "unknown"),
        "wiki": raw.get("wiki", "unknown"),
        "title": raw.get("title"),
        "user": raw.get("user"),
        "occurred_at": occurred_at,
        "bot": bool(raw.get("bot", False)),
    }
