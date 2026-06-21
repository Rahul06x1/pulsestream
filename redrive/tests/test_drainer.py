import base64
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from redrive.drainer import drain

SUB = "projects/p/subscriptions/events-dlq-sub"


def _msg(payload: str, ack_id: str):
    data = base64.b64encode(payload.encode())
    return SimpleNamespace(ack_id=ack_id, message=SimpleNamespace(data=data))


def test_drain_reinserts_valid_and_acks():
    sub = MagicMock()
    sub.pull.return_value = SimpleNamespace(
        received_messages=[_msg(json.dumps({"event_id": "1"}), "a1")]
    )
    reinsert = MagicMock()
    quarantine = MagicMock()

    stats = drain(sub, SUB, reinsert, quarantine)

    assert stats == {"pulled": 1, "reinserted": 1, "quarantined": 0}
    reinsert.assert_called_once()
    quarantine.assert_not_called()
    sub.acknowledge.assert_called_once()
    assert sub.acknowledge.call_args[1]["request"]["ack_ids"] == ["a1"]


def test_drain_quarantines_on_failure():
    sub = MagicMock()
    sub.pull.return_value = SimpleNamespace(
        received_messages=[_msg("not-json", "a2")]
    )
    reinsert = MagicMock(side_effect=RuntimeError("bad"))
    quarantine = MagicMock()

    stats = drain(sub, SUB, reinsert, quarantine)

    assert stats == {"pulled": 1, "reinserted": 0, "quarantined": 1}
    quarantine.assert_called_once()
    row = quarantine.call_args[0][0]
    assert row["raw"] == "not-json"
    assert "reason" in row
    sub.acknowledge.assert_called_once()


def test_drain_noop_when_empty():
    sub = MagicMock()
    sub.pull.return_value = SimpleNamespace(received_messages=[])

    stats = drain(sub, SUB, MagicMock(), MagicMock())

    assert stats == {"pulled": 0, "reinserted": 0, "quarantined": 0}
    sub.acknowledge.assert_not_called()
