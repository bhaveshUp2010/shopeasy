from datetime import datetime, timedelta , timezone
import sqlite3
from shopeasy.app.database.connection import get_connection, DB_PATH, SCHEMA

def iso_days_ago(days: int) -> str:
    """Return a deterministic relative date/time for seed records."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).replace(
        microsecond=0
    ).isoformat()


def seed_db(conn: sqlite3.Connection)  -> None:
    now = iso_days_ago(0)

    customers = [
            (1, "Aarav Sharma", "aarav.sharma@example.test", "9000000001", "active", iso_days_ago(420)),
            (2, "Priya Verma", "priya.verma@example.test", "9000000002", "active", iso_days_ago(390)),
            (3, "Rahul Mehta", "rahul.mehta@example.test", "9000000003", "active", iso_days_ago(300)),
            (4, "Ananya Singh", "ananya.singh@example.test", "9000000004", "active", iso_days_ago(250)),
            (5, "Kabir Khan", "kabir.khan@example.test", "9000000005", "active", iso_days_ago(180)),
            (6, "Isha Gupta", "isha.gupta@example.test", "9000000006", "active", iso_days_ago(150)),
            (7, "Rohan Patel", "rohan.patel@example.test", "9000000007", "active", iso_days_ago(90)),
            (8, "Meera Joshi", "meera.joshi@example.test", "9000000008", "active", iso_days_ago(30)),
        ]
    conn.executemany(
            """INSERT OR IGNORE INTO customers
            (customer_id, full_name, email, phone, account_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            customers,
        )

    addresses = [
            (1, 1, "shipping", "12 Green Park Road", "Near Metro Station", "New Delhi", "Delhi", "110016", "India", 1),
            (2, 2, "shipping", "44 Indiranagar", "12th Main", "Bengaluru", "Karnataka", "560038", "India", 1),
            (3, 3, "shipping", "8 Baner Road", None, "Pune", "Maharashtra", "411045", "India", 1),
            (4, 4, "shipping", "21 Salt Lake", "Sector V", "Kolkata", "West Bengal", "700091", "India", 1),
            (5, 5, "shipping", "16 Banjara Hills", None, "Hyderabad", "Telangana", "500034", "India", 1),
            (6, 6, "shipping", "9 Civil Lines", None, "Jaipur", "Rajasthan", "302006", "India", 1),
            (7, 7, "shipping", "71 Vastrapur", None, "Ahmedabad", "Gujarat", "380015", "India", 1),
            (8, 8, "shipping", "5 Panaji Market Road", None, "Panaji", "Goa", "403001", "India", 1),
        ]
    conn.executemany(
            """INSERT OR IGNORE INTO customer_addresses
            (address_id, customer_id, address_type, line1, line2, city, state,
                postal_code, country, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            addresses,
        )

    products = [
            (1, "PHN-001", "Nova X5 Smartphone", "Electronics", 2499900, 40, 1),
            (2, "AUD-002", "SonicBuds Wireless Earbuds", "Electronics", 399900, 100, 1),
            (3, "LAP-003", "AeroBook 14 Laptop", "Computers", 6299900, 15, 1),
            (4, "WAT-004", "PulseFit Smartwatch", "Wearables", 599900, 60, 1),
            (5, "HOM-005", "BrewMate Coffee Maker", "Home", 289900, 35, 1),
            (6, "ACC-006", "65W USB-C Charger", "Accessories", 179900, 150, 1),
            (7, "HOM-007", "AirPure Mini", "Home", 749900, 25, 1),
            (8, "ACC-008", "Protective Phone Case", "Accessories", 49900, 200, 1),
            (9, "TAB-009", "ReadPro 10 Tablet", "Electronics", 1899900, 22, 1),
            (10, "CAM-010", "SnapShot Compact Camera", "Electronics", 3299900, 12, 1),
        ]
    conn.executemany(
            """INSERT OR IGNORE INTO products
            (product_id, sku, product_name, category, unit_price_paise, stock_quantity, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            products,
        )

        # Each order: id, number, customer, status, days ago, item tuples,
        # discount paise, shipping fee paise.
    order_specs = [
            (1001, "SE-2026-01001", 1, "delivered", 5,  [(1, 1), (8, 1)], 100000, 0),
            (1002, "SE-2026-01002", 1, "shipped", 1,   [(2, 1), (6, 1)], 0, 5000),
            (1003, "SE-2026-01003", 2, "cancelled", 3, [(3, 1)], 0, 0),
            (1004, "SE-2026-01004", 2, "delivered", 45, [(5, 1), (6, 1)], 20000, 0),
            (1005, "SE-2026-01005", 3, "processing", 0, [(9, 1)], 0, 0),
            (1006, "SE-2026-01006", 3, "return_requested", 12, [(4, 1), (2, 1)], 0, 0),
            (1007, "SE-2026-01007", 4, "delivered", 18, [(7, 1)], 0, 0),
            (1008, "SE-2026-01008", 4, "delivered", 4, [(6, 2), (8, 2)], 0, 0),
            (1009, "SE-2026-01009", 5, "cancelled", 2, [(10, 1)], 0, 0),
            (1010, "SE-2026-01010", 5, "delivered", 8, [(1, 1)], 250000, 0),
            (1011, "SE-2026-01011", 6, "shipped", 2, [(5, 1), (2, 1)], 0, 5000),
            (1012, "SE-2026-01012", 7, "returned", 25, [(9, 1)], 0, 0),
            (1013, "SE-2026-01013", 8, "placed", 0, [(8, 2), (6, 1)], 0, 5000),
        ]

    item_id = 1
    order_rows = []
    item_rows = []
    for order_id, order_no, customer_id, status, age, items, discount, shipping in order_specs:
        subtotal = 0
        for product_id, quantity in items:
            price = conn.execute(
                "SELECT unit_price_paise FROM products WHERE product_id = ?",
                (product_id,),
            ).fetchone()[0]
            line_total = price * quantity
            subtotal += line_total
            item_rows.append((item_id, order_id, product_id, quantity, price, line_total))
            item_id += 1

        total = subtotal - discount + shipping
        placed = iso_days_ago(age)
        order_rows.append((
            order_id, order_no, customer_id, customer_id, status,
            subtotal, discount, shipping, total, "INR", placed, now
        ))

    conn.executemany(
        """INSERT OR IGNORE INTO orders
        (order_id, order_number, customer_id, shipping_address_id, order_status,
            subtotal_paise, discount_paise, shipping_fee_paise, total_amount_paise,
            currency, placed_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        order_rows,
    )
    conn.executemany(
        """INSERT OR IGNORE INTO order_items
        (order_item_id, order_id, product_id, quantity, unit_price_paise, line_total_paise)
        VALUES (?, ?, ?, ?, ?, ?)""",
        item_rows,
    )

    # Payment status is deliberately varied to test payment and refund questions.
    payment_specs = [
        (5001, 1001, "Razorpay", "UPI", "captured", "PAY-SE-1001", 5),
        (5002, 1002, "Razorpay", "credit_card", "captured", "PAY-SE-1002", 1),
        (5003, 1003, "Razorpay", "UPI", "refunded", "PAY-SE-1003", 3),
        (5004, 1004, "Cashfree", "debit_card", "captured", "PAY-SE-1004", 45),
        (5005, 1005, "Razorpay", "UPI", "pending", None, None),
        (5006, 1006, "Razorpay", "wallet", "captured", "PAY-SE-1006", 12),
        (5007, 1007, "Cashfree", "credit_card", "captured", "PAY-SE-1007", 18),
        (5008, 1008, "Razorpay", "UPI", "captured", "PAY-SE-1008", 4),
        (5009, 1009, "Razorpay", "net_banking", "failed", None, None),
        (5010, 1010, "Cashfree", "credit_card", "partially_refunded", "PAY-SE-1010", 8),
        (5011, 1011, "Razorpay", "UPI", "captured", "PAY-SE-1011", 2),
        (5012, 1012, "Razorpay", "debit_card", "refunded", "PAY-SE-1012", 25),
        (5013, 1013, "Razorpay", "UPI", "pending", None, None),
    ]
    payment_rows = []
    for payment_id, order_id, provider, method, status, ref, age in payment_specs:
        paid_at = iso_days_ago(age) if age is not None else None
        payment_rows.append((payment_id, order_id, provider, method,
                            conn.execute("SELECT total_amount_paise FROM orders WHERE order_id=?", (order_id,)).fetchone()[0],
                            status, ref, paid_at))
    conn.executemany(
        """INSERT OR IGNORE INTO payments
        (payment_id, order_id, payment_provider, payment_method, amount_paise,
            payment_status, transaction_reference, paid_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        payment_rows,
    )

    shipment_rows = [
        (6001, 1001, "Delhivery", "DLV-SE-1001", "delivered", iso_days_ago(4), iso_days_ago(0), iso_days_ago(0), "Delivered to customer"),
        (6002, 1002, "Blue Dart", "BD-SE-1002", "in_transit", iso_days_ago(1), iso_days_ago(-2), None, "Arrived at regional hub"),
        (6004, 1004, "Delhivery", "DLV-SE-1004", "delivered", iso_days_ago(43), iso_days_ago(40), iso_days_ago(40), "Delivered"),
        (6006, 1006, "Ecom Express", "EC-SE-1006", "delivered", iso_days_ago(11), iso_days_ago(9), iso_days_ago(9), "Delivered"),
        (6007, 1007, "Blue Dart", "BD-SE-1007", "delivered", iso_days_ago(17), iso_days_ago(15), iso_days_ago(15), "Delivered"),
        (6008, 1008, "Delhivery", "DLV-SE-1008", "delivered", iso_days_ago(3), iso_days_ago(1), iso_days_ago(1), "Delivered"),
        (6010, 1010, "Ecom Express", "EC-SE-1010", "delivered", iso_days_ago(7), iso_days_ago(5), iso_days_ago(5), "Delivered"),
        (6011, 1011, "Blue Dart", "BD-SE-1011", "in_transit", iso_days_ago(1), iso_days_ago(-2), None, "Shipment moving between hubs"),
        (6012, 1012, "Delhivery", "DLV-SE-1012", "returned_to_sender", iso_days_ago(24), iso_days_ago(21), None, "Return to seller completed"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO shipments
        (shipment_id, order_id, carrier, tracking_number, shipment_status,
            shipped_at, estimated_delivery, delivered_at, last_tracking_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        shipment_rows,
    )

    return_rows = [
        (7001, 1006, 9, 3, "Defective product", "Smartwatch does not charge.", "requested", iso_days_ago(1), None, None, None),
        (7002, 1007, 11, 4, "Changed mind", "Customer says the air purifier is no longer needed.", "approved", iso_days_ago(2), iso_days_ago(1), None, "refund"),
        (7003, 1012, 18, 7, "Wrong item received", "Customer received a different tablet model.", "completed", iso_days_ago(22), iso_days_ago(21), iso_days_ago(19), "refund"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO returns
        (return_id, order_id, order_item_id, customer_id, return_reason,
            customer_note, return_status, requested_at, reviewed_at, received_at, resolution)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        return_rows,
    )

    refund_rows = [
        (8001, 1003, 5003, None, 2, 6299900, "Order cancelled before dispatch",
        "completed", 0, iso_days_ago(3), iso_days_ago(3), iso_days_ago(3),
        iso_days_ago(2), "RF-SE-1003", "Payment reversal confirmed by provider"),
        (8002, 1007, 5007, 7002, 4, 749900, "Return approved",
        "pending_approval", 1, iso_days_ago(2), None, None, None, None,
        "Awaiting support manager review"),
        (8003, 1010, 5010, None, 5, 50000, "Partial goodwill refund",
        "completed", 0, iso_days_ago(6), iso_days_ago(6), iso_days_ago(6),
        iso_days_ago(5), "RF-SE-1010-P1", "Partial refund completed"),
        (8004, 1012, 5012, 7003, 7, 1899900, "Return received",
        "completed", 0, iso_days_ago(20), iso_days_ago(20), iso_days_ago(20),
        iso_days_ago(19), "RF-SE-1012", "Refund completed"),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO refunds
        (refund_id, order_id, payment_id, return_id, customer_id, amount_paise,
            refund_reason, refund_status, approval_required, requested_at,
            reviewed_at, initiated_at, completed_at, provider_refund_ref, decision_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        refund_rows,
    )

    ticket_rows = [
        (9001, "TKT-SE-9001", 1, 1002, "delivery", "Where is my package?",
        "The tracking page has not changed since yesterday.", "medium", "open", iso_days_ago(0), now),
        (9002, "TKT-SE-9002", 3, 1006, "product", "Smartwatch is not charging",
        "The watch does not power on even after charging overnight.", "high", "in_progress", iso_days_ago(1), now),
        (9003, "TKT-SE-9003", 4, 1007, "refund", "Refund status for returned item",
        "The return was approved. Please tell me when the refund will arrive.", "medium", "waiting_for_internal_team", iso_days_ago(1), now),
        (9004, "TKT-SE-9004", 5, 1009, "payment", "Payment failed but order is cancelled",
        "Please confirm that no amount was captured.", "low", "resolved", iso_days_ago(2), iso_days_ago(1)),
        (9005, "TKT-SE-9005", 6, None, "account", "Update contact number",
        "I need help updating the phone number on my account.", "low", "open", iso_days_ago(0), now),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO support_tickets
        (ticket_id, ticket_number, customer_id, order_id, category, subject,
            description, priority, ticket_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ticket_rows,
    )

    message_rows = [
        (10001, 9001, "customer", "Can you check the latest location of my package?", iso_days_ago(0)),
        (10002, 9001, "agent", "I can see the shipment is in transit at the regional hub.", now),
        (10003, 9002, "customer", "I have tried another charger as well.", iso_days_ago(1)),
        (10004, 9002, "agent", "We have escalated the issue to the product support team.", now),
        (10005, 9003, "customer", "Please share the expected refund timeline.", iso_days_ago(1)),
        (10006, 9004, "agent", "The payment provider reports that the transaction failed.", iso_days_ago(1)),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO ticket_messages
        (message_id, ticket_id, sender_type, message_text, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        message_rows,
    )

    preference_rows = [
        (11001, 1, "preferred_contact_channel", "email", "customer_provided", iso_days_ago(30), now),
        (11002, 1, "language", "English", "customer_provided", iso_days_ago(30), now),
        (11003, 3, "preferred_contact_channel", "phone", "customer_provided", iso_days_ago(20), now),
        (11004, 4, "delivery_instruction", "Call before delivery", "customer_provided", iso_days_ago(10), now),
        (11005, 6, "language", "Hindi", "customer_provided", iso_days_ago(15), now),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO customer_preferences
        (preference_id, customer_id, preference_key, preference_value,
            source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        preference_rows,
    )

    audit_rows = [
        (12001, 1, "thread-customer-1-demo", "get_order_status",
        "Retrieved status for order SE-2026-01002", "success", now),
        (12002, 4, "thread-customer-4-demo", "create_refund_request",
        "Created refund request for approved return", "success", now),
    ]
    conn.executemany(
        """INSERT OR IGNORE INTO agent_audit_log
        (audit_id, customer_id, thread_id, tool_name, action_summary, outcome, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        audit_rows,
    )



def print_summary(conn: sqlite3.Connection) -> None:
    tables = [
        "customers", "customer_addresses", "products", "orders", "order_items",
        "payments", "shipments", "returns", "refunds", "support_tickets",
        "ticket_messages", "customer_preferences", "agent_audit_log",
    ]
    print(f"\ndata ingested at: {DB_PATH}")
    print("\nSeeded record counts:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:24s} {count:>4}")

    print("\nDemo customer IDs: 1 through 8")
    print("Useful demo orders: 1001 through 1013")
    print("Useful demo tickets: 9001 through 9005")
    print("Useful demo refunds: 8001 through 8004")


def create_db(conn: sqlite3.Connection):

    try :
        conn.executescript(SCHEMA)
        conn.commit()
        print("DB create succesfully")
    except Exception:
        print(Exception)
        conn.rollback()
        raise

    


if __name__ == "__main__":
    conn = get_connection()

    try:
        with conn:
            create_db(conn)
            seed_db(conn)
        print_summary(conn)

    finally:
        conn.close()
