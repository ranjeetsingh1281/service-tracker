import streamlit as st
import pandas as pd
import os
from io import BytesIO

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

# ==============================
# 🧠 HELPERS
# ==============================
def safe_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None

def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load():
    files = os.listdir('.')

    def f(name):
        return next((x for x in files if name.lower() in x.lower()), None)

    m = pd.read_excel(f("Master_Data")) if f("Master_Data") else pd.DataFrame()
    od = pd.read_excel(f("Master_OD_Data")) if f("Master_OD_Data") else pd.DataFrame()
    foc = pd.read_excel(f("FOC")) if f("FOC") else pd.DataFrame()
    s = pd.read_excel(f("Service")) if f("Service") else pd.DataFrame()

    for d in [m, od, foc, s]:
        if not d.empty:
            d.columns = d.columns.str.strip()

    return m, od, foc, s

master_df, master_od_df, foc_df, service_df = load()

# ==============================
# 🧭 MENU
# ==============================
st.sidebar.title("🏢 ELGi Menu")
choice = st.sidebar.radio("Select Tracker", ["DPSAC Tracker", "INDUSTRIAL Tracker"])

# ==============================
# 📊 DASHBOARD FUNCTION
# ==============================
def dashboard(df, title, industrial=False):

    st.title(f"🛠️ {title}")

    cust_col = safe_col(df, "customer")
    fab_col = safe_col(df, "fabrication")
    status_col = safe_col(df, "status")

    # ==============================
    # 📊 METRICS
    # ==============================
    if status_col:
        total = len(df)
        active = len(df[df[status_col].astype(str).str.contains("Active", case=False, na=False)])
        shifted = len(df[df[status_col].astype(str).str.contains("Shifted", case=False, na=False)])
        sold = len(df[df[status_col].astype(str).str.contains("Sold", case=False, na=False)])

        st.markdown(f"""
        | Total | Active | Shifted | Sold |
        |---|---|---|---|
        | **{total}** | **{active}** | **{shifted}** | **{sold}** |
        """)

    # ==============================
    # CATEGORY
    # ==============================
    cat_col = safe_col(df, "category")
    if cat_col:
        st.subheader("📊 Category Count")
        st.dataframe(df[cat_col].value_counts().reset_index().rename(columns={"index":"Category", cat_col:"Count"}))

    # ==============================
    # TABS
    # ==============================
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tab1:

        if not cust_col or not fab_col:
            st.error("❌ Required columns missing (Customer/Fabrication)")
            return

        col1, col2 = st.columns(2)

        customers = ["All"] + sorted(df[cust_col].astype(str).unique())
        sel_c = col1.selectbox("Customer", customers)

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs)

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

# ==============================
# COLUMN 1
# ==============================
with c1:
    st.markdown("### **📋 Customer Info**")
    st.write(f"**Customer:** {row.get(cust_col)}")
    st.write(f"**Model:** {row.get(safe_col(df,'model'))}")
    st.write(f"**Location:** {row.get(safe_col(df,'location'))}")
    st.write(f"**Running Hrs:** {row.get(safe_col(df,'hmr'))}")

# ==============================
# COLUMN 2
# ==============================
with c2:
    st.markdown("### **🔧 Replacement Dates**")

    if not industrial:
        rep_map = {
            "Oil": "Oil R-Date",
            "AFC": "AFC R-Date",
            "AFE": "AFE R-Date",
            "MOF": "MOF R-Date",
            "ROF": "ROF R-Date",
            "AOS": "AOS R-Date",
            "RGT": "Greasing R-Date",
            "1500K": "1500 Kit R-Date",
            "3000K": "3000 Kit R-Date"
        }
    else:
        rep_map = {
            "Oil": "MDA Oil R Date",
            "AF": "MDA AF R Date",
            "OF": "MDA OF R Date",
            "AOS": "MDA AOS R Date",
            "RGT": "MDA RGT R Date",
            "VK": "MDA Valvekit R Date",
            "PF": "MDA PF R DATE",
            "FF": "MDA FF R DATE",
            "CF": "MDA CF R DATE"
        }

    for k, v in rep_map.items():
        col = safe_col(df, v)
        st.write(f"**{k}:** {fmt(row.get(col)) if col else 'N/A'}")

# ==============================
# COLUMN 3
# ==============================
with c3:
    st.markdown("### **⚙️ Remaining Hours**")

    if not industrial:
        rem_map = {
            "Oil": "HMR - Oil remaining",
            "AFC": "Air filter Compressor Remaining Hours",
            "AFE": "Air filter Engine Remaining Hours",
            "MOF": "Main Oil filter Remaining Hours",
            "ROF": "Return Oil filter Remaining Hours",
            "AOS": "Separator Remaining Hours",
            "RGT": "Motor Greasing Remaining Hours",
            "1500K": "1500 Kit Remaining Hours",
            "3000K": "3000 Kit Remaining Hours"
        }
    else:
        rem_map = {
            "AF": "AF Rem. HMR Till date",
            "OF": "OF Rem. HMR Till date",
            "OIL": "OIL Rem. HMR Till date",
            "AOS": "AOS Rem. HMR Till date",
            "VK": "VK Rem. HMR Till date",
            "RGT": "RGT Rem. HMR Till date"
        }

    for k, v in rem_map.items():
        col = safe_col(df, v)
        val = row.get(col) if col else None
        st.write(f"**{k}:** {val if pd.notna(val) else 'N/A'}")

# ==============================
# COLUMN 4
# ==============================
with c4:
    st.markdown("### **🚨 Due Dates**")

    if not industrial:
        due_map = {
            "OIL": "OIL DUE DATE",
            "AFC": "AFC DUE DATE",
            "AFE": "AFE DUE DATE",
            "MOF": "MOF DUE DATE",
            "ROF": "ROF DUE DATE",
            "AOS": "AOS DUE DATE",
            "RGT": "RGT DUE DATE",
            "1500K": "1500 KIT DUE DATE",
            "3000K": "3000 KIT DUE DATE"
        }
    else:
        due_map = {
            "AF": "AF DUE DATE",
            "OF": "OF DUE DATE",
            "OIL": "OIL DUE DATE",
            "AOS": "AOS DUE DATE",
            "VK": "VALVEKIT DUE DATE",
            "RGT": "RGT DUE DATE",
            "PF": "PF DUE DATE",
            "FF": "FF DUE DATE",
            "CF": "CF DUE DATE"
        }

    for k, v in due_map.items():
        col = safe_col(df, v)
        st.write(f"**{k}:** {fmt(row.get(col)) if col else 'N/A'}")

            # ==============================
            # FOC
            # ==============================
            foc_col = safe_col(foc_df, "fabrication")
            if foc_col:
                st.subheader("🎁 FOC Details")
                st.dataframe(foc_df[foc_df[foc_col].astype(str) == sel_f])

            # ==============================
            # SERVICE
            # ==============================
            serv_col = safe_col(service_df, "fabrication")
            if serv_col:
                st.subheader("🕒 Service History")
                st.dataframe(service_df[service_df[serv_col].astype(str) == sel_f])

    with tab2:
        st.dataframe(foc_df)

    with tab3:
        over_col = safe_col(df, "over")
        if over_col:
            pending = df[df[over_col] != 0]
            st.write(f"Pending Count: {len(pending)}")
            st.dataframe(pending)

# ==============================
# RUN
# ==============================
if choice == "DPSAC Tracker":
    dashboard(master_df, "DPSAC Tracker", False)
else:
    dashboard(master_od_df, "INDUSTRIAL Tracker", True)

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
