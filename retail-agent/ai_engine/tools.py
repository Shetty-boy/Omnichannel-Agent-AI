import os
from typing import Optional
from langchain.tools import tool
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Optional 

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
try:
    client = MongoClient(MONGO_URL)
    db = client["aura_db"]
    products_collection = db["products"]
    customers_collection = db["customers"]
    print(" Recommendation Agent connected to MongoDB.")
except Exception as e:
    print(f" Database connection failed: {e}")

# --- The Recommendation Agent ---

@tool
def get_recommendations(category: Optional[str] = None, price: Optional[int] = None, query: Optional[str] = None):
    """
    Args:
    - category (str): The type of product (e.g., "dress", "shoes", "jacket").
    - budget (int): Optional maximum price.
    - query (str): General search terms (e.g., "summer wear", "formal").
    """
    try:
        mongo_query = {}
        
        if category:
            mongo_query["category"] = {"$regex": category, "$options": "i"}
        
        if query:
            mongo_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
            
        if price:
            mongo_query["price"] = {"$lte": price}

        results = list(products_collection.find(mongo_query, {"_id": 0}).limit(5))

        if not results:
            return f"I checked our catalog, but I couldn't find any products matching '{query or category}' within that budget."

        formatted_response = "Here are the top recommendations found:\n"
        for product in results:
            stock_status = "In Stock" if product.get('stock', 0) > 0 else "Out of Stock"
            formatted_response += (
                f"- {product['name']} (${product['price']})\n"
                f"  Description: {product.get('description', 'N/A')}\n"
                f"  Status: {stock_status}\n\n"
            )
            
        return formatted_response

    except Exception as e:
        return f"Error in Recommendation Agent: {str(e)}"
    