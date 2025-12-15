from llm_client import llm

INTENTS = [
    "PRODUCT_DISCOVERY",
    "AVAILABILITY_CHECK",
    "PRICE_OFFERS",
    "BUY_NOW",
    "POST_PURCHASE"
]

def detect_intent(message: str) -> str:
    prompt = f"""
Classify the customer's intent into ONE of the following:
{", ".join(INTENTS)}

Customer message:
"{message}"

Return ONLY the intent name.
"""
    intent = llm(prompt)
    return intent if intent in INTENTS else "PRODUCT_DISCOVERY"
