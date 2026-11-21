import sqlite3
from pathlib import Path 

DB_PATH = Path(__file__).resolve().parent.parent / "support.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_order(order_id: int, cust_id: int) -> sqlite3.Row | None:
    conn = get_connection()

    try:
        cursor = conn.execute(
            """SELECT *
            FROM orders
            WHERE order_id = ? AND customer_id = ?;""",
            (order_id, cust_id))
        return cursor.fetchone()
    finally:
        conn.close()


    

def get_customer_orders(cust_id: int) -> list[sqlite3.Row] :
    conn = get_connection()

    try:
        cursor = conn.execute(
            """SELECT *
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC;
            """,
            (cust_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def create_ticket(
    customer_id: int,
    subject: str,
    description: str,
    priority: str,
    order_id: int | None = None
):

    conn = get_connection()

    try:
        cursor = conn.execute("""
        INSERT INTO tickets (
        customer_id,
        order_id,
        subject,
        description,
        priority
        )
        VALUES (?, ?, ?, ?, ?);""",
        (customer_id, order_id, subject, description, priority)
        )
        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def create_refund(
    order_id: int,
    amount_cents: int,
    reason: str

):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO refunds (
            order_id,
            amount_cents,
            reason
        )
        VALUES (?, ?, ?);""",
        (order_id, amount_cents, reason)
        )
        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
