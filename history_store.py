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
