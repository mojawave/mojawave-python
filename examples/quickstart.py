"""Minimal end-to-end example. Run with MOJAWAVE_API_KEY set in your env."""

from mojawave import MojaWave, InsufficientBalanceError

client = MojaWave()  # reads MOJAWAVE_API_KEY

# Check balance first.
balances = client.credits.balance()
print(f"SMS credits remaining: {balances.sms.balance}")

# Send a single message.
try:
    msg = client.sms.send(
        to="+255753276939",
        sender="MojaWave",
        message="Hello from Mojawave! Your code is 1234.",
        metadata={"customer_id": "cust98765"},
    )
    print(f"Sent {msg.id} — status={msg.status}, cost={msg.credits_cost}")
except InsufficientBalanceError:
    print("Top up your account to send messages.")

# Bulk send with per-recipient personalization.
job = client.sms.bulk(
    name="Marketing Campaign Q1",
    sender="MojaWave",
    message="Hello {name}, your code is {code}",
    recipients=[
        {"to": "+255712345678", "personalization": {"name": "John", "code": "ABC123"}},
        {"to": "+255712345679", "personalization": {"name": "Jane", "code": "XYZ789"}},
    ],
)
print(f"Bulk job {job.id}: {job.status} ({job.total_recipients} recipients)")
