"""Exception types raised by the MojaWave SDK.

Every error returned by the API carries a machine-readable ``code`` and a
human-readable ``message``. We map each documented HTTP status onto a dedicated
exception subclass so callers can catch precisely what they care about while
still being able to fall back to :class:`MojaWaveError`.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


class MojaWaveError(Exception):
    """Base class for every error raised by the SDK.

    Attributes:
        message: Human-readable description of what went wrong.
        code: Machine-readable error code from the API (e.g. ``invalid_request``),
            or ``None`` for transport-level failures.
        status_code: HTTP status code, or ``None`` if the request never completed.
        request_id: The ``X-Request-Id`` response header, when present. Useful when
            contacting MojaWave support.
        response: The raw decoded JSON body, when available.
    """

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        response: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.request_id = request_id
        self.response = response

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        parts = [self.message]
        if self.code:
            parts.append(f"code={self.code}")
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " | ".join(parts)


class APIConnectionError(MojaWaveError):
    """The request could not reach MojaWave (network failure, DNS, timeout)."""


class APITimeoutError(APIConnectionError):
    """The request exceeded the configured timeout."""


class InvalidRequestError(MojaWaveError):
    """400 — required parameters are missing or malformed."""


class AuthenticationError(MojaWaveError):
    """401 — the API key is missing or invalid."""


class InsufficientBalanceError(MojaWaveError):
    """402 — the account balance is too low to complete the request."""


class UnprocessableError(MojaWaveError):
    """422 — the request body failed validation."""


class RateLimitError(MojaWaveError):
    """429 — too many requests; back off and retry.

    Attributes:
        retry_after: Seconds to wait before retrying, derived from the
            ``Retry-After`` or ``X-RateLimit-Reset`` headers when available.
    """

    def __init__(self, *args: Any, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class ServerError(MojaWaveError):
    """5xx — something went wrong on MojaWave's end."""


# Maps documented API error codes / HTTP statuses onto exception classes.
_STATUS_TO_EXCEPTION = {
    400: InvalidRequestError,
    401: AuthenticationError,
    402: InsufficientBalanceError,
    422: UnprocessableError,
    429: RateLimitError,
}


def error_from_response(
    status_code: int,
    *,
    code: Optional[str],
    message: str,
    request_id: Optional[str] = None,
    response: Optional[Mapping[str, Any]] = None,
    retry_after: Optional[float] = None,
) -> MojaWaveError:
    """Build the most specific :class:`MojaWaveError` for an HTTP response."""

    kwargs: dict[str, Any] = dict(
        code=code,
        status_code=status_code,
        request_id=request_id,
        response=response,
    )

    if status_code == 429:
        return RateLimitError(message, retry_after=retry_after, **kwargs)
    if status_code >= 500:
        return ServerError(message, **kwargs)

    exc_class = _STATUS_TO_EXCEPTION.get(status_code, MojaWaveError)
    return exc_class(message, **kwargs)
