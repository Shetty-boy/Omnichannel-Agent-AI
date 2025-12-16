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

orders_col = db["orders"]
payments_col = db["payments"]
pos_col = db["pos_transactions"]

print("[Payment Agent] Connected to MongoDB")
print("[Payment Agent] Using DB: EY")

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def generate_payment_id():
    return f"PAY-{uuid.uuid4().hex[:8].upper()}"

def simulate_gateway_process(method, amount):
    """
    Mock payment gateway logic.
    """
    method = method.lower()

    if method == "pos":
        return True, "Authorized by POS Terminal"

    if "upi" in method:
        return True, "UPI Payment Successful"

    if "card" in method:
        return True, "Card Authorized"

    return False, "Unsupported Payment Method"

# -------------------------------------------------------------------
# LANGCHAIN TOOL
# -------------------------------------------------------------------

@tool
def process_payment(order_id: str, payment_method: str):
    """
    Processes payment for an order and updates order status.
    """

    order = orders_col.find_one({"orderId": order_id})
    if not order:
        return f"❌ Payment Failed: Order '{order_id}' not found."

    if order.get("status") == "PAID":
        return f"✅ Order already paid. Payment ID: {order.get('paymentId')}"

    amount = order["totalAmount"]
    success, msg = simulate_gateway_process(payment_method, amount)

    payment_id = generate_payment_id()

    payments_col.insert_one({
        "paymentId": payment_id,
        "orderId": order_id,
        "amount": amount,
        "method": payment_method,
        "status": "SUCCESS" if success else "FAILED",
        "timestamp": datetime.datetime.now()
    })

    if not success:
        return f"❌ Payment failed: {msg}"

    orders_col.update_one(
        {"orderId": order_id},
        {"$set": {"status": "PAID", "paymentId": payment_id}}
    )

    return (
        f"💳 PAYMENT SUCCESS\n"
        f"Payment ID: {payment_id}\n"
        f"Amount: ₹{amount}\n"
        f"Order closed."
    )


# -------------------------------------------------------------------
# TEST BLOCK
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("\n[TEST] Payment Agent\n")

    print(process_payment.invoke({
        "order_id": "ORD-TEST-1234",
        "payment_method": "upi"
    }))
