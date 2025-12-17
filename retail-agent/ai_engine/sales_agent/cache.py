import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

# 1. SETUP CONNECTION
# We read the credentials from your .env file
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 15000))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")

redis_client = None

try:
    # ⚡ THIS IS THE CONNECTION LINE (Updated for Cloud)
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        decode_responses=True, # Keeps text as text (not bytes)
        socket_timeout=5       # Don't wait forever if internet is slow
    )
    
    redis_client.ping() # Test the connection immediately
    print("[Cache] ✅ Connected to Redis Cloud!")

except Exception as e:
    print(f"[Cache] ⚠️ Redis Connection Failed: {e}")
    print("[Cache] Memory features will be disabled.")
    redis_client = None

# --- SESSION FUNCTIONS ---

def get_session(session_id):
    """Loads the user's conversation state."""
    if not redis_client: return {}
    try:
        data = redis_client.get(f"session:{session_id}")
        if data and isinstance(data, str):
            return json.loads(data)
        return {}
    except:
        return {}

def save_session(session_id, session_data):
    """Saves the user's state (Expires in 24 hours)."""
    if not redis_client: return
    try:
        redis_client.setex(f"session:{session_id}", 86400, json.dumps(session_data))
    except Exception as e:
        print(f"[Cache Error] Could not save session: {e}")

# --- PRODUCT CACHING FUNCTIONS ---

def get_cached_product(product_name):
    """Retrieves product details from cache."""
    if not redis_client: return None
    try:
        key = f"product_map:{product_name.lower().strip()}"
        data = redis_client.get(key)
        if data and isinstance(data, str):
            return json.loads(data)
        return None
    except:
        return None

def cache_product(product_name, product_data):
    """Saves product details to cache for 1 hour."""
    if not redis_client: return
    try:
        key = f"product_map:{product_name.lower().strip()}"
        redis_client.setex(key, 3600, json.dumps(product_data))
    except Exception as e:
        print(f"[Cache Error] Could not cache product: {e}")