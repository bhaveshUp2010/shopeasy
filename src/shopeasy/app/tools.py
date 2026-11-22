from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import Literal
from shopeasy.app.db import *
from shopeasy.rag.vectorstore import get_retriever
from langgraph.types import interrupt
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

def _rupees(cents: int) -> str:
    return f"Rs{cents / 100:,.2f}"

@tool
def create_refund(config: RunnableConfig, order_id: int, reason: str) -> str:
    """Request a refund for one of the customer's delivered orders.

    Use only when the customer clearly asks for a refund and has given an order
    and a reason. Eligibility is checked automatically. Refunds of ₹2,000 or less
    are processed instantly; larger ones are sent to a manager for review.
    The refund is always for the full order total. Report only what this tool returns.
    """
    cust_id = config["configurable"]["customer_id"]
    thread_id = config["configurable"]["thread_id"]

    result = create_refund_db(
        cust_id=cust_id, order_id=order_id, reason=reason, thread_id=thread_id
    )
    if not result["success"]:
        return result["message"]

    amount = _rupees(result["amount_cents"])
    rid = result["refund_id"]

    if not result["needs_approval"]:
        return f"Refund #{rid} of {amount} for order {order_id} has been approved and processed."
    return (f"Refund request #{rid} for {amount} on order {order_id} has been submitted. "
            f"Because it is over ₹2,000, a manager needs to review it. "
            f"The customer can ask for its status at any time.")


@tool
def rag_tool(query: str) : 
    """
    Retrieve relevant information from the PDF document.

    Use this tool when the user asks factual or conceptual questions
    that may be answered using the stored docs in vector db.

    Args:
        query: The question or search query used to retrieve PDF content.
    """

    retriever = get_retriever()
    docs = retriever.invoke(query)

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