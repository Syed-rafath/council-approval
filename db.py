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

CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY,
    photo_id INTEGER NOT NULL REFERENCES photos(id),
    friend_id INTEGER NOT NULL REFERENCES friends(id),
    vote TEXT NOT NULL,          -- keep | delete
    created_at TEXT NOT NULL,
    UNIQUE(photo_id, friend_id)
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


# ── Friends ───────────────────────────────────────────────────────────────────

def create_friend(name: str, token: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO friends (name, token) VALUES (?, ?)",
            (name, token),
        )
        return cur.lastrowid


def list_friends():
    with get_db() as conn:
        return conn.execute(
            "SELECT id, name, token FROM friends ORDER BY id"
        ).fetchall()


def get_friend_by_token(token: str):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, name, token FROM friends WHERE token = ?",
            (token,),
        ).fetchone()


# ── Votes ─────────────────────────────────────────────────────────────────────

def record_vote(photo_id: int, friend_id: int, vote: str):
    """Insert or replace a vote (allows changing mind)."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO votes (photo_id, friend_id, vote, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(photo_id, friend_id) DO UPDATE SET vote=excluded.vote, created_at=excluded.created_at
            """,
            (photo_id, friend_id, vote, utc_now()),
        )


def get_next_unvoted(friend_id: int):
    """Return the next photo this friend has not voted on yet."""
    with get_db() as conn:
        return conn.execute(
            """
            SELECT p.id, p.thumb_filename, p.batch_id
            FROM photos p
            WHERE p.id NOT IN (
                SELECT photo_id FROM votes WHERE friend_id = ?
            )
            ORDER BY p.id
            LIMIT 1
            """,
            (friend_id,),
        ).fetchone()


def count_unvoted(friend_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM photos
            WHERE id NOT IN (SELECT photo_id FROM votes WHERE friend_id = ?)
            """,
            (friend_id,),
        ).fetchone()
        return row[0]


# ── Results / apply ───────────────────────────────────────────────────────────

def get_vote_tallies(batch_id: int):
    """Return every photo in a batch with keep/delete counts."""
    with get_db() as conn:
        return conn.execute(
            """
            SELECT
                p.id, p.filename, p.thumb_filename, p.status,
                SUM(CASE WHEN v.vote = 'keep'   THEN 1 ELSE 0 END) AS keep_count,
                SUM(CASE WHEN v.vote = 'delete' THEN 1 ELSE 0 END) AS delete_count,
                COUNT(v.id) AS total_votes
            FROM photos p
            LEFT JOIN votes v ON v.photo_id = p.id
            WHERE p.batch_id = ?
            GROUP BY p.id
            ORDER BY p.id
            """,
            (batch_id,),
        ).fetchall()


def count_friends() -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM friends").fetchone()[0]


def update_photo_status(photo_id: int, status: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE photos SET status = ? WHERE id = ?",
            (status, photo_id),
        )
