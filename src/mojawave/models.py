"""Typed response models for the MojaWave API.

Each model is a frozen dataclass built from the JSON ``data`` object of a
response. Unknown fields are preserved on ``.raw`` so that new API fields never
break deserialization — callers can always reach through to the original dict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Mapping, Optional


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp (including trailing ``Z``) into a datetime."""

    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class Timeline:
    """Delivery checkpoints for a message."""

    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> "Timeline":
        data = data or {}
        return cls(
            queued_at=_parse_dt(data.get("queued_at")),
            sent_at=_parse_dt(data.get("sent_at")),
            delivered_at=_parse_dt(data.get("delivered_at")),
        )


@dataclass(frozen=True)
class Message:
    """A single SMS message resource.

    The same shape is returned by ``sms.send`` and ``messages.get``; fields that
    a given endpoint omits are left as ``None``.
    """

    id: str
    status: str
    raw: Mapping[str, Any] = field(repr=False)
    type: Optional[str] = None
    to: Optional[str] = None
    sender: Optional[str] = None
    body: Optional[str] = None
    segments: Optional[int] = None
    credits_cost: Optional[float] = None
    timeline: Timeline = field(default_factory=Timeline)
    failure_reason: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Message":
        # The send endpoint returns the timeline flattened onto the top level;
        # the get endpoint nests it under "timeline". Support both.
        timeline_data = data.get("timeline")
        if timeline_data is None and ("queued_at" in data or "sent_at" in data):
            timeline_data = {
                "queued_at": data.get("queued_at"),
                "sent_at": data.get("sent_at"),
                "delivered_at": data.get("delivered_at"),
            }
        return cls(
            id=data["id"],
            status=data["status"],
            raw=data,
            type=data.get("type"),
            to=data.get("to"),
            sender=data.get("from"),
            body=data.get("body") or data.get("message"),
            segments=data.get("segments"),
            credits_cost=data.get("credits_cost"),
            timeline=Timeline.from_dict(timeline_data),
            failure_reason=data.get("failure_reason"),
            metadata=data.get("metadata"),
        )

    @property
    def delivered(self) -> bool:
        return self.status == "delivered"

    @property
    def failed(self) -> bool:
        return self.status == "failed"


@dataclass(frozen=True)
class BulkJob:
    """A bulk SMS job, returned by ``sms.bulk`` and ``sms.get_bulk``."""

    id: str
    status: str
    raw: Mapping[str, Any] = field(repr=False)
    name: Optional[str] = None
    total_recipients: Optional[int] = None
    sent_count: Optional[int] = None
    progress_percent: Optional[float] = None
    estimated_credits: Optional[float] = None
    total_credits_cost: Optional[float] = None
    has_personalization: Optional[bool] = None
    personalization_fields: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BulkJob":
        # ``sms.bulk`` returns the identifier as ``job_id``; ``get_bulk`` as ``id``.
        job_id = data.get("id") or data.get("job_id")
        if job_id is None:
            raise KeyError("bulk job response is missing both 'id' and 'job_id'")
        return cls(
            id=job_id,
            status=data["status"],
            raw=data,
            name=data.get("name"),
            total_recipients=data.get("total_recipients"),
            sent_count=data.get("sent_count"),
            progress_percent=data.get("progress_percent"),
            estimated_credits=data.get("estimated_credits"),
            total_credits_cost=data.get("total_credits_cost"),
            has_personalization=data.get("has_personalization"),
            personalization_fields=data.get("personalization_fields"),
            scheduled_at=_parse_dt(data.get("scheduled_at")),
            created_at=_parse_dt(data.get("created_at")),
            completed_at=_parse_dt(data.get("completed_at")),
        )

    @property
    def is_complete(self) -> bool:
        return self.status in ("completed", "failed")


@dataclass(frozen=True)
class ServiceCredits:
    """Credit balance for a single service (``sms`` or ``email``)."""

    service_type: str
    balance: int
    raw: Mapping[str, Any] = field(repr=False)
    total_purchased: Optional[int] = None
    total_consumed: Optional[int] = None
    low_balance_threshold: Optional[int] = None
    is_low_balance: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ServiceCredits":
        return cls(
            service_type=data["service_type"],
            balance=data["balance"],
            raw=data,
            total_purchased=data.get("total_purchased"),
            total_consumed=data.get("total_consumed"),
            low_balance_threshold=data.get("low_balance_threshold"),
            is_low_balance=data.get("is_low_balance"),
        )


@dataclass(frozen=True)
class CreditBalances:
    """Credit balances across all services, returned by ``credits.balance``."""

    sms: Optional[ServiceCredits]
    email: Optional[ServiceCredits]
    raw: Mapping[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CreditBalances":
        return cls(
            sms=ServiceCredits.from_dict(data["sms"]) if data.get("sms") else None,
            email=ServiceCredits.from_dict(data["email"]) if data.get("email") else None,
            raw=data,
        )
