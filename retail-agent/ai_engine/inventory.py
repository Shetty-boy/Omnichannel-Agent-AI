import os
from langchain.tools import tool
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URL)
    db = client["aura_db"]
    products_collection = db["products"]
except Exception as e:
    print(f"❌ Inventory Agent Database Error: {e}")


@tool
def check_inventory(product_name: str):
    """
    Checks real-time stock levels for a specific product.
    Use this when the customer asks "Do you have this?", "Is it in stock?", 
    or before processing a purchase to ensure availability.
    
    Args:
    - product_name (str): The name or partial name of the item (e.g., "Emerald Dress").
    """
    try:
        query = {"name": {"$regex": product_name, "$options": "i"}}
        product = products_collection.find_one(query)

        if not product:
            return f"I checked the inventory, but I couldn't find any product matching '{product_name}'."

        stock = product.get("stock", 0)
        name = product["name"]
        price = product["price"]

        if stock > 0:
            status = f" In Stock: We have {stock} units of '{name}' available."
            if stock < 3:
                status += " ( Low Stock! selling fast)"
            return f"{status} Price: ${price}."
        else:
            return f" Out of Stock: '{name}' is currently unavailable."

    except Exception as e:
        return f"System Error in Inventory Check: {str(e)}"

# --- TEST BLOCK (Run this file to test independently) ---
# if __name__ == "__main__":
#     print("\n📦 TESTING INVENTORY AGENT...")
    
#     # Test 1: Existing Item (Make sure you ran seed_db.py!)
#     print(check_inventory.invoke({"product_name": "Emerald"}))
    
#     # Test 2: Out of Stock Item (The Denim Jacket)
#     print(check_inventory.invoke({"product_name": "Denim"}))