from intent_detector import detect_intent
from llm_client import llm

# Placeholder agent calls (you will replace later)
def call_recommendation_agent():
    return "I’ll suggest some festive and ethnic wear that suits your needs."

def call_inventory_agent():
    return "I’ll check availability in nearby stores for you."

def call_offers_agent():
    return "I’ll apply the best discounts and loyalty offers available."

def call_payment_agent():
    return "I’ll proceed with secure payment."

def call_fulfillment_agent():
    return "I’ll arrange delivery or in-store pickup."


def sales_agent_chat(user_message: str, session_context: dict):
    # 1. Detect intent
    intent = detect_intent(user_message)
    session_context["last_intent"] = intent

    # 2. Decide action
    if intent == "PRODUCT_DISCOVERY":
        raw_action = call_recommendation_agent()

    elif intent == "AVAILABILITY_CHECK":
        raw_action = call_inventory_agent()

    elif intent == "PRICE_OFFERS":
        raw_action = call_offers_agent()

    elif intent == "BUY_NOW":
        raw_action = (
            call_payment_agent() + " " + call_fulfillment_agent()
        )

    elif intent == "POST_PURCHASE":
        return (
            "I can help you track, return, or exchange your order.",
            session_context
        )

    else:
        raw_action = "How can I assist you today?"

    # 3. Ask LLM to generate final reply
    prompt = f"""
You are a retail sales associate talking to a customer.

The customer's message was:
"{user_message}"

The detected intent is:
{intent}

You have decided to take this action:
{raw_action}

Now respond naturally to the customer in 1–2 sentences.
"""
    reply = llm(prompt)

    return reply, session_context


if __name__ == "__main__":
    context = {}
    while True:
        msg = input("User: ").strip()
        if not msg:
            continue
        
        if msg.lower() == "exit":
            break

        reply, _ = sales_agent_chat(msg, context)
        print("Agent:", reply, "\n")
