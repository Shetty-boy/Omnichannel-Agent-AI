import os
from typing import Optional, List, Dict
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "EY")

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------

client = MongoClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000,
    tls=True,
    tlsCAFile=certifi.where()
)

db = client[DB_NAME]

products_col = db["products"]
categories_col = db["categories"]

print("\n[Recommendation Agent] Connected to MongoDB")
print("[Recommendation Agent] Using DB:", DB_NAME)
print("[DEBUG] Collections:", db.list_collection_names())

# -------------------------------------------------------------------
# Parent → Child category hierarchy (from your DB)
# -------------------------------------------------------------------

PARENT_CATEGORY_MAP = {
    "Apparel": ["T-Shirts"],
    "Sportswear": ["Footwear"],
    "Electronics": ["Smartphones", "Laptops"],
}

# -------------------------------------------------------------------
# Helper: Resolve categoryIds (supports hierarchy)
# -------------------------------------------------------------------

def resolve_category_ids(category_name: str) -> List[str]:
    """
    Converts semantic category (parent or leaf)
    into one or more internal categoryIds.
    """

    if not category_name:
        return []

    category_ids = []

    # 1️⃣ If category is a parent, expand children
    if category_name in PARENT_CATEGORY_MAP:
        for child_name in PARENT_CATEGORY_MAP[category_name]:
            doc = categories_col.find_one(
                {"name": {"$regex": f"^{child_name}$", "$options": "i"}}
            )
            if doc:
                category_ids.append(doc["categoryId"])

        return category_ids

    # 2️⃣ Otherwise treat as leaf category
    doc = categories_col.find_one(
        {"name": {"$regex": f"^{category_name}$", "$options": "i"}}
    )
    if doc:
        return [doc["categoryId"]]

    return []

# -------------------------------------------------------------------
# Recommendation Agent (Worker Agent)
# -------------------------------------------------------------------

def get_recommendations(
    category: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Fetch products using hierarchical category resolution.
    """

    try:
        mongo_query = {}

        # -------------------------------
        # CATEGORY-BASED SEARCH
        # -------------------------------
        if category:
            category_ids = resolve_category_ids(category)

            print("[DEBUG] Resolved Category:", category)
            print("[DEBUG] Resolved categoryIds:", category_ids)

            if not category_ids:
                return []

            mongo_query = {
                "category": {"$in": category_ids}
            }

        # -------------------------------
        # FREE-TEXT SEARCH (fallback)
        # -------------------------------
        elif query:
            mongo_query = {
                "name": {"$regex": query, "$options": "i"}
            }

        else:
            return []

        print("[DEBUG] Product query:", mongo_query)

        results = list(
            products_col.find(mongo_query, {"_id": 0}).limit(limit)
        )

        print("[DEBUG] Product results:", results)

        return results

    except Exception as e:
        print("[Recommendation Agent] Error:", e)
        return []
