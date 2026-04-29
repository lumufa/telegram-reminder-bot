from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS reminders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    message     TEXT    NOT NULL,
    fire_at     TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    fired       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reminders_pending
    ON reminders(fired, fire_at);
"""


@dataclass
class Reminder:
    id: int
    chat_id: int
    user_id: int
    message: str
    fire_at: datetime


class ReminderStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def add(
        self, chat_id: int, user_id: int, message: str, fire_at: datetime
    ) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO reminders (chat_id, user_id, message, fire_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                user_id,
                message,
                fire_at.astimezone(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid or 0

    def mark_fired(self, reminder_id: int) -> None:
        self._conn.execute(
            "UPDATE reminders SET fired = 1 WHERE id = ?", (reminder_id,)
        )
        self._conn.commit()

    def cancel(self, reminder_id: int, user_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ? AND fired = 0",
            (reminder_id, user_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def list_pending_for_user(self, user_id: int) -> list[Reminder]:
        rows = self._conn.execute(
            """
            SELECT id, chat_id, user_id, message, fire_at
            FROM reminders
            WHERE user_id = ? AND fired = 0
            ORDER BY fire_at ASC
            """,
            (user_id,),
        ).fetchall()
        return [self._row_to_reminder(r) for r in rows]

    def list_all_pending(self) -> list[Reminder]:
        rows = self._conn.execute(
            """
            SELECT id, chat_id, user_id, message, fire_at
            FROM reminders
            WHERE fired = 0
            """
        ).fetchall()
        return [self._row_to_reminder(r) for r in rows]

    @staticmethod
    def _row_to_reminder(row: tuple) -> Reminder:
        return Reminder(
            id=row[0],
            chat_id=row[1],
            user_id=row[2],
            message=row[3],
            fire_at=datetime.fromisoformat(row[4]),
        )

    def close(self) -> None:
        self._conn.close()
