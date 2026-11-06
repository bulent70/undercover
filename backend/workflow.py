"""The claim workflow: starting, steps, decisions, payments and sign-off."""

import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal, Self

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from backend import db
from backend.claims import Database, claim_view, record, status

PAYOUT_LIMIT: float = db.read_json("company.json")["payout_approval_limit"]

router = APIRouter(prefix="/api/claims/{claim_id}")


class Step(BaseModel):
    kind: Literal["model", "tool_call", "tool_result"]
    text: str


class Decision(BaseModel):
    decision: Literal["approve", "decline", "refer"]
    payout: float
    reason: str
    section: str

    @model_validator(mode="after")
    def payout_matches_decision(self) -> Self:
        """An approval pays something; a decline or referral pays nothing."""
        if (self.decision == "approve") != (self.payout > 0):
            raise ValueError("approve needs a payout above 0, other decisions 0")
        return self


class Payment(BaseModel):
    amount: float


class SignOff(BaseModel):
    handler_id: str


def now() -> str:
    """Return the current time in UTC as ISO 8601."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def set_status(database: sqlite3.Connection, claim_id: str, new_status: str) -> None:
    """Move a claim to a new status."""
    database.execute(
        "UPDATE claims SET status = ? WHERE claim_id = ?", (new_status, claim_id)
    )


def record_payment(
    database: sqlite3.Connection, claim_id: str, amount: float, handler_id: str | None
) -> dict[str, Any]:
    """Record a payment, mark the claim decided and return the claim."""
    database.execute(
        "INSERT INTO payments (claim_id, amount, handler_id, paid_at)"
        " VALUES (?, ?, ?, ?)",
        (claim_id, amount, handler_id, now()),
    )
    set_status(database, claim_id, "decided")
    database.commit()
    return claim_view(database, claim_id)


def start(database: sqlite3.Connection, claim_id: str) -> dict[str, Any]:
    """Move a waiting claim, or one left in progress, to in progress."""
    if status(database, claim_id) not in {"waiting", "in_progress"}:
        raise HTTPException(409, f"{claim_id} has already been decided")
    set_status(database, claim_id, "in_progress")
    database.commit()
    return claim_view(database, claim_id)


@router.post("/start", operation_id="start_claim")
def start_claim(claim_id: str, database: Database) -> dict[str, Any]:
    """Mark a claim as in progress when the agent starts work on it."""
    return start(database, claim_id)


@router.post("/steps", operation_id="add_step")
def add_step(claim_id: str, step: Step, database: Database) -> dict[str, Any]:
    """Record one step of the agent's work on a claim."""
    status(database, claim_id)
    created_at = now()
    cursor = database.execute(
        "INSERT INTO steps (claim_id, kind, text, created_at) VALUES (?, ?, ?, ?)",
        (claim_id, step.kind, step.text, created_at),
    )
    database.commit()
    return {"step_id": cursor.lastrowid, **step.model_dump(), "created_at": created_at}


@router.get("/steps", operation_id="list_steps")
def list_steps(claim_id: str, database: Database) -> list[dict[str, Any]]:
    """List the agent's steps on a claim, oldest first."""
    status(database, claim_id)
    rows = database.execute(
        "SELECT step_id, kind, text, created_at FROM steps"
        " WHERE claim_id = ? ORDER BY step_id",
        (claim_id,),
    )
    return [dict(row) for row in rows]


@router.post("/decision", operation_id="decide_claim")
def decide_claim(
    claim_id: str, decision: Decision, database: Database
) -> dict[str, Any]:
    """Approve, decline or refer a claim, with the payout, reason and section."""
    if status(database, claim_id) != "in_progress":
        raise HTTPException(409, f"{claim_id} is not in progress")
    database.execute(
        "INSERT OR REPLACE INTO decisions"
        " (claim_id, decision, payout, reason, section, decided_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, *decision.model_dump().values(), now()),
    )
    if decision.decision != "approve":
        set_status(database, claim_id, "decided")
    elif decision.payout > PAYOUT_LIMIT:
        set_status(database, claim_id, "waiting_for_signoff")
    database.commit()
    return claim_view(database, claim_id)


@router.post("/payment", operation_id="pay_claim")
def pay_claim(claim_id: str, payment: Payment, database: Database) -> dict[str, Any]:
    """Pay an approved claim the approved payout, if the payment rule allows it."""
    claim = claim_view(database, claim_id)
    decision = claim["decision"]
    if claim["payment"]:
        raise HTTPException(409, f"{claim_id} has already been paid")
    if not decision or decision["decision"] != "approve":
        raise HTTPException(409, f"{claim_id} has not been approved")
    if round(payment.amount, 2) != round(decision["payout"], 2):
        raise HTTPException(
            409,
            f"The amount must equal the approved payout, ${decision['payout']:,.2f}",
        )
    if decision["payout"] > PAYOUT_LIMIT:
        raise HTTPException(
            409,
            f"A payout over ${PAYOUT_LIMIT:,.2f} needs a handler's sign-off."
            " The payment waits until a handler signs off.",
        )
    return record_payment(database, claim_id, payment.amount, None)


@router.post("/sign-off", operation_id="sign_off_claim")
def sign_off_claim(
    claim_id: str, sign_off: SignOff, database: Database
) -> dict[str, Any]:
    """Sign off a payout over the limit as a handler, and pay it."""
    handler = record(database, "handlers", "handler_id", sign_off.handler_id)
    if status(database, claim_id) != "waiting_for_signoff":
        raise HTTPException(409, f"{claim_id} is not waiting for sign-off")
    if not handler["can_approve_over_limit"]:
        raise HTTPException(403, f"{handler['name']} cannot sign off this payout")
    payout = claim_view(database, claim_id)["decision"]["payout"]
    return record_payment(database, claim_id, payout, sign_off.handler_id)
