import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT    DEFAULT (datetime('now', 'localtime')),
            qr_content  TEXT,
            status      TEXT,
            message     TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_config() -> dict:
    defaults = {
        "student_id":    "",
        "password":      "",
        "url_keyword":   "",
        "login_url":     "",
        "scan_interval": "1",
        "max_checkins":  "2",
    }
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    for row in rows:
        defaults[row["key"]] = row["value"]
    return defaults


def save_config(data: dict):
    conn = get_db()
    for key, value in data.items():
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
    conn.commit()
    conn.close()
