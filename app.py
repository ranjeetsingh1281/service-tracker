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

def find_col(df, keywords):
    for c in df.columns:
        if all(k.lower() in c.lower() for k in keywords):
            return c
    return None

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load_file(name):
    files = os.listdir('.')
    f = next((x for x in files if name.lower() in x.lower()), None)
    if f:
        df = pd.read_excel(f)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

master_df = load_file("Master_Data")
master_od_df = load_file("Master_OD_Data")
foc_df = load_file("FOC")
service_df = load_file("Service")

# ==============================
# 🧭 SIDEBAR
# ==============================
st.sidebar.title("🏢 ELGi Menu")

tracker = st.sidebar.radio(
    "Select Tracker",
    ["DPSAC Tracker", "INDUSTRIAL Tracker"]
)

# SWITCH DATA
df = master_df if tracker == "DPSAC Tracker" else master_od_df

# ==============================
# COLUMN DETECTION
# ==============================
cust_col = find_col(df, ["customer"])
fab_col = find_col(df, ["fabrication"])
status_col = find_col(df, ["unit", "status"])
cat_col = find_col(df, ["category"])

# ==============================
# 📊 SIDEBAR METRICS
# ==============================
if status_col:
    total = len(df)
    active = df[df[status_col].astype(str).str.contains("Active", case=False, na=False)].shape[0]
    shifted = df[df[status_col].astype(str).str.contains("Shifted", case=False, na=False)].shape[0]
    sold = df[df[status_col].astype(str).str.contains("Sold", case=False, na=False)].shape[0]

    st.sidebar.markdown("### 📊 Unit Summary")
    st.sidebar.write(f"Total: {total}")
    st.sidebar.write(f"Active: {active}")
    st.sidebar.write(f"Shifted: {shifted}")
    st.sidebar.write(f"Sold: {sold}")

# CATEGORY
if cat_col:
    st.sidebar.markdown("### 📦 Category Count")
    for k, v in df[cat_col].value_counts().items():
        st.sidebar.write(f"{k}: {v}")

# ==============================
# MAIN TITLE
# ==============================
st.title(f"🛠️ {tracker}")

# ==============================
# 📊 CHARTS
# ==============================
st.subheader("📊 Dashboard Analytics")

colA, colB = st.columns(2)

if status_col:
    colA.plotly_chart({
        "data": [{
            "labels": ["Active", "Shifted", "Sold"],
            "values": [active, shifted, sold],
            "type": "pie"
        }]
    }, use_container_width=True)

if cat_col:
    cat_df = df[cat_col].value_counts().reset_index()
    cat_df.columns = ["Category", "Count"]

    colB.plotly_chart({
        "data": [{
            "x": cat_df["Category"],
            "y": cat_df["Count"],
            "type": "bar"
        }]
    }, use_container_width=True)

# ==============================
# FILTER
# ==============================
col1, col2 = st.columns(2)

customers = ["All"] + sorted(df[cust_col].astype(str).unique()) if cust_col else ["All"]
sel_c = col1.selectbox("Customer", customers)

df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique()) if fab_col else ["Select"]
sel_f = col2.selectbox("Fabrication No", fabs)

# ==============================
# DETAILS
# ==============================
if sel_f != "Select":

    row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    # COLUMN 1
    with c1:
        st.markdown("### **📋 Customer Info**")
        st.write(f"**Customer:** {row.get(cust_col)}")
        st.write(f"**Model:** {row.get(find_col(df,['model']))}")
        st.write(f"**Location:** {row.get(find_col(df,['location']))}")
        st.write(f"**Running Hrs:** {row.get(find_col(df,['hmr']))}")

    # COLUMN 2 (REPLACEMENT)
    with c2:
        st.markdown("### **🔧 Replacement Dates**")
        for p in ["oil","afc","afe","mof","rof","aos","greasing","1500","3000"]:
            col = next((c for c in df.columns if p in c.lower() and "date" in c.lower()), None)
            st.write(f"**{p.upper()}:** {fmt(row.get(col)) if col else 'N/A'}")

    # COLUMN 3 (REMAINING)
    with c3:
        st.markdown("### **⚙️ Remaining Hours (Live)**")

        try:
            last_hmr = float(row.get(find_col(df,["last","hmr"])) or 0)
            avg = float(row.get(find_col(df,["avg"])) or 0)
            last_date = pd.to_datetime(row.get(find_col(df,["last","date"])))

            days = (pd.Timestamp.today() - last_date).days
            live_hmr = int(last_hmr + (days * avg))

            st.write(f"**Live HMR:** {live_hmr}")
        except:
            live_hmr = 0
            st.write("Live HMR: N/A")

        for p in ["oil","afc","afe","mof","rof","aos","1500","3000"]:
            col = next((c for c in df.columns if p in c.lower() and "remaining" in c.lower()), None)

            if col and pd.notna(row[col]):
                rem = int(float(row[col]) - live_hmr)

                if rem > 0:
                    st.write(f"**{p.upper()}:** 🟢 {rem}")
                elif rem > -50:
                    st.write(f"**{p.upper()}:** 🟡 {rem}")
                else:
                    st.write(f"**{p.upper()}:** 🔴 {rem}")
            else:
                st.write(f"**{p.upper()}:** N/A")

    # COLUMN 4 (DUE)
    with c4:
        st.markdown("### **🚨 Due Dates**")
        for col in df.columns:
            if "due" in col.lower():
                st.write(f"**{col}:** {fmt(row.get(col))}")

    # FOC
    st.subheader("🎁 FOC Details")
    foc_col = find_col(foc_df, ["fabrication"])
    if foc_col:
        st.dataframe(foc_df[foc_df[foc_col].astype(str) == sel_f])

    # SERVICE
    st.subheader("🕒 Service History")
    serv_col = find_col(service_df, ["fabrication"])
    if serv_col:
        st.dataframe(service_df[service_df[serv_col].astype(str) == sel_f])

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
