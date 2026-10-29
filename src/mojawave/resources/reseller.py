"""Reseller resource: manage customers attached to you.

Only available to accounts MojaWave has made a reseller (others get 403), and the
API key needs the ``reseller:manage`` permission.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .._transport import Transport


class ResellerResource:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def customers(self) -> List[Dict[str, Any]]:
        """Customers attached to you."""
        return self._transport.request("GET", "/reseller/customers")

    def create_customer(
        self,
        *,
        name: str,
        email: str,
        owner_name: str,
        phone: Optional[str] = None,
        business_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a customer. Its owner gets an email to set a password."""
        body = {"name": name, "email": email, "owner_name": owner_name}
        if phone is not None:
            body["phone"] = phone
        if business_type is not None:
            body["business_type"] = business_type
        return self._transport.request("POST", "/reseller/customers", json=body)

    def customer(self, customer_id: str) -> Dict[str, Any]:
        return self._transport.request("GET", f"/reseller/customers/{customer_id}")

    def set_prices(
        self,
        customer_id: str,
        tiers: Sequence[Mapping[str, Any]],
        channel: str = "sms",
    ) -> None:
        """Set what a customer pays per credit. Refused below your own cost."""
        body = {
            "channel": channel,
            "tiers": [
                {"min_credits": t["min_credits"], "price_per_credit": str(t["price_per_credit"])}
                for t in tiers
            ],
        }
        self._transport.request("PUT", f"/reseller/customers/{customer_id}/prices", json=body)

    def transfer(
        self,
        customer_id: str,
        *,
        credits: int,
        service_type: str = "sms",
        note: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move credits from your wallet to a customer's. Safe to retry with the same key."""
        body: Dict[str, Any] = {"credits": credits, "service_type": service_type}
        if note is not None:
            body["note"] = note
        return self._transport.request(
            "POST",
            f"/reseller/customers/{customer_id}/wallet/transfer",
            json=body,
            extra_headers={"Idempotency-Key": idempotency_key or str(uuid.uuid4())},
        )

    def usage(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        return self._transport.request(
            "GET", f"/reseller/customers/{customer_id}/usage", params={"days": days}
        )

    def commissions(self) -> Dict[str, Any]:
        """Commissions earned when your customers buy credits directly from MojaWave."""
        return self._transport.request("GET", "/reseller/commissions")
