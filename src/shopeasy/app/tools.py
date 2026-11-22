from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Literal
from shopeasy.app.db import *
from shopeasy.rag.vectorstore import get_retriever

@tool
def get_order_status(config: RunnableConfig, order_id: int):
    """Return order status for a specific order """

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
    """Create a support ticket or add a complaint to an existing ticket."""

    customer_id = config["configurable"]["customer_id"]

    result = create_ticket_db(
        customer_id=customer_id,
        subject=subject,
        description=description,
        priority=priority,
        order_id=order_id
    )

    return result


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

    refund = create_refund_db(
        cust_id,
        order_id,
        amount_cents,
        reason
    )

    return refund


@tool
def rag_tool(qurey: str) : 
    """
    Retrieve relevant information from the PDF document.

    Use this tool when the user asks factual or conceptual questions
    that may be answered using the stored PDF documents.

    Args:
        query: The question or search query used to retrieve PDF content.
    """

    retriever = get_retriever()
    docs = retriever.invoke(qurey)

    if not docs:
        return "no relevant docs found in the vector store "
    formatted_docs = []

    for index, doc in enumerate(docs, start= 1):

        souce = doc.metadata.get("source", "unknown")
        formatted_docs.append(
            f"Document {index}\n"
            f"Source {souce}\n"
            f"content {doc.page_content}"
        )

    return "\n\n".join(formatted_docs)