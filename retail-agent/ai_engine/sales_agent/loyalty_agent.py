import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

MAX_POINT_COVERAGE = 0.50  # 50%

client = MongoClient(MONGO_URL)
db = client["EY"]

products_col = db["products"]
promotions_col = db["promotions"]
loyalty_col = db["loyalty_accounts"]

print("[Loyalty Agent] Connected to MongoDB")
print("[Loyalty Agent] Using DB: EY")


def get_loyalty_balance(customer_id):
    acc = loyalty_col.find_one({"customerId": customer_id})
    return acc.get("points", 0) if acc else 0


def find_applicable_promotion(coupon_code, product):
    if not coupon_code:
        return None, 0

    promo = promotions_col.find_one({
        "$or": [
            {"promoId": coupon_code.upper()},
            {"name": {"$regex": coupon_code, "$options": "i"}}
        ]
    })

    if not promo:
        return None, 0

    return promo.get("name"), promo.get("discount", 0)


def calculate_final_price(
    product_name: str,
    base_price: float,
    customer_id: str,
    coupon_code: str | None = None,
    use_points: bool = False
):
    """
    Calculates final payable price using coupons and loyalty points.
    """

    product = products_col.find_one(
        {"name": {"$regex": product_name, "$options": "i"}}
    )
    if not product:
        return "❌ Product not found."

    current_price = float(base_price)
    total_savings = 0
    logs = []

    # Coupon
    if coupon_code:
        promo_name, discount = find_applicable_promotion(coupon_code, product)
        if discount:
            d_amt = base_price * discount / 100
            current_price -= d_amt
            total_savings += d_amt
            logs.append(f"🎫 Coupon {promo_name}: -₹{d_amt:.2f}")
        else:
            logs.append("⚠️ Invalid coupon")

    # Loyalty
    if use_points:
        balance = get_loyalty_balance(customer_id)
        cap = current_price * MAX_POINT_COVERAGE
        redeem = min(balance, cap)

        if redeem > 0:
            current_price -= redeem
            total_savings += redeem
            logs.append(f"💎 Loyalty applied: -₹{redeem:.2f}")

    return (
        f"💰 PRICE SUMMARY\n"
        f"Original: ₹{base_price}\n"
        f"{chr(10).join(logs)}\n"
        f"------------------\n"
        f"Final: ₹{current_price:.2f}\n"
        f"You saved: ₹{total_savings:.2f}"
    )
