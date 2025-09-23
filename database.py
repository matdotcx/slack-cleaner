import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, Optional

DATABASE_PATH = "deletion_requests.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_timestamp TEXT NOT NULL,
                message_ts TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                channel_name TEXT,
                message_author_id TEXT NOT NULL,
                message_author_name TEXT,
                message_text TEXT NOT NULL,
                requester_id TEXT NOT NULL,
                requester_name TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                admin_id TEXT,
                admin_name TEXT,
                action_timestamp TEXT,
                admin_message_ts TEXT,
                notes TEXT
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_request_timestamp
            ON deletion_requests(request_timestamp)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON deletion_requests(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_author
            ON deletion_requests(message_author_id)
        """)

def create_deletion_request(
    message_ts: str,
    channel_id: str,
    channel_name: str,
    message_author_id: str,
    message_author_name: str,
    message_text: str,
    requester_id: str,
    requester_name: str,
    admin_message_ts: str
) -> int:
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO deletion_requests (
                request_timestamp,
                message_ts,
                channel_id,
                channel_name,
                message_author_id,
                message_author_name,
                message_text,
                requester_id,
                requester_name,
                admin_message_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            message_ts,
            channel_id,
            channel_name,
            message_author_id,
            message_author_name,
            message_text,
            requester_id,
            requester_name,
            admin_message_ts
        ))
        return cursor.lastrowid

def update_deletion_request(
    request_id: int,
    status: str,
    admin_id: str,
    admin_name: str,
    notes: Optional[str] = None
):
    with get_db() as conn:
        conn.execute("""
            UPDATE deletion_requests
            SET status = ?,
                admin_id = ?,
                admin_name = ?,
                action_timestamp = ?,
                notes = ?
            WHERE id = ?
        """, (
            status,
            admin_id,
            admin_name,
            datetime.utcnow().isoformat(),
            notes,
            request_id
        ))

def get_deletion_request_by_admin_message(admin_message_ts: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute("""
            SELECT * FROM deletion_requests
            WHERE admin_message_ts = ?
        """, (admin_message_ts,)).fetchone()

        if row:
            return dict(row)
        return None

def get_recent_requests(limit: int = 50) -> list[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM deletion_requests
            ORDER BY request_timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]