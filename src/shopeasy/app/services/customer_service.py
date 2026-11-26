from shopeasy.app.database.connection import get_connection

class CustomerNotFound(Exception):
    """"""

def get_customer_profile(customer_id: int) -> dict:

    with get_connection() as conn:
        customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)).fetchone()

        if customer is None:
            raise CustomerNotFound(f"No customer exist with id : {customer_id}")

    return dict(customer)


def get_customer_prefrence(customer_id: int) -> list[dict]:

    with get_connection() as conn:
        prefrences = conn.execute("""
        SELECT *
        FROM customer_preferences
        WHERE customer_id = ?""",
        (customer_id,)).fetchall()
    return [dict(prefrence) for prefrence in prefrences]
