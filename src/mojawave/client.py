"""The public :class:`MojaWave` client — the main entry point to the SDK."""

from __future__ import annotations

import os
from typing import Optional

import requests

from ._transport import DEFAULT_BASE_URL, RateLimit, Transport
from .resources import CreditsResource, SMSResource

# Environments share a host; the key prefix (sk_live_ / sk_test_) selects live
# vs. sandbox server-side. We keep the enum for clarity and forward-compat.
_ENVIRONMENTS = {"live", "sandbox"}


class MojaWave:
    """Client for the MojaWave REST API.

    Example:
        >>> from mojawave import MojaWave
        >>> client = MojaWave(api_key="sk_test_mw_...")
        >>> msg = client.sms.send(to="+255712345678", message="Hi!")
        >>> print(msg.status)

    Args:
        api_key: Your MojaWave API key. Falls back to the ``MOJAWAVE_API_KEY``
            environment variable when omitted.
        environment: ``"live"`` or ``"sandbox"``. Informational; the key prefix
            is what actually selects the environment server-side.
        base_url: Override the API base URL (useful for testing/self-hosting).
        timeout: Per-request timeout in seconds.
        max_retries: How many times to retry 429 / 5xx responses with backoff.
        session: An existing ``requests.Session`` to reuse (e.g. for custom
            adapters, proxies, or connection pooling).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        environment: str = "live",
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        session: Optional[requests.Session] = None,
    ) -> None:
        api_key = api_key or os.environ.get("MOJAWAVE_API_KEY")
        if not api_key:
            raise ValueError(
                "An API key is required. Pass api_key=... or set the "
                "MOJAWAVE_API_KEY environment variable."
            )
        if environment not in _ENVIRONMENTS:
            raise ValueError(
                f"environment must be one of {sorted(_ENVIRONMENTS)}, got {environment!r}"
            )

        self.environment = environment
        self._transport = Transport(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            session=session,
        )

        self.sms = SMSResource(self._transport)
        self.credits = CreditsResource(self._transport)

    @property
    def rate_limit(self) -> Optional[RateLimit]:
        """Rate-limit headers from the most recent response, if any."""

        return self._transport.last_rate_limit

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._transport.close()

    def __enter__(self) -> "MojaWave":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
