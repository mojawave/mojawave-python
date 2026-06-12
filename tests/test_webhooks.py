import json

import pytest

from mojawave import (
    WebhookVerificationError,
    compute_signature,
    construct_event,
    verify_signature,
)

SECRET = "whsec_test"


def _payload() -> bytes:
    return json.dumps(
        {
            "id": "evt_3r9qhz7b1k",
            "type": "message.delivered",
            "created_at": "2026-04-05T12:05:01Z",
            "livemode": True,
            "data": {"id": "abc", "status": "delivered", "to": "+255753276939"},
        }
    ).encode("utf-8")


def test_verify_signature_roundtrip():
    body = _payload()
    sig = compute_signature(body, SECRET)
    assert verify_signature(body, sig, SECRET) is True
    assert verify_signature(body, "deadbeef", SECRET) is False
    assert verify_signature(body, None, SECRET) is False


def test_construct_event_ok():
    body = _payload()
    sig = compute_signature(body, SECRET)
    event = construct_event(body, sig, SECRET)
    assert event.type == "message.delivered"
    assert event.data["status"] == "delivered"
    assert event.livemode is True
    assert event.created_at is not None


def test_construct_event_bad_signature():
    with pytest.raises(WebhookVerificationError):
        construct_event(_payload(), "bad", SECRET)
