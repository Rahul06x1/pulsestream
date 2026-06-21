from adapter.normalize import normalize

RAW = {
    "id": 12345,
    "type": "edit",
    "title": "Main Page",
    "user": "Alice",
    "bot": False,
    "wiki": "enwiki",
    "timestamp": 1700000000,
    "meta": {"id": "uuid-abc", "dt": "2023-11-14T22:13:20Z"},
}


def test_normalize_maps_core_fields():
    event = normalize(RAW)
    assert event["event_id"] == "uuid-abc"
    assert event["event_type"] == "edit"
    assert event["wiki"] == "enwiki"
    assert event["title"] == "Main Page"
    assert event["user"] == "Alice"
    assert event["occurred_at"] == "2023-11-14T22:13:20Z"
    assert event["bot"] is False


def test_normalize_falls_back_to_timestamp_when_no_meta_dt():
    raw = {**RAW, "meta": {"id": "x"}}
    event = normalize(raw)
    assert event["occurred_at"].startswith("2023-11-14T")


def test_normalize_handles_missing_fields():
    event = normalize({"meta": {"id": "y"}})
    assert event["event_id"] == "y"
    assert event["event_type"] == "unknown"
    assert event["wiki"] == "unknown"
    assert event["bot"] is False
