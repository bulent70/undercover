"""The UnderCover database: SQLite, created and seeded from data/ on first use."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_FILES = (
    "claims.json",
    "policies.json",
    "customers.json",
    "handlers.json",
    "plans.json",
    "company.json",
    "policy_wording.md",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    record TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'waiting'
);
CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY, record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY, record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS handlers (
    handler_id TEXT PRIMARY KEY, record TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    claim_id TEXT PRIMARY KEY REFERENCES claims,
    decision TEXT NOT NULL,
    payout REAL NOT NULL,
    reason TEXT NOT NULL,
    section TEXT NOT NULL,
    decided_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
    claim_id TEXT PRIMARY KEY REFERENCES claims,
    amount REAL NOT NULL,
    handler_id TEXT REFERENCES handlers,
    paid_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL REFERENCES claims,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

SEED_TABLES = (
    ("claims", "claim_id", "claims.json"),
    ("policies", "policy_id", "policies.json"),
    ("customers", "customer_id", "customers.json"),
    ("handlers", "handler_id", "handlers.json"),
)


def read_data(name: str) -> str:
    """Read one of the named files in data/."""
    if name not in DATA_FILES:
        raise ValueError(f"{name} is not one of the data files")
    return (DATA_DIR / name).read_text(encoding="utf-8")


def read_json(name: str) -> Any:
    """Read one of the named JSON files in data/."""
    return json.loads(read_data(name))


def database_path() -> Path:
    """Return the database file: UNDERCOVER_DB, or undercover.db at the repo root."""
    return Path(os.getenv("UNDERCOVER_DB", ROOT / "undercover.db"))


def seed(connection: sqlite3.Connection) -> None:
    """Create the tables and load the records from data/, skipping any already there."""
    connection.executescript(SCHEMA)
    for table, key, file in SEED_TABLES:
        connection.executemany(
            f"INSERT OR IGNORE INTO {table} ({key}, record) VALUES (?, ?)",  # noqa: S608
            [(row[key], json.dumps(row)) for row in read_json(file)],
        )
    connection.commit()


def connect() -> sqlite3.Connection:
    """Open the database, creating and seeding it if it is new."""
    path = database_path()
    is_new = not path.exists()
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    if is_new:
        seed(connection)
    return connection
