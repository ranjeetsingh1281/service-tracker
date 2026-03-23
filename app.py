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

    return (
        pd.read_excel(f("Master_Data")) if f("Master_Data") else pd.DataFrame(),
        pd.read_excel(f("Master_OD_Data")) if f("Master_OD_Data") else pd.DataFrame(),
        pd.read_excel(f("FOC")) if f("FOC") else pd.DataFrame(),
        pd.read_excel(f("Service")) if f("Service") else pd.DataFrame()
    )

master_df, master_od_df, foc_df, service_df = load()

# ==============================
# 📊 COMMON DASHBOARD FUNCTION
# ==============================
def dashboard(df, title):
    st.title(title)

    status_col = find_col(df, "status")
    cust_col = find_col(df, "customer")
    fab_col = find_col(df, "fabrication")

    # METRICS
    if status_col:
        total = len(df)
        active = len(df[df[status_col].astype(str).str.contains("Active", case=False)])
        shifted = len(df[df[status_col].astype(str).str.contains("Shifted", case=False)])
        sold = len(df[df[status_col].astype(str).str.contains("Sold", case=False)])

        st.markdown(f"""
        | Total | Active | Shifted | Sold |
        |---|---|---|---|
        | {total} | {active} | {shifted} | {sold} |
        """)

    # CHARTS
    st.subheader("📊 Analytics")
    c1, c2 = st.columns(2)

    if status_col:
        s = df[status_col].value_counts().reset_index()
        s.columns = ["Status", "Count"]
        c1.plotly_chart(px.pie(s, names="Status", values="Count"), use_container_width=True)

    if cust_col:
        c = df[cust_col].value_counts().head(10).reset_index()
        c.columns = ["Customer", "Count"]
        c2.plotly_chart(px.bar(c, x="Customer", y="Count"), use_container_width=True)

    # ALERT
    over_col = find_col(df, "over")
    if over_col:
        alerts = df[df[over_col] != 0]
        if not alerts.empty:
            st.error(f"🚨 {len(alerts)} Machines Overdue!")

    # TABS
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    # MACHINE TRACKER
    with tab1:
        col1, col2 = st.columns(2)

        customers = ["All"] + sorted(df[cust_col].astype(str).unique())
        sel_c = col1.selectbox("Customer", customers, key=title+"c")

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs, key=title+"f")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.info("Customer Info")
                st.write(f"Customer: {row.get(cust_col)}")
                st.write(f"Model: {row.get(find_col(df,'model'))}")
                st.write(f"Warranty: {row.get(find_col(df,'warranty'))}")
                st.write(f"Location: {row.get(find_col(df,'location'))}")
                st.write(f"Avg Run Hrs: {row.get(find_col(df,'avg'))}")
                st.write(f"Running Hrs: {row.get(find_col(df,'hmr'))}")

            with c2:
                st.info("Replacement Dates")
                for col in df.columns:
                    if "replaced" in col.lower():
                        st.write(f"{col}: {fmt(row.get(col))}")

            with c3:
                st.info("Remaining Hours")
                for col in df.columns:
                    if "remaining" in col.lower():
                        st.write(f"{col}: {row.get(col)}")

            with c4:
                st.error("Due Dates")
                for col in df.columns:
                    if "due" in col.lower():
                        st.write(f"{col}: {fmt(row.get(col))}")

            # FOC
            foc_col = find_col(foc_df, "fabrication")
            if foc_col:
                foc_data = foc_df[foc_df[foc_col].astype(str) == sel_f]
                st.subheader("🎁 FOC Details")
                st.dataframe(foc_data)

            # SERVICE
            serv_col = find_col(service_df, "fabrication")
            if serv_col:
                serv_data = service_df[service_df[serv_col].astype(str) == sel_f]
                st.subheader("🕒 Service History")
                st.dataframe(serv_data)

    # FOC LIST
    with tab2:
        st.download_button("Export FOC", to_excel(foc_df), f"{title}_FOC.xlsx")
        st.dataframe(foc_df)

    # SERVICE PENDING
    with tab3:
        if over_col:
            p = df[df[over_col] != 0]
            st.write(f"Pending Count: {len(p)}")
            st.dataframe(p)

# ==============================
# 🧭 MENU
# ==============================
st.sidebar.title("🏢 ELGi Menu")
choice = st.sidebar.radio("Select Tracker", ["DPSAC Tracker", "INDUSTRIAL Tracker"])

if choice == "DPSAC Tracker":
    dashboard(master_df, "DPSAC Tracker - Standard Machine Data")

else:
    dashboard(master_od_df, "INDUSTRIAL Tracker - Industrial Data")

# ==============================
# 🚪 LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
