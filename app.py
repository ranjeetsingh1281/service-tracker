import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_CREDENTIALS = {
    "admin": "1234",
    "ranjeet": "elgi2024"
}

def login():
    st.title("🔐 ELGi Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
            st.session_state["login"] = True
            st.success("Login Successful 🚀")
            st.rerun()
        else:
            st.error("Invalid Credentials")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ==============================
# 📱 MOBILE UI FIX
# ==============================
st.set_page_config(page_title="ELGi Tracker Pro", layout="wide")

st.markdown("""
<style>
.block-container {
    padding: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# ☁️ DATABASE (SQLite)
# ==============================
conn = sqlite3.connect("elgi.db", check_same_thread=False)

def load_data():
    return pd.read_sql("SELECT * FROM master_data", conn)

def insert_sample_data():
    df = pd.DataFrame({
        "customer": ["TATA", "JSW", "L&T", "ADANI"],
        "model": ["X1", "X2", "X3", "X4"],
        "status": ["Active", "Active", "Sold", "Shifted"],
        "location": ["Delhi", "Mumbai", "Chennai", "Kolkata"],
        "due": [0, 1, 0, 1]
    })
    df.to_sql("master_data", conn, if_exists="replace", index=False)

# Initialize DB
insert_sample_data()
df = load_data()

# ==============================
# 🤖 ALERT SYSTEM
# ==============================
alerts = df[df["due"] != 0]

if not alerts.empty:
    st.warning(f"🚨 {len(alerts)} Machines Need Attention!")

# ==============================
# 📊 DASHBOARD
# ==============================
st.title("📊 ELGi Global Tracker Pro")

col1, col2 = st.columns(2)

# Status Chart
status_counts = df["status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
fig1 = px.pie(status_counts, names="Status", values="Count", title="Unit Status")
col1.plotly_chart(fig1, use_container_width=True)

# Customer Chart
cust_counts = df["customer"].value_counts().reset_index()
cust_counts.columns = ["Customer", "Count"]
fig2 = px.bar(cust_counts, x="Customer", y="Count", title="Customer Distribution")
col2.plotly_chart(fig2, use_container_width=True)

# ==============================
# 🔎 FILTER SECTION
# ==============================
st.subheader("🔍 Filter Data")

customers = ["All"] + list(df["customer"].unique())
selected_customer = st.selectbox("Select Customer", customers)

filtered_df = df if selected_customer == "All" else df[df["customer"] == selected_customer]

st.dataframe(filtered_df, use_container_width=True)

# ==============================
# ➕ ADD NEW DATA
# ==============================
st.subheader("➕ Add New Machine")

c1, c2 = st.columns(2)

new_customer = c1.text_input("Customer")
new_model = c2.text_input("Model")
new_status = c1.selectbox("Status", ["Active", "Sold", "Shifted"])
new_location = c2.text_input("Location")

if st.button("Add Data"):
    new_row = pd.DataFrame([{
        "customer": new_customer,
        "model": new_model,
        "status": new_status,
        "location": new_location,
        "due": 0
    }])
    new_row.to_sql("master_data", conn, if_exists="append", index=False)
    st.success("Data Added ✅")
    st.rerun()

# ==============================
# 📥 DOWNLOAD
# ==============================
st.download_button(
    "📥 Download Data",
    filtered_df.to_csv(index=False),
    "elgi_data.csv"
)

# ==============================
# 🚪 LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
