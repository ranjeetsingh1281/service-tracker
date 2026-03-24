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
    try:
        val = pd.to_datetime(dt)
        if val.year <= 1970: return "N/A"
        return val.strftime('%d-%b-%y')
    except: return "N/A"

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
# 🏢 NAVIGATION & SIDEBAR
# ==============================
role = st.session_state["role"]
st.sidebar.title(f"👋 {st.session_state['user'].upper()}")
if role == "all":
    nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"])
elif role == "dpsac": nav = "DPSAC Tracker"
else: nav = "INDUSTRIAL Tracker"

# --- SIDEBAR STATS ---
active_v_df = master_df if nav == "DPSAC Tracker" else master_od_df
if not active_v_df.empty and nav != "📢 Automation Center":
    scol = find_col(active_v_df, ["unit", "status"])
    if scol:
        st.sidebar.markdown("### 📋 Unit Status")
        for s in ["Active", "Shifted", "Sold"]:
            c_val = len(active_v_df[active_v_df[scol].astype(str).str.contains(s, case=False, na=False)])
            st.sidebar.write(f"**{s}:** {c_val}")
    catcol = find_col(active_v_df, ["category"])
    if catcol:
        st.sidebar.markdown("### 📦 Category Breakdown")
        for k, v in active_v_df[catcol].value_counts().items():
            st.sidebar.write(f"**{k}:** {v}")

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    # 🚨 OVERDUE ALERTS
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    if overdue_col:
        crit_data = df[df[overdue_col] != 0]
        if not crit_data.empty:
            st.error(f"⚠️ {len(crit_data)} Machines are OVERDUE!")
            st.download_button(f"📥 Export Pending List", to_excel(crit_data), f"{name}_Pending.xlsx", key=f"dl_p_{key_suffix}")

    t1, t2, t3 = st.tabs(["Machine Tracker", "📦 FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        cust_col, fab_col = find_col(df, ["customer"]), find_col(df, ["fabrication"])
        sel_c = colA.selectbox(f"Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox(f"Select Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            
            # --- CALCULATIONS ---
            last_h = float(row.get(find_col(df, ["hmr", "cal"]), 0))
            avg_hrs_day = float(row.get(find_col(df, ["avg", "running"]), 0))
            last_call_h = float(row.get(find_col(df, ["last", "call", "hmr"]), 0))
            l_date_val = pd.to_datetime(row.get(find_col(df, ["hmr", "date"])))
            l_call_date = pd.to_datetime(row.get(find_col(df, ["last", "call", "date"])))
            
            days_passed = (pd.Timestamp.today() - l_date_val).days
            live_hmr = int(last_h + (max(0, days_passed) * avg_hrs_day))
            since_service = (pd.Timestamp.today() - l_call_date).days if not pd.isna(l_call_date) else 0

            m1, m2, m3, m4 = st.columns(4)
            with m1: # --- CUSTOMER INFO SECTION ---
                st.info("📋 Info")
                st.write(f"**Cust:** {row[cust_col]}")
                st.write(f"**Live HMR:** `{live_hmr}`")
                st.write(f"**Avg Running/Day:** {avg_hrs_day} Hrs")
                st.write(f"**Last Call HMR:** {last_call_h}")
                st.write(f"**Last Call Date:** {fmt(l_call_date)}")
                st.write(f"**Since Last Service:** {since_service} Days")
                st.download_button("📄 Export Machine Data", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"ex_{sel_f}")
            
            # --- 9 PARTS LOOKUP FIX ---
            pm = {
                "OIL": ["oil"], "AF": ["af"], "OF": ["of"], "AOS": ["aos"], 
                "RGT": ["rgt"], "VK": ["vk", "valve"], "PF": ["pf"], "FF": ["ff"], "CF": ["cf"]
            } if name == "INDUSTRIAL" else {
                "OIL": ["oil"], "AFC": ["afc"], "AFE": ["afe"], "MOF": ["mof"], 
                "ROF": ["rof"], "AOS": ["aos"], "RGT": ["rgt"], "1500": ["1500"], "3000": ["3000"]
            }
            
            with m2: # Replacement History
                st.info("🔧 History (9 Parts)")
                for lbl, ks in pm.items():
                    c = next((x for x in df.columns if all(k in x.lower() for k in ks) and "date" in x.lower() and "due" not in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            
            with m3: # Live Remaining
                st.info("⏳ Remaining (9 Parts)")
                for lbl, ks in pm.items():
                    rc = next((x for x in df.columns if all(k in x.lower() for k in ks) and "remaining" in x.lower()), None)
                    if rc and pd.notna(row[rc]):
                        act_r = int(float(row[rc]) - (live_hmr - last_h))
                        icon = "🟢" if act_r > 100 else "🟡" if act_r > 0 else "🔴"
                        st.write(f"**{lbl}:** {icon} {act_r}")
                    else: st.write(f"**{lbl}:** N/A")
            
            with m4: # Next Due Dates
                st.error("🚨 Next Due (9 Parts)")
                for lbl, ks in pm.items():
                    dc = next((x for x in df.columns if all(k in x.lower() for k in ks) and "due" in x.lower() and "date" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(dc))}")

            st.divider()
            h1, h2 = st.tabs(["🎁 FOC Details", "🕒 Service History"])
            with h1:
                f_c = find_col(foc_df, ["fabrication"])
                if f_c: st.dataframe(foc_df[foc_df[f_c].astype(str) == sel_f], use_container_width=True)
            with h2:
                s_c = find_col(service_df, ["fabrication"])
                if s_c: st.dataframe(service_df[service_df[s_c].astype(str) == sel_f], use_container_width=True)

    with t2: # FOC Master List Export
        st.subheader(f"📦 {name} FOC List")
        f_c = find_col(foc_df, ["fabrication"])
        f_list = foc_df[foc_df[f_c].astype(str).isin(df[fab_col].astype(str))] if not foc_df.empty else pd.DataFrame()
        st.download_button(f"📥 Export FOC List", to_excel(f_list), f"{name}_FOC.xlsx", key=f"f_ex_{key_suffix}")
        st.dataframe(f_list, use_container_width=True)

    with t3: # Service Pending List Export
        st.subheader(f"⏳ {name} Service Pending")
        st.download_button(f"📥 Export Pending List", to_excel(crit_data), f"{name}_Pending.xlsx", key=f"p_ex_{key_suffix}")
        st.dataframe(crit_data, use_container_width=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
