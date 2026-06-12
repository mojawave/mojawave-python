"""Low-level HTTP transport shared by the sync client.

This module is intentionally private. It owns the ``requests`` session,
authentication headers, retry/backoff policy, and translation of HTTP errors
into typed :mod:`mojawave.errors` exceptions. Resource classes call
:meth:`Transport.request` and receive the already-unwrapped ``data`` object.
"""

from __future__ import annotations

import random
import time
from typing import Any, Mapping, Optional

import requests

from . import __version__
from .errors import (
    APIConnectionError,
    APITimeoutError,
    MojaWaveError,
    error_from_response,
)

DEFAULT_BASE_URL = "https://api.mojawave.com/v1"


class RateLimit:
    """Snapshot of the rate-limit headers from the most recent response."""

    __slots__ = ("limit", "remaining", "reset")

    def __init__(
        self,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset: Optional[int] = None,
    ) -> None:
        self.limit = limit
        self.remaining = remaining
        self.reset = reset

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "RateLimit":
        def _int(name: str) -> Optional[int]:
            value = headers.get(name)
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        return cls(
            limit=_int("X-RateLimit-Limit"),
            remaining=_int("X-RateLimit-Remaining"),
            reset=_int("X-RateLimit-Reset"),
        )

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"RateLimit(limit={self.limit}, remaining={self.remaining}, "
            f"reset={self.reset})"
        )


class Transport:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        session: Optional[requests.Session] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = session or requests.Session()
        self._user_agent = user_agent or f"mojawave-python/{__version__}"
        self.last_rate_limit: Optional[RateLimit] = None

    # -- public API ---------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Perform a request and return the unwrapped ``data`` payload.

        Retries idempotent failures (429 and 5xx) up to ``max_retries`` times
        with exponential backoff that honours ``Retry-After`` when present.
        """

        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }

        attempt = 0
        while True:
            try:
                response = self._session.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout as exc:
                raise APITimeoutError(
                    f"Request to {url} timed out after {self.timeout}s"
                ) from exc
            except requests.exceptions.RequestException as exc:
                raise APIConnectionError(f"Could not reach MojaWave: {exc}") from exc

            self.last_rate_limit = RateLimit.from_headers(response.headers)

            if response.status_code < 400:
                return self._unwrap(response)

            # Decide whether this error is retryable.
            retryable = response.status_code == 429 or response.status_code >= 500
            if retryable and attempt < self.max_retries:
                attempt += 1
                time.sleep(self._backoff(response, attempt))
                continue

            raise self._build_error(response)

    # -- helpers ------------------------------------------------------------

    def _unwrap(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError as exc:
            raise MojaWaveError(
                "MojaWave returned a non-JSON response",
                status_code=response.status_code,
                request_id=response.headers.get("X-Request-Id"),
            ) from exc

        if isinstance(payload, Mapping) and "data" in payload:
            return payload["data"]
        return payload

    def _build_error(self, response: requests.Response) -> MojaWaveError:
        code: Optional[str] = None
        message = f"HTTP {response.status_code}"
        body: Optional[Mapping[str, Any]] = None
        try:
            body = response.json()
            if isinstance(body, Mapping):
                nested = body.get("error")
                err: Mapping[str, Any] = nested if isinstance(nested, Mapping) else body
                code = err.get("code") or body.get("code")
                message = err.get("message") or body.get("message") or message
        except ValueError:
            text = response.text.strip()
            if text:
                message = text

        return error_from_response(
            response.status_code,
            code=code,
            message=message,
            request_id=response.headers.get("X-Request-Id"),
            response=body,
            retry_after=self._retry_after(response),
        )

    def _retry_after(self, response: requests.Response) -> Optional[float]:
        header = response.headers.get("Retry-After")
        if header:
            try:
                return float(header)
            except ValueError:
                pass
        reset = response.headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delta = int(reset) - int(time.time())
                if delta > 0:
                    return float(delta)
            except ValueError:
                pass
        return None

    def _backoff(self, response: requests.Response, attempt: int) -> float:
        explicit = self._retry_after(response)
        if explicit is not None:
            return min(explicit, 30.0)
        # Exponential backoff with full jitter: base 0.5s, capped at 8s.
        return random.uniform(0, min(8.0, 0.5 * (2 ** attempt)))

    def close(self) -> None:
        self._session.close()
