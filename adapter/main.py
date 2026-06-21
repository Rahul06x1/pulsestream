"""PulseStream adapter (Cloud Run service).

Opens a long-lived SSE connection to Wikimedia EventStreams, normalizes each event, and
publishes it to Pub/Sub. A tiny HTTP server satisfies Cloud Run's port requirement and
exposes /healthz; the SSE consumer runs in a background thread (keep min-instances=1).

Local run:
    pip install -e . && python main.py
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from adapter.logger import get_logger
from adapter.normalize import normalize
from adapter.publisher import EventPublisher

log = get_logger("pulsestream-adapter")

STREAM_URL = os.environ.get(
    "STREAM_URL", "https://stream.wikimedia.org/v2/stream/recentchange"
)
PROJECT_ID = os.environ.get("GCP_PROJECT", "")
TOPIC = os.environ.get("PUBSUB_TOPIC", "events")
PORT = int(os.environ.get("PORT", "8080"))

_consumed = {"count": 0}


def consume_stream(publisher: EventPublisher, url: str = STREAM_URL) -> None:
    """Consume the SSE feed forever, publishing each `message` event."""
    log.info("connecting to stream", extra={"context": {"url": url}})
    with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}, timeout=60) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            try:
                raw = json.loads(line[len("data:"):].strip())
                event = normalize(raw)
                publisher.publish(event)
                _consumed["count"] += 1
            except Exception as exc:  # noqa: BLE001 - never let one bad line kill the loop
                log.error("failed to process event", extra={"context": {"error": str(exc)}})


class _Health(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - http.server API
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "consumed": _consumed["count"]}).encode())

    def log_message(self, *args):  # silence default stderr logging
        return


def main() -> None:
    publisher = EventPublisher(PROJECT_ID, TOPIC)
    thread = threading.Thread(target=consume_stream, args=(publisher,), daemon=True)
    thread.start()
    HTTPServer(("0.0.0.0", PORT), _Health).serve_forever()


if __name__ == "__main__":
    main()
