"""
SQLite database for auto-deploy user payment tracking
"""

import os
import sqlite3
import time
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deploy.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            paid_type TEXT NOT NULL DEFAULT 'free',
            paid_at TEXT,
            expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            paid_type TEXT,
            created_at TEXT NOT NULL,
            paid_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    conn.commit()

    # Migration: add is_admin column if not exists
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "is_admin" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    if "created_at" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # Migration: add credits column if not exists
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "credits" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0")
        conn.commit()

    # Create credit_logs table
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS credit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL DEFAULT 'consume',
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()

    # Create deploy_logs table
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS deploy_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            project_name TEXT,
            deploy_type TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            message TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()

    # Create user_credentials table for login/register
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    conn.commit()
    conn.close()


def get_user(user_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_user(user_id: str, paid_type: str, paid_at: str = None, expires_at: str = None):
    conn = get_conn()
    from datetime import datetime
    conn.execute(
        """INSERT INTO users (user_id, paid_type, paid_at, expires_at, created_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
             paid_type = excluded.paid_type,
             paid_at = excluded.paid_at,
             expires_at = excluded.expires_at""",
        (user_id, paid_type, paid_at, expires_at, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM user_credentials WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user_with_auth(username: str, password_hash: str) -> str:
    conn = get_conn()
    from datetime import datetime
    now = datetime.now().isoformat()
    user_id = f"user_{int(time.time() * 1000)}"
    conn.execute(
        "INSERT INTO users (user_id, paid_type, created_at) VALUES (?, 'free', ?)",
        (user_id, now),
    )
    conn.execute(
        "INSERT INTO user_credentials (username, password, user_id, created_at) VALUES (?, ?, ?, ?)",
        (username, password_hash, user_id, now),
    )
    conn.commit()
    conn.close()
    return user_id


def register_user(user_id: str) -> dict:
    conn = get_conn()
    from datetime import datetime
    now = datetime.now().isoformat()
    existing = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if existing:
        conn.close()
        return dict(existing)
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    is_admin = 1 if count == 0 else 0
    conn.execute(
        "INSERT INTO users (user_id, paid_type, created_at, is_admin) VALUES (?, 'free', ?, ?)",
        (user_id, now, is_admin),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def is_paid(user_id: str) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    credits = user.get("credits", 0)
    if credits > 0:
        return True
    pt = user["paid_type"]
    if pt == "permanent":
        return True
    if pt in ("yearly", "monthly") and user.get("expires_at"):
        from datetime import datetime
        try:
            exp = datetime.fromisoformat(user["expires_at"])
            return exp.timestamp() > time.time()
        except Exception:
            return False
    return False


def get_user_credits(user_id: str) -> int:
    user = get_user(user_id)
    if not user:
        return 0
    return user.get("credits", 0)


def deduct_credits(user_id: str, amount: int, description: str = "") -> bool:
    conn = get_conn()
    from datetime import datetime
    user = conn.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user or user["credits"] < amount:
        conn.close()
        return False
    conn.execute(
        "UPDATE users SET credits = credits - ? WHERE user_id = ?",
        (amount, user_id),
    )
    conn.execute(
        "INSERT INTO credit_logs (user_id, amount, type, description, created_at) VALUES (?, ?, 'consume', ?, ?)",
        (user_id, -amount, description, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return True


def add_credits(user_id: str, amount: int, credit_type: str = "recharge", description: str = "") -> bool:
    conn = get_conn()
    from datetime import datetime
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return False
    conn.execute(
        "UPDATE users SET credits = credits + ? WHERE user_id = ?",
        (amount, user_id),
    )
    conn.execute(
        "INSERT INTO credit_logs (user_id, amount, type, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, credit_type, description, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return True


def get_credit_logs(user_id: str = None, limit: int = 100) -> list:
    conn = get_conn()
    if user_id:
        rows = conn.execute(
            "SELECT * FROM credit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM credit_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_admin(user_id: str) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    return bool(user.get("is_admin", 0))


def set_admin(user_id: str, admin: bool = True):
    conn = get_conn()
    conn.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (1 if admin else 0, user_id))
    conn.commit()
    conn.close()


def create_order(order_id: str, user_id: str, amount: float, paid_type: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT INTO orders (order_id, user_id, amount, status, paid_type, created_at) VALUES (?, ?, ?, 'pending', ?, ?)",
        (order_id, user_id, amount, paid_type, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def update_order_status(order_id: str, status: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET status = ?, paid_at = ? WHERE order_id = ?",
        (status, datetime.now().isoformat() if status == "paid" else None, order_id),
    )
    conn.commit()
    conn.close()


def get_order(order_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_orders() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_admin_stats() -> dict:
    conn = get_conn()
    from datetime import datetime
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    paid_users = conn.execute("SELECT COUNT(*) FROM users WHERE credits > 0 OR paid_type != 'free'").fetchone()[0]
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    monthly_income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'paid' AND created_at >= ?",
        (month_start,),
    ).fetchone()[0]
    total_income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'paid'"
    ).fetchone()[0]
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    paid_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'").fetchone()[0]
    total_credits_recharged = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM credit_logs WHERE type = 'recharge'"
    ).fetchone()[0]
    total_credits_consumed = conn.execute(
        "SELECT COALESCE(SUM(ABS(amount)), 0) FROM credit_logs WHERE type = 'consume'"
    ).fetchone()[0]
    conn.close()
    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "free_users": total_users - paid_users,
        "monthly_income": monthly_income,
        "total_income": total_income,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_credits_recharged": total_credits_recharged,
        "total_credits_consumed": total_credits_consumed,
    }


def update_user_paid(user_id: str, paid_type: str, expires_at: str = None):
    conn = get_conn()
    from datetime import datetime
    paid_at = datetime.now().isoformat() if paid_type != "free" else None
    conn.execute(
        "UPDATE users SET paid_type = ?, paid_at = ?, expires_at = ? WHERE user_id = ?",
        (paid_type, paid_at, expires_at, user_id),
    )
    conn.commit()
    conn.close()


def add_deploy_log(user_id: str, project_name: str, deploy_type: str, status: str, message: str = ""):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT INTO deploy_logs (user_id, project_name, deploy_type, status, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, project_name, deploy_type, status, message, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_deploy_logs(limit: int = 100) -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM deploy_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()
