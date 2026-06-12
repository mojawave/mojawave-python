"""Sample script to test the MojaWave SDK against the real API.

Setup:
    pip install mojawave        # or: pip install --break-system-packages mojawave

Edit the two values below (or set them as env vars), then run:
    python test_sdk.py
"""

import os
import time

from mojawave import MojaWave, MojaWaveError

# --- configure these -------------------------------------------------------
API_KEY = os.environ.get("MOJAWAVE_API_KEY", "sk_test_mw_PASTE_YOUR_KEY")
TO = os.environ.get("MOJAWAVE_TEST_TO", "+255XXXXXXXXX")  # your own phone, E.164
# ---------------------------------------------------------------------------


def main() -> None:
    client = MojaWave(api_key=API_KEY)

    # 1. Check credit balance (cheap call — proves your key works).
    print("→ Checking credits...")
    balances = client.credits.balance()
    print(f"  SMS credits:   {balances.sms.balance}")
    print(f"  Email credits: {balances.email.balance if balances.email else 'n/a'}")

    # 2. Send a single SMS.
    print(f"\n→ Sending SMS to {TO}...")
    msg = client.sms.send(
        to=TO,
        sender="MojaWave",
        message="Hello from the MojaWave Python SDK! Your code is 1234.",
        metadata={"customer_id": "test-001"},
    )
    print(f"  id:     {msg.id}")
    print(f"  status: {msg.status}")
    print(f"  cost:   {msg.credits_cost} credit(s)")

    # 3. Poll the message until it's delivered (or failed).
    print("\n→ Polling delivery status...")
    for _ in range(10):
        time.sleep(10)
        current = client.sms.get(msg.id)
        print(f"  status: {current.status}")
        if current.status == "delivered":
            print(f"  ✓ delivered at {current.timeline.delivered_at}")
            break
        if current.status == "failed":
            print(f"  ✗ failed: {current.failure_reason}")
            break
    else:
        print("  … still pending — check the dashboard.")

    # 4. Show rate-limit headroom from the last response.
    rl = client.rate_limit
    if rl:
        print(f"\nRate limit: {rl.remaining}/{rl.limit} requests remaining")

    client.close()


if __name__ == "__main__":
    try:
        main()
    except MojaWaveError as exc:
        # Every API error is a MojaWaveError subclass with a code + message.
        print(f"\nAPI error: {exc}")
