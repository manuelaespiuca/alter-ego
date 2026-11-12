"""Histórico de conversas salvo em SQLite (biblioteca padrão do Python)."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from . import config


def _connect():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK (role IN ('user', 'model')),
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def add_message(role, text):
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO messages (role, text, created_at) VALUES (?, ?, ?)",
            (role, text, agora),
        )


def load_recent(limit):
    """Últimas `limit` mensagens, da mais antiga para a mais nova."""
    with closing(_connect()) as conn:
        linhas = conn.execute(
            "SELECT role, text, created_at FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    linhas.reverse()
    return [{"role": r, "text": t, "created_at": c} for r, t, c in linhas]


def clear():
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM messages")
