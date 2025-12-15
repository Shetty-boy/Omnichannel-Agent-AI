import os
from typing import Optional, List, Dict
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client["aura_db"]
    products_collection = db["products"]
    print("[Recommendation Agent] Connected to MongoDB")
except Exception as e:
    print(f"[Recommendation Agent] Database connection failed: {e}")
    products_collection = None


# -------------------------------------------------------------------
# Recommendation Agent (Worker Agent)
# -------------------------------------------------------------------

def get_recommendations(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Fetch product recommendations from MongoDB.
    Returns structured product data ONLY.
    """

    if products_collection is None:
        return []

    try:
        mongo_query = {}

        if category:
            mongo_query["category"] = {"$regex": category, "$options": "i"}

        if query:
            mongo_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]

        if max_price:
            mongo_query["price"] = {"$lte": max_price}

        results = list(
            products_collection.find(mongo_query, {"_id": 0}).limit(limit)
        )

        return results

    except Exception as e:
        print(f"[Recommendation Agent] Error: {e}")
        return []
