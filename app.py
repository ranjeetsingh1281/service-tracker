import streamlit as st
import pandas as pd
import os

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
# 🚀 DASHBOARD
# ==============================
def dashboard(df, title):

    st.title(f"🛠️ {title}")

    cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
    fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
    status_col = next((c for c in df.columns if "unit status" in c.lower()), None)
    cat_col = next((c for c in df.columns if "category" in c.lower()), None)

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

        st.sidebar.markdown("### 📊 Unit Summary")
        st.sidebar.write(f"Total: {total}")
        st.sidebar.write(f"Active: {active}")
        st.sidebar.write(f"Shifted: {shifted}")
        st.sidebar.write(f"Sold: {sold}")

    if cat_col:
        st.sidebar.markdown("### 📦 Category Count")
        for k, v in df[cat_col].value_counts().items():
            st.sidebar.write(f"{k}: {v}")

    # ==============================
    # TRACKER
    # ==============================
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tab1:

        if not cust_col or not fab_col:
            st.error("Missing required columns")
            return

        col1, col2 = st.columns(2)

        customers = ["All"] + sorted(df[cust_col].astype(str).unique())
        sel_c = col1.selectbox("Customer", customers)

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs)

        if sel_f != "Select":

            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            # ==============================
            # 4 COLUMNS (SAFE BLOCK)
            # ==============================
            c1, c2, c3, c4 = st.columns(4)

            # COLUMN 1
            with c1:
                st.markdown("### **Customer Info**")
                st.write(f"Customer: {row.get(cust_col)}")
                st.write(f"Model: {row.get(next((c for c in df.columns if 'model' in c.lower()), None))}")
                st.write(f"Location: {row.get(next((c for c in df.columns if 'location' in c.lower()), None))}")
                st.write(f"Running Hrs: {row.get(next((c for c in df.columns if 'hmr' in c.lower()), None))}")

            # COLUMN 2
            with c2:
                st.markdown("### **Replacement Dates**")

                rep_cols = [
                    "Oil R-Date","AFC R-Date","AFE R-Date","MOF R-Date",
                    "ROF R-Date","AOS R-Date","Greasing R-Date",
                    "1500 Kit R-Date","3000 Kit R-Date"
                ]

                for col_name in rep_cols:
                    col = next((c for c in df.columns if col_name in c), None)
                    st.write(f"{col_name}: {fmt(row.get(col)) if col else 'N/A'}")

            # COLUMN 3 (FINAL FIXED)
            with c3:
                st.markdown("### **Remaining Hours (Live)**")

                try:
                    last_hmr = float(row.get(next((c for c in df.columns if "last call hmr" in c.lower()), None)) or 0)
                    avg = float(row.get(next((c for c in df.columns if "avg" in c.lower()), None)) or 0)
                    last_date = pd.to_datetime(row.get(next((c for c in df.columns if "last call" in c.lower() and "date" in c.lower()), None)))

                    days = (pd.Timestamp.today() - last_date).days
                    live_hmr = int(last_hmr + (days * avg))

                    st.write(f"Live HMR: {live_hmr}")

                except:
                    st.write("Live HMR: N/A")

            # COLUMN 4
            with c4:
                st.markdown("### **Due Dates**")

                due_cols = [
                    "OIL DUE DATE","AFC DUE DATE","AFE DUE DATE","MOF DUE DATE",
                    "ROF DUE DATE","AOS DUE DATE","RGT DUE DATE",
                    "1500 KIT DUE DATE","3000 KIT DUE DATE"
                ]

                for col_name in due_cols:
                    col = next((c for c in df.columns if col_name in c), None)
                    st.write(f"{col_name}: {fmt(row.get(col)) if col else 'N/A'}")

            # FOC
            st.subheader("🎁 FOC Details")
            foc_col = next((c for c in foc_df.columns if "fabrication" in c.lower()), None)
            if foc_col:
                st.dataframe(foc_df[foc_df[foc_col].astype(str) == sel_f])

            # SERVICE
            st.subheader("🕒 Service History")
            serv_col = next((c for c in service_df.columns if "fabrication" in c.lower()), None)
            if serv_col:
                st.dataframe(service_df[service_df[serv_col].astype(str) == sel_f])

    with tab2:
        st.dataframe(foc_df)

    with tab3:
        st.dataframe(df)

# ==============================
# RUN
# ==============================
if choice == "DPSAC Tracker":
    dashboard(master_df, "DPSAC Tracker")
else:
    dashboard(master_od_df, "INDUSTRIAL Tracker")

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
