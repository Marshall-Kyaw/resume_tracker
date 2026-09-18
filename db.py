"""
Database layer for the Job Application Tracker.
SQLite-backed. This is the only module that touches the database directly.
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "job_tracker.db"

STATUS_OPTIONS = [
    "Saved", "Applying", "Applied", "In Process",
    "Interviewing", "Offer", "Rejected", "Closed / No Response"
]

MARKET_OPTIONS = ["Malaysia", "Singapore", "UAE", "Japan", "Thailand", "Other"]

SOURCE_OPTIONS = ["LinkedIn", "Company Website", "Referral", "Recruiter", "Job Board", "Other"]

# Statuses considered "active" for stale-application flagging
ACTIVE_STATUSES = {"Applying", "Applied", "In Process", "Interviewing"}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role_title TEXT NOT NULL,
                target_market TEXT,
                status TEXT DEFAULT 'Saved',
                date_applied TEXT,
                resume_version TEXT,
                source TEXT,
                job_url TEXT,
                referral_contact TEXT,
                salary_range TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                follow_up_date TEXT,
                description TEXT,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                round_type TEXT,
                interview_date TEXT,
                notes TEXT,
                outcome TEXT,
                FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
            )
        """)


# ---------- Applications ----------

def add_application(data: dict) -> int:
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO applications
            (company, role_title, target_market, status, date_applied, resume_version,
             source, job_url, referral_contact, salary_range, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("company"), data.get("role_title"), data.get("target_market"),
            data.get("status", "Saved"), data.get("date_applied"), data.get("resume_version"),
            data.get("source"), data.get("job_url"), data.get("referral_contact"),
            data.get("salary_range"), data.get("notes"), now, now
        ))
        return cur.lastrowid


def update_application(app_id: int, data: dict):
    now = datetime.now().isoformat()
    fields, values = [], []
    for key in ["company", "role_title", "target_market", "status", "date_applied",
                "resume_version", "source", "job_url", "referral_contact",
                "salary_range", "notes"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    fields.append("updated_at = ?")
    values.append(now)
    values.append(app_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE applications SET {', '.join(fields)} WHERE id = ?", values)


def delete_application(app_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM follow_ups WHERE application_id = ?", (app_id,))
        conn.execute("DELETE FROM interviews WHERE application_id = ?", (app_id,))
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))


def get_all_applications():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM applications ORDER BY date_applied DESC").fetchall()
        return [dict(r) for r in rows]


def get_application(app_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return dict(row) if row else None


# ---------- Follow-ups ----------

def add_follow_up(application_id: int, follow_up_date: str, description: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO follow_ups (application_id, follow_up_date, description, completed)
            VALUES (?, ?, ?, 0)
        """, (application_id, follow_up_date, description))


def get_follow_ups(include_completed=False):
    query = """
        SELECT f.*, a.company, a.role_title
        FROM follow_ups f JOIN applications a ON f.application_id = a.id
    """
    if not include_completed:
        query += " WHERE f.completed = 0"
    query += " ORDER BY f.follow_up_date ASC"
    with get_conn() as conn:
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]


def complete_follow_up(follow_up_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE follow_ups SET completed = 1 WHERE id = ?", (follow_up_id,))


def delete_follow_up(follow_up_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM follow_ups WHERE id = ?", (follow_up_id,))


# ---------- Interviews ----------

def add_interview(application_id: int, round_type: str, interview_date: str, notes: str, outcome: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO interviews (application_id, round_type, interview_date, notes, outcome)
            VALUES (?, ?, ?, ?, ?)
        """, (application_id, round_type, interview_date, notes, outcome))


def get_interviews(application_id=None):
    with get_conn() as conn:
        if application_id:
            rows = conn.execute("""
                SELECT * FROM interviews WHERE application_id = ? ORDER BY interview_date DESC
            """, (application_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT i.*, a.company, a.role_title
                FROM interviews i JOIN applications a ON i.application_id = a.id
                ORDER BY i.interview_date DESC
            """).fetchall()
        return [dict(r) for r in rows]


def delete_interview(interview_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
