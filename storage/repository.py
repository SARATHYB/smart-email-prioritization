# storage/repository.py
"""
SQLite Storage Repository for Smart Email Prioritization.
Provides high-performance persistence, filtering, and state management.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.config import settings
from core.models import (
    PrioritizedEmail, EmailCategory, PriorityTier, EmailFolder
)
from core.logger import get_logger

logger = get_logger("repository")


class EmailRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.absolute_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes database schema and indexes."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    sender_name TEXT,
                    sender_email TEXT NOT NULL,
                    body TEXT NOT NULL,
                    cleaned_body TEXT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    category_confidence REAL NOT NULL,
                    relevance_score REAL NOT NULL,
                    deadline_str TEXT,
                    deadline_dt TEXT,
                    hours_remaining REAL,
                    tuds_score REAL NOT NULL,
                    priority_tier TEXT NOT NULL,
                    folder TEXT NOT NULL DEFAULT 'inbox',
                    tags TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_folder ON emails(folder)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON emails(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tuds_score ON emails(tuds_score DESC)")
            conn.commit()

    def upsert_email(self, email: PrioritizedEmail) -> None:
        """Inserts or updates an email record."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO emails (
                    id, subject, sender_name, sender_email, body, cleaned_body,
                    timestamp, category, category_confidence, relevance_score,
                    deadline_str, deadline_dt, hours_remaining, tuds_score,
                    priority_tier, folder, tags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    tuds_score = excluded.tuds_score,
                    priority_tier = excluded.priority_tier,
                    hours_remaining = excluded.hours_remaining,
                    deadline_str = excluded.deadline_str,
                    deadline_dt = excluded.deadline_dt,
                    category = excluded.category,
                    category_confidence = excluded.category_confidence
            """, (
                email.id,
                email.subject,
                email.sender_name,
                email.sender_email,
                email.body,
                email.cleaned_body,
                email.timestamp.isoformat(),
                email.category.value,
                email.category_confidence,
                email.relevance_score,
                email.deadline_str,
                email.deadline_dt.isoformat() if email.deadline_dt else None,
                email.hours_remaining,
                email.tuds_score,
                email.priority_tier.value,
                email.folder.value,
                json.dumps(email.tags),
                email.created_at.isoformat()
            ))
            conn.commit()

    def upsert_batch(self, emails: List[PrioritizedEmail]) -> int:
        for email in emails:
            self.upsert_email(email)
        return len(emails)

    def list_emails(
        self,
        folder: Optional[EmailFolder] = None,
        category: Optional[EmailCategory] = None,
        priority_tier: Optional[PriorityTier] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> List[PrioritizedEmail]:
        """Queries emails with dynamic filtering and score-based sorting."""
        conditions = []
        params = []

        if folder is not None:
            conditions.append("folder = ?")
            params.append(folder.value)

        if category is not None:
            conditions.append("category = ?")
            params.append(category.value)

        if priority_tier is not None:
            conditions.append("priority_tier = ?")
            params.append(priority_tier.value)

        if search_query:
            conditions.append("(subject LIKE ? OR sender_name LIKE ? OR body LIKE ?)")
            q = f"%{search_query.strip()}%"
            params.extend([q, q, q])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT * FROM emails
            {where_clause}
            ORDER BY tuds_score DESC, timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_email(row) for row in rows]

    def set_folder(self, email_id: str, folder: EmailFolder) -> bool:
        """Moves an email between folders (inbox, saved, trash)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE emails SET folder = ? WHERE id = ?",
                (folder.value, email_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns overview analytics for the dashboard metrics."""
        with self._get_connection() as conn:
            total_inbox = conn.execute(
                "SELECT COUNT(*) FROM emails WHERE folder = 'inbox'"
            ).fetchone()[0]
            total_saved = conn.execute(
                "SELECT COUNT(*) FROM emails WHERE folder = 'saved'"
            ).fetchone()[0]
            total_trash = conn.execute(
                "SELECT COUNT(*) FROM emails WHERE folder = 'trash'"
            ).fetchone()[0]
            urgent_count = conn.execute(
                "SELECT COUNT(*) FROM emails WHERE folder = 'inbox' AND priority_tier = 'Urgent'"
            ).fetchone()[0]

            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM emails WHERE folder = 'inbox' GROUP BY category"
            ).fetchall()
            cat_counts = {row["category"]: row["cnt"] for row in cat_rows}

        return {
            "total_inbox": total_inbox,
            "total_saved": total_saved,
            "total_trash": total_trash,
            "urgent_count": urgent_count,
            "category_counts": cat_counts
        }

    def clear_all(self):
        """Truncates the database (useful for resetting demo)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM emails")
            conn.commit()

    def _row_to_email(self, row: sqlite3.Row) -> PrioritizedEmail:
        return PrioritizedEmail(
            id=row["id"],
            subject=row["subject"],
            sender_name=row["sender_name"] or "",
            sender_email=row["sender_email"],
            body=row["body"],
            cleaned_body=row["cleaned_body"] or "",
            timestamp=datetime.fromisoformat(row["timestamp"]),
            category=EmailCategory(row["category"]),
            category_confidence=row["category_confidence"],
            relevance_score=row["relevance_score"],
            deadline_str=row["deadline_str"] or "No deadline found",
            deadline_dt=datetime.fromisoformat(row["deadline_dt"]) if row["deadline_dt"] else None,
            hours_remaining=row["hours_remaining"],
            tuds_score=row["tuds_score"],
            priority_tier=PriorityTier(row["priority_tier"]),
            folder=EmailFolder(row["folder"]),
            tags=json.loads(row["tags"] or "[]"),
            created_at=datetime.fromisoformat(row["created_at"])
        )


repository = EmailRepository()
