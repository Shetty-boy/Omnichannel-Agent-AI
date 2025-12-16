import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

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

print("[Inventory Agent] Connected to MongoDB")
print("[Inventory Agent] Using DB:", DB_NAME)

# -------------------------------------------------------------------
# CORE LOGIC
# -------------------------------------------------------------------

def inventory_agent_run(payload: dict) -> dict:
    product_name = payload.get("product_name")

    if not product_name:
        return {"availability": {"status": "error", "reason": "No product provided"}, "store": "N/A"}

    try:
        # 1️⃣ Find product
        product = products_col.find_one(
            {"name": {"$regex": product_name, "$options": "i"}}
        )

        if not product:
            return {"availability": {"status": "not_found"}, "store": "N/A"}

        product_id = product.get("productId")

        # 2️⃣ Find inventory using productId
        inventory = inventory_col.find_one({"productId": product_id})

        if not inventory:
            return {
                "availability": {
                    "status": "out_of_stock",
                    "total_qty": 0,
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "locations": {}
                },
                "store": "Omnichannel"
            }

        # 3️⃣ Parse stockByLocation
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
                "name": product.get("name"),
                "price": product.get("price"),
                "locations": location_breakdown
            },
            "store": "Omnichannel"
        }

    except Exception as e:
        print("[Inventory Agent ERROR]:", e)
        return {"availability": {"status": "error", "reason": str(e)}, "store": "Error"}


# -------------------------------------------------------------------
# SIMPLE TEST
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("\n[TEST] Inventory Agent\n")
    result = inventory_agent_run({"product_name": "Smartphone A1"})
    print(result)
