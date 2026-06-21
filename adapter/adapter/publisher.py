"""Publishes normalized events to a Pub/Sub topic."""

from __future__ import annotations

import json
from typing import Any

from google.cloud import pubsub_v1


class EventPublisher:
    """Thin wrapper around the Pub/Sub publisher client.

    The `event_type` is set as a message attribute so subscribers can filter without
    decoding the body.
    """

    def __init__(self, project_id: str, topic: str, client: pubsub_v1.PublisherClient | None = None):
        self._client = client or pubsub_v1.PublisherClient()
        self._topic_path = self._client.topic_path(project_id, topic)

    def publish(self, event: dict[str, Any]) -> str:
        data = json.dumps(event).encode("utf-8")
        future = self._client.publish(
            self._topic_path,
            data,
            event_type=str(event.get("event_type", "unknown")),
        )
        return future.result()
