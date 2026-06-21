import base64
import json
from unittest.mock import patch

import pytest

import main

VALID = {
    "event_id": "1",
    "event_type": "edit",
    "wiki": "enwiki",
    "occurred_at": "2023-11-14T22:13:20Z",
    "bot": False,
}


@pytest.fixture
def client():
    main.app.config.update(TESTING=True)
    return main.app.test_client()


def _envelope(event: dict) -> dict:
    data = base64.b64encode(json.dumps(event).encode()).decode()
    return {"message": {"data": data, "messageId": "m1"}}


def test_valid_push_inserts_and_returns_204(client):
    with patch("main.insert_event") as insert:
        resp = client.post("/", json=_envelope(VALID))
    assert resp.status_code == 204
    insert.assert_called_once()


def test_invalid_event_returns_400(client):
    bad = {k: v for k, v in VALID.items() if k != "wiki"}
    with patch("main.insert_event") as insert:
        resp = client.post("/", json=_envelope(bad))
    assert resp.status_code == 400
    insert.assert_not_called()


def test_insert_failure_returns_500(client):
    with patch("main.insert_event", side_effect=RuntimeError("bq down")):
        resp = client.post("/", json=_envelope(VALID))
    assert resp.status_code == 500


def test_missing_envelope_returns_400(client):
    resp = client.post("/", json={"not": "an envelope"})
    assert resp.status_code == 400
