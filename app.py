import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
import plotly.express as px

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_CREDENTIALS = {"admin": "1234"}

def login():
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("Invalid Credentials")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ==============================
# 📱 PAGE CONFIG
# ==============================
st.set_page_config(page_title="ELGi Tracker Pro", layout="wide")

st.markdown("""
<style>
.block-container {padding: 1rem;}
</style>
""", unsafe_allow_html=True)

# ==============================
# 🧠 HELPERS
# ==============================
def find_column(df, keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

def format_dt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load_data():
    files = os.listdir('.')

    def get_file(name):
        return next((f for f in files if name.lower() in f.lower()), None)

    master = get_file("Master_Data")
    foc = get_file("FOC")
    service = get_file("Service")

    master_df = pd.read_excel(master) if master else pd.DataFrame()
    foc_df = pd.read_excel(foc) if foc else pd.DataFrame()
    service_df = pd.read_excel(service) if service else pd.DataFrame()

    return master_df, foc_df, service_df

master_df, foc_df, service_df = load_data()

# ==============================
# 📊 DASHBOARD METRICS
# ==============================
st.title("🛠️ DPSAC Tracker")

if not master_df.empty:
    status_col = find_column(master_df, "status")

    total = len(master_df)
    active = len(master_df[master_df[status_col].astype(str).str.contains("Active", case=False, na=False)])
    shifted = len(master_df[master_df[status_col].astype(str).str.contains("Shifted", case=False, na=False)])
    sold = len(master_df[master_df[status_col].astype(str).str.contains("Sold", case=False, na=False)])

    st.markdown(f"""
    | Total | Active | Shifted | Sold |
    |---|---|---|---|
    | {total} | {active} | {shifted} | {sold} |
    """)

    # 📊 Charts
    st.subheader("📊 Analytics")

    col1, col2 = st.columns(2)

    status_counts = master_df[status_col].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    col1.plotly_chart(px.pie(status_counts, names='Status', values='Count'), use_container_width=True)

    cust_col = find_column(master_df, "customer")
    cust_counts = master_df[cust_col].value_counts().head(10).reset_index()
    cust_counts.columns = ['Customer', 'Count']
    col2.plotly_chart(px.bar(cust_counts, x='Customer', y='Count'), use_container_width=True)

# ==============================
# 🤖 ALERTS
# ==============================
due_col = find_column(master_df, "over")

if due_col:
    alerts = master_df[master_df[due_col] != 0]
    if not alerts.empty:
        st.error(f"🚨 {len(alerts)} Machines Overdue!")

# ==============================
# 🔎 MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

cust_col = find_column(master_df, "customer")
fab_col = find_column(master_df, "fabrication")

customers = ["All"] + sorted(master_df[cust_col].astype(str).unique())
sel_c = st.selectbox("Customer", customers)

df_filtered = master_df if sel_c == "All" else master_df[master_df[cust_col] == sel_c]

fabrics = ["Select"] + sorted(df_filtered[fab_col].astype(str).unique())
sel_f = st.selectbox("Fabrication No", fabrics)

if sel_f != "Select":
    row = df_filtered[df_filtered[fab_col].astype(str) == sel_f].iloc[0]

    st.write("### 📋 Details")
    st.write(row)

    # ==============================
    # 🎁 FOC
    # ==============================
    foc_col = find_column(foc_df, "fabrication")

    if foc_col:
        foc_data = foc_df[foc_df[foc_col].astype(str) == sel_f]

        if not foc_data.empty:
            st.subheader("🎁 FOC Details")
            st.download_button("📥 Export FOC", to_excel(foc_data), "FOC.xlsx")
            st.dataframe(foc_data)

    # ==============================
    # 🕒 SERVICE HISTORY
    # ==============================
    serv_col = find_column(service_df, "fabrication")

    if serv_col:
        service_data = service_df[service_df[serv_col].astype(str) == sel_f]

        if not service_data.empty:
            st.subheader("🕒 Service History")
            st.dataframe(service_data)

# ==============================
# 🚪 LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
