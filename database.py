from config import get_db


def add_log(qr_content: str, status: str, message: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (qr_content, status, message) VALUES (?, ?, ?)",
        (qr_content, status, message),
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 100) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT id, detected_at, qr_content, status, message "
        "FROM logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
