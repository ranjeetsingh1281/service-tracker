import streamlit as st
import pandas as pd
import os
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
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
            st.session_state["login"], st.session_state["user"], st.session_state["role"] = True, u, USER_DB[u]["role"]
            st.rerun()
        else: st.error("Invalid Credentials")

if "login" not in st.session_state or not st.session_state["login"]:
    login(); st.stop()

# ==============================
# ⚙️ HELPERS
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
def load_data():
    f_list = os.listdir('.')
    def f(name): return next((x for x in f_list if name.lower() in x.lower() and x.endswith('.xlsx')), None)
    m_df = pd.read_excel(f("Master_Data"), engine='openpyxl') if f("Master_Data") else pd.DataFrame()
    m_od_df = pd.read_excel(f("Master_OD_Data"), engine='openpyxl') if f("Master_OD_Data") else pd.DataFrame()
    foc_df = pd.read_excel(f("Active_FOC"), engine='openpyxl') if f("Active_FOC") else pd.DataFrame()
    srv_df = pd.read_excel(f("Service_Details"), engine='openpyxl') if f("Service_Details") else pd.DataFrame()
    for d in [m_df, m_od_df, foc_df, srv_df]:
        if not d.empty: d.columns = [str(c).strip() for c in d.columns]
    return m_df, m_od_df, foc_df, srv_df

master_df, master_od_df, foc_df, service_df = load_data()

# ==============================
# 🏢 NAVIGATION
# ==============================
role = st.session_state["role"]
st.sidebar.title(f"👋 {st.session_state['user'].upper()}")
nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"]) if role == "all" else (nav := "DPSAC Tracker" if role == "dpsac" else "INDUSTRIAL Tracker")

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")

    # 📊 GRAPHS SECTION
    with st.expander("📊 Click to View Dashboard Analytics & Graphs", expanded=False):
        c1, c2 = st.columns(2)
        sc = find_col(df, ["unit", "status"])
        if sc: 
            c1.subheader("Unit Status Distribution")
            c1.bar_chart(df[sc].value_counts())
        cc = find_col(df, ["category"])
        if cc: 
            c2.subheader("Category Breakdown")
            c2.bar_chart(df[cc].value_counts())
            
    # Identify Overdue first
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    crit = df[df[overdue_col] != 0] if overdue_col else pd.DataFrame()
    
    t1, t2, t3 = st.tabs(["Machine Tracker", "📦 FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        cust_col, fab_col = find_col(df, ["customer"]), find_col(df, ["fabrication"])
        sel_c = colA.selectbox(f"Select Customer ({name})", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_filtered = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox(f"Select Fabrication ({name})", ["Select"] + sorted(df_filtered[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_filtered[df_filtered[fab_col].astype(str) == sel_f].iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Info")
                st.info("📋 Info")
                st.write(f"**Cust:** {row[cust_col]}")
                st.write(f"**Avg Running/Day:** {row.get(find_col(df, ['avg', 'running']), 'N/A')}")
                st.write(f"**Current HMR (BL):** `{row.get('CURRENT HMR', 'N/A')}`")
                st.write(f"**Load HMR (BM):** `{row.get('CURRENT LOAD HMR', 'N/A')}`")
                st.write(f"**Unload HMR (BN):** `{row.get('CURRENT UNLOAD HMR', 'N/A')}`")
                st.write(f"**Difference HMR (BO):** `{row.get('DIFFRENT HMR', 'N/A')}`")
                st.write(f"**Total Last HMR (DU):** `{row.get('MDA Total Hours', 'N/A')}`")
                st.write(f"**Last Service Date:** {fmt(row.get(find_col(df, ['last', 'call', 'date'])))}")
                st.download_button("📄 Export Report", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"ex_{sel_f}")
            
            # Mapping Parts
            if name == "INDUSTRIAL":
                pm = {"OIL":["oil","r","date"],"AF":["af","r","date"],"OF":["of","r","date"],"AOS":["aos","r","date"],"RGT":["rgt","r","date"],"VK":["valvekit","r","date"],"PF":["pf","due"],"FF":["ff","due"],"CF":["cf","due"]}

            else:
                pm = {"OIL":["oil","repl"],"AFC":["afc","repl"],"AFE":["afe","repl"],"MOF":["mof","repl"],"ROF":["rof","repl"],"AOS":["aos","repl"],"RGT":["rgt","repl"],"1500":["1500","repl"],"3000":["3000","repl"]}
            with m2:
                st.info("🔧 History (R Date)")
                for lbl, ks in pm.items():
                    c = next((x for x in df.columns if all(k in x.lower() for k in ks)), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            with m3:
                st.info("⏳ Remaining (HMR)")
                for lbl, ks in pm.items():
                    rc = next((x for x in df.columns if lbl.lower() in x.lower() and "rem" in x.lower()), None)
                    val = row.get(rc, "N/A")
                    icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                    st.write(f"**{lbl}:** {icon} {val}")
            with m4:
                st.error("🚨 Next Due (Date)")
                for lbl, ks in pm.items():
                    dc = next((x for x in df.columns if lbl.lower() in x.lower() and "due" in x.lower() and "date" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(dc))}")

    with t2: # --- FOC LIST FIXED ---
        st.subheader(f"📦 {name} FOC Master List")
        f_fab_col = find_col(foc_df, ["fabrication"])
        fab_nos = df[fab_col].astype(str).unique()
        f_display = foc_df[foc_df[f_fab_col].astype(str).isin(fab_nos)] if f_fab_col else pd.DataFrame()
        
        if not f_display.empty:
            st.download_button(f"📥 Export {name} FOC", to_excel(f_display), f"{name}_FOC.xlsx", key=f"fex_{key_suffix}")
            st.dataframe(f_display, use_container_width=True)
        else: st.warning("No FOC entries found for this category.")

    with t3: # --- SERVICE PENDING FIXED ---
        st.subheader(f"⏳ {name} Service Overdue List")
        if not crit.empty:
            st.download_button(f"📥 Export {name} Pending", to_excel(crit), f"{name}_Pending.xlsx", key=f"pex_{key_suffix}")
            st.dataframe(crit, use_container_width=True)
        else: st.success("All machines are healthy! No pending service.")

# ==============================
# 📢 AUTOMATION CENTER
# ==============================
if nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📱 WhatsApp Broadcast")
        w_msg = st.text_area("Message:", "Critical Alert: Check overdue machines.")
        w_link = f"https://wa.me/917061158953?text={urllib.parse.quote(w_msg)}"
        st.markdown(f'<a href="{w_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:10px; border-radius:5px; border:none; width:100%;">Send WhatsApp</button></a>', unsafe_allow_html=True)
    with c2:
        st.subheader("📧 Email Broadcast")
        st.write("Target: crm@primepower.in")
        e_sub = st.text_input("Subject:", "ELGi Service Alert")
        if st.button("📧 Send Email"): st.info("Email feature requires SMTP App Password in code.")

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
