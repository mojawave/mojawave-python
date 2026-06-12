"""MojaWave Python SDK.

A thin, typed client for the MojaWave REST API — send SMS (single, bulk, OTP),
check credit balances, and verify webhooks.

    from mojawave import MojaWave

    client = MojaWave(api_key="sk_live_mw_...")
    client.sms.send(to="+255712345678", message="Hello!")
"""

from __future__ import annotations

__version__ = "1.0.0"

from .client import MojaWave
from .errors import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InsufficientBalanceError,
    InvalidRequestError,
    MojaWaveError,
    RateLimitError,
    ServerError,
    UnprocessableError,
)
from .models import (
    BulkJob,
    CreditBalances,
    Message,
    ServiceCredits,
    Timeline,
)
from .webhooks import (
    SIGNATURE_HEADER,
    WebhookEvent,
    WebhookVerificationError,
    compute_signature,
    construct_event,
    verify_signature,
)

__all__ = [
    "__version__",
    "MojaWave",
    # errors
    "MojaWaveError",
    "APIConnectionError",
    "APITimeoutError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "InvalidRequestError",
    "RateLimitError",
    "ServerError",
    "UnprocessableError",
    # models
    "BulkJob",
    "CreditBalances",
    "Message",
    "ServiceCredits",
    "Timeline",
    # webhooks
    "SIGNATURE_HEADER",
    "WebhookEvent",
    "WebhookVerificationError",
    "compute_signature",
    "construct_event",
    "verify_signature",
]
