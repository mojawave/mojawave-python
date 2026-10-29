import json

import responses

BASE = "https://api.mojawave.test/v1"


@responses.activate
def test_create_customer_maps_fields(client):
    responses.post(f"{BASE}/reseller/customers", status=201, json={"data": {"id": "c1", "name": "FPCT"}})
    c = client.reseller.create_customer(name="FPCT", email="a@b.co", owner_name="Head Teacher")
    assert c["id"] == "c1"
    assert json.loads(responses.calls[0].request.body) == {"name": "FPCT", "email": "a@b.co", "owner_name": "Head Teacher"}


@responses.activate
def test_transfer_always_carries_an_idempotency_key(client):
    responses.post(f"{BASE}/reseller/customers/c1/wallet/transfer", status=201,
                   json={"data": {"transfer_id": "t1", "credits": 500, "your_balance": 1500}})
    r = client.reseller.transfer("c1", credits=500)
    assert r["your_balance"] == 1500
    assert responses.calls[0].request.headers["Idempotency-Key"]


@responses.activate
def test_set_prices_sends_strings(client):
    responses.put(f"{BASE}/reseller/customers/c1/prices", json={"data": {"updated": True}})
    client.reseller.set_prices("c1", [{"min_credits": 1, "price_per_credit": 15}])
    body = json.loads(responses.calls[0].request.body)
    assert body["tiers"] == [{"min_credits": 1, "price_per_credit": "15"}]
