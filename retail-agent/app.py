import streamlit as st
import pandas as pd
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="Retail Omnichannel Agentic AI", layout="wide")

st.title("🛍️ Omnichannel Retail Agentic AI")
st.caption("Channel-Adaptive Conversational Sales | Agentic Orchestration")

# -------------------------------------------------
# Session State
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_data" not in st.session_state:
    st.session_state.agent_data = {}

if "previous_channel" not in st.session_state:
    st.session_state.previous_channel = None

# -------------------------------------------------
# Sidebar – Channel Switching
# -------------------------------------------------
st.sidebar.header("Channel Context")

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
# Conversation Logic
# -------------------------------------------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    intent = "browse"
    if any(x in user_input.lower() for x in ["buy", "checkout", "purchase"]):
        intent = "checkout"
    elif any(x in user_input.lower() for x in ["reserve", "try"]):
        intent = "reserve"
    elif any(x in user_input.lower() for x in ["return", "exchange", "refund", "track"]):
        intent = "post_purchase"

    response = f"""
🧠 **Sales Agent**

Channel: **{channel}**  
Customer: **{customer}**  
Intent: **{intent.upper()}**

Routing to relevant agents…
"""
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # -------------------------------------------------
    # Worker Agents – Core Commerce
    # -------------------------------------------------
    st.session_state.agent_data["recommendations"] = pd.DataFrame({
        "Product": ["Festive Kurta", "Ethnic Jacket"],
        "Price (₹)": [2499, 3999],
        "Match (%)": [94, 87]
    })

    st.session_state.agent_data["inventory"] = pd.DataFrame({
        "Product": ["Festive Kurta", "Ethnic Jacket"],
        "Availability": ["Available", "Limited"],
        "Store": ["Phoenix Mall", "Phoenix Mall"]
    })

    # -------------------------------------------------
    # Loyalty & AOV Agent
    # -------------------------------------------------
    loyalty_tier = random.choice(["Silver", "Gold", "Platinum"])
    points_earned = random.randint(120, 350)

    st.session_state.agent_data["loyalty"] = {
        "Tier": loyalty_tier,
        "Points Earned": points_earned,
        "Upsell Recommendation": "Add matching stole for ₹799",
        "AOV Uplift": "↑ 18%"
    }

    # -------------------------------------------------
    # Fulfillment & Payment
    # -------------------------------------------------
    if reserve_mode or intent == "reserve":
        st.session_state.agent_data["fulfillment"] = {
            "Mode": "Reserved In-Store",
            "Store": "Phoenix Mall",
            "Status": "Reserved for 24 hours"
        }
        st.session_state.agent_data["payment"] = {
            "Mode": "Pay at Store",
            "Status": "Pending"
        }
    else:
        st.session_state.agent_data["payment"] = {
            "Mode": "Online",
            "Status": "Completed"
        }

    # -------------------------------------------------
    # Post-Purchase Support Agent
    # -------------------------------------------------
    if intent == "post_purchase":
        st.session_state.agent_data["support"] = {
            "Actions Available": ["Return", "Exchange", "Track Order"],
            "Ticket Status": "Resolved via AI",
            "Customer Satisfaction": "⭐⭐⭐⭐⭐"
        }

# -------------------------------------------------
# Worker Agent Tabs
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
            st.success("Fulfillment Confirmed")
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
if "fulfillment" in st.session_state.agent_data:
    st.markdown("---")
    if st.button("📄 Download Order Confirmation PDF"):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(tmp.name, pagesize=A4)

        c.drawString(50, 800, "Retail Order Confirmation")
        c.drawString(50, 770, f"Customer: {customer}")
        c.drawString(50, 750, f"Channel: {channel}")
        c.drawString(50, 730, f"Loyalty Tier: {st.session_state.agent_data['loyalty']['Tier']}")
        c.drawString(50, 710, f"AOV Impact: {st.session_state.agent_data['loyalty']['AOV Uplift']}")

        c.showPage()
        c.save()

        with open(tmp.name, "rb") as f:
            st.download_button(
                "⬇️ Download PDF",
                f,
                file_name="order_confirmation.pdf",
                mime="application/pdf"
            )
