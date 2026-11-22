import sqlite3
from pathlib import Path 
from datetime import timezone, datetime, date

DB_PATH = Path(__file__).resolve().parent.parent / "support.db"

ACTIVE_REFUND_MESSAGES = {
    "processed": ("already_processed", "A refund has already been processed for this order."),
    "approved":  ("already_approved",  "A refund for this order has already been approved."),
    "requested": ("already_requested", "A refund request is already pending for this order."),
}


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


def check_refund_eligibility(order) -> tuple[bool, str]:

    if order["status"] != "delivered":
        return False, f"only delivered oderers can be refunded"

    delivered = date.fromisoformat(order["delivered_at"])

    days_since = (date.today() - delivered).days
    if days_since > 30:
        return False, f"The {30}-day refund window has passed ({days_since} days since delivery)."

    return True, "eligeble"

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
    cust_id: int,
    order_id: int,
    reason: str,
    thread_id: str
):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute(
            """SELECT order_id, status, delivered_at, total_amount_cents
               FROM orders WHERE order_id = ? AND customer_id = ?;""",
            (order_id, cust_id),
        ).fetchone()

        if not order:
            conn.rollback()
            return {"success": False, "action": "not_found",
                    "message": "Order not found in this customer's account."}

        refunds = conn.execute(
            "SELECT * FROM refunds WHERE order_id = ? ORDER BY refund_id DESC;",
            (order_id,),
        ).fetchall()

        for r in refunds:
            if r["status"] == "requested" and  r["approval_thread_id"] == thread_id:
                conn.rollback()
                return {"success": True,
                        "action": "pending_resume",
                        "refund_id": r["refund_id"],
                        "order_id": r["order_id"],
                        "amount_cents": r["amount_cents"],
                        "needs_approval": True}

        for r in refunds:
            if r["status"] in ACTIVE_REFUND_MESSAGES:
                action, msg = ACTIVE_REFUND_MESSAGES[r["status"]]
                conn.rollback()
                return {"success": False, "action": action, "message": msg}

        eligible, why = check_refund_eligibility(order)
        if not eligible:
            conn.rollback()
            return {"success": False, "action": "not_eligible", "message": why}
        amount = order["total_amount_cents"]

        needs_approval = amount > 200000
        if needs_approval:
            cursor = conn.execute(
                """INSERT INTO refunds
                   (order_id, amount_cents, reason, status, approval_thread_id)
                   VALUES (?, ?, ?, 'requested', ?);""",
                   (order_id, amount, reason, thread_id)
            )
        else:
            cursor = conn.execute(
                """INSERT INTO refunds
                   (order_id, amount_cents, reason, status, approval_thread_id,
                    approved_by, decided_at, processed_at)
                   VALUES (?, ?, ?, 'processed', ?, 'auto',
                           CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);""",
                (order_id, amount, reason, thread_id),
            )

        refund_id = cursor.lastrowid
        conn.commit()

        return {"success": True, "action": "created", "refund_id": refund_id,
                "order_id": order_id,"amount_cents": amount, "needs_approval": needs_approval}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def resolve_refund_db(
    refund_id: int,
    approved: int, 
    approved_by: str,
    note: str = ""
) -> dict :
    conn = get_connection()

    try:
        with conn:
            cursor = conn.execute(
                """UPDATE refunds
                   SET status = ?, approved_by = ?, decision_note = ?,
                       decided_at = CURRENT_TIMESTAMP,
                       processed_at = CASE WHEN ? THEN CURRENT_TIMESTAMP END
                   WHERE refund_id = ? AND status = 'requested';""",
                ("processed" if approved else "rejected",
                 approved_by, note, approved, refund_id),   
            )

        if cursor.rowcount == 0 :
            return {"success": False, "message": "This refund was already decided or no longer exists."}

        return {"success" : True}
    finally:
        conn.close()