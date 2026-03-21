import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

# ==============================
# 🔐 LOGIN
# ==============================
USER_CREDENTIALS = {"admin": "1234"}

def login():
    st.title("🔐 Login")
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
# ⚙️ CONFIG
# ==============================
st.set_page_config(layout="wide")
st.markdown("<style>.block-container{padding:1rem;}</style>", unsafe_allow_html=True)

# ==============================
# 🧠 HELPERS
# ==============================
def find_col(df, key):
    return next((c for c in df.columns if key.lower() in c.lower()), None)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load():
    files = os.listdir('.')
    def f(x): return next((i for i in files if x.lower() in i.lower()), None)

    m = pd.read_excel(f("Master_Data")) if f("Master_Data") else pd.DataFrame()
    foc = pd.read_excel(f("FOC")) if f("FOC") else pd.DataFrame()
    s = pd.read_excel(f("Service")) if f("Service") else pd.DataFrame()

    return m, foc, s

master_df, foc_df, service_df = load()

# ==============================
# 📊 HEADER + METRICS
# ==============================
st.title("🛠️ DPSAC Tracker - Standard Machine Data")

status_col = find_col(master_df, "status")
cust_col = find_col(master_df, "customer")
fab_col = find_col(master_df, "fabrication")

if status_col:
    total = len(master_df)
    active = len(master_df[master_df[status_col].astype(str).str.contains("Active", case=False)])
    shifted = len(master_df[master_df[status_col].astype(str).str.contains("Shifted", case=False)])
    sold = len(master_df[master_df[status_col].astype(str).str.contains("Sold", case=False)])

    st.markdown(f"""
    | Total | Active | Shifted | Sold |
    |---|---|---|---|
    | {total} | {active} | {shifted} | {sold} |
    """)

# ==============================
# 📊 CHARTS
# ==============================
st.subheader("📊 Analytics")
colA, colB = st.columns(2)

if status_col:
    st1 = master_df[status_col].value_counts().reset_index()
    st1.columns = ["Status", "Count"]
    colA.plotly_chart(px.pie(st1, names="Status", values="Count"), use_container_width=True)

if cust_col:
    st2 = master_df[cust_col].value_counts().head(10).reset_index()
    st2.columns = ["Customer", "Count"]
    colB.plotly_chart(px.bar(st2, x="Customer", y="Count"), use_container_width=True)

# ==============================
# 🤖 ALERT
# ==============================
over_col = find_col(master_df, "over")
if over_col:
    alert = master_df[master_df[over_col] != 0]
    if not alert.empty:
        st.error(f"🚨 {len(alert)} Machines Overdue!")

# ==============================
# 🔀 TABS
# ==============================
tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

# =========================================
# 🛠️ MACHINE TRACKER
# =========================================
with tab1:
    col1, col2 = st.columns(2)

    customers = ["All"] + sorted(master_df[cust_col].astype(str).unique())
    sel_c = col1.selectbox("Customer", customers)

    df_f = master_df if sel_c == "All" else master_df[master_df[cust_col] == sel_c]

    fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
    sel_f = col2.selectbox("Fabrication No", fabs)

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        # COLUMN 1: CUSTOMER INFO
        with c1:
            st.info("Customer Info")
            st.write(f"Customer: {row.get(cust_col)}")
            st.write(f"Model: {row.get(find_col(master_df,'model'))}")
            st.write(f"Warranty: {row.get(find_col(master_df,'warranty'))}")
            st.write(f"Location: {row.get(find_col(master_df,'location'))}")
            st.write(f"Avg Run Hrs: {row.get(find_col(master_df,'avg'))}")
            st.write(f"Running Hrs: {row.get(find_col(master_df,'hmr'))}")

        # COLUMN 2: REPLACEMENT
        with c2:
            st.info("Replacement Dates")
            for col in master_df.columns:
                if "date" in col.lower() and "replaced" in col.lower():
                    st.write(f"{col}: {fmt(row.get(col))}")

        # COLUMN 3: REMAINING
        with c3:
            st.info("Remaining Hours")
            for col in master_df.columns:
                if "remaining" in col.lower():
                    st.write(f"{col}: {row.get(col)}")

        # COLUMN 4: DUE
        with c4:
            st.error("Due Dates")
            for col in master_df.columns:
                if "due" in col.lower():
                    st.write(f"{col}: {fmt(row.get(col))}")

        # FOC DETAILS
        foc_col = find_col(foc_df, "fabrication")
        if foc_col:
            foc_data = foc_df[foc_df[foc_col].astype(str) == sel_f]
            st.subheader("🎁 FOC Details")
            st.download_button("Download FOC", to_excel(foc_data), "FOC.xlsx")
            st.dataframe(foc_data)

        # SERVICE HISTORY
        serv_col = find_col(service_df, "fabrication")
        if serv_col:
            serv_data = service_df[service_df[serv_col].astype(str) == sel_f]
            st.subheader("🕒 Service History")
            st.dataframe(serv_data)

# =========================================
# 📦 FOC LIST
# =========================================
with tab2:
    st.subheader("FOC List")
    st.download_button("Export FOC", to_excel(foc_df), "FOC.xlsx")
    st.dataframe(foc_df)

# =========================================
# ⏳ SERVICE PENDING
# =========================================
with tab3:
    st.subheader("Service Pending")

    if over_col:
        overdue = master_df[master_df[over_col] != 0]
        st.write(f"Overdue Count: {len(overdue)}")
        st.dataframe(overdue)

# ==============================
# 🚪 LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
