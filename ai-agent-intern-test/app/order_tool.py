import json
import re
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
BASE_DIR = Path(__file__).resolve().parent.parent
ORDERS_PATH = BASE_DIR / "data" / "orders.json"


def normalize_order_id(order_id):
    order_id = order_id.strip().upper()
    order_id = re.sub(r"[^\w-]", "", order_id)
    return order_id

logging.info("Order ID normalization function loaded successfully.")
def load_orders():
    with open(ORDERS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

logging.info("Orders loaded successfully.")
def lookup_order(order_id):
    data = load_orders()
    normalized_id = normalize_order_id(order_id)

    for order in data["orders"]:
        if order["order_id"] == normalized_id:

            return {
                "order_id": order["order_id"],
                "membership_tier": order["membership_tier"],
                "items": [
                    {
                        "name": item["name"],
                        "quantity": item["quantity"],
                        "final_sale": item["final_sale"]
                    }
                    for item in order["items"]
                ],
                "placed_at": order["placed_at"],
                "status": order["status"],
                "status_updated_at": order["status_updated_at"],
                "shipped_at": order["shipped_at"],
                "delivered_at": order["delivered_at"],
                "carrier": order["carrier"],
                "tracking_number": order["tracking_number"],
                "estimated_delivery": order["estimated_delivery"],
                "customer_safe_message": order["customer_safe_message"]
            }

    return None

logging.info("Order lookup function loaded successfully.")
def get_order_status(order):
    if order is None:
        return (
            "The order was not found. Please check the order ID or contact support."
            "Please check the order ID or contact support."
        )
    status = order["status"]

    if status == "cancelled":
        return "This order has been cancelled and will not be shipped."

    if status == "returned":
        return "This order has been returned."

    if status == "exception":
        return "This order requires support review."

    if status == "shipped":
        carrier = order.get("carrier")
        estimated_delivery = order.get("estimated_delivery")

        if estimated_delivery is None:
            return (
                f"The order has shipped with {carrier}. "
                "The delivery estimate is unavailable."
            )

        delivery_date = datetime.strptime(
            estimated_delivery,
            "%Y-%m-%d"
        ).strftime("%B %d, %Y")


        
        return (
            f"The order has shipped with {carrier} and is currently "
            f"estimated to arrive on {delivery_date}."
        )

    return order["customer_safe_message"]

logging.info("Order status retrieval function loaded successfully.")
if __name__ == "__main__":
   if __name__ == "__main__":
    order = lookup_order("ORD-1007")

    print("ORDER:", order)
    print("ETA VALUE:", order.get("estimated_delivery") if order else None)
    print(
        "ETA TYPE:",
        type(order.get("estimated_delivery")) if order else type(None),
    )
    print("STATUS RESPONSE:", get_order_status(order))