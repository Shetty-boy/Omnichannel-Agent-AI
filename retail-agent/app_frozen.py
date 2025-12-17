"""
UI + ORCHESTRATION (CONNECTED)
------------------------------
Status: Connected to Backend API
Purpose: Frontend for Sales Agent + Redis Memory
"""

import streamlit as st
import pandas as pd
import requests
import uuid
import random
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
# 1. Generate a unique Session ID for Redis
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "previous_channel" not in st.session_state:
    st.session_state.previous_channel = None

# Initialize Dashboard Data (Placeholder for visualization)
if "agent_data" not in st.session_state:
    st.session_state.agent_data = {
        "recommendations": pd.DataFrame({
            "Product": ["Festive Kurta", "Ethnic Jacket"],
            "Price (₹)": [2499, 3999],
            "Match (%)": [94, 87]
        }),
        "inventory": pd.DataFrame({
            "Product": ["Festive Kurta", "Ethnic Jacket"],
            "Availability": ["Available", "Limited"],
            "Store": ["Phoenix Mall", "Phoenix Mall"]
        }),
        "loyalty": {
            "Tier": "Gold",
            "Points Earned": 150,
            "Upsell Recommendation": "Add matching stole for ₹799",
            "AOV Uplift": "↑ 18%"
        },
        "payment": {
            "Mode": "Pending", 
            "Status": "Waiting for User"
        },
        "fulfillment": {
            "Mode": "N/A", 
            "Status": "Not Started"
        },
        "support": None
    }

# -------------------------------------------------
# Sidebar – Channel Switching
# -------------------------------------------------
st.sidebar.header(f"Session: {st.session_state.session_id[:8]}")

channel = st.sidebar.selectbox(
    "Customer Channel",
    ["Web Chat", "Mobile App", "WhatsApp / Telegram", "In-Store Kiosk", "Voice Assistant"]
)

customer = st.sidebar.selectbox(
    "Customer Profile",
    [
        "Aarav – Frequent Buyer",
        "Neha – Discount Seeker",
        "Rohan – Occasion Shopper",
        "Priya – Loyalty Member"
    ]
)

st.sidebar.markdown("---")
reserve_mode = st.sidebar.checkbox("Reserve In-Store", False)

if st.sidebar.button("🧹 Clear Chat Memory"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

# -------------------------------------------------
# Detect Channel Switch
# -------------------------------------------------
if st.session_state.previous_channel and st.session_state.previous_channel != channel:
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🔁 **Channel Switch:** {st.session_state.previous_channel} → {channel}. Context retained."
    })

st.session_state.previous_channel = channel

# -------------------------------------------------
# Display Chat History
# -------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------
# Input Handling
# -------------------------------------------------
if channel == "Voice Assistant":
    user_input = st.text_input("🎤 Speak (simulated)")
else:
    user_input = st.chat_input("Talk to the Sales Assistant...")

# -------------------------------------------------
# Conversation Logic (CONNECTED TO BACKEND)
# -------------------------------------------------
if user_input:
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Call Backend API
    try:
        with st.spinner("🤖 Aura is thinking..."):
            payload = {
                "message": user_input,
                "session_id": st.session_state.session_id
            }
            
            # 🚀 SEND REQUEST TO PYTHON BACKEND
            response = requests.post(BACKEND_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                bot_reply = data.get("reply", "⚠️ No response from agent.")
                stage = data.get("stage", "UNKNOWN")
                
                # Optional: You can trigger UI updates based on 'stage' here
                if stage == "PAYMENT":
                    st.toast("💰 Payment Gateway Activated")
                    
            else:
                bot_reply = f"❌ Server Error: {response.status_code}"

    except Exception as e:
        bot_reply = f"❌ Connection Error: Ensure 'backend/main.py' is running. ({e})"

    # 3. Display Assistant Response
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

# -------------------------------------------------
# Worker Agent Tabs (Dashboard)
# -------------------------------------------------
if channel not in ["WhatsApp / Telegram", "Voice Assistant"]:
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "🛍 Recommendations",
            "📦 Inventory",
            "🎁 Loyalty & AOV",
            "💳 Payment",
            "🚚 Fulfillment",
            "🔁 Post-Purchase Support"
        ]
    )

    with tab1:
        st.dataframe(st.session_state.agent_data.get("recommendations", pd.DataFrame()))

    with tab2:
        st.dataframe(st.session_state.agent_data.get("inventory", pd.DataFrame()))

    with tab3:
        loyalty = st.session_state.agent_data.get("loyalty")
        if loyalty:
            st.success(f"Loyalty Tier: {loyalty['Tier']}")
            st.write(loyalty)

    with tab4:
        payment = st.session_state.agent_data.get("payment")
        if payment:
            st.success(payment["Status"])
            st.write("Mode:", payment["Mode"])

    with tab5:
        fulfillment = st.session_state.agent_data.get("fulfillment")
        if fulfillment:
            st.write(fulfillment)

    with tab6:
        support = st.session_state.agent_data.get("support")
        if support:
            st.success("Post-Purchase Support Handled")
            st.write(support)
        else:
            st.info("No post-purchase request yet.")

# -------------------------------------------------
# PDF Confirmation
# -------------------------------------------------
st.markdown("---")
if st.button("📄 Download Order Confirmation PDF"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)

    c.drawString(50, 800, "Retail Order Confirmation")
    c.drawString(50, 770, f"Customer: {customer}")
    c.drawString(50, 750, f"Channel: {channel}")
    c.drawString(50, 730, f"Session ID: {st.session_state.session_id}")
    c.drawString(50, 710, "Status: Processed via Omnichannel Agent")

    c.showPage()
    c.save()

    with open(tmp.name, "rb") as f:
        st.download_button(
            "⬇️ Download PDF",
            f,
            file_name="order_confirmation.pdf",
            mime="application/pdf"
        )