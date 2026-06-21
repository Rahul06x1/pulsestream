import pytest

from mapper.validation import ValidationError, validate_event

VALID = {
    "event_id": "1",
    "event_type": "edit",
    "wiki": "enwiki",
    "occurred_at": "2023-11-14T22:13:20Z",
    "bot": False,
}


def test_valid_event_passes():
    validate_event(VALID)  # should not raise


def test_missing_required_field_fails():
    bad = {k: v for k, v in VALID.items() if k != "wiki"}
    with pytest.raises(ValidationError):
        validate_event(bad)


def test_empty_event_id_fails():
    with pytest.raises(ValidationError):
        validate_event({**VALID, "event_id": ""})
