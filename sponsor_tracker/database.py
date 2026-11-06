"""All the SQLite code lives here, so the rest of the project never writes SQL."""

import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

from sponsor_tracker.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT NOT NULL,
    file_hash     TEXT NOT NULL UNIQUE,
    register_date TEXT NOT NULL,
    row_count     INTEGER NOT NULL,
    loaded_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sponsors (
    upload_id   INTEGER NOT NULL REFERENCES uploads(id),
    key         TEXT NOT NULL,
    name        TEXT NOT NULL,
    name_key    TEXT NOT NULL,
    town        TEXT,
    county      TEXT,
    route       TEXT,
    worker_type TEXT,
    rating      TEXT,
    PRIMARY KEY (upload_id, key)
);

CREATE INDEX IF NOT EXISTS idx_sponsors_town ON sponsors(upload_id, town);
"""

SPONSOR_COLUMNS = [
    "key", "name", "name_key", "town", "county", "route", "worker_type", "rating",
]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open the database and make sure the tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.executescript(SCHEMA)
    return connection


def file_hash(path: Path) -> str:
    """Fingerprint of a file. Same file gives the same hash every time."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def already_loaded(connection: sqlite3.Connection, hash_value: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM uploads WHERE file_hash = ?", (hash_value,)
    ).fetchone()
    return row is not None


def save_upload(
    connection: sqlite3.Connection,
    sponsors: pd.DataFrame,
    filename: str,
    hash_value: str,
    register_date: str,
) -> int:
    """Save one cleaned snapshot. All or nothing: a failure saves nothing."""
    with connection:
        cursor = connection.execute(
            "INSERT INTO uploads (filename, file_hash, register_date, row_count) "
            "VALUES (?, ?, ?, ?)",
            (filename, hash_value, register_date, len(sponsors)),
        )
        upload_id = cursor.lastrowid
        rows = sponsors[SPONSOR_COLUMNS].assign(upload_id=upload_id)
        rows.to_sql("sponsors", connection, if_exists="append", index=False)
    return upload_id


def list_uploads(connection: sqlite3.Connection) -> pd.DataFrame:
    """All uploads, newest register date first."""
    return pd.read_sql_query(
        "SELECT id, filename, register_date, row_count FROM uploads "
        "ORDER BY register_date DESC, id DESC",
        connection,
    )


def get_sponsors(connection: sqlite3.Connection, upload_id: int) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT * FROM sponsors WHERE upload_id = ?", connection, params=(upload_id,)
    )