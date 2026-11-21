from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Literal
from shopeasy.app.db import *

@tool
def get_order_status(config: RunnableConfig, order_id: int):
    """Return order status for a specific order 
    input args:config: Runnable config, order id: int"""

    cust_id = config["configurable"]["customer_id"]

    order = get_order(order_id=order_id, cust_id=cust_id)
    if not order:
        return "this order does not belong to you or does not exist"
    return dict(order)


@tool
def get_all_orders(config: RunnableConfig):
    """Return all orders for a customer"""

    cust_id = config["configurable"]["customer_id"]
    orders = get_customer_orders(cust_id)

    if not orders:
        return "no existing orders for the customer"
    return [dict(order) for order in orders]


@tool
def create_ticket(
    config: RunnableConfig,
    subject: str,
    description: str,
    priority: Literal["low", "medium", "high"],
    order_id: int | None = None
):
    """Create a customer support ticket."""

    cust_id = config["configurable"]["customer_id"]

    # Verify order ownership if an order ID is provided
    if order_id is not None:
        order = get_order(order_id=order_id, cust_id=cust_id)

        if not order:
            return "Cannot create ticket: invalid order ID."

    ticket_id = create_ticket_db(
        cust_id,
        subject,
        description,
        priority,
        order_id
    )

    return {
        "message": "Support ticket created successfully.",
        "ticket_id": ticket_id
    }

@tool
def create_refund(
    config: RunnableConfig,
    reason: str,
    order_id: int 
):

    """Create a refund request after verifying order ownership
    and refund eligibility. Calculate the amount using database data."""
    cust_id = config["configurable"]["customer_id"]
    order = get_order(order_id= order_id, cust_id= cust_id)
    if not order:
        return "Cannot create Refund: Invalid order id"

    amount_cents = order["total_amount_cents"]

    refund_id = create_refund_db(
        order_id,
        amount_cents,
        reason
    )

    return {
        "message": "refund create successfully",
        "refund_id": refund_id
    }