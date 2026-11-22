import sqlite3
from pathlib import Path 
from datetime import timezone, datetime

DB_PATH = Path(__file__).resolve().parent.parent / "support.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_order(order_id: int, cust_id: int) -> sqlite3.Row | None:
    """get order info"""
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

def get_refunds(order_id: int) -> list[sqlite3.Row]:
    """Return all refunds associated with an order."""

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT *
            FROM refunds
            WHERE order_id = ?
            ORDER BY requested_at DESC, refund_id DESC;
            """,
            (order_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_customer_orders(cust_id: int) -> list[sqlite3.Row] :

    """Return all orders for a customer"""
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


def create_ticket_db(
    customer_id: int,
    subject: str,
    description: str,
    priority: str,
    order_id: int | None = None
) -> dict:
    """Create a ticket or append a complaint to an existing active ticket."""

    priority_order = {
        "low": 1,
        "medium": 2,
        "high": 3
    }

    if priority not in priority_order:
        raise ValueError("Invalid ticket priority.")

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        # Verify ownership when an order ID is provided.
        if order_id is not None:
            order = conn.execute(
                """
                SELECT order_id
                FROM orders
                WHERE order_id = ?
                  AND customer_id = ?;
                """,
                (order_id, customer_id)
            ).fetchone()

            if not order:
                conn.rollback()
                return {
                    "success": False,
                    "action": "order_not_found",
                    "message": "Order not found in this customer's account."
                }

            # Find an existing active ticket.
            existing = conn.execute(
                """
                SELECT *
                FROM tickets
                WHERE customer_id = ?
                  AND order_id = ?
                  AND status IN ('open', 'in_progress')
                ORDER BY ticket_id DESC
                LIMIT 1;
                """,
                (customer_id, order_id)
            ).fetchone()

            if existing:
                ticket_id = existing["ticket_id"]

                timestamp = datetime.now(timezone.utc).isoformat()

                appended_description = (
                    f"{existing['description']}\n\n"
                    f"[Additional complaint - {timestamp}]\n"
                    f"Subject: {subject}\n"
                    f"Description: {description}"
                )

                old_priority = existing["priority"]

                # Increase priority only; never downgrade it.
                new_priority = (
                    priority
                    if priority_order[priority] > priority_order[old_priority]
                    else old_priority
                )

                conn.execute(
                    """
                    UPDATE tickets
                    SET description = ?,
                        priority = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ticket_id = ?
                      AND customer_id = ?;
                    """,
                    (
                        appended_description,
                        new_priority,
                        ticket_id,
                        customer_id
                    )
                )

                conn.commit()

                return {
                    "success": True,
                    "action": "updated",
                    "ticket_id": ticket_id,
                    "priority": new_priority,
                    "message": (
                        f"Complaint added to existing ticket #{ticket_id}."
                    )
                }

        # No active ticket found, or order_id is None.
        cursor = conn.execute(
            """
            INSERT INTO tickets (
                customer_id,
                order_id,
                subject,
                description,
                priority
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                customer_id,
                order_id,
                subject,
                description,
                priority
            )
        )

        ticket_id = cursor.lastrowid

        conn.commit()

        return {
            "success": True,
            "action": "created",
            "ticket_id": ticket_id,
            "priority": priority,
            "message": f"New support ticket #{ticket_id} created."
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
        
def create_refund_db(
    customer_id: int,
    order_id: int,
    amount_cents: int,
    reason: str
):
    conn = get_connection() 

    try:
        conn.execute("BEGIN IMMEDIATE")
        order = get_order(cust_id=customer_id, order_id= order_id)

        if not order:
            conn.rollback()
            return {
                "status" : False,
                "action" : "not found",
                "messge": "order not foung in this customer account"
            }

        refunds = get_refunds(order_id= order_id)

        processed = next(
            (r for r in refunds if r["status"] == "processed"),
            None
        )
        if processed:
            conn.rollback()
            return {
                "success": False,
                "action": "already_processed",
                "refund": dict(processed),
                "message": "A refund has already been processed for this order."
            }

        approved = next(
            (r for r in refunds if r["status"] == "approved"),
            None
        )   
        if approved:
            conn.rollback()
            return {
                "success": False,
                "action": "already_approved",
                "refund": dict(approved),
                "message": "A refund for this order has already been approved."
            }
        requested = next(
            (r for r in refunds if r["status"] == "requested"),
            None
        )
        if requested:
            conn.rollback()
            return {
                "success": False,
                "action": "already_requested",
                "refund": dict(requested),
                "message": "A refund request is already pending for this order."
            }
        cursor = conn.execute("""
        INSERT INTO refunds (
                order_id,
                amount_cents,
                reason,
                status
            )
            VALUES (?, ?, ?, 'requested');""",
            (order_id, amount_cents, reason))

        refund_id = cursor.lastrowid
        conn.commit()

        return {
            "success": True,
            "action": "created",
            "refund_id": refund_id,
            "message": f"Refund request #{refund_id} created successfully."
        }

    except Exception as e:
        conn.rollback()
        raise 

    finally:
        conn.close()
