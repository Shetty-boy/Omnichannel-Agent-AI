"""
AGENT CONTRACTS (Reference Interface)
-------------------------------------
These signatures match the actual implementation in 'ai_engine'.
"""

def sales_agent_chat(user_message: str, session: dict) -> tuple:
    """
    Main Orchestrator.
    Args:
        user_message: Raw text input
        session: Dict loaded from Redis
    Returns:
        (response_string, updated_session_dict)
    """
    raise NotImplementedError("See ai_engine/sales_agent/sales_agent.py")

def inventory_agent_run(payload: dict) -> dict:
    """
    Checks Stock (Redis Cache -> MongoDB).
    Args:
        payload: {"product_name": "..."}
    Returns:
        dict: { "availability": {...}, "store": "..." }
    """
    raise NotImplementedError("See ai_engine/sales_agent/inventory_agent.py")