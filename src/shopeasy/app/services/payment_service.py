from shopeasy.app.database.connection import get_connection

def get_payment_status(order_id: int) -> dict:
    with get_connection() as conn:
            payment_status = conn.execute("""
            SELECT payment_id, order_id, paid_at
            payment_provider,payment_method, payment_status
            FROM payments
            WHERE order_id = ?
            """,
            (order_id,)).fetchone()
    
    
    return dict(payment_status)

def get_refund_history(order_id: int) -> dict:
    with get_connection() as conn:
        refund_history = conn.execute("""
        select payment_id, order_id, paid_at,
        payment_provider,payment_method, payment_status
        from payments
        where order_id = ?
        and payment_status = 'refunded'
        """,(order_id,)).fetchone() 

        if not refund_history :
            return {
                "message": "no refund history found for the order",
                "order_id": order_id
            }

    return dict(refund_history)





    