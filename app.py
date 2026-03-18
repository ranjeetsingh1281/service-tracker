import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DYNAMIC FILE LOADER ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(target):
        for f in folder_files:
            if f.lower() == target.lower(): return f
        return None

    m_name = find_file("Master_Data.xlsx")
    s_name = find_file("Service_Details.xlsx")
    f_name = find_file("Active_FOC.xlsx")
    
    if not m_name or not s_name or not f_name:
        return None, None, None, [f for f in ["Master_Data.xlsx", "Service_Details.xlsx", "Active_FOC.xlsx"] if not find_file(f)]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Error or Missing Files: {missing}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Detailed Machine Tracker")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer", options=["All"] + customer_list)
    
    filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    selected_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(filtered_df['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = filtered_df[filtered_df['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # Calculations
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if pd.notna(curr_hmr) and pd.notna(last_hmr) else 0

        # --- DISPLAY C1 to C4 ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**Avg Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')}")
            st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')}")
            st.write(f"**Last Call HMR:** {m_info.get('Last Call HMR', 'N/A')}")
        with c2:
            st.info("📅 Replacement")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Live Remaining")
            # Logic for remaining hours
            for col, label in [('HMR - Oil remaining', 'Oil'), ('Air filter replaced - Compressor Remaining Hours', 'AFC'), ('HMR - Separator remaining', 'AOS')]:
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce') - elapsed
                st.write(f"**{label}:** {int(val)} Hrs" if val > 0 else f"**{label}:** 🚨 {int(val)} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # --- FOC FOR SPECIFIC MACHINE ---
        st.divider()
        st.subheader("🎁 FOC Parts for this Machine")
        f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
        foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
        if not foc_match.empty:
            st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
        else: st.info("No FOC record.")

        # --- SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                header = f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR | 🛠️ {row.get('Call Type', 'N/A')}"
                with st.expander(header):
                    st.info(row.get('Service Engineer Comments', 'N/A'))

# --- 2. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    st.write("Yahan aap poori FOC history dekh sakte hain.")
    st.download_button("📥 Download Full FOC List", to_excel(foc_df), "Full_FOC_List.xlsx")
    st.dataframe(foc_df, use_container_width=True)

# --- 3. SERVICE PENDING DASHBOARD ---
elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    b1, b2, b3 = st.columns(3)
    pending_list = pd.DataFrame()

    if b1.button("🔴 BIS Over Due", use_container_width=True):
        pending_list = master_df[master_df['BIS Over Due'] != 0].copy()
    if b2.button("🟡 BIS Current Month", use_container_width=True):
        pending_list = master_df[master_df['BIS Current Month Due'] != 0].copy()
    if b3.button("🟢 BIS Next Month", use_container_width=True):
        pending_list = master_df[master_df['BIS Next Month Due'] != 0].copy()

    if not pending_list.empty:
        st.success(f"Records Found: {len(pending_list)}")
        st.download_button("📥 Download Excel", to_excel(pending_list), "Pending_List.xlsx")
        st.dataframe(pending_list[['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE', 'HMR Cal.']], use_container_width=True)
    else:
        st.info("Kripya ek option select karein.")
