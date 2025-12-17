from recommendation_agent import get_recommendations
from inventory_agent import inventory_agent_run
from fulfillment_agent import place_order
from payment_agent import process_payment
from loyalty_agent import calculate_final_price
from post_purchase_agent import handle_post_purchase
from cache import get_session, save_session
import re

# -------------------------------------------------------------------
# SEMANTIC NORMALIZATION
# -------------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "Electronics": ["phone", "mobile", "smartphone", "laptop", "computer"],
    "Sportswear": ["shoe", "shoes", "sports shoes", "running shoes"],
    "Apparel": ["t shirt", "t-shirt", "tshirt", "shirt", "clothing"],
    "Accessories": ["watch", "belt", "wallet", "accessory"],
    "Home Decor": ["decor", "home decor"],
    "Bags": ["bag", "bags", "backpack"]
}

YES_WORDS = ["yes", "yeah", "yep", "sure", "ok"]
STORE_WORDS = ["store", "shop", "outlet", "nearby"]
DELIVERY_WORDS = ["delivery", "home", "ship", "online"]
PAYMENT_WORDS = ["upi", "card", "pos", "gift"]
POST_WORDS = ["track", "return", "feedback"]

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def resolve_category(text):
    text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return None


def parse_product_selection(text, recommendations):
    text = text.lower().strip()

    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(recommendations):
            return recommendations[idx]

    for product in recommendations:
        if product["name"].lower() in text:
            return product

    return None


# -------------------------------------------------------------------
# SALES AGENT (ORCHESTRATOR)
# -------------------------------------------------------------------

def sales_agent_chat(user_message: str, session: dict):

    session.setdefault("stage", "BROWSING")
    session.setdefault("recommendations", [])
    session.setdefault("selected_product", None)
    session.setdefault("order_id", None)
    session.setdefault("customer_id", "CUST_GUEST")

    msg = user_message.lower().strip()

    # --------------------------------------------------
    # POST PURCHASE (TRACK / RETURN / FEEDBACK)
    # --------------------------------------------------
    if any(w in msg for w in POST_WORDS):
        if not session.get("order_id"):
            return "Please provide your order ID first.", session

        if "track" in msg:
            return handle_post_purchase(
                request_type="TRACK",
                order_id=session["order_id"]
            ), session

        if "return" in msg:
            return handle_post_purchase(
                request_type="RETURN",
                order_id=session["order_id"],
                details="User initiated return"
            ), session

        if "feedback" in msg:
            return handle_post_purchase(
                request_type="FEEDBACK",
                order_id=session["order_id"],
                details=msg,
                rating=5
            ), session

    # --------------------------------------------------
    # PRODUCT SELECTION
    # --------------------------------------------------
    if session["stage"] == "AWAITING_SELECTION":
        selected = parse_product_selection(msg, session["recommendations"])

        if not selected:
            return "Please select a valid option number or product name.", session

        session["selected_product"] = selected
        session["stage"] = "AVAILABILITY"

        return (
            f"Great choice! You selected **{selected['name']}**. "
            "Would you like me to check availability near you?",
            session
        )

    # --------------------------------------------------
    # AVAILABILITY CONFIRM
    # --------------------------------------------------
    if msg in YES_WORDS and session["stage"] == "AVAILABILITY":
        return (
            "I can check availability at nearby stores or for home delivery. "
            "Which would you prefer?",
            session
        )

    # --------------------------------------------------
    # STORE AVAILABILITY
    # --------------------------------------------------
    if any(w in msg for w in STORE_WORDS):
        product = session["selected_product"]

        inventory = inventory_agent_run({"product_name": product["name"]})
        availability = inventory.get("availability", {})
        locations = availability.get("locations", {})

        if availability.get("status") != "in_stock":
            return "Sorry, this product is out of stock.", session

        session["stage"] = "CONFIRM_RESERVATION"

        store_list = "\n".join(
            [f"{k}: {v} units" for k, v in locations.items() if v > 0]
        )

        return (
            f"Available at:\n{store_list}\n\n"
            "Would you like me to reserve it?",
            session
        )

    # --------------------------------------------------
    # PLACE ORDER (FULFILLMENT)
    # --------------------------------------------------
    if msg in YES_WORDS and session["stage"] == "CONFIRM_RESERVATION":
        product = session["selected_product"]

        result = place_order.invoke({
            "product_name": product["name"],
            "quantity": 1,
            "fulfillment_type": "PICKUP",
            "location_query": "Mall"
        })  
        
        match = re.search(r"(ORD-[A-Z0-9]+|#\d+|Order\s+#?\d+)", result, re.IGNORECASE)
        
        if match:
            raw_id = match.group()
            session["order_id"] = raw_id.replace("Order ", "").strip()
            
            session["stage"] = "LOYALTY"
            
            return (
                f"{result}\n\n"
                f"Do you want to apply coupons or loyalty points?",
                session
            )
        else:
            return (
                f" Order attempt finished, but I couldn't verify the ID.\nResponse: {result}\n"
                "Would you like to try again?",
                session
            )

    # --------------------------------------------------
    # LOYALTY
    # --------------------------------------------------
    if session["stage"] == "LOYALTY":
        product = session["selected_product"]

        price_info = calculate_final_price(
            product_name=product["name"],
            base_price=product["price"],
            customer_id=session["customer_id"],
            use_points=True
        )

        session["stage"] = "PAYMENT"

        return (
            f"{price_info}\n\n"
            "How would you like to pay? (UPI / Card / POS / Gift)",
            session
        )

    # --------------------------------------------------
    # PAYMENT
    # --------------------------------------------------
    if session["stage"] == "PAYMENT":
        result = process_payment.invoke({
            "order_id": session["order_id"],
            "payment_method": msg.upper()
        })

        session["stage"] = "COMPLETED"

        return (
            f"{result}\n\n"
            "🎉 Thank you for shopping with us!\n"
            "You can track, return, or leave feedback anytime.",
            session
        )

    # --------------------------------------------------
    # PRODUCT DISCOVERY
    # --------------------------------------------------
    category = resolve_category(msg)

    if category:
        recommendations = get_recommendations(category=category)
        session["recommendations"] = recommendations
        session["stage"] = "AWAITING_SELECTION"

        product_list = "\n".join(
            [f"{i+1}️⃣ {p['name']} – ₹{p['price']}"
             for i, p in enumerate(recommendations)]
        )

        return (
            f"Here are the available options:\n{product_list}\n\n"
            "Please select an option.",
            session
        )

    return "How can I assist you today?", session


# -------------------------------------------------------------------
# TERMINAL MODE
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uuid
    # Static ID for testing persistence (Use a random one in production)
    TEST_SESSION_ID = "CONSOLE_TEST_USER_001"
    
    print(f"\nSales Agent Running (Session: {TEST_SESSION_ID})")
    print("   Type 'exit' to quit. Type 'clear' to reset memory.\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            break
        
        # 1. LOAD SESSION FROM REDIS
        if user_input.lower() == "clear":
            session = {}
            save_session(TEST_SESSION_ID, {}) # Wipe Redis
            print("🧹 Memory wiped!")
            continue
        else:
            session = get_session(TEST_SESSION_ID)

        # 2. RUN AGENT
        reply, updated_session = sales_agent_chat(user_input, session)
        
        # 3. SAVE SESSION TO REDIS
        save_session(TEST_SESSION_ID, updated_session)
        
        print("Agent:", reply, "\n")