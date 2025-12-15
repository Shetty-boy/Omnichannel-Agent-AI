from fastapi import FastAPI
from pydantic import BaseModel
from sales_agent import sales_agent_chat

app = FastAPI()

SESSION_STORE = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    context: dict


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.session_id not in SESSION_STORE:
        SESSION_STORE[req.session_id] = {
            "last_intent": None
        }

    context = SESSION_STORE[req.session_id]
    reply, updated_context = sales_agent_chat(req.message, context)

    SESSION_STORE[req.session_id] = updated_context

    return ChatResponse(
        reply=reply,
        context=updated_context
    )
