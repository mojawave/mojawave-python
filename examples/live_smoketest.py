"""Live smoke test against the real MojaWave API.

Sends ONE real SMS and polls it to delivery. This costs real credits and
delivers a real message — only run with a number you own.

    export MOJAWAVE_API_KEY="sk_live_mw_..."
    export MOJAWAVE_TEST_TO="+255XXXXXXXXX"   # your own phone, E.164
    python examples/live_smoketest.py
"""

import os
import time

from mojawave import MojaWave, MojaWaveError

to = os.environ["MOJAWAVE_TEST_TO"]

with MojaWave() as client:  # reads MOJAWAVE_API_KEY
    # 1. Auth + balance check (cheap, proves the key works).
    bal = client.credits.balance()
    print(f"✓ Auth OK — SMS credits: {bal.sms.balance}")
    if bal.sms.balance < 1:
        raise SystemExit("Not enough credits to run the live test.")

    # 2. Send one real message.
    msg = client.sms.send(
        to=to,
        message="MojaWave SDK live smoke test ✅",
    )
    print(f"✓ Sent {msg.id} — status={msg.status}, cost={msg.credits_cost}")

    # 3. Poll until delivered/failed (or give up after ~30s).
    for _ in range(15):
        time.sleep(2)
        try:
            current = client.sms.get(msg.id)
        except MojaWaveError as e:
            print(f"  lookup error: {e}")
            continue
        print(f"  status={current.status}")
        if current.status == "delivered":
            print(f"✓ Delivered at {current.timeline.delivered_at}")
            break
        if current.status == "failed":
            print(f"✗ Failed: {current.failure_reason}")
            break
    else:
        print("… still pending after 30s — check the dashboard.")

    rl = client.rate_limit
    if rl:
        print(f"Rate limit: {rl.remaining}/{rl.limit} remaining")
