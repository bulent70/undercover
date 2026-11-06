from pathlib import Path

import pytest

from backend import db


def test_seed_gives_25_waiting_claims():
    connection = db.connect()
    statuses = [
        row["status"] for row in connection.execute("SELECT status FROM claims")
    ]
    assert len(statuses) == 25
    assert set(statuses) == {"waiting"}


def test_seeding_twice_does_not_duplicate():
    connection = db.connect()
    db.seed(connection)
    assert connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 25
    assert connection.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 50


def test_seed_reads_only_the_named_files(monkeypatch):
    read = []
    original = Path.read_text

    def spy(path, *args, **kwargs):
        read.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", spy)
    db.connect()
    assert read
    assert all(path.parent == db.DATA_DIR for path in read)
    assert {path.name for path in read} <= set(db.DATA_FILES)


def test_read_data_refuses_other_files():
    with pytest.raises(ValueError, match="not one of the data files"):
        db.read_data("evals/decisions.json")
