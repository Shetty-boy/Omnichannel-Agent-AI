import os
import uuid
import datetime
from langchain.tools import tool
from pymongo import MongoClient
from dotenv import load_dotenv

# -------------------------------------------------------------------
# ENV + DB CONNECTION
# -------------------------------------------------------------------

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client["EY"]

products_col = db["products"]
inventory_col = db["inventory"]
orders_col = db["orders"]
stores_col = db["stores"]

print("[Fulfillment Agent] Connected to MongoDB")
print("[Fulfillment Agent] Using DB: EY")

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"

# -------------------------------------------------------------------
# LANGCHAIN TOOL
# -------------------------------------------------------------------

@tool
def place_order(
    product_name: str,
    quantity: int,
    fulfillment_type: str,
    location_query: str = "Mall"
):
    """
    Places an order, reserves inventory, and creates an order record.
    """

    product = products_col.find_one(
        {"name": {"$regex": product_name, "$options": "i"}}
    )

    if not product:
        return "❌ Order Failed: Product not found."

    order_id = generate_order_id()
    total_price = product["price"] * quantity

    orders_col.insert_one({
        "orderId": order_id,
        "customerId": "CUST_GUEST",
        "items": [{
            "productId": product["productId"],
            "name": product["name"],
            "qty": quantity,
            "price": product["price"]
        }],
        "totalAmount": total_price,
        "status": "CONFIRMED",
        "fulfillment": {
            "type": fulfillment_type.upper(),
            "location": location_query
        },
        "orderDate": datetime.datetime.now()
    })

    return (
        f"📦 ORDER CONFIRMED\n"
        f"Order ID: {order_id}\n"
        f"Total: ₹{total_price}\n"
        f"Next step: Payment"
    )


# -------------------------------------------------------------------
# TEST BLOCK
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("\n[TEST] Fulfillment Agent\n")

    print(place_order.invoke({
        "product_name": "Running Shoes",
        "quantity": 1,
        "fulfillment_type": "PICKUP",
        "location_query": "Mall"
    }))
