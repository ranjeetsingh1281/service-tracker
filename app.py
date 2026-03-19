import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- SMART FILE LOADER ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(target_base):
        for f in folder_files:
            if f.lower().startswith(target_base.lower()): return f
        return None

    m_name = find_file("Master_Data")
    m_od_name = find_file("Master_OD_Data")
    s_name = find_file("Service_Details")
    f_name = find_file("Active_FOC")
    
    try:
        m_df = pd.read_excel(m_name, engine='openpyxl') if m_name else pd.DataFrame()
        m_od_df = pd.read_excel(m_od_name, engine='openpyxl') if m_od_name else pd.DataFrame()
        s_df = pd.read_excel(s_name, engine='openpyxl') if s_name else pd.DataFrame()
        f_df = pd.read_excel(f_name, engine='openpyxl') if f_name else pd.DataFrame()
        
        for df in [m_df, m_od_df, s_df, f_df]:
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
        return m_df, m_od_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, master_od_df, service_df, foc_df, errors = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Dashboard Select Karein:", 
                        ["Standard Machine Tracker", "OD Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- SHARED PARTS MAPPING ---
std_parts = {
    'Oil': {'rem': 'HMR - Oil remaining', 'date': 'Oil Replacement Date', 'due': 'OIL DUE DATE'},
    'AFC': {'rem': 'Air filter replaced - Compressor Remaining Hours', 'date': 'Air filter Compressor Replaced Date', 'due': 'AFC DUE DATE'},
    'AOS': {'rem': 'HMR - Separator remaining', 'date': 'AOS Replaced Date', 'due': 'AOS DUE DATE'}
}
od_parts_map = {
    'Oil': {'rem': 'MDA OIL Remaining Hours', 'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'rem': 'AF Remaining Hours', 'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'AOS': {'rem': 'AOS Remaining Hours', 'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'}
}

# --- 1. & 2. TRACKER LOGIC (SAME AS BEFORE) ---
if page == "Standard Machine Tracker":
    st.title("🛠️ Standard Machine Tracker")
    # (Existing Standard Tracker Code...)

elif page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker (Live Hours)")
    # (Existing OD Tracker Code with Live Calc...)

# --- 3. FOC TRACKER ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker")
    query = st.text_input("🔍 Search Customer, Part No or FOC No", "")
    f_disp = foc_df[foc_df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)] if query else foc_df
    st.dataframe(f_disp, use_container_width=True, hide_index=True)

# --- 4. SERVICE PENDING LIST (IRON-CLAD UPDATE) ---
elif page == "Service Pending List":
    st.title("⏳ Combined Service Pending Dashboard")
    st.write("Dono Master Files (Standard + OD) se pending units yahan dikhenge.")
    
    b1, b2, b3 = st.columns(3)
    pending_list = pd.DataFrame()
    
    # Logic for Overdue (Red)
    if b1.button("🔴 Overdue Units (Red)", use_container_width=True):
        p_std = master_df[master_df.get('BIS Over Due', 0) != 0].copy() if not master_df.empty else pd.DataFrame()
        p_od = master_od_df[master_od_df.get('Red Count', 0) != 0].copy() if not master_od_df.empty else pd.DataFrame()
        if not p_od.empty: p_od = p_od.rename(columns={'Customer Name': 'CUSTOMER NAME'})
        pending_list = pd.concat([p_std, p_od], ignore_index=True, sort=False)

    # Logic for Current Month (Yellow)
    if b2.button("🟡 Current Month Due (Yellow)", use_container_width=True):
        p_std = master_df[master_df.get('BIS Current Month Due', 0) != 0].copy() if not master_df.empty else pd.DataFrame()
        p_od = master_od_df[master_od_df.get('Yellow Count', 0) != 0].copy() if not master_od_df.empty else pd.DataFrame()
        if not p_od.empty: p_od = p_od.rename(columns={'Customer Name': 'CUSTOMER NAME'})
        pending_list = pd.concat([p_std, p_od], ignore_index=True, sort=False)

    # Logic for Next Month (Green)
    if b3.button("🟢 Next Month Due (Green)", use_container_width=True):
        p_std = master_df[master_df.get('BIS Next Month Due', 0) != 0].copy() if not master_df.empty else pd.DataFrame()
        p_od = master_od_df[master_od_df.get('Green Count', 0) != 0].copy() if not master_od_df.empty else pd.DataFrame()
        if not p_od.empty: p_od = p_od.rename(columns={'Customer Name': 'CUSTOMER NAME'})
        pending_list = pd.concat([p_std, p_od], ignore_index=True, sort=False)

    if not pending_list.empty:
        st.success(f"Total Pending Records: {len(pending_list)}")
        # Columns select karein jo dono mein common hain
        disp_cols = ['CUSTOMER NAME', 'Fabrication No', 'Model', 'Category', 'OIL DUE DATE', 'AOS DUE DATE']
        # Sirf wahi dikhao jo available hain
        actual_cols = [c for c in disp_cols if c in pending_list.columns]
        
        st.download_button("📊 Export Combined Pending List", to_excel(pending_list), "Combined_Pending.xlsx")
        st.dataframe(pending_list[actual_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Kripya ek button click karein pending units dekhne ke liye.")
