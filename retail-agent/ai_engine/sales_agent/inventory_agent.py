import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
from cache import get_cached_product, cache_product  # <--- NEW IMPORT

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
inventory_col = db["inventory"]

# -------------------------------------------------------------------
# CORE LOGIC
# -------------------------------------------------------------------

def inventory_agent_run(payload: dict) -> dict:
    product_name = payload.get("product_name")

    if not product_name:
        return {"availability": {"status": "error", "reason": "No product provided"}, "store": "N/A"}

    try:
        product_id = None
        price = 0
        real_name = product_name

        # ⚡ STEP 1: CHECK REDIS CACHE
        # We try to get the ID and Price directly from memory to skip 1 DB call
        cached_data = get_cached_product(product_name)
        
        if cached_data:
            print(f"[Inventory] 🚀 Cache Hit for '{product_name}'")
            product_id = cached_data["productId"]
            price = cached_data["price"]
            real_name = cached_data["name"]
        
        else:
            # 🐢 STEP 1.5: DB LOOKUP (Only if not in cache)
            print(f"[Inventory] 🐢 Cache Miss. Querying DB for '{product_name}'")
            product = products_col.find_one(
                {"name": {"$regex": product_name, "$options": "i"}}
            )

            if not product:
                return {"availability": {"status": "not_found"}, "store": "N/A"}

            product_id = product.get("productId")
            price = product.get("price")
            real_name = product.get("name")
            
            # 💾 SAVE TO CACHE for next time
            cache_product(product_name, {
                "productId": product_id,
                "price": price,
                "name": real_name
            })

        # STEP 2: FIND INVENTORY (Always check DB for stock as it changes fast)
        inventory = inventory_col.find_one({"productId": product_id})

        if not inventory:
            return {
                "availability": {
                    "status": "out_of_stock",
                    "total_qty": 0,
                    "name": real_name,
                    "price": price,
                    "locations": {}
                },
                "store": "Omnichannel"
            }

        # STEP 3: PARSE LOCATIONS
        stock_data = inventory.get("stockByLocation", [])
        total_qty = 0
        location_breakdown = {}

        for entry in stock_data:
            qty = int(entry.get("qty", 0))
            loc = entry.get("locationId", "UNKNOWN")
            total_qty += qty
            location_breakdown[loc] = qty

        return {
            "availability": {
                "status": "in_stock" if total_qty > 0 else "out_of_stock",
                "total_qty": total_qty,
                "name": real_name,
                "price": price,
                "locations": location_breakdown
            },
            "store": "Omnichannel"
        }

    except Exception as e:
        print("[Inventory Agent ERROR]:", e)
        return {"availability": {"status": "error", "reason": str(e)}, "store": "Error"}

if __name__ == "__main__":
    print("\n[TEST] Inventory Agent\n")
    # Run twice to test cache: First time = Cache Miss, Second time = Cache Hit
    print(inventory_agent_run({"product_name": "Smartphone A1"}))