"""Local webhook receiver to watch real MojaWave delivery events.

No Flask required — uses only the standard library. It verifies the
X-MojaWave-Signature on every request and prints each event.

  1. Set your webhook signing secret (from the MojaWave dashboard):
        export MOJAWAVE_WEBHOOK_SECRET="whsec_..."
     (Leave it unset to skip verification while experimenting.)

  2. Start this listener:
        python examples/webhook_listener.py            # listens on :4242

  3. Expose it to the internet so MojaWave can reach it:
        ngrok http 4242
     ...and copy the https URL ngrok prints, e.g.
        https://ab12cd34.ngrok-free.app

  4. Send an SMS with that URL as webhook_url (see send_with_webhook.py),
     then watch events land here.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from mojawave import SIGNATURE_HEADER, construct_event, verify_signature

PORT = int(os.environ.get("PORT", "4242"))
SECRET = os.environ.get("MOJAWAVE_WEBHOOK_SECRET")  # None => skip verification


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)  # RAW bytes — needed for signature check
        signature = self.headers.get(SIGNATURE_HEADER)

        if SECRET:
            if not verify_signature(raw, signature, SECRET):
                print("✗ signature verification FAILED — rejecting (403)")
                self.send_response(403)
                self.end_headers()
                return
            event = construct_event(raw, signature, SECRET)
            payload = event.raw
            etype, data = event.type, event.data
        else:
            payload = json.loads(raw or b"{}")
            etype = payload.get("type", "?")
            data = payload.get("data", {})
            print("  (verification skipped — no MOJAWAVE_WEBHOOK_SECRET set)")

        print(f"\n📨 {etype}")
        print(f"   message id: {data.get('id')}")
        print(f"   status:     {data.get('status')}")
        if data.get("to"):
            print(f"   to:         {data.get('to')}")
        if data.get("failure_reason"):
            print(f"   reason:     {data.get('failure_reason')}")

        # Always 200 so MojaWave marks the event delivered.
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args: object) -> None:  # silence default access log
        pass


if __name__ == "__main__":
    mode = "verifying signatures" if SECRET else "NOT verifying (no secret set)"
    print(f"Listening on http://0.0.0.0:{PORT}  ({mode})")
    print("Expose with:  ngrok http", PORT)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
