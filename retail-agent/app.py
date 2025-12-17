import streamlit as st
import pandas as pd
import requests
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

# -------------------------------------------------
# Configuration
# -------------------------------------------------
BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Retail Omnichannel Agentic AI", layout="wide")

st.title("🛍️ Omnichannel Retail Agentic AI")
st.caption("Channel-Adaptive Conversational Sales | Powered by Redis & MongoDB")

# -------------------------------------------------
# Session State & Memory
# -------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "previous_channel" not in st.session_state:
    st.session_state.previous_channel = None

# Initialize empty placeholders to prevent crashes
if "agent_data" not in st.session_state:
    st.session_state.agent_data = {
        "recommendations": pd.DataFrame(columns=["Product Name", "Price", "Category"]),
        "inventory": pd.DataFrame(columns=["Product", "Availability", "Store"]),
        "loyalty": {"Tier": "-", "Points": 0},
        "payment": {"Mode": "-", "Status": "Not Started"},
        "fulfillment": {"Mode": "-", "Status": "Not Started"},
        "support": None
    }

# -------------------------------------------------
# Sidebar: Controls & Live Dashboard
# -------------------------------------------------
with st.sidebar:
    st.header(f"Session: {st.session_state.session_id[:8]}")

    # --- 1. User Controls ---
    with st.expander("🛠️ User Settings", expanded=True):
        channel = st.selectbox(
            "Channel",
            ["Web Chat", "Mobile App", "WhatsApp", "In-Store Kiosk"]
        )
        customer = st.selectbox(
            "Profile",
            ["Aarav – Frequent Buyer", "Neha – Discount Seeker", "Rohan – Occasion"]
        )
        if st.button("🧹 New Chat"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

    st.divider()

    # --- 2. The Live "Brain" Dashboard (Hidden from Main Chat) ---
    st.subheader("🧠 Agent Live State")
    
    with st.expander("🛍️ Recommendations", expanded=True):
        st.dataframe(st.session_state.agent_data.get("recommendations"), hide_index=True)

    with st.expander("📦 Inventory Data"):
        st.dataframe(st.session_state.agent_data.get("inventory"), hide_index=True)

    with st.expander("🎁 Loyalty"):
        l = st.session_state.agent_data.get("loyalty")
        if l: st.write(l)

    with st.expander("💳 Payment & Fulfillment"):
        st.write("Payment:", st.session_state.agent_data.get("payment"))
        st.write("Fulfillment:", st.session_state.agent_data.get("fulfillment"))

# -------------------------------------------------
# Channel Switch Detection
# -------------------------------------------------
if st.session_state.previous_channel and st.session_state.previous_channel != channel:
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🔁 **Channel Switch:** {st.session_state.previous_channel} → {channel}. Context retained."
    })
st.session_state.previous_channel = channel

# -------------------------------------------------
# Main Chat Area (Clean & Focused)
# -------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------
# Input Handling & Backend Connection
# -------------------------------------------------
if user_input := st.chat_input("Talk to the Sales Assistant..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Initialize variable to prevent "Unbound" error
    bot_reply = None

    # 2. Call Backend API
    try:
        with st.spinner("🤖 Aura is thinking..."):
            payload = {
                "message": user_input,
                "session_id": st.session_state.session_id
            }
            
            response = requests.post(BACKEND_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                bot_reply = data.get("reply", "⚠️ No response.")
                
                # --- UPDATE STATE ---
                # Save the reply to history immediately
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
                # Update "Brain" Data for the Sidebar
                if data.get("recommendations"):
                    st.session_state.agent_data["recommendations"] = pd.DataFrame(data["recommendations"])
                
                if data.get("inventory"):
                    st.session_state.agent_data["inventory"] = pd.DataFrame(data["inventory"])

                if data.get("loyalty"):
                    st.session_state.agent_data["loyalty"] = data.get("loyalty")

                if data.get("payment"):
                    st.session_state.agent_data["payment"] = data.get("payment")

                # Force reload so Sidebar updates instantly
                st.rerun()
                
            else:
                # Assign error to bot_reply so we can print it below
                bot_reply = f"❌ Server Error: {response.status_code}"

    except Exception as e:
        # Assign error to bot_reply so we can print it below
        bot_reply = f"❌ Connection Error: Is 'backend/main.py' running? ({e})"

    # 3. Display Assistant Response (Only if we didn't rerun)
    if bot_reply:
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

# -------------------------------------------------
# PDF Confirmation (Only shows when relevant)
# -------------------------------------------------
if st.session_state.agent_data["payment"].get("Status") == "Completed":
    st.divider()
    if st.button("📄 Download Invoice"):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(tmp.name, pagesize=A4)
        c.drawString(50, 800, f"INVOICE - {st.session_state.session_id[:8]}")
        c.drawString(50, 780, f"Customer: {customer}")
        c.save()
        with open(tmp.name, "rb") as f:
            st.download_button("⬇️ Download PDF", f, file_name="invoice.pdf")