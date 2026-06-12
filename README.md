# MojaWave Python SDK

A thin, typed Python client for the [MojaWave](https://mojawave.com) REST API —
send SMS (single, bulk, OTP), check credit balances, and verify webhooks across
Tanzania's telco networks (Vodacom, Tigo, Airtel, Halotel).

```bash
pip install mojawave
```

Requires Python 3.8+.

## Quickstart

```python
from mojawave import MojaWave

client = MojaWave(api_key="sk_live_mw_...")  # or set MOJAWAVE_API_KEY

msg = client.sms.send(
    to="+255753276939",
    sender="MojaWave",
    message="Hello from Mojawave! Your verification code is 1234.",
)
print(msg.id, msg.status)
```

The client reads `MOJAWAVE_API_KEY` from the environment when `api_key` is
omitted. Use an `sk_test_mw_` key for the sandbox — no real messages are sent
and no charges apply.

> **Never** expose your live API key in client-side code. Use environment
> variables and server-side requests only.

## Sending SMS

### Single message

```python
msg = client.sms.send(
    to="+255712345678",
    sender="MojaWave",                 # sender ID (≤11 alphanumeric chars); defaults to MojaWave
    message="Your code is 1234.",
    webhook_url="https://example.com/webhooks/sms",  # optional delivery receipts
    schedule_at="2026-07-01T09:00:00Z",              # optional ISO-8601 schedule
    metadata={"customer_id": "cust98765"},           # optional, echoed back
    tags=["onboarding", "verification"],             # optional
)
```

### Look up a message

```python
msg = client.sms.get("89b82624-f1a2-4f5e-85b5-102e79a06779")
if msg.delivered:
    print("Delivered at", msg.timeline.delivered_at)
elif msg.failed:
    print("Failed:", msg.failure_reason)
```

### Bulk send (up to 10,000 recipients)

Bulk jobs run asynchronously — you get a job back immediately, then poll it.

```python
job = client.sms.bulk(
    name="Marketing Campaign Q1",
    sender="MojaWave",
    message="Hello {name}, your code is {code}",
    recipients=[
        {"to": "+255712345678", "personalization": {"name": "John", "code": "ABC123"}},
        {"to": "+255712345679", "personalization": {"name": "Jane", "code": "XYZ789"}},
        "+255712345680",  # a bare string works too (no personalization)
    ],
    webhook_url="https://example.com/webhooks",
)
print(job.id, job.status, job.total_recipients)

# Poll for progress
job = client.sms.get_bulk(job.id)
print(f"{job.progress_percent}% — {job.sent_count} sent")
```

> Unicode messages have a 70-character per-segment limit (vs. 160 for plain
> SMS). Plan message length accordingly.

## Credits

```python
balances = client.credits.balance()
print(balances.sms.balance, balances.sms.is_low_balance)
print(balances.email.balance)
```

## Webhooks

MojaWave signs every webhook with an `X-MojaWave-Signature` header (HMAC-SHA256
of the raw body). Always verify against the **raw** request bytes — parsing to
JSON first can change whitespace and break the check.

```python
from mojawave import construct_event, WebhookVerificationError, SIGNATURE_HEADER

# Flask / Django view
signature = request.headers.get(SIGNATURE_HEADER)
try:
    event = construct_event(request.get_data(), signature, WEBHOOK_SECRET)
except WebhookVerificationError:
    return "Forbidden", 403

if event.type == "message.delivered":
    ...
```

Event types: `message.sent`, `message.delivered`, `message.failed`,
`credits.low`. See `examples/flask_webhook.py` for a full handler.

If you only need a boolean, use `verify_signature(payload, signature, secret)`.

## Error handling

Every documented HTTP status maps to a typed exception. All inherit from
`MojaWaveError`.

| Exception | HTTP | Code |
|---|---|---|
| `InvalidRequestError` | 400 | `invalid_request` |
| `AuthenticationError` | 401 | `unauthorized` |
| `InsufficientBalanceError` | 402 | `insufficient_balance` |
| `UnprocessableError` | 422 | `unprocessable` |
| `RateLimitError` | 429 | `rate_limit_exceeded` |
| `ServerError` | 5xx | `server_error` |
| `APIConnectionError` / `APITimeoutError` | — | transport failures |

```python
from mojawave import InsufficientBalanceError, RateLimitError

try:
    client.sms.send(to="+255712345678", message="hi")
except InsufficientBalanceError:
    ...  # top up
except RateLimitError as e:
    time.sleep(e.retry_after or 1)
```

The client automatically retries `429` and `5xx` responses with exponential
backoff (honouring `Retry-After`), controlled by `max_retries` (default 2).

## Configuration

```python
client = MojaWave(
    api_key="sk_live_mw_...",
    environment="live",        # or "sandbox"
    timeout=30.0,              # seconds
    max_retries=2,
    base_url="https://api.mojawave.com/v1",
)
```

Rate-limit headers from the most recent response are available on
`client.rate_limit` (`.limit`, `.remaining`, `.reset`). The client is usable as
a context manager to ensure the HTTP session is closed:

```python
with MojaWave() as client:
    client.sms.send(to="+255712345678", message="hi")
```

## Development

```bash
pip install -e ".[dev]"
pytest
mypy
```

## License

MIT
