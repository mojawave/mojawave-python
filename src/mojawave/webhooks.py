"""Webhook signature verification and event parsing.

MojaWave signs every webhook with an ``X-MojaWave-Signature`` header containing
an HMAC-SHA256 hex digest of the *raw* request body. Always verify against the
raw bytes — parsing to JSON first can alter whitespace and invalidate the check.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Union

from .errors import MojaWaveError
from .models import _parse_dt

SIGNATURE_HEADER = "X-MojaWave-Signature"


class WebhookVerificationError(MojaWaveError):
    """Raised when a webhook signature is missing or does not match."""


@dataclass(frozen=True)
class WebhookEvent:
    """A decoded webhook event envelope."""

    id: str
    type: str
    data: Mapping[str, Any]
    raw: Mapping[str, Any] = field(repr=False)
    created_at: Optional[datetime] = None
    livemode: Optional[bool] = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WebhookEvent":
        return cls(
            id=payload.get("id", ""),
            type=payload.get("type", ""),
            data=payload.get("data", {}),
            raw=payload,
            created_at=_parse_dt(payload.get("created_at")),
            livemode=payload.get("livemode"),
        )


def _to_bytes(payload: Union[str, bytes]) -> bytes:
    return payload.encode("utf-8") if isinstance(payload, str) else payload


def compute_signature(payload: Union[str, bytes], secret: str) -> str:
    """Compute the expected HMAC-SHA256 hex signature for ``payload``."""

    return hmac.new(
        secret.encode("utf-8"),
        _to_bytes(payload),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(
    payload: Union[str, bytes],
    signature: Optional[str],
    secret: str,
) -> bool:
    """Return ``True`` if ``signature`` matches ``payload`` signed with ``secret``.

    Uses a constant-time comparison to avoid timing attacks. Never raises for a
    bad signature — it simply returns ``False``; use :func:`construct_event` when
    you'd prefer an exception.
    """

    if not signature:
        return False
    expected = compute_signature(payload, secret)
    return hmac.compare_digest(expected, signature)


def construct_event(
    payload: Union[str, bytes],
    signature: Optional[str],
    secret: str,
) -> WebhookEvent:
    """Verify ``payload`` and return the parsed :class:`WebhookEvent`.

    Raises:
        WebhookVerificationError: if the signature is missing or invalid.
        MojaWaveError: if the verified payload is not valid JSON.
    """

    if not verify_signature(payload, signature, secret):
        raise WebhookVerificationError("Webhook signature verification failed")

    try:
        body = json.loads(_to_bytes(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise MojaWaveError("Webhook payload is not valid JSON") from exc

    return WebhookEvent.from_dict(body)
