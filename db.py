import sqlite3
from datetime import datetime, timezone

from config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    label TEXT
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    filename TEXT NOT NULL,
    thumb_filename TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def create_batch(label):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO batches (created_at, label) VALUES (?, ?)",
            (utc_now(), label),
        )
        return cur.lastrowid


def add_photo(batch_id, filename, thumb_filename):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO photos (batch_id, filename, thumb_filename, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (batch_id, filename, thumb_filename, utc_now()),
        )


def list_batches():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.created_at, b.label, COUNT(p.id) AS photo_count
            FROM batches b
            LEFT JOIN photos p ON p.batch_id = b.id
            GROUP BY b.id
            ORDER BY b.id DESC
            """
        ).fetchall()
    return rows


def get_batch(batch_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, created_at, label FROM batches WHERE id = ?",
            (batch_id,),
        ).fetchone()


def list_photos(batch_id):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT id, filename, thumb_filename, status
            FROM photos
            WHERE batch_id = ?
            ORDER BY id
            """,
            (batch_id,),
        ).fetchall()
