"""SMS resource: single send, bulk send, and message/job lookups."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional, Sequence, Union

from .._transport import Transport
from ..models import BulkJob, Message

# A recipient for a bulk send may be a bare phone string or a dict carrying
# ``to`` plus a ``personalization`` mapping.
Recipient = Union[str, Mapping[str, Any]]


def _normalize_recipient(recipient: Recipient) -> Mapping[str, Any]:
    if isinstance(recipient, str):
        return {"to": recipient}
    if "to" not in recipient:
        raise ValueError("each recipient dict must include a 'to' key")
    return recipient


class SMSResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def send(
        self,
        *,
        to: str,
        message: str,
        sender: str = "MojaWave",
        webhook_url: Optional[str] = None,
        schedule_at: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> Message:
        """Send a single SMS.

        Args:
            to: Recipient phone in E.164 format, e.g. ``+255712345678``.
            message: Message content. Long messages are split into segments.
            sender: Sender ID (max 11 alphanumeric chars) or ``MOJAWAVE``. Sent to
                the API as the ``from`` field.
            webhook_url: URL to receive delivery-status webhooks for this message.
            schedule_at: ISO-8601 timestamp for scheduled delivery.
            metadata: Custom key-value pairs echoed back for your own tracking.
            tags: Optional labels for categorising the message.

        Returns:
            The created :class:`~mojawave.models.Message`.
        """

        body: dict[str, Any] = {"to": to, "from": sender, "message": message}
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if schedule_at is not None:
            body["schedule_at"] = schedule_at
        if metadata is not None:
            body["metadata"] = dict(metadata)
        if tags is not None:
            body["tags"] = list(tags)

        data = self._transport.request("POST", "/sms/send", json=body)
        return Message.from_dict(data)

    def get(self, message_id: str) -> Message:
        """Retrieve full details of a message, including its delivery timeline."""

        data = self._transport.request("GET", f"/messages/{message_id}")
        return Message.from_dict(data)

    def bulk(
        self,
        *,
        recipients: Iterable[Recipient],
        message: str,
        sender: str = "MojaWave",
        name: Optional[str] = None,
        webhook_url: Optional[str] = None,
        schedule_at: Optional[str] = None,
    ) -> BulkJob:
        """Send the same message to many recipients (up to 10,000) in one call.

        Bulk jobs are processed asynchronously: a :class:`~mojawave.models.BulkJob`
        is returned immediately. Poll :meth:`get_bulk` for progress.

        Each recipient may be a phone-number string, or a dict with ``to`` and a
        ``personalization`` mapping whose keys are interpolated into ``message``.
        """

        normalized: List[Mapping[str, Any]] = [
            _normalize_recipient(r) for r in recipients
        ]
        if not normalized:
            raise ValueError("bulk() requires at least one recipient")

        body: dict[str, Any] = {
            "from": sender,
            "message": message,
            "recipients": normalized,
        }
        if name is not None:
            body["name"] = name
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if schedule_at is not None:
            body["schedule_at"] = schedule_at

        data = self._transport.request("POST", "/sms/bulk", json=body)
        return BulkJob.from_dict(data)

    def get_bulk(self, job_id: str) -> BulkJob:
        """Retrieve status, progress, and statistics for a bulk SMS job."""

        data = self._transport.request("GET", f"/sms/bulk/{job_id}")
        return BulkJob.from_dict(data)
