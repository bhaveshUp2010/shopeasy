
import sqlite3
from pathlib import Path
from datetime import date, timedelta


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DB_PATH = Path(__file__).resolve().parent.parent / "support.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------------------------
# DATABASE SCHEMA
# --------------------------------------------------

def create_db():
    conn = get_connection()

    try:
        conn.executescript("""

        DROP TABLE IF EXISTS customer_memory;
        DROP TABLE IF EXISTS tickets;
        DROP TABLE IF EXISTS refunds;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            phone TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            total_amount_cents INTEGER NOT NULL
                CHECK(total_amount_cents >= 0),
            currency TEXT NOT NULL DEFAULT 'INR',
            status TEXT NOT NULL CHECK(
                status IN (
                    'placed', 'shipped', 'delivered',
                    'cancelled', 'returned'
                )
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            delivered_at TEXT,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),

            CHECK (
                (status = 'delivered' AND delivered_at IS NOT NULL)
                OR
                (status != 'delivered' AND delivered_at IS NULL)
            )
        );

        CREATE TABLE refunds (
            refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            reason TEXT NOT NULL,
            status TEXT NOT NULL CHECK(
                status IN (
                    'requested', 'approved',
                    'rejected', 'processed'
                )
            ),
            requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            processed_at TEXT,

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
        );

        CREATE TABLE tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_id INTEGER,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open' CHECK(
                status IN (
                    'open', 'in_progress',
                    'resolved', 'closed'
                )
            ),
            priority TEXT NOT NULL DEFAULT 'medium' CHECK(
                priority IN ('low', 'medium', 'high')
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),

            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
        );

        CREATE TABLE customer_memory (
            memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            memory_type TEXT NOT NULL,
            memory_content TEXT NOT NULL,
            source_ticket_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),

            FOREIGN KEY (source_ticket_id)
                REFERENCES tickets(ticket_id)
        );

        CREATE INDEX idx_orders_customer
        ON orders(customer_id);

        CREATE INDEX idx_tickets_customer
        ON tickets(customer_id);

        CREATE INDEX idx_memory_customer
        ON customer_memory(customer_id);

        CREATE INDEX idx_refunds_order
        ON refunds(order_id);

        """)

        conn.commit()
        print("Database schema created successfully!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# --------------------------------------------------
# SYNTHETIC CUSTOMERS
# --------------------------------------------------

customers = [
    (1, "Aarav Sharma", "aarav@gmail.com", "9876543210"),
    (2, "Priya Verma", "priya@gmail.com", "9876543211"),
    (3, "Rahul Mehta", "rahul@gmail.com", "9876543212"),
    (4, "Ananya Singh", "ananya@gmail.com", "9876543213"),
    (5, "Kabir Khan", "kabir@gmail.com", "9876543214"),
    (6, "Isha Gupta", "isha@gmail.com", "9876543215"),
    (7, "Rohan Patel", "rohan@gmail.com", "9876543216"),
    (8, "Meera Joshi", "meera@gmail.com", "9876543217"),
    (9, "Arjun Reddy", "arjun@gmail.com", "9876543218"),
    (10, "Sneha Kapoor", "sneha@gmail.com", "9876543219"),
]


# --------------------------------------------------
# SYNTHETIC ORDERS
# Amounts are stored in paise.
# Customer 10 intentionally has no orders.
# --------------------------------------------------

orders = [
    (1001, 1, 459900, "INR", "delivered", "2026-11-10"),
    (1002, 1, 129900, "INR", "shipped", None),
    (1003, 1, 89900, "INR", "returned", None),

    (1004, 2, 259900, "INR", "delivered", "2026-06-01"),
    (1005, 2, 79900, "INR", "cancelled", None),
    (1006, 2, 159900, "INR", "placed", None),

    (1007, 3, 899900, "INR", "delivered", "2026-03-15"),
    (1008, 3, 499900, "INR", "returned", None),
    (1009, 3, 59900, "INR", "shipped", None),

    (1010, 4, 199900, "INR", "delivered", "2026-11-05"),
    (1011, 4, 299900, "INR", "delivered", "2026-08-10"),
    (1012, 4, 99900, "INR", "cancelled", None),

    (1013, 5, 149900, "INR", "shipped", None),
    (1014, 5, 349900, "INR", "delivered", "2026-10-28"),
    (1015, 5, 89900, "INR", "placed", None),

    (1016, 6, 699900, "INR", "returned", None),
    (1017, 6, 129900, "INR", "delivered", "2026-11-15"),
    (1018, 6, 49900, "INR", "cancelled", None),

    (1019, 7, 399900, "INR", "delivered", "2026-07-20"),
    (1020, 7, 199900, "INR", "shipped", None),
    (1021, 7, 79900, "INR", "placed", None),

    (1022, 8, 599900, "INR", "delivered", "2026-11-01"),
    (1023, 8, 89900, "INR", "returned", None),
    (1024, 8, 129900, "INR", "shipped", None),

    (1025, 9, 249900, "INR", "cancelled", None),
    (1026, 9, 799900, "INR", "delivered", "2026-05-12"),
    (1027, 9, 159900, "INR", "returned", None),

    # These three orders belong to customer 9.
    # Customer 10 intentionally has zero orders.
    (1028, 9, 99900, "INR", "delivered", "2026-09-15"),
    (1029, 9, 449900, "INR", "shipped", None),
    (1030, 9, 299900, "INR", "placed", None),
]


# --------------------------------------------------
# SYNTHETIC REFUNDS
# --------------------------------------------------

refunds = [
    (1, 1003, 89900, "Product was damaged", "processed"),
    (2, 1005, 79900, "Customer cancelled order", "processed"),
    (3, 1008, 499900, "Wrong product delivered", "approved"),
    (4, 1012, 99900, "Order cancellation", "processed"),
    (5, 1016, 699900, "Product stopped working", "requested"),
    (6, 1018, 49900, "Duplicate order", "rejected"),
    (7, 1023, 89900, "Received defective product", "processed"),
    (8, 1025, 249900, "Delivery taking too long", "processed"),
    (9, 1027, 159900, "Product not as described", "requested"),
]


# --------------------------------------------------
# SYNTHETIC SUPPORT TICKETS
# --------------------------------------------------

tickets = [
    (1, 1, 1003, "Damaged product received",
     "The product arrived with a broken outer casing.",
     "resolved", "high"),

    (2, 1, 1002, "Delivery status inquiry",
     "My order has been shipped but tracking has not updated.",
     "open", "medium"),

    (3, 2, 1005, "Cancellation confirmation",
     "I cancelled my order but want to confirm the refund.",
     "resolved", "medium"),

    (4, 2, 1006, "Product information",
     "Can you confirm the expected delivery date?",
     "open", "low"),

    (5, 3, 1008, "Wrong product delivered",
     "I received a different product from what I ordered.",
     "in_progress", "high"),

    (6, 4, 1010, "Invoice request",
     "I need an invoice for my recent purchase.",
     "closed", "low"),

    (7, 4, 1012, "Refund status",
     "Please confirm whether my cancelled order was refunded.",
     "resolved", "medium"),

    (8, 5, 1013, "Shipping delay",
     "My order has been shipped but is taking longer than expected.",
     "open", "medium"),

    (9, 6, 1016, "Product stopped working",
     "The product stopped working after two days of usage.",
     "in_progress", "high"),

    (10, 7, 1020, "Tracking information",
     "Please provide the latest tracking information.",
     "open", "low"),

    (11, 8, 1023, "Defective product",
     "The product does not turn on after delivery.",
     "resolved", "high"),

    (12, 9, 1025, "Order cancellation",
     "I want to cancel this order because of the delay.",
     "closed", "medium"),

    (13, 9, 1027, "Product mismatch",
     "The received product does not match the description.",
     "open", "high"),

    (14, 10, None, "Payment issue",
     "I was charged twice for a purchase.",
     "in_progress", "high"),

    # No order linked because customer 10 has no orders.
    (15, 10, None, "General support inquiry",
     "Can you help me understand the available products?",
     "open", "medium"),
]


# --------------------------------------------------
# SYNTHETIC CUSTOMER MEMORIES
# --------------------------------------------------

memories = [
    (1, 1, "preference",
     "Prefers email communication over phone calls.", None),

    (2, 1, "issue",
     "Previously received a damaged product and requested a refund.", 1),

    (3, 2, "preference",
     "Prefers quick refunds instead of replacement products.", None),

    (4, 2, "preference",
     "Usually asks for delivery estimates before purchasing.", 4),

    (5, 3, "issue",
     "Previously received an incorrect product.", 5),

    (6, 4, "preference",
     "Requires invoices for purchases.", 6),

    (7, 5, "preference",
     "Prefers SMS updates for shipping notifications.", None),

    (8, 6, "issue",
     "Previously reported an electronic product malfunction.", 9),

    (9, 7, "preference",
     "Prefers concise customer support responses.", None),

    (10, 8, "issue",
     "Previously received a defective product.", 11),

    (11, 9, "preference",
     "Prefers cancellation and refund when delivery is significantly delayed.", 12),

    (12, 10, "issue",
     "Previously reported a possible duplicate payment.", 14),
]


# --------------------------------------------------
# SEED DATABASE
# --------------------------------------------------


def seed_database():

    conn = get_connection()

    try:
        with conn:

            conn.executemany("""
                INSERT INTO customers
                (customer_id, name, email, phone)
                VALUES (?, ?, ?, ?)
            """, customers)

            # Fixed reference date for reproducible seed data
            reference_date = date(2026, 11, 21)

            orders_with_created_at = []

            for order in orders:

                order_id, customer_id, amount, currency, status, delivered_at = order

                if delivered_at:
                    # Order must be created before delivery
                    delivery_date = date.fromisoformat(delivered_at)
                    days_before = 2 + (order_id % 6)
                    created_at = delivery_date - timedelta(days=days_before)

                else:
                    # Assign realistic ages based on order status
                    if status == "shipped":
                        days_old = 1 + (order_id % 4)

                    elif status == "placed":
                        days_old = order_id % 2

                    elif status == "returned":
                        days_old = 14 + (order_id % 20)

                    elif status == "cancelled":
                        days_old = 2 + (order_id % 14)

                    created_at = reference_date - timedelta(days=days_old)

                orders_with_created_at.append((
                    order_id,
                    customer_id,
                    amount,
                    currency,
                    status,
                    created_at.isoformat(),
                    delivered_at
                ))

            conn.executemany("""
                INSERT INTO orders
                (order_id, customer_id, total_amount_cents,
                 currency, status, created_at, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, orders_with_created_at)

            conn.executemany("""
                INSERT INTO refunds
                (refund_id, order_id, amount_cents,
                 reason, status)
                VALUES (?, ?, ?, ?, ?)
            """, refunds)

            conn.executemany("""
                INSERT INTO tickets
                (ticket_id, customer_id, order_id,
                 subject, description, status, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, tickets)

            conn.executemany("""
                INSERT INTO customer_memory
                (memory_id, customer_id, memory_type,
                 memory_content, source_ticket_id)
                VALUES (?, ?, ?, ?, ?)
            """, memories)

        print("Database seeded successfully!")

        print("Customers:", len(customers))
        print("Orders:", len(orders))
        print("Refunds:", len(refunds))
        print("Tickets:", len(tickets))
        print("Memories:", len(memories))

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

# --------------------------------------------------
# VERIFY DATABASE
# --------------------------------------------------

def verify_database():

    conn = get_connection()

    try:
        tables = [
            "customers",
            "orders",
            "refunds",
            "tickets",
            "customer_memory"
        ]

        print("\nDATABASE VERIFICATION")

        for table in tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count} records")

        no_order_customers = conn.execute("""
            SELECT c.customer_id, c.name
            FROM customers c
            LEFT JOIN orders o
                ON c.customer_id = o.customer_id
            WHERE o.order_id IS NULL
        """).fetchall()

        print("\nCustomers without orders:", no_order_customers)

        foreign_key_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("Foreign key errors:", foreign_key_errors)
        invalid_orders = conn.execute("""
            SELECT order_id, created_at, delivered_at
            FROM orders
            WHERE delivered_at IS NOT NULL
            AND created_at >= delivered_at
        """).fetchall()

        print("Orders with invalid timestamps:", invalid_orders)

    finally:
        conn.close()


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    create_db()
    seed_database()
    verify_database()
