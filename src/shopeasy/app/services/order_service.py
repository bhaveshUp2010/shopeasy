from shopeasy.app.database.connection import get_connection

class OrderNotFound(Exception):
    """"""

def get_order_details(customer_id: int, order_id: int) -> dict:

    with get_connection() as conn:
        order = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE order_id = ?
              AND customer_id = ?
            """,
            (order_id, customer_id)
        ).fetchone()

        if order is None:
            raise OrderNotFound("order not found for this user")

        items = conn.execute(
            """
            SELECT
                oi.product_id,
                p.product_name,
                oi.quantity,
                oi.unit_price_paise
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,)
        ).fetchall()

        payment = conn.execute(
            """
            SELECT
                payment_status,
                payment_method,
                amount_paise
            FROM payments
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

        # 4. Retrieve shipment information.
        shipment = conn.execute(
            """
            SELECT
                carrier,
                tracking_number,
                shipment_status,
                estimated_delivery
            FROM shipments
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

    # 5. Convert database rows into ordinary Python dictionaries.
    return {
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "order_date": order["placed_at"],
        "status": order["order_status"],
        "total_amount_rupees": order["total_amount_paise"] / 100,

        "items": [
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price_rupees": item["unit_price_paise"] / 100
            }
            for item in items
        ],

        "payment": dict(payment) if payment else None,
        "shipment": dict(shipment) if shipment else None
    }


def get_order_status(customer_id: int, order_id: int) -> dict:
    with get_connection() as conn:
        order = conn.execute(
                    """
                    SELECT *
                    FROM orders
                    WHERE order_id = ?
                      AND customer_id = ?
                    """,
                    (order_id, customer_id)
                ).fetchone()

        if order is None:
            raise OrderNotFound("order not found")

        return {
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "status": order["order_status"]
        }

def get_order_history(customer_id: int) -> list[dict]:
    with get_connection() as conn:
        orders = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchall()

        if orders is None:
            raise OrderNotFound("customer has no orders")

        return [dict(order) for order in orders]
# print(get_order_details(1,1001))


print(get_order_history(1))