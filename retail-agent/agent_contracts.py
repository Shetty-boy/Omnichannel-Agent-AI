"""
AGENT CONTRACTS
---------------
All agents must follow this structure.
No UI code inside agents.
"""

def sales_agent_handle(user_text: str, context: dict) -> dict:
    """
    Expected return:
    {
        "response": str,
        "intent": str,
        "stage": str,
        "next_actions": list
    }
    """
    raise NotImplementedError("Sales Agent not connected yet")


def recommendation_agent_run(payload: dict) -> dict:
    """
    Expected return:
    {
        "products": list,
        "explanation": str
    }
    """
    raise NotImplementedError("Recommendation Agent not connected yet")


def inventory_agent_run(payload: dict) -> dict:
    """
    Expected return:
    {
        "availability": dict,
        "store": str
    }
    """
    raise NotImplementedError("Inventory Agent not connected yet")
