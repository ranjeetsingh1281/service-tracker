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

master_df, master_od_df, service_df, foc_df, errors = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
main_menu = st.sidebar.radio("Main Section:", ["DPSAC Tracker", "INDUATIAL Tracker"])

if main_menu == "DPSAC Tracker":
    page = st.sidebar.selectbox("Standard Dashboard:", ["Machine Tracker", "FOC List", "Service Pending"])
else:
    page = st.sidebar.selectbox("OD Dashboard:", ["Machine Tracker", "FOC List", "Service Pending"])

# --- 1. STANDARD DATA SECTION ---
if main_menu == "DPSAC Tracker":
    if page == "Machine Tracker":
        st.title("🛠️ DPSAC Units Tracker")
        cust_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("Customer", options=["All"] + cust_list, key="std_cust")
        df_f = master_df if sel_cust == "All" else master_df[master_df['CUSTOMER NAME'] == sel_cust]
        sel_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_fab")

        if sel_fab != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
            # ... [C1-C4 display logic same as before with Live HMR calculation]
            st.success(f"Viewing Standard Machine: {sel_fab}")
            # [Yahan C1-C4 ka Standard wala code rahega]

    elif page == "FOC List":
        st.title("📦 DPSAC FOC Tracker List")
        # Filters only for DPSAC Fabrication Numbers
        std_fabs = master_df['Fabrication No'].astype(str).unique()
        f_std = foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)]
        st.dataframe(f_std, use_container_width=True)

    elif page == "Service Pending":
        st.title("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        if b1.button("🔴 Overdue"): st.dataframe(master_df[master_df['BIS Over Due'] != 0])
        if b2.button("🟡 Current Month"): st.dataframe(master_df[master_df['BIS Current Month Due'] != 0])
        if b3.button("🟢 Next Month"): st.dataframe(master_df[master_df['BIS Next Month Due'] != 0])

# --- 2. OD DATA SECTION ---
elif main_menu == "INDUATIAL Tracker":
    if page == "Machine Tracker":
        st.title("🛡️ INDUATRIAL Tracker")
        cust_list_od = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust_od = st.sidebar.selectbox("Customer", options=["All"] + cust_list_od, key="od_cust")
        df_od_f = master_od_df if sel_cust_od == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust_od]
        sel_fab_od = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_od_f['Fabrication No'].astype(str).unique()), key="od_fab")

        if sel_fab_od != "Select":
            row_od = df_od_f[df_od_f['Fabrication No'].astype(str) == sel_fab_od].iloc[0]
            # ... [C1-C4 display logic with MDA Live Hours calculation]
            st.success(f"Viewing OD Machine: {sel_fab_od}")

    elif page == "FOC List":
        st.title("📦 INDUATRIAL FOC Tracker List")
        od_fabs = master_od_df['Fabrication No'].astype(str).unique()
        f_od = foc_df[foc_df['FABRICATION NO'].astype(str).isin(od_fabs)]
        st.dataframe(f_od, use_container_width=True)

    elif page == "Service Pending":
        st.title("⏳ INDUATRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        if o1.button("🔴 Red Count (Overdue)"): st.dataframe(master_od_df[master_od_df['Red Count'] != 0])
        if o2.button("🟡 Yellow Count (Current)"): st.dataframe(master_od_df[master_od_df['Yellow Count'] != 0])
        if o3.button("🟢 Green Count (Next Month)"): st.dataframe(master_od_df[master_od_df['Green Count'] != 0])
