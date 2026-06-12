"""Credits resource: check SMS and email balances."""

from __future__ import annotations

from .._transport import Transport
from ..models import CreditBalances


class CreditsResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def balance(self) -> CreditBalances:
        """Retrieve SMS and email credit balances in a single call."""

        data = self._transport.request("GET", "/credits")
        return CreditBalances.from_dict(data)
