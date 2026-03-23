import streamlit as st
import pandas as pd
import os
import smtplib
import pywhatkit as kit
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        else:
            st.error("Invalid Credentials")

if "login" not in st.session_state or not st.session_state["login"]:
    login()
    st.stop()

# ==============================
# 📧 AUTOMATION (Email & WhatsApp)
# ==============================
def send_email_alert(subject, body):
    sender = "crm@primepower.in" 
    receiver = "crm@primepower.in"
    password = "YOUR_GMAIL_APP_PASSWORD" # Boss, yahan App Password daalein
    
    msg = MIMEMultipart()
    msg['From'], msg['To'], msg['Subject'] = sender, receiver, subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

def send_whatsapp_alert(message):
    try:
        # Isse WhatsApp Web ke zariye message chala jayega
        kit.sendwhatmsg_instantly("+917061158953", message, wait_time=15, tab_close=True)
        return True
    except: return False

# ==============================
# 🧠 HELPERS
# ==============================
def fmt(dt):
    if pd.isna(dt) or dt == 0: return "N/A"
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
    files = os.listdir('.')
    def f(name): return next((x for x in files if name.lower() in x.lower() and x.endswith('.xlsx')), None)
    m_df = pd.read_excel(f("Master_Data")) if f("Master_Data") else pd.DataFrame()
    m_od_df = pd.read_excel(f("Master_OD_Data")) if f("Master_OD_Data") else pd.DataFrame()
    foc_df = pd.read_excel(f("Active_FOC")) if f("Active_FOC") else pd.DataFrame()
    srv_df = pd.read_excel(f("Service_Details")) if f("Service_Details") else pd.DataFrame()
    for d in [m_df, m_od_df, foc_df, srv_df]:
        if not d.empty: d.columns = d.columns.str.strip()
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

if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()

# ==============================
# 💎 TRACKER CORE ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    status_col = find_col(df, ["unit", "status"])
    cust_col = find_col(df, ["customer"])
    fab_col = find_col(df, ["fabrication"])

    # 🚨 OVERDUE ALERTS SECTION
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    if overdue_col:
        critical = df[df[overdue_col] != 0]
        if not critical.empty:
            st.error(f"⚠️ {len(critical)} Machines are OVERDUE!")
            c1, c2 = st.columns(2)
            if c1.button(f"📧 Send Email Alert ({key_suffix})"):
                msg = f"ELGi Alert: {len(critical)} machines are overdue in {name} Tracker."
                if send_email_alert(f"CRITICAL: {name} Alert", msg): st.success("Email Sent!")
            if c2.button(f"📱 Send WhatsApp Alert ({key_suffix})"):
                send_whatsapp_alert(f"ELGi Global: {len(critical)} machines are RED in {name}.")

    # 🔍 MACHINE SEARCH & LIVE HMR
    st.divider()
    col1, col2 = st.columns(2)
    sel_c = col1.selectbox("Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"c_{key_suffix}")
    df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
    sel_f = col2.selectbox("Select Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"f_{key_suffix}")

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
        try:
            last_h = float(row.get(find_col(df, ["hmr", "cal"]), 0))
            avg = float(row.get(find_col(df, ["avg", "running"]), 0))
            l_date = pd.to_datetime(row.get(find_col(df, ["hmr", "date"])))
            live_hmr = int(last_h + (max(0, (pd.Timestamp.today() - l_date).days) * avg))
        except: live_hmr = int(row.get(find_col(df, ["hmr", "cal"]), 0))

        st.success(f"Live Report for: {sel_f}")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.info("📋 Info")
            st.write(f"**Cust:** {row[cust_col]}\n**Live HMR:** `{live_hmr}`")
            st.download_button("📄 Export", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx")
        with m2:
            st.info("🔧 History")
            for p in ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]:
                col = next((c for c in df.columns if p in c.lower() and "date" in c.lower() and "due" not in c.lower()), None)
                if col: st.write(f"**{p.upper()}:** {fmt(row.get(col))}")
        with m3:
            st.info("⏳ Remaining")
            for p in ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]:
                rem_c = next((c for c in df.columns if p in c.lower() and "remaining" in c.lower()), None)
                if rem_c and pd.notna(row[rem_c]):
                    act_rem = int(float(row[rem_c]) - (live_hmr - last_h))
                    icon = "🟢" if act_rem > 100 else "🟡" if act_rem > 0 else "🔴"
                    st.write(f"**{p.upper()}:** {icon} {act_rem}")
        with m4:
            st.error("🚨 Next Due")
            for p in ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]:
                due_c = next((c for c in df.columns if p in c.lower() and "due" in c.lower() and "date" in c.lower()), None)
                if due_c: st.write(f"**{p.upper()}:** {fmt(row.get(due_c))}")

# ==============================
# 📢 EXECUTION
# ==============================
if nav == "DPSAC Tracker":
    run_tracker(master_df, "DPSAC", "DPSAC")
elif nav == "INDUSTRIAL Tracker":
    run_tracker(master_od_df, "INDUSTRIAL", "IND")
elif nav == "📢 Automation Center":
    st.header("📢 Manual Broadcast")
    msg = st.text_area("Message:", "Daily Update: All machines are healthy.")
    if st.button("Send WhatsApp to +917061158953"):
        send_whatsapp_alert(msg)
