import sqlite3 
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "shopeasy.db"

SCHEMA = SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id       INTEGER PRIMARY KEY,
    full_name         TEXT NOT NULL,
    email             TEXT NOT NULL UNIQUE COLLATE NOCASE,
    phone             TEXT,
    account_status    TEXT NOT NULL DEFAULT 'active'
                      CHECK (account_status IN ('active', 'suspended', 'closed')),
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_addresses (
    address_id        INTEGER PRIMARY KEY,
    customer_id       INTEGER NOT NULL,
    address_type      TEXT NOT NULL CHECK (address_type IN ('shipping', 'billing')),
    line1             TEXT NOT NULL,
    line2             TEXT,
    city              TEXT NOT NULL,
    state             TEXT NOT NULL,
    postal_code       TEXT NOT NULL,
    country           TEXT NOT NULL DEFAULT 'India',
    is_default        INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS products (
    product_id        INTEGER PRIMARY KEY,
    sku               TEXT NOT NULL UNIQUE,
    product_name      TEXT NOT NULL,
    category          TEXT NOT NULL,
    unit_price_paise  INTEGER NOT NULL CHECK (unit_price_paise >= 0),
    stock_quantity    INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS orders (
    order_id              INTEGER PRIMARY KEY,
    order_number          TEXT NOT NULL UNIQUE,
    customer_id           INTEGER NOT NULL,
    shipping_address_id   INTEGER,
    order_status          TEXT NOT NULL CHECK (
        order_status IN (
            'placed', 'processing', 'shipped', 'delivered',
            'cancelled', 'return_requested', 'returned'
        )
    ),
    subtotal_paise       INTEGER NOT NULL CHECK (subtotal_paise >= 0),
    discount_paise       INTEGER NOT NULL DEFAULT 0 CHECK (discount_paise >= 0),
    shipping_fee_paise   INTEGER NOT NULL DEFAULT 0 CHECK (shipping_fee_paise >= 0),
    total_amount_paise   INTEGER NOT NULL CHECK (total_amount_paise >= 0),
    currency             TEXT NOT NULL DEFAULT 'INR' CHECK (currency = 'INR'),
    placed_at            TEXT NOT NULL,
    updated_at           TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (shipping_address_id) REFERENCES customer_addresses(address_id),
    CHECK (total_amount_paise = subtotal_paise - discount_paise + shipping_fee_paise)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id       INTEGER PRIMARY KEY,
    order_id            INTEGER NOT NULL,
    product_id          INTEGER NOT NULL,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_paise    INTEGER NOT NULL CHECK (unit_price_paise >= 0),
    line_total_paise    INTEGER NOT NULL CHECK (line_total_paise = quantity * unit_price_paise),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id             INTEGER PRIMARY KEY,
    order_id               INTEGER NOT NULL UNIQUE,
    payment_provider       TEXT NOT NULL,
    payment_method         TEXT NOT NULL CHECK (
        payment_method IN ('UPI', 'credit_card', 'debit_card', 'net_banking', 'COD', 'wallet')
    ),
    amount_paise           INTEGER NOT NULL CHECK (amount_paise >= 0),
    payment_status         TEXT NOT NULL CHECK (
        payment_status IN ('pending', 'authorized', 'captured', 'failed',
                           'partially_refunded', 'refunded')
    ),
    transaction_reference  TEXT UNIQUE,
    paid_at                TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id          INTEGER PRIMARY KEY,
    order_id             INTEGER NOT NULL UNIQUE,
    carrier              TEXT NOT NULL,
    tracking_number      TEXT NOT NULL UNIQUE,
    shipment_status      TEXT NOT NULL CHECK (
        shipment_status IN ('label_created', 'picked_up', 'in_transit',
                            'out_for_delivery', 'delivered', 'exception', 'returned_to_sender')
    ),
    shipped_at           TEXT,
    estimated_delivery   TEXT,
    delivered_at         TEXT,
    last_tracking_note   TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS returns (
    return_id           INTEGER PRIMARY KEY,
    order_id            INTEGER NOT NULL,
    order_item_id       INTEGER,
    customer_id         INTEGER NOT NULL,
    return_reason       TEXT NOT NULL,
    customer_note       TEXT,
    return_status       TEXT NOT NULL CHECK (
        return_status IN ('requested', 'approved', 'rejected', 'pickup_scheduled',
                          'in_transit', 'received', 'completed', 'cancelled')
    ),
    requested_at        TEXT NOT NULL,
    reviewed_at         TEXT,
    received_at         TEXT,
    resolution          TEXT CHECK (resolution IN ('refund', 'replacement', 'store_credit')),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (order_item_id) REFERENCES order_items(order_item_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS refunds (
    refund_id               INTEGER PRIMARY KEY,
    order_id                INTEGER NOT NULL,
    payment_id              INTEGER NOT NULL,
    return_id               INTEGER,
    customer_id             INTEGER NOT NULL,
    amount_paise            INTEGER NOT NULL CHECK (amount_paise > 0),
    refund_reason           TEXT NOT NULL,
    refund_status           TEXT NOT NULL CHECK (
        refund_status IN ('requested', 'pending_approval', 'approved', 'rejected',
                          'processing', 'completed', 'failed')
    ),
    approval_required       INTEGER NOT NULL DEFAULT 1 CHECK (approval_required IN (0, 1)),
    requested_at            TEXT NOT NULL,
    reviewed_at             TEXT,
    initiated_at            TEXT,
    completed_at            TEXT,
    provider_refund_ref     TEXT UNIQUE,
    decision_note           TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (payment_id) REFERENCES payments(payment_id),
    FOREIGN KEY (return_id) REFERENCES returns(return_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id          INTEGER PRIMARY KEY,
    ticket_number      TEXT NOT NULL UNIQUE,
    customer_id        INTEGER NOT NULL,
    order_id           INTEGER,
    category           TEXT NOT NULL CHECK (
        category IN ('order_status', 'payment', 'return', 'refund', 'delivery',
                     'product', 'account', 'other')
    ),
    subject            TEXT NOT NULL,
    description        TEXT NOT NULL,
    priority           TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    ticket_status      TEXT NOT NULL CHECK (
        ticket_status IN ('open', 'in_progress', 'waiting_for_customer',
                          'waiting_for_internal_team', 'resolved', 'closed')
    ),
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS ticket_messages (
    message_id         INTEGER PRIMARY KEY,
    ticket_id          INTEGER NOT NULL,
    sender_type        TEXT NOT NULL CHECK (sender_type IN ('customer', 'agent', 'system')),
    message_text       TEXT NOT NULL,
    created_at         TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS customer_preferences (
    preference_id      INTEGER PRIMARY KEY,
    customer_id        INTEGER NOT NULL,
    preference_key     TEXT NOT NULL,
    preference_value   TEXT NOT NULL,
    source             TEXT NOT NULL DEFAULT 'customer_provided',
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    UNIQUE (customer_id, preference_key),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_audit_log (
    audit_id           INTEGER PRIMARY KEY,
    customer_id        INTEGER,
    thread_id          TEXT,
    tool_name          TEXT NOT NULL,
    action_summary     TEXT NOT NULL,
    outcome            TEXT NOT NULL CHECK (outcome IN ('success', 'failure', 'denied')),
    created_at         TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX IF NOT EXISTS idx_returns_customer ON returns(customer_id);
CREATE INDEX IF NOT EXISTS idx_refunds_customer ON refunds(customer_id);
CREATE INDEX IF NOT EXISTS idx_refunds_order ON refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_status ON support_tickets(customer_id, ticket_status);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_preferences_customer ON customer_preferences(customer_id);
"""


def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

