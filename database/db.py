import sqlite3
from pathlib import Path
from config import DATABASE

DB_PATH = Path(__file__).resolve().parents[1] / DATABASE


def _ensure_column(conn, table_name, column_name, column_type):
    columns = {
        row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def init_db():

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY,
            title TEXT,
            code TEXT UNIQUE,
            app TEXT,
            discount INTEGER,
            issuer TEXT,
            source TEXT,
            url TEXT
        )
        """)
        _ensure_column(conn, "coupons", "issuer", "TEXT")
        _ensure_column(conn, "coupons", "source", "TEXT")
        _ensure_column(conn, "coupons", "url", "TEXT")
        conn.commit()


def save_coupon(coupon):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO coupons (title, code, app, discount, issuer, source, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                coupon["title"],
                coupon["code"],
                coupon["app"],
                coupon["discount"],
                coupon.get("issuer", ""),
                coupon.get("source", ""),
                coupon.get("url", ""),
            ),
        )
        conn.commit()
    return cursor.rowcount > 0


def list_coupons():

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT id, title, code, app, discount, issuer, source, url
            FROM coupons
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
    return rows
