import pytest
import responses

from mojawave import (
    AuthenticationError,
    InsufficientBalanceError,
    RateLimitError,
    UnprocessableError,
)

BASE = "https://api.mojawave.test/v1"


@responses.activate
def test_credits_balance(client):
    responses.get(
        f"{BASE}/credits",
        status=200,
        json={
            "success": True,
            "data": {
                "sms": {
                    "service_type": "sms",
                    "balance": 5000,
                    "total_purchased": 10000,
                    "total_consumed": 5000,
                    "low_balance_threshold": 500,
                    "is_low_balance": False,
                },
                "email": {
                    "service_type": "email",
                    "balance": 200,
                    "total_purchased": 1000,
                    "total_consumed": 800,
                    "low_balance_threshold": 100,
                    "is_low_balance": True,
                },
            },
        },
    )
    bal = client.credits.balance()
    assert bal.sms.balance == 5000
    assert bal.sms.is_low_balance is False
    assert bal.email.is_low_balance is True


@responses.activate
def test_unauthorized_raises(client):
    responses.post(
        f"{BASE}/sms/send",
        status=401,
        json={"success": False, "code": "unauthorized", "message": "Invalid API key"},
    )
    with pytest.raises(AuthenticationError) as exc:
        client.sms.send(to="+255712345678", message="hi")
    assert exc.value.code == "unauthorized"
    assert exc.value.status_code == 401


@responses.activate
def test_insufficient_balance(client):
    responses.post(
        f"{BASE}/sms/send",
        status=402,
        json={"code": "insufficient_balance", "message": "Top up needed"},
    )
    with pytest.raises(InsufficientBalanceError):
        client.sms.send(to="+255712345678", message="hi")


@responses.activate
def test_unprocessable(client):
    responses.post(
        f"{BASE}/sms/send",
        status=422,
        json={"code": "unprocessable", "message": "bad phone"},
    )
    with pytest.raises(UnprocessableError):
        client.sms.send(to="bad", message="hi")


@responses.activate
def test_rate_limit_retries_then_raises(client):
    # Two 429s exhaust the default 2 retries, then surface the error.
    for _ in range(3):
        responses.post(
            f"{BASE}/sms/send",
            status=429,
            headers={"Retry-After": "0"},
            json={"code": "rate_limit_exceeded", "message": "slow down"},
        )
    with pytest.raises(RateLimitError) as exc:
        client.sms.send(to="+255712345678", message="hi")
    assert exc.value.retry_after == 0.0
    assert len(responses.calls) == 3


@responses.activate
def test_rate_limit_headers_captured(client):
    responses.get(
        f"{BASE}/credits",
        status=200,
        headers={
            "X-RateLimit-Limit": "600",
            "X-RateLimit-Remaining": "599",
            "X-RateLimit-Reset": "1700000000",
        },
        json={"success": True, "data": {"sms": None, "email": None}},
    )
    client.credits.balance()
    rl = client.rate_limit
    assert rl.limit == 600
    assert rl.remaining == 599
