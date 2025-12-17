import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------
# 🔧 PATH FIXES (Critical for Imports)
# ------------------------------------------------------------------
# 1. Get the path of the 'backend' folder
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Get the root 'retail-agent' folder
root_dir = os.path.dirname(current_dir)

# 3. Get the specific 'sales_agent' folder
agent_dir = os.path.join(root_dir, "ai_engine", "sales_agent")

# 4. Add BOTH to Python's search path
sys.path.append(root_dir)   # Allows: from ai_engine.sales_agent...
sys.path.append(agent_dir)  # Allows: from recommendation_agent import...

# ------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------
# Now these imports will work perfectly
from ai_engine.sales_agent.sales_agent import sales_agent_chat
from ai_engine.sales_agent.cache import get_session, save_session

app = FastAPI()

# Enable CORS (Allows React/Streamlit to talk to this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.get("/")
def health_check():
    return {"status": "active", "service": "Omnichannel Sales Agent"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        # 1. Load Context from Redis
        session_data = get_session(request.session_id)
        
        # 2. Run the Logic
        bot_reply, updated_session = sales_agent_chat(request.message, session_data)
        
        # 3. Save Context to Redis
        save_session(request.session_id, updated_session)
        
        # 4. Return EVERYTHING the UI needs
        return {
            "reply": bot_reply,
            "session_id": request.session_id,
            "stage": updated_session.get("stage"),
            
            # 🚀 DATA FOR TABS
            "recommendations": updated_session.get("recommendations", []),
            "inventory": updated_session.get("inventory", []),  # List of dicts
            "loyalty": updated_session.get("loyalty", None),    # Dict
            "payment": updated_session.get("payment", None),    # Dict
            "fulfillment": updated_session.get("fulfillment", None) # Dict
        }

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)