from fastmcp import FastMCP
from langchain_core.runnables import RunnableConfig
from shopeasy.app.services.customer_service import get_customer_prefrence, get_customer_profile
from shopeasy.app.services.order_service import get_order_history, get_order_details, get_order_status
from shopeasy.app.services.payment_service import get_refund_history, get_payment_status


def get_customer_id() -> int:
    return 1

mcp = FastMCP(name= "Shopeasy")

#Customer level Tools
@mcp.tool
def customer_profile() -> dict:
    """Retrieve the profile of an authenticated ShopEasy customer."""
    customer_id = get_customer_id()
    return get_customer_profile(customer_id)


@mcp.tool
def customer_prefrence(config: RunnableConfig) -> list[dict]:
    """Retrieve a list of dict of customer prefencese"""
    customer_id = config["configurable"]["customer_id"]
    return get_customer_prefrence(customer_id)


#Order level Tools
@mcp.tool
def order_details(config: RunnableConfig, order_id):
    """Get order deatils for a cutomer order"""
    customer_id = config["configurable"]["customer_id"]

    return get_order_details(customer_id, order_id)

@mcp.tool
def order_status(config: RunnableConfig, order_id):
    """Get order status for a cutomer order"""
    customer_id = config["configurable"]["customer_id"]

    return get_order_status(customer_id, order_id)

@mcp.tool
def order_history(config: RunnableConfig):
    """get customer order history"""
    customer_id = config["configurable"]["customer_id"]

    return get_order_history(customer_id)

#Payment level tools
@mcp.tool
def order_details(order_id: int):
    """Get order deatils for a cutomer order"""
    return get_payment_status(order_id)
@mcp.tool
def refund_history(order_id: int):
    """get order refund history"""
    return get_refund_history(order_id)


if __name__ == "__main__":
    mcp.run()