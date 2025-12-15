from recommendation_agent import get_recommendations
from intent_detector import detect_intent
from llm_client import llm

# -------------------------------------------------------------------
# Placeholder Worker Agent Calls
# (Replace these with real agents later)
# -------------------------------------------------------------------

def call_recommendation_agent(query: str):
    return get_recommendations(query=query)

def call_inventory_agent():
    return "Check product availability in nearby stores."

def call_offers_agent():
    return "Apply applicable discounts and loyalty benefits."

def call_payment_agent():
    return "Proceed with secure payment."

def call_fulfillment_agent():
    return "Arrange delivery or in-store pickup."


# -------------------------------------------------------------------
# SALES AGENT (CORE BRAIN)
# -------------------------------------------------------------------

def sales_agent_chat(user_message: str, session_context: dict):
    """
    Central Sales Agent:
    - Understands customer intent
    - Maintains conversation state
    - Tracks what item the user is talking about
    - Orchestrates worker agents
    - Responds in natural language
    """

    # -------------------------------
    # 1. Initialize session memory
    # -------------------------------
    if "stage" not in session_context:
        session_context["stage"] = "BROWSING"

    if "last_intent" not in session_context:
        session_context["last_intent"] = None

    if "current_item" not in session_context:
        session_context["current_item"] = None

    # -------------------------------
    # 2. Detect customer intent
    # -------------------------------
    intent = detect_intent(user_message)
    session_context["last_intent"] = intent

    # -------------------------------
    # 3. Decide system action + update memory
    # -------------------------------
    if intent == "PRODUCT_DISCOVERY":
        session_context["stage"] = "DISCOVERY"
        session_context["current_item"] = user_message

        recommendations = call_recommendation_agent(user_message)
        session_context["recommendations"] = recommendations

        action = "Present product recommendations from catalog."


    elif intent == "AVAILABILITY_CHECK":
        session_context["stage"] = "AVAILABILITY"
        action = call_inventory_agent()

    elif intent == "PRICE_OFFERS":
        session_context["stage"] = "PRICING"
        action = call_offers_agent()

    elif intent == "BUY_NOW":
        session_context["stage"] = "CHECKOUT"
        action = call_payment_agent() + " " + call_fulfillment_agent()

    elif intent == "POST_PURCHASE":
        session_context["stage"] = "POST_PURCHASE"
        return (
            "I can help you track, return, or exchange your order. What would you like to do?",
            session_context
        )

    else:
        action = "Assist the customer."

    # -------------------------------
    # 4. Generate natural response (LLM)
    # -------------------------------
    prompt = f"""
You are a professional retail sales associate.

Customer journey stage: {session_context['stage']}
Detected intent: {intent}

The customer is currently interested in:
{session_context['current_item']}

Customer message:
"{user_message}"

Recommended products from catalog:
{session_context.get("recommendations")}

Briefly introduce 1–2 products from this list.
Do NOT invent products outside this list.


Respond naturally in 1–2 sentences.
Be clear about the product you are referring to.
Avoid repeating earlier suggestions.
Do not invent prices, stock, locations, or offers.
"""

    reply = llm(prompt)

    # -------------------------------
    # 5. Debug log (development only)
    # -------------------------------
    print(
        f"[DEBUG] Intent={intent}, "
        f"Stage={session_context['stage']}, "
        f"Item={session_context['current_item']}"
    )

    return reply, session_context


# -------------------------------------------------------------------
# TERMINAL TEST MODE
# -------------------------------------------------------------------

if __name__ == "__main__":
    context = {}

    print("\nSales Agent is running. Type 'exit' to quit.\n")

    while True:
        user_input = input("User: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            break

        reply, context = sales_agent_chat(user_input, context)
        print("Agent:", reply, "\n")
