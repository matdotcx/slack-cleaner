import os
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, Optional

# Detect database type from environment
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    DATABASE_PATH = "deletion_requests.db"

@contextmanager
def get_db():
    """Get database connection (PostgreSQL or SQLite based on environment)."""
    if USE_POSTGRES:
        # PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        # SQLite connection (local development)
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
    """Initialise database schema (works for both PostgreSQL and SQLite)."""
    with get_db() as conn:
        cursor = conn.cursor()

        if USE_POSTGRES:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deletion_requests (
                    id SERIAL PRIMARY KEY,
                    request_timestamp TIMESTAMP NOT NULL,
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
                    action_timestamp TIMESTAMP,
                    admin_message_ts TEXT,
                    notes TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_request_timestamp
                ON deletion_requests(request_timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON deletion_requests(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_author
                ON deletion_requests(message_author_id)
            """)
        else:
            # SQLite schema
            cursor.execute("""
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

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_request_timestamp
                ON deletion_requests(request_timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON deletion_requests(status)
            """)

            cursor.execute("""
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
    """Create a new deletion request record."""
    timestamp = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute("""
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                timestamp,
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
            return cursor.fetchone()[0]
        else:
            cursor.execute("""
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
                timestamp.isoformat(),
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
    """Update a deletion request with admin action."""
    timestamp = datetime.utcnow()

    with get_db() as conn:
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute("""
                UPDATE deletion_requests
                SET status = %s,
                    admin_id = %s,
                    admin_name = %s,
                    action_timestamp = %s,
                    notes = %s
                WHERE id = %s
            """, (
                status,
                admin_id,
                admin_name,
                timestamp,
                notes,
                request_id
            ))
        else:
            cursor.execute("""
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
                timestamp.isoformat(),
                notes,
                request_id
            ))

def get_deletion_request_by_admin_message(admin_message_ts: str) -> Optional[Dict[str, Any]]:
    """Retrieve a deletion request by admin message timestamp."""
    with get_db() as conn:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM deletion_requests
                WHERE admin_message_ts = %s
            """, (admin_message_ts,))
            row = cursor.fetchone()

            if row:
                # Convert RealDictRow to regular dict and handle datetime serialisation
                result = dict(row)
                # Convert datetime objects to ISO format strings for consistency
                if result.get('request_timestamp'):
                    result['request_timestamp'] = result['request_timestamp'].isoformat()
                if result.get('action_timestamp'):
                    result['action_timestamp'] = result['action_timestamp'].isoformat()
                return result
            return None
        else:
            cursor = conn.cursor()
            row = cursor.execute("""
                SELECT * FROM deletion_requests
                WHERE admin_message_ts = ?
            """, (admin_message_ts,)).fetchone()

            if row:
                return dict(row)
            return None

def get_recent_requests(limit: int = 50) -> list[Dict[str, Any]]:
    """Retrieve recent deletion requests."""
    with get_db() as conn:
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM deletion_requests
                ORDER BY request_timestamp DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()

            # Convert RealDictRow to regular dict and handle datetime serialisation
            results = []
            for row in rows:
                result = dict(row)
                if result.get('request_timestamp'):
                    result['request_timestamp'] = result['request_timestamp'].isoformat()
                if result.get('action_timestamp'):
                    result['action_timestamp'] = result['action_timestamp'].isoformat()
                results.append(result)
            return results
        else:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT * FROM deletion_requests
                ORDER BY request_timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]
