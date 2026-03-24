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
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

def find_col(df, keywords):
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

# Sidebar Stats
active_v_df = master_df if nav == "DPSAC Tracker" else master_od_df
if not active_v_df.empty and nav != "📢 Automation Center":
    scol = find_col(active_v_df, ["unit", "status"])
    if scol:
        st.sidebar.markdown("### 📋 Unit Status Counts")
        for s in ["Active", "Shifted", "Sold"]:
            st.sidebar.write(f"**{s}:** {len(active_v_df[active_v_df[scol].astype(str).str.contains(s, case=False, na=False)])}")
    catcol = find_col(active_v_df, ["category"])
    if catcol:
        st.sidebar.markdown("### 📦 Category Breakdown")
        for k, v in active_v_df[catcol].value_counts().items(): st.sidebar.write(f"**{k}:** {v}")

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    if overdue_col:
        crit = df[df[overdue_col] != 0]
        if not crit.empty:
            st.error(f"⚠️ {len(crit)} Machines are OVERDUE!")
            st.download_button(f"📥 Export Pending List", to_excel(crit), f"{name}_Pending.xlsx", key=f"p_{key_suffix}")

    t1, t2, t3 = st.tabs(["Machine Tracker", "⏳ Service Pending", "📦 FOC List"])
    
    with t1:
        colA, colB = st.columns(2)
        cust_col, fab_col = find_col(df, ["customer"]), find_col(df, ["fabrication"])
        sel_c = colA.selectbox(f"Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox(f"Select Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            
            # --- 📊 CUSTOMER INFO & HMR FIELDS ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Info")
                st.write(f"**Cust:** {row[cust_col]}")
                st.write(f"**Avg Running/Day:** {row.get(find_col(df, ['avg', 'running']), 'N/A')}🏃")
                st.write(f"**Current HMR (BL):** `{row.get('CURRENT HMR', 'N/A')}`🎰")
                st.write(f"**Load HMR (BM):** `{row.get('CURRENT LOAD HMR', 'N/A')}`🎰")
                st.write(f"**Unload HMR (BN):** `{row.get('CURRENT UNLOAD HMR', 'N/A')}`🎰")
                st.write(f"**Difference HMR (BO):** `{row.get('DIFFRENT HMR', 'N/A')}`🎰")
                st.write(f"**Total Last HMR (DU):** `{row.get('MDA Total Hours', 'N/A')}`🎰")
                st.write(f"**Last Service Date:** {fmt(row.get(find_col(df, ['last', 'call', 'date'])))}📅")
                st.download_button("📄 Export Report", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"ex_{sel_f}")
            
            # --- 🔧 9 PARTS DIRECT LOOKUP ---
            if name == "INDUSTRIAL":
                pm = {"OIL":["oil","r","date"],"AF":["af","r","date"],"OF":["of","r","date"],"AOS":["aos","r","date"],"RGT":["rgt","r","date"],"VK":["valvekit","r","date"],"PF":["pf","due"],"FF":["ff","due"],"CF":["cf","due"]}
            else:
                pm = {"OIL":["oil"],"AFC":["afc"],"AFE":["afe"],"MOF":["mof"],"ROF":["rof"],"AOS":["aos"],"RGT":["rgt"],"1500":["1500"],"3000":["3000"]}

            with m2:
                st.info("🔧 History (R Date)")
                for lbl, ks in pm.items():
                    c = next((x for x in df.columns if all(k in x.lower() for k in ks)), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            with m3:
                st.info("⏳ Remaining (HMR)")
                for lbl, ks in pm.items():
                    rc = next((x for x in df.columns if ks[0] in x.lower() and "rem" in x.lower() and "hmr" in x.lower()), None)
                    val = row.get(rc, "N/A")
                    icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                    st.write(f"**{lbl}:** {icon} {val}")
            with m4:
                st.error("🚨 Next Due (Date)")
                for lbl, ks in pm.items():
                    dc = next((x for x in df.columns if lbl.lower() in x.lower() and "due" in x.lower() and "date" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(dc))}")

            st.divider()
            h1, h2 = st.tabs(["🏷️ FOC Details", "📱 Service History"])
            with h1:
                f_c = find_col(foc_df, ["fabrication"])
                if f_c: st.dataframe(foc_df[foc_df[f_c].astype(str) == sel_f], use_container_width=True)
            with h2:
                s_c = find_col(service_df, ["fabrication"])
                if s_c: st.dataframe(service_df[service_df[s_c].astype(str) == sel_f], use_container_width=True)

# ==============================
# 📢 AUTOMATION CENTER
# ==============================
if nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    msg = st.text_area("Broadcast Message:", "Daily Report: Overdue machines require attention.")
    wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer;">📱 Send WhatsApp Alert</button></a>', unsafe_allow_html=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
