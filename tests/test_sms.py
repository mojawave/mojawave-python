import responses

from mojawave import Message, BulkJob

BASE = "https://api.mojawave.test/v1"


@responses.activate
def test_send_sms(client):
    responses.post(
        f"{BASE}/sms/send",
        status=201,
        json={
            "success": True,
            "data": {
                "id": "89b82624-f1a2-4f5e-85b5-102e79a06779",
                "type": "sms",
                "to": "+255753276939",
                "status": "sent",
                "segments": 1,
                "credits_cost": 1,
                "queued_at": "2026-04-05T12:03:04.485Z",
                "sent_at": "2026-04-05T12:04:04.393Z",
            },
        },
    )

    msg = client.sms.send(
        to="+255753276939",
        message="Hello!",
        sender="MojaWave",
        metadata={"customer_id": "cust98765"},
        tags=["onboarding"],
    )

    assert isinstance(msg, Message)
    assert msg.status == "sent"
    assert msg.segments == 1
    # Flattened timeline is normalized onto the Timeline object.
    assert msg.timeline.queued_at is not None
    assert msg.timeline.sent_at is not None

    sent = responses.calls[0].request
    assert sent.headers["Authorization"] == "Bearer sk_test_mw_unit"
    import json

    body = json.loads(sent.body)
    assert body["from"] == "MojaWave"
    assert body["metadata"] == {"customer_id": "cust98765"}
    assert body["tags"] == ["onboarding"]


@responses.activate
def test_get_message(client):
    mid = "89b82624-f1a2-4f5e-85b5-102e79a06779"
    responses.get(
        f"{BASE}/messages/{mid}",
        status=200,
        json={
            "success": True,
            "data": {
                "id": mid,
                "type": "sms",
                "status": "delivered",
                "credits_cost": 1,
                "timeline": {
                    "queued_at": "2026-04-05T12:03:04.485Z",
                    "sent_at": "2026-04-05T12:04:04.393Z",
                    "delivered_at": "2026-04-05T12:05:06.751Z",
                },
            },
        },
    )

    msg = client.sms.get(mid)
    assert msg.delivered is True
    assert msg.timeline.delivered_at is not None


@responses.activate
def test_bulk_send(client):
    responses.post(
        f"{BASE}/sms/bulk",
        status=202,
        json={
            "success": True,
            "data": {
                "job_id": "ec0fb57c-8b90-4e21-9f96-48235d6a05ac",
                "status": "scheduled",
                "total_recipients": 2,
                "estimated_credits": 2,
                "has_personalization": True,
                "personalization_fields": ["code", "name"],
            },
        },
    )

    job = client.sms.bulk(
        name="Q1",
        message="Hi {name}, code {code}",
        sender="MOJAWAVE",
        recipients=[
            {"to": "+255712345678", "personalization": {"name": "John", "code": "A1"}},
            "+255712345679",
        ],
    )
    assert isinstance(job, BulkJob)
    # job_id is mapped onto .id
    assert job.id == "ec0fb57c-8b90-4e21-9f96-48235d6a05ac"
    assert job.total_recipients == 2
    assert job.is_complete is False


@responses.activate
def test_get_bulk(client):
    jid = "ec0fb57c-8b90-4e21-9f96-48235d6a05ac"
    responses.get(
        f"{BASE}/sms/bulk/{jid}",
        status=200,
        json={
            "success": True,
            "data": {
                "id": jid,
                "name": "Q1",
                "status": "completed",
                "total_recipients": 2,
                "sent_count": 2,
                "progress_percent": 100.0,
                "total_credits_cost": 2,
                "completed_at": "2026-04-05T12:08:09.610Z",
            },
        },
    )
    job = client.sms.get_bulk(jid)
    assert job.is_complete is True
    assert job.progress_percent == 100.0
    assert job.completed_at is not None
