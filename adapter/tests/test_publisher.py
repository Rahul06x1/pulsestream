import json
from unittest.mock import MagicMock

from adapter.publisher import EventPublisher


def test_publish_sends_json_with_event_type_attribute():
    client = MagicMock()
    client.topic_path.return_value = "projects/p/topics/events"
    future = MagicMock()
    future.result.return_value = "msg-1"
    client.publish.return_value = future

    pub = EventPublisher("p", "events", client=client)
    msg_id = pub.publish({"event_id": "1", "event_type": "edit"})

    assert msg_id == "msg-1"
    args, kwargs = client.publish.call_args
    assert args[0] == "projects/p/topics/events"
    assert json.loads(args[1].decode()) == {"event_id": "1", "event_type": "edit"}
    assert kwargs["event_type"] == "edit"
