"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException

from backend import db

INSTRUCTIONS = Path(__file__).parent / "instructions.md"

app = FastAPI(title="UnderCover")


def connection() -> Iterator[sqlite3.Connection]:
    """Give each request its own database connection."""
    database = db.connect()
    try:
        yield database
    finally:
        database.close()


Database = Annotated[sqlite3.Connection, Depends(connection)]


def record(database: sqlite3.Connection, table: str, key: str, value: str) -> Any:
    """Return one stored JSON record, or raise 404."""
    row = database.execute(
        f"SELECT record FROM {table} WHERE {key} = ?",  # noqa: S608
        (value,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"{value} not found")
    return json.loads(row["record"])


def claim_view(database: sqlite3.Connection, claim_id: str) -> dict[str, Any]:
    """Return a claim with its status, decision and payment."""
    claim = record(database, "claims", "claim_id", claim_id)
    status = database.execute(
        "SELECT status FROM claims WHERE claim_id = ?", (claim_id,)
    ).fetchone()["status"]
    decision = database.execute(
        "SELECT decision, payout, reason, section, decided_at FROM decisions"
        " WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    payment = database.execute(
        "SELECT amount, handler_id, paid_at FROM payments WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    return claim | {
        "status": status,
        "decision": dict(decision) if decision else None,
        "payment": dict(payment) if payment else None,
    }


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims(database: Database) -> list[dict[str, Any]]:
    """List the claims queue with where each claim stands."""
    rows = database.execute(
        "SELECT record, status FROM claims ORDER BY claim_id"
    ).fetchall()
    fields = ("claim_id", "summary", "claim_type", "submitted_on", "amount_claimed")
    return [
        {field: json.loads(row["record"])[field] for field in fields}
        | {"status": row["status"]}
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
