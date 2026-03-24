import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 ROLE-BASED LOGIN SYSTEM
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

# --- SIDEBAR STATUS COUNTS ---
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
            
            # --- 📊 CUSTOMER INFO & HMR FIELDS ---
            # Columns BL (Current), BM (Load), BN (Unload), BO (Diff)
            avg_run = row.get(find_col(df, ["avg", "running"]), "N/A")
            curr_hmr = row.get("CURRENT HMR", "N/A") 
            load_hmr = row.get("CURRENT LOAD HMR", "N/A") 
            unload_hmr = row.get("CURRENT UNLOAD HMR", "N/A") 
            diff_hmr = row.get("DIFFRENT HMR", "N/A") 
            l_call_date = row.get(find_col(df, ["last", "call", "date"]))

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Info")
                st.write(f"**Cust:** {row[cust_col]}")
                st.write(f"**Avg Running/Day:** {avg_run}")
                st.write(f"**Current HMR:** `{curr_hmr}`")
                st.write(f"**Load HMR:** `{load_hmr}`")
                st.write(f"**Unload HMR:** `{unload_hmr}`")
                st.write(f"**Difference HMR:** `{diff_hmr}`")
                st.write(f"**Last Service:** {fmt(l_call_date)}")
                st.download_button("📄 Export Report", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"ex_{sel_f}")
            
            # --- 🔧 9 PARTS DIRECT LOOKUP ---
            if name == "INDUSTRIAL":
                # Mapping keywords to match "Rem. HMR Till date" columns
                pm = {
                    "AF": ["af", "rem", "hmr"], "OF": ["of", "rem", "hmr"], 
                    "OIL": ["oil", "rem", "hmr"], "AOS": ["aos", "rem", "hmr"], 
                    "VK": ["vk", "rem", "hmr"], "RGT": ["rgt", "rem", "hmr"],
                    "PF": ["pf", "due"], "FF": ["ff", "due"], "CF": ["cf", "due"]
                }
            else:
                pm = {"OIL": ["oil"],"AFC": ["afc"],"AFE": ["afe"],"MOF": ["mof"],"ROF": ["rof"],"AOS": ["aos"],"RGT": ["rgt"],"1500": ["1500"],"3000": ["3000"]}

            with m2:
                st.info("🔧 History (Dates)")
                for lbl, ks in pm.items():
                    c = next((x for x in df.columns if all(k in x.lower() for k in ks) and "date" in x.lower() and "due" not in x.lower()), None)
                    if not c: c = next((x for x in df.columns if lbl.lower() in x.lower() and "replaced" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            
            with m3:
                st.info("⏳ Remaining (Direct Lookup)")
                for lbl, ks in pm.items():
                    # Direct lookup from Excel headers: "Rem. HMR Till date"
                    rc = next((x for x in df.columns if all(k in x.lower() for k in ks) and "rem" in x.lower()), None)
                    val = row.get(rc, "N/A")
                    if pd.notna(val) and val != "N/A":
                        try:
                            # Color icon based on value
                            icon = "🟢" if float(val) > 100 else "🔴"
                            st.write(f"**{lbl}:** {icon} {val}")
                        except: st.write(f"**{lbl}:** {val}")
                    else: st.write(f"**{lbl}:** N/A")
            
            with m4:
                st.error("🚨 Next Due")
                for lbl, ks in pm.items():
                    dc = next((x for x in df.columns if lbl.lower() in x.lower() and "due" in x.lower() and "date" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(dc))}")

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
        st.download_button(f"📥 Export FOC List", to_excel(f_list), f"{name}_FOC.xlsx", key=f"f_ex_{key_suffix}")
        st.dataframe(f_list, use_container_width=True)

    with t3:
        st.subheader(f"⏳ {name} Service Pending")
        st.download_button(f"📥 Export Pending List", to_excel(crit_data), f"{name}_Pending.xlsx", key=f"p_ex_{key_suffix}")
        st.dataframe(crit_data, use_container_width=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
