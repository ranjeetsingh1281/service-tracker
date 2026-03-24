import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 ROLE-BASED LOGIN
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user1": {"pass": "dpsac123", "role": "dpsac"},
    "user2": {"pass": "ind123", "role": "industrial"}
}

def login():
    st.title("🔐 ELGi Global Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["user"] = u
            st.session_state["role"] = USER_DB[u]["role"]
            st.rerun()
        else: st.error("Invalid Credentials")

if "login" not in st.session_state or not st.session_state["login"]:
    login(); st.stop()

# ==============================
# ⚙️ CONFIG & HELPERS
# ==============================
st.set_page_config(page_title="ELGi Global Tracker Pro", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def find_col(df, keywords):
    if df.empty: return None
    for c in df.columns:
        if all(k.lower() in str(c).lower() for k in keywords): return c
    return None

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==============================
# 📂 DATA LOADING
# ==============================
@st.cache_data
def load():
    f_list = os.listdir('.')
    def f(name): return next((x for x in f_list if name.lower() in x.lower() and x.endswith('.xlsx')), None)
    
    m_df = pd.read_excel(f("Master_Data"), engine='openpyxl') if f("Master_Data") else pd.DataFrame()
    m_od_df = pd.read_excel(f("Master_OD_Data"), engine='openpyxl') if f("Master_OD_Data") else pd.DataFrame()
    foc_df = pd.read_excel(f("Active_FOC"), engine='openpyxl') if f("Active_FOC") else pd.DataFrame()
    srv_df = pd.read_excel(f("Service_Details"), engine='openpyxl') if f("Service_Details") else pd.DataFrame()
    
    for d in [m_df, m_od_df, foc_df, srv_df]:
        if not d.empty: d.columns = [str(c).strip() for c in d.columns]
    return m_df, m_od_df, foc_df, srv_df

master_df, master_od_df, foc_df, service_df = load()

# ==============================
# 🏢 NAVIGATION (RBAC)
# ==============================
role = st.session_state["role"]
st.sidebar.title(f"👋 {st.session_state['user'].upper()}")
if role == "all":
    nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"])
elif role == "dpsac": nav = "DPSAC Tracker"
else: nav = "INDUSTRIAL Tracker"

# --- 📊 SIDEBAR COUNTS & CATEGORIES ---
st.sidebar.markdown("---")
active_df = master_df if nav == "DPSAC Tracker" else master_od_df
if not active_df.empty:
    s_col = find_col(active_df, ["unit", "status"])
    if s_col:
        st.sidebar.markdown("### 📋 Unit Status Counts")
        for s in ["Active", "Shifted", "Sold"]:
            count = len(active_df[active_df[s_col].astype(str).str.contains(s, case=False, na=False)])
            st.sidebar.write(f"**{s}:** {count}")
    
    cat_col = find_col(active_df, ["category"])
    if cat_col:
        st.sidebar.markdown("### 📦 Category Breakdown")
        for k, v in active_df[cat_col].value_counts().items():
            st.sidebar.write(f"**{k}:** {v}")

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    # Graphs & Charts
    with st.expander("📊 Dashboard Analytics & Graphs", expanded=False):
        c1, c2 = st.columns(2)
        sc = find_col(df, ["unit", "status"])
        if sc: c1.bar_chart(df[sc].value_counts())
        cc = find_col(df, ["category"])
        if cc: c2.bar_chart(df[cc].value_counts())

    # Alerts
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    if overdue_col:
        critical = df[df[overdue_col] != 0]
        if not critical.empty:
            st.error(f"⚠️ {len(critical)} Machines are OVERDUE!")
            st.download_button(f"📥 Export Pending List", to_excel(critical), f"{name}_Pending.xlsx")

    # Tabs
    t1, t2, t3 = st.tabs(["Machine Tracker", "📦 FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        cust_col, fab_col = find_col(df, ["customer"]), find_col(df, ["fabrication"])
        sel_c = colA.selectbox("Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"c_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox("Select Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"f_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            try:
                last_h = float(row.get(find_col(df, ["hmr", "cal"]), 0))
                avg = float(row.get(find_col(df, ["avg", "running"]), 0))
                l_date = pd.to_datetime(row.get(find_col(df, ["hmr", "date"])))
                live_hmr = int(last_h + (max(0, (pd.Timestamp.today() - l_date).days) * avg))
            except: live_hmr = int(row.get(find_col(df, ["hmr", "cal"]), 0))

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Info")
                st.write(f"**Cust:** {row[cust_col]}\n**HMR Live:** `{live_hmr}`")
                st.download_button("📄 Export Report", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx")
            
            # Master Parts List (Synchronized for all sections)
            parts = ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"] if name == "DPSAC" else ["oil","af","of","aos","rgt","vk","pf","ff","cf"]
            
            with m2:
                st.info("🔧 History (9 Parts)")
                for p in parts:
                    col = next((c for c in df.columns if p in c.lower() and "date" in c.lower() and "due" not in c.lower()), None)
                    st.write(f"**{p.upper()}:** {fmt(row.get(col))}")
            
            with m3:
                st.info("⏳ Remaining (9 Parts)")
                for p in parts:
                    # Searching for remaining columns dynamically
                    rem_c = next((c for c in df.columns if p in c.lower() and "remaining" in c.lower()), None)
                    if rem_c and pd.notna(row[rem_c]):
                        # Adjusting remaining based on live HMR delta
                        act_rem = int(float(row[rem_c]) - (live_hmr - last_h))
                        icon = "🟢" if act_rem > 100 else "🟡" if act_rem > 0 else "🔴"
                        st.write(f"**{p.upper()}:** {icon} {act_rem}")
                    else:
                        st.write(f"**{p.upper()}:** N/A")
            
            with m4:
                st.error("🚨 Next Due (9 Parts)")
                for p in parts:
                    due_c = next((c for c in df.columns if p in c.lower() and "due" in c.lower() and "date" in c.lower()), None)
                    if due_c: st.write(f"**{p.upper()}:** {fmt(row.get(due_c))}")

            st.divider()
            h1, h2 = st.tabs(["🎁 FOC Details", "🕒 Service History"])
            with h1:
                f_c = find_col(foc_df, ["fabrication"])
                if f_c: st.dataframe(foc_df[foc_df[f_c].astype(str) == sel_f], use_container_width=True)
            with h2:
                s_c = find_col(service_df, ["fabrication"])
                if s_c: st.dataframe(service_df[service_df[s_c].astype(str) == sel_f], use_container_width=True)

    with t2:
        st.subheader(f"📦 {name} FOC List")
        f_c = find_col(foc_df, ["fabrication"])
        f_list = foc_df[foc_df[f_c].astype(str).isin(df[fab_col].astype(str))] if not foc_df.empty else pd.DataFrame()
        st.download_button(f"📥 Export FOC List", to_excel(f_list), f"{name}_FOC.xlsx")
        st.dataframe(f_list, use_container_width=True)

    with t3:
        st.subheader(f"⏳ {name} Service Pending")
        st.download_button(f"📥 Export Pending List", to_excel(critical), f"{name}_Pending.xlsx")
        st.dataframe(critical, use_container_width=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker":
    run_tracker(master_df, "DPSAC", "DPSAC")
elif nav == "INDUSTRIAL Tracker":
    run_tracker(master_od_df, "INDUSTRIAL", "IND")
