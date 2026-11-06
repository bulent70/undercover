import pytest

from backend import db

CLAIM = "/api/claims/CLM-1001"


def approve(client, payout):
    client.post(f"{CLAIM}/start")
    return client.post(
        f"{CLAIM}/decision",
        json={
            "decision": "approve",
            "payout": payout,
            "reason": "Covered delay.",
            "section": "3. Trip Delay",
        },
    )


def test_start_claim(client):
    response = client.post(f"{CLAIM}/start")
    assert response.json()["status"] == "in_progress"
    assert client.post(f"{CLAIM}/start").status_code == 200


def test_start_unknown_claim(client):
    assert client.post("/api/claims/CLM-9999/start").status_code == 404


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_decline_or_refer_decides_the_claim(client, decision):
    client.post(f"{CLAIM}/start")
    response = client.post(
        f"{CLAIM}/decision",
        json={"decision": decision, "payout": 0, "reason": "No.", "section": "9."},
    )
    claim = response.json()
    assert claim["status"] == "decided"
    assert claim["decision"]["decision"] == decision
    assert client.post(f"{CLAIM}/start").status_code == 409


def test_decide_needs_the_claim_in_progress(client):
    response = client.post(
        f"{CLAIM}/decision",
        json={"decision": "decline", "payout": 0, "reason": "No.", "section": "9."},
    )
    assert response.status_code == 409


def test_payout_must_match_the_decision(client):
    client.post(f"{CLAIM}/start")
    response = client.post(
        f"{CLAIM}/decision",
        json={"decision": "decline", "payout": 50, "reason": "No.", "section": "9."},
    )
    assert response.status_code == 422


def test_approve_and_pay(client):
    assert approve(client, 420.0).json()["status"] == "in_progress"
    claim = client.post(f"{CLAIM}/payment", json={"amount": 420.0}).json()
    assert claim["status"] == "decided"
    assert claim["payment"]["amount"] == 420.0
    assert claim["payment"]["handler_id"] is None
    assert client.post(f"{CLAIM}/payment", json={"amount": 420.0}).status_code == 409


def test_payment_over_the_limit_waits_for_signoff(client):
    assert approve(client, 1250.0).json()["status"] == "waiting_for_signoff"
    response = client.post(f"{CLAIM}/payment", json={"amount": 1250.0})
    assert response.status_code == 409
    assert "sign-off" in response.json()["detail"]
    assert client.get(CLAIM).json()["payment"] is None


def test_payment_must_equal_the_payout(client):
    approve(client, 420.0)
    response = client.post(f"{CLAIM}/payment", json={"amount": 500.0})
    assert response.status_code == 409
    assert client.get(CLAIM).json()["payment"] is None


def test_payment_needs_an_approval(client):
    assert client.post(f"{CLAIM}/payment", json={"amount": 10}).status_code == 409


def test_sign_off_pays(client):
    approve(client, 1250.0)
    claim = client.post(f"{CLAIM}/sign-off", json={"handler_id": "HND-01"}).json()
    assert claim["status"] == "decided"
    assert claim["payment"]["amount"] == 1250.0
    assert claim["payment"]["handler_id"] == "HND-01"
    assert claim["payment"]["paid_at"]


def test_sign_off_needs_a_claim_waiting_for_it(client):
    approve(client, 420.0)
    response = client.post(f"{CLAIM}/sign-off", json={"handler_id": "HND-01"})
    assert response.status_code == 409


def test_sign_off_needs_a_known_handler(client):
    approve(client, 1250.0)
    response = client.post(f"{CLAIM}/sign-off", json={"handler_id": "HND-99"})
    assert response.status_code == 404


def test_sign_off_needs_a_handler_who_may(client):
    approve(client, 1250.0)
    connection = db.connect()
    connection.execute(
        "UPDATE handlers SET record = json_set(record, '$.can_approve_over_limit',"
        " json('false')) WHERE handler_id = 'HND-03'"
    )
    connection.commit()
    response = client.post(f"{CLAIM}/sign-off", json={"handler_id": "HND-03"})
    assert response.status_code == 403


def test_steps_come_back_in_order(client):
    for text in ("first", "second", "third"):
        client.post(f"{CLAIM}/steps", json={"kind": "model", "text": text})
    steps = client.get(f"{CLAIM}/steps").json()
    assert [step["text"] for step in steps] == ["first", "second", "third"]
    assert client.get("/api/claims/CLM-9999/steps").status_code == 404
