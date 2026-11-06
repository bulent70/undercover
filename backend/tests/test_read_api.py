EVAL_FIELDS = {"failure_class", "difficulty", "tiny", "needs", "over_approval_limit"}


def test_list_claims(client):
    claims = client.get("/api/claims").json()
    assert len(claims) == 25
    assert set(claims[0]) >= {
        "claim_id",
        "summary",
        "claim_type",
        "amount_claimed",
        "status",
    }
    assert {claim["status"] for claim in claims} == {"waiting"}


def test_get_claim(client):
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["story"].startswith("My flight home from Rome")
    assert len(claim["items"]) == 3
    assert len(claim["documents"]) == 4
    assert claim["status"] == "waiting"
    assert claim["decision"] is None
    assert claim["payment"] is None


def test_unknown_claim(client):
    assert client.get("/api/claims/CLM-9999").status_code == 404


def test_get_policy(client):
    policy = client.get("/api/policies/POL-2001").json()
    assert policy["plan"] == "premium"


def test_claim_history_has_no_contact_details(client):
    response = client.get("/api/customers/CUS-3001/claims")
    history = response.json()
    assert history[0]["claim_id"] == "CLM-0412"
    for field in ("email", "phone", "address", "maya.patel"):
        assert field not in response.text


def test_get_plan(client):
    plan = client.get("/api/plans/premium").json()
    assert plan["trip_delay_max"] == 800.0
    assert plan["deductible"] == 50.0
    assert plan["deductible_applies_to"] == ["baggage", "emergency_medical"]
    assert len(plan["add_ons"]) == 3


def test_unknown_plan(client):
    assert client.get("/api/plans/platinum").status_code == 404


def test_policy_wording_and_instructions(client):
    wording = client.get("/api/policy-wording").json()["text"]
    assert wording.startswith("# UnderCover Travel Insurance: Policy Wording")
    instructions = client.get("/api/instructions").json()["text"]
    assert instructions.startswith("# The UnderCover Agent")


def test_list_handlers(client):
    handlers = client.get("/api/handlers").json()
    assert [handler["name"] for handler in handlers][0] == "Dana Whitfield"


def keys(value):
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in keys(item)}
    return set()


def test_no_get_response_carries_eval_fields(client):
    paths = [
        route.path.format(
            claim_id="CLM-1001",
            policy_id="POL-2001",
            customer_id="CUS-3001",
            plan="premium",
        )
        for route in client.app.routes
        if "GET" in getattr(route, "methods", set()) and route.path.startswith("/api")
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert not keys(response.json()) & EVAL_FIELDS, path


def test_every_operation_has_an_id_and_summary(client):
    for path in client.app.openapi()["paths"].values():
        for operation in path.values():
            assert operation["operationId"]
            assert operation["summary"]
            assert operation["description"]
