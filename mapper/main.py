"""PulseStream mapper (Cloud Run service).

Receives Pub/Sub push messages over HTTP, validates them against the contract, and
streaming-inserts them into BigQuery. Response codes drive Pub/Sub delivery:

  204  success           -> message acked
  400  invalid payload   -> nacked; after max attempts Pub/Sub routes to the dead-letter
  500  transient failure -> nacked; retried, then dead-lettered

Local run:
    pip install -e . && functions-framework --target=... is not used; this is a Flask app:
    flask --app main run --port 8080
"""

from __future__ import annotations

import base64
import json
import os

from flask import Flask, request

from mapper.backend import insert_event
from mapper.logger import get_logger
from mapper.validation import ValidationError, validate_event

log = get_logger("pulsestream-mapper")

PROJECT_ID = os.environ.get("GCP_PROJECT", "")
DATASET = os.environ.get("BQ_DATASET", "events")
TABLE = os.environ.get("BQ_TABLE", "raw_stream")

app = Flask(__name__)


def _table_ref() -> str:
    return f"{PROJECT_ID}.{DATASET}.{TABLE}"


def _decode_push(envelope: dict) -> dict:
    """Extract and JSON-decode the event from a Pub/Sub push envelope."""
    message = envelope["message"]
    data = base64.b64decode(message["data"]).decode("utf-8")
    return json.loads(data)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200


@app.post("/")
def handle_push():
    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        return {"error": "expected Pub/Sub push envelope"}, 400

    try:
        event = _decode_push(envelope)
    except Exception as exc:  # noqa: BLE001 - malformed payload is non-retryable
        log.error("undecodable message", extra={"context": {"error": str(exc)}})
        return {"error": "undecodable"}, 400

    try:
        validate_event(event)
    except ValidationError as exc:
        log.error("invalid event", extra={"context": {"error": str(exc)}})
        return {"error": "invalid", "detail": str(exc)}, 400

    try:
        insert_event(_table_ref(), event)
    except Exception as exc:  # noqa: BLE001 - transient: let Pub/Sub retry
        log.error("insert failed", extra={"context": {"error": str(exc)}})
        return {"error": "insert_failed"}, 500

    return "", 204
