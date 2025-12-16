import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URL)
db = client["EY"]

orders_col = db["orders"]
inventory_col = db["inventory"]
feedback_col = db["feedback"]

print("[Post-Purchase Agent] Connected to MongoDB")
print("[Post-Purchase Agent] Using DB: EY")


def handle_post_purchase(
    request_type: str,
    order_id: str,
    details: str | None = None,
    rating: int = 5
):
    """
    Handles post-purchase requests:
    - TRACK
    - RETURN
    - FEEDBACK
    """

    order = orders_col.find_one({"orderId": order_id})
    if not order:
        return f"❌ Order '{order_id}' not found."

    status = order.get("status", "UNKNOWN")
    fulfillment = order.get("fulfillment", {})

    # ---------------- TRACK ----------------
    if request_type.upper() == "TRACK":
        return (
            f"📦 TRACKING INFO\n"
            f"Order ID: {order_id}\n"
            f"Status: {status}\n"
            f"Fulfillment: {fulfillment.get('type', 'N/A')}"
        )

    # ---------------- RETURN ----------------
    if request_type.upper() == "RETURN":
        orders_col.update_one(
            {"orderId": order_id},
            {"$set": {
                "status": "RETURNED",
                "returnReason": details,
                "returnDate": datetime.datetime.now()
            }}
        )

        for item in order.get("items", []):
            inventory_col.update_one(
                {"productId": item["productId"],
                 "stockByLocation.locationId": fulfillment.get("locationId", "ONLINE")},
                {"$inc": {"stockByLocation.$.qty": item["qty"]}}
            )

        return f"🔄 RETURN PROCESSED for Order {order_id}"

    # ---------------- FEEDBACK ----------------
    if request_type.upper() == "FEEDBACK":
        feedback_col.insert_one({
            "orderId": order_id,
            "customerId": order.get("customerId", "GUEST"),
            "rating": rating,
            "comment": details,
            "date": datetime.datetime.now()
        })

        return f"⭐ Feedback received ({rating}/5). Thank you!"

    return "❌ Invalid post-purchase request."
