"""
history_store.py

Persists a snapshot of your stats every time you load the dashboard, so
Stratify can plot a REAL trend over time and forecast where you're
headed with actual linear regression on real points - not a guess
dressed up as AI.

Uses a local SQLite file (stdlib sqlite3, zero extra dependencies).

Honest caveat: if this runs somewhere with an ephemeral filesystem (a
free-tier host that wipes disk on restart/redeploy), this file - and
your history with it - can reset. For guaranteed persistence, point
DB_PATH at a mounted volume or swap this for a hosted database. For
local use (`streamlit run app.py` on your own machine) this just works.
"""

import sqlite3
from datetime import date

import pandas as pd

DB_PATH = "stratify_history.db"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            username TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            total_solved INTEGER,
            easy_solved INTEGER,
            medium_solved INTEGER,
            hard_solved INTEGER,
            readiness_score REAL,
            PRIMARY KEY (username, snapshot_date)
        )
    """)
    return conn


def log_snapshot(username, total_solved, easy_solved, medium_solved, hard_solved,
                  readiness_score, snapshot_date=None):
    """
    Logs one row per (username, day). Re-running the app the same day
    overwrites that day's row (INSERT OR REPLACE) instead of creating
    duplicate points on the trend chart - the trend is meant to show
    day-over-day change, not every refresh.
    """
    snapshot_date = snapshot_date or date.today().isoformat()
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO snapshots
                (username, snapshot_date, total_solved, easy_solved, medium_solved, hard_solved, readiness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, snapshot_date, total_solved, easy_solved, medium_solved, hard_solved, readiness_score),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(username):
    """Returns all logged snapshots for this username, oldest first."""
    conn = _get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM snapshots WHERE username = ? ORDER BY snapshot_date ASC",
            conn,
            params=(username,),
        )
    finally:
        conn.close()
    return df


if __name__ == "__main__":
    log_snapshot("testuser", 100, 60, 35, 5, 62.5, snapshot_date="2026-07-01")
    log_snapshot("testuser", 110, 65, 38, 7, 66.0, snapshot_date="2026-07-08")
    log_snapshot("testuser", 122, 70, 42, 10, 71.5, snapshot_date="2026-07-15")
    print(get_history("testuser"))