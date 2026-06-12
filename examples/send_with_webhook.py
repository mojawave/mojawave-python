"""Send one SMS that reports its delivery status to your webhook URL.

Run webhook_listener.py + ngrok first, then:

    export MOJAWAVE_API_KEY="sk_live_mw_..."
    export MOJAWAVE_TEST_TO="+255753276939"
    export MOJAWAVE_WEBHOOK_URL="https://ab12cd34.ngrok-free.app"
    python examples/send_with_webhook.py

Watch the listener terminal — a message.delivered (or message.failed)
event arrives once the telco returns a receipt.
"""

import os

from mojawave import MojaWave

with MojaWave() as client:  # reads MOJAWAVE_API_KEY
    msg = client.sms.send(
        to=os.environ["MOJAWAVE_TEST_TO"],
        sender="MojaWave",
        message="Webhook delivery test from the MojaWave SDK.",
        webhook_url=os.environ["MOJAWAVE_WEBHOOK_URL"],
    )
    print(f"Sent {msg.id} (status={msg.status}).")
    print("Now watch your webhook_listener terminal for delivery events.")
