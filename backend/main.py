"""The UnderCover backend."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from backend import db, workflow
from backend.claims import Database, claim_view, record

INSTRUCTIONS = Path(__file__).parent / "instructions.md"

app = FastAPI(title="UnderCover")
app.include_router(workflow.router)


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims(database: Database) -> list[dict[str, Any]]:
    """List the claims queue with where each claim stands and its decision."""
    rows = database.execute(
        "SELECT claims.record, claims.status, decisions.decision, decisions.payout"
        " FROM claims LEFT JOIN decisions USING (claim_id) ORDER BY claim_id"
    ).fetchall()
    fields = ("claim_id", "summary", "claim_type", "submitted_on", "amount_claimed")
    return [
        {field: json.loads(row["record"])[field] for field in fields}
        | {
            "status": row["status"],
            "decision": row["decision"],
            "payout": row["payout"],
        }
        for row in rows
    ]


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str, database: Database) -> dict[str, Any]:
    """Get one claim in full, with its decision and payment."""
    return claim_view(database, claim_id)


@app.get("/api/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str, database: Database) -> dict[str, Any]:
    """Get one policy: the plan, add-ons, trip and travelers."""
    return record(database, "policies", "policy_id", policy_id)


@app.get("/api/customers/{customer_id}/claims", operation_id="get_claim_history")
def get_claim_history(customer_id: str, database: Database) -> list[dict[str, Any]]:
    """Get a customer's previous claims, without their contact details."""
    return record(database, "customers", "customer_id", customer_id)["previous_claims"]


@app.get("/api/plans/{plan}", operation_id="get_plan")
def get_plan(plan: str) -> dict[str, Any]:
    """Get a plan's limits, where its deductible applies, and the add-ons."""
    plans = db.read_json("plans.json")
    match = [row for row in plans["plans"] if row["plan"] == plan]
    if not match:
        raise HTTPException(404, f"{plan} not found")
    return match[0] | {
        "deductible_applies_to": plans["deductible_applies_to"],
        "add_ons": plans["add_ons"],
    }


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording() -> dict[str, str]:
    """Get the policy wording as markdown."""
    return {"text": db.read_data("policy_wording.md")}


@app.get("/api/instructions", operation_id="get_instructions")
def get_instructions() -> dict[str, str]:
    """Get the UnderCover Agent's instructions as markdown."""
    return {"text": INSTRUCTIONS.read_text(encoding="utf-8")}


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers(database: Database) -> list[dict[str, Any]]:
    """List the claims handlers."""
    rows = database.execute("SELECT record FROM handlers ORDER BY handler_id")
    return [json.loads(row["record"]) for row in rows]
