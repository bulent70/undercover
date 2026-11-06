"""Shared pieces of the API: the database connection and the claim view."""

import json
import sqlite3
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends, HTTPException

from backend import db


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


def status(database: sqlite3.Connection, claim_id: str) -> str:
    """Return where a claim stands, or raise 404."""
    row = database.execute(
        "SELECT status FROM claims WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"{claim_id} not found")
    return row["status"]


def claim_view(database: sqlite3.Connection, claim_id: str) -> dict[str, Any]:
    """Return a claim with its status, decision and payment."""
    claim = record(database, "claims", "claim_id", claim_id)
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
        "status": status(database, claim_id),
        "decision": dict(decision) if decision else None,
        "payment": dict(payment) if payment else None,
    }
