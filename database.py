"""SQLite persistence for EscrowFlow data."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "escrowflow.db"


def normalize_email(raw: str) -> str:
    """Strip, fix common Unicode @ variants, lowercase for storage/lookup."""
    if not raw:
        return ""
    s = raw.strip()
    # Fullwidth commercial at (U+FF20) — looks like @ but is not ASCII
    s = s.replace("\uff20", "@")
    for ch in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        s = s.replace(ch, "")
    return s.lower()


def is_valid_email_format(raw: str) -> bool:
    """
    Lenient check: exactly one '@', non-empty local and domain (e.g. name@gmail.com or name@mail.az).
    """
    email = normalize_email(raw)
    if not email:
        return False
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    return bool(local.strip()) and bool(domain.strip())


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'customer',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                customer_ref TEXT,
                category TEXT,
                start_date TEXT,
                end_date TEXT,
                budget REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (owner_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                worker_user_id INTEGER NOT NULL,
                bid_amount REAL,
                estimated_days INTEGER,
                cover_letter TEXT,
                status TEXT NOT NULL DEFAULT 'submitted',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (worker_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                customer_user_id INTEGER NOT NULL,
                worker_user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                signed_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (customer_user_id) REFERENCES users(id),
                FOREIGN KEY (worker_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                contract_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL DEFAULT 0,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (contract_id) REFERENCES contracts(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escrow_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                contract_id INTEGER,
                milestone_id INTEGER,
                initiated_by_user_id INTEGER,
                tx_type TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'created',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (milestone_id) REFERENCES milestones(id),
                FOREIGN KEY (initiated_by_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS disputes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                contract_id INTEGER,
                raised_by_user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                resolution TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                resolved_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (raised_by_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_user_id INTEGER,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                action TEXT NOT NULL,
                payload_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (actor_user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hex_hash = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return secrets.compare_digest(dk.hex(), hex_hash)
    except ValueError:
        return False


def create_user(
    email: str,
    password: str,
    full_name: str,
    phone: str,
    role: str,
) -> tuple[bool, str | None]:
    email = normalize_email(email)
    full_name = (full_name or "").strip()
    phone = (phone or "").strip()
    if not email or not password:
        return False, "Email and password are required."
    if not is_valid_email_format(email):
        return (
            False,
            "Invalid email. Use exactly one @ between name and domain (e.g. name@gmail.com).",
        )
    if not full_name:
        return False, "Please enter your full name."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if role not in ("customer", "worker"):
        role = "customer"

    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return False, "An account with this email already exists."
        ph = _hash_password(password)
        conn.execute(
            "INSERT INTO users (email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, ?)",
            (email, ph, full_name, phone, role),
        )
        conn.commit()
    return True, None


def authenticate_user(email: str, password: str) -> dict | None:
    email = normalize_email(email)
    if not email or not password:
        return None
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            return None
        if not _verify_password(password, row["password_hash"]):
            return None
        return dict(row)


def create_project(
    owner_user_id: int,
    title: str,
    description: str,
    customer_ref: str,
    category: str,
    start_date: str,
    end_date: str,
    budget_raw: str,
    status: str = "published",
) -> tuple[bool, str | None, int | None]:
    title = (title or "").strip()
    if not title:
        return False, "Project title is required.", None

    cleaned_budget = (budget_raw or "").strip().replace("$", "").replace(",", "")
    try:
        budget = float(cleaned_budget) if cleaned_budget else 0.0
    except ValueError:
        return False, "Budget must be a valid number.", None
    if budget < 0:
        return False, "Budget cannot be negative.", None

    if status not in ("draft", "published", "active", "completed", "cancelled"):
        status = "published"

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (
                owner_user_id, title, description, customer_ref, category,
                start_date, end_date, budget, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_user_id,
                title,
                (description or "").strip(),
                (customer_ref or "").strip(),
                (category or "").strip(),
                (start_date or "").strip(),
                (end_date or "").strip(),
                budget,
                status,
            ),
        )
        project_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO audit_events (actor_user_id, entity_type, entity_id, action, payload_json)
            VALUES (?, 'project', ?, ?, ?)
            """,
            (owner_user_id, project_id, "create", None),
        )
        conn.commit()
    return True, None, project_id


def create_password_reset_token(user_id: int, ttl_minutes: int = 30) -> tuple[str, str]:
    """Create reset token and persist only its hash."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, datetime('now', ?))
            """,
            (user_id, token_hash, f"+{int(ttl_minutes)} minutes"),
        )
        conn.commit()
    return token, token_hash


def get_projects_for_user(owner_user_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                title,
                description,
                customer_ref,
                category,
                start_date,
                end_date,
                budget,
                status
            FROM projects
            WHERE owner_user_id = ?
            ORDER BY id DESC
            """,
            (owner_user_id,),
        ).fetchall()
    return [dict(r) for r in rows]
