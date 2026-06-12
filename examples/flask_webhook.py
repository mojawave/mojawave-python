"""Receive and verify MojaWave webhooks with Flask.

    pip install flask
    MOJAWAVE_WEBHOOK_SECRET=whsec_... python examples/flask_webhook.py
"""

import os

from flask import Flask, request

from mojawave import SIGNATURE_HEADER, WebhookVerificationError, construct_event

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["MOJAWAVE_WEBHOOK_SECRET"]


@app.post("/webhooks/mojawave")
def handle_webhook():
    signature = request.headers.get(SIGNATURE_HEADER)
    try:
        # Verify against the RAW body — never the parsed JSON.
        event = construct_event(request.get_data(), signature, WEBHOOK_SECRET)
    except WebhookVerificationError:
        return "Forbidden", 403

    if event.type == "message.delivered":
        print(f"Delivered: {event.data['id']} -> {event.data['to']}")
    elif event.type == "message.failed":
        print(f"Failed: {event.data['id']} ({event.data.get('failure_reason')})")
    elif event.type == "credits.low":
        print("Credit balance is low — top up soon.")

    return "", 204


if __name__ == "__main__":
    app.run(port=4242)
