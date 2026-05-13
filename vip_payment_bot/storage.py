from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    username: str | None
    amount: int
    status: str
    transaction_id: str | None
    payment_url: str | None
    qr_path: str | None
    invite_link: str | None
    created_at: str
    updated_at: str
    expires_at: str


class Store:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        if self.db_path.parent != Path("."):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    transaction_id TEXT,
                    payment_url TEXT,
                    qr_path TEXT,
                    invite_link TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status)"
            )
            self._conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_transaction_id
                ON orders(transaction_id)
                WHERE transaction_id IS NOT NULL
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(id)
                )
                """
            )

    def create_order(
        self,
        user_id: int,
        username: str | None,
        amount: int,
        expires_at: str,
    ) -> Order:
        now = utc_now_iso()
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO orders (
                    user_id, username, amount, status, created_at, updated_at, expires_at
                ) VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """,
                (user_id, username, amount, now, now, expires_at),
            )
            order_id = int(cursor.lastrowid)
        order = self.get_order(order_id)
        if order is None:
            raise RuntimeError("Order gagal dibuat.")
        return order

    def attach_payment(
        self,
        order_id: int,
        transaction_id: str | None,
        payment_url: str | None,
        qr_path: str | None,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE orders
                SET transaction_id = ?, payment_url = ?, qr_path = ?, updated_at = ?
                WHERE id = ?
                """,
                (transaction_id, payment_url, qr_path, utc_now_iso(), order_id),
            )

    def mark_paid(self, order_id: int, invite_link: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE orders
                SET status = 'paid', invite_link = ?, updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (invite_link, utc_now_iso(), order_id),
            )

    def mark_expired(self, order_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE orders
                SET status = 'expired', updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (utc_now_iso(), order_id),
            )

    def mark_failed(self, order_id: int, reason: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE orders
                SET status = 'failed', updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (utc_now_iso(), order_id),
            )
            self._conn.execute(
                """
                INSERT INTO order_events(order_id, event_type, payload, created_at)
                VALUES (?, 'failure', ?, ?)
                """,
                (order_id, reason[:1000], utc_now_iso()),
            )

    def add_event(self, order_id: int, event_type: str, payload: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO order_events(order_id, event_type, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, event_type, payload[:2000], utc_now_iso()),
            )

    def get_order(self, order_id: int) -> Order | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
        return self._row_to_order(row)

    def get_active_order_for_user(self, user_id: int) -> Order | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT * FROM orders
                WHERE user_id = ? AND status = 'pending'
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_order(row)

    def pending_orders(self) -> list[Order]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM orders
                WHERE status = 'pending' AND transaction_id IS NOT NULL
                ORDER BY id ASC
                """
            ).fetchall()
        return [order for row in rows if (order := self._row_to_order(row)) is not None]

    def stats(self) -> dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT status, COUNT(*) AS total FROM orders GROUP BY status"
            ).fetchall()
        return {str(row["status"]): int(row["total"]) for row in rows}

    def _row_to_order(self, row: sqlite3.Row | None) -> Order | None:
        if row is None:
            return None
        data: dict[str, Any] = dict(row)
        return Order(**data)

    def close(self) -> None:
        with self._lock:
            self._conn.close()
