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
page = st.sidebar.radio("Select Dashboard:", ["Standard Tracker", "OD Machine Tracker", "FOC Tracker List", "Service Pending List"])

# Mapping for Standard Dashboard (9 Parts)
std_parts = {
    'Oil': {'rem': 'HMR - Oil remaining', 'date': 'Oil Replacement Date', 'due': 'OIL DUE DATE'},
    'AFC': {'rem': 'Air filter replaced - Compressor Remaining Hours', 'date': 'Air filter Compressor Replaced Date', 'due': 'AFC DUE DATE'},
    'AFE': {'rem': 'Air filter replaced - Engine Remaining Hours', 'date': 'Air filter Engine Replaced Date', 'due': 'AFE DUE DATE'},
    'MOF': {'rem': 'Main Oil filter Remaining Hours', 'date': 'Main Oil filter Replaced Date', 'due': 'MOF DUE DATE'},
    'ROF': {'rem': 'Return Oil filter Remaining Hours', 'date': 'Return Oil filter Replaced Date', 'due': 'ROF DUE DATE'},
    'AOS': {'rem': 'HMR - Separator remaining', 'date': 'AOS Replaced Date', 'due': 'AOS DUE DATE'},
    'Greasing': {'rem': 'HMR - Motor regressed remaining', 'date': 'Greasing Done Date', 'due': 'RGT DUE DATE'},
    '1500 Kit': {'rem': '1500 Valve kit Remaining Hours', 'date': '1500 Valve kit Replaced Date', 'due': '1500 KIT DUE DATE'},
    '3000 Kit': {'rem': '3000 Valve kit Remaining Hours', 'date': '3000 Valve kit Replaced Date', 'due': '3000 KIT DUE DATE'}
}

# Mapping for OD Dashboard (9 Parts)
od_parts_map = {
    'Oil': {'rem': 'MDA OIL Remaining Hours', 'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'rem': 'AF Remaining Hours', 'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'rem': 'OF Remaining Hours', 'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'rem': 'AOS Remaining Hours', 'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'rem': 'RGT Remaining Hours', 'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'Valvekit': {'rem': 'Valve Kit Remaining Hours', 'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'rem': 'MDA PF R DATE', 'date': 'MDA PF R DATE', 'due': 'PF DUE DATE'},
    'FF': {'rem': 'MDA FF R DATE', 'date': 'MDA FF R DATE', 'due': 'FF DUE DATE'},
    'CF': {'rem': 'MDA CF R DATE', 'due': 'MDA CF R DATE', 'due_alt': 'CF DUE DATE'}
}

# --- 1. STANDARD TRACKER ---
if page == "Standard Tracker":
    st.title("🛠️ Standard Machine Tracker")
    if master_df.empty: st.warning("Master_Data load nahi hui.")
    else:
        cust_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("Customer", options=["All"] + cust_list)
        df_f = master_df if sel_cust == "All" else master_df[master_df['CUSTOMER NAME'] == sel_cust]
        sel_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()))
        
        if sel_fab != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
            curr_hmr = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_hmr = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}")
                st.write(f"**Model:** {row.get('MODEL', 'N/A')}")
            with c2:
                st.info("📅 Replacement")
                for p, cols in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(cols['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, cols in std_parts.items():
                    val = pd.to_numeric(row.get(cols['rem'], 0), errors='coerce')
                    rem = int(val - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem} (Due)")
            with c4:
                st.error("🚨 DUE DATES")
                for p, cols in std_parts.items(): st.write(f"**{p} Due:** {format_dt(row.get(cols['due']))}")

# --- 2. OD MACHINE TRACKER (LIVE FIXED) ---
elif page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker (Live Calculation)")
    if master_od_df.empty: st.error("Master_OD_Data detect nahi hui.")
    else:
        cust_list_od = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust_od = st.sidebar.selectbox("Customer (OD)", options=["All"] + cust_list_od)
        df_od_f = master_od_df if sel_cust_od == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust_od]
        sel_fab_od = st.sidebar.selectbox("Fabrication No (OD)", options=["Select"] + sorted(df_od_f['Fabrication No'].astype(str).unique()))

        if sel_fab_od != "Select":
            row_od = df_od_f[df_od_f['Fabrication No'].astype(str) == sel_fab_od].iloc[0]
            hmr_date = pd.to_datetime(row_od.get('MDA HMR Date'), errors='coerce')
            days_passed = (pd.Timestamp(datetime.now().date()) - hmr_date).days if pd.notna(hmr_date) else 0
            avg_hrs = pd.to_numeric(row_od.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_od = days_passed * (avg_hrs if pd.notna(avg_hrs) else 0)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info"); st.write(f"**Customer:** {row_od.get('Customer Name')}"); st.write(f"**Model:** {row_od.get('Model', 'N/A')}")
            with c2:
                st.info("📅 Replacement"); [st.write(f"**{p}:** {format_dt(row_od.get(cls['date']))}") for p, cls in od_parts_map.items()]
            with c3:
                st.info("⚙️ Live Remaining")
                for p, cls in od_parts_map.items():
                    val = pd.to_numeric(row_od.get(cls['rem'], 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_od)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 DUE DATES"); [st.write(f"**{p} Due:** {format_dt(row_od.get(cls['due']))}") for p, cls in od_parts_map.items()]

# --- 3. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    query = st.text_input("🔍 Search Customer or Part", "")
    f_disp = foc_df[foc_df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)] if query else foc_df
    st.dataframe(f_disp, use_container_width=True, hide_index=True)

# --- 4. SERVICE PENDING LIST (FIXED & RESTORED) ---
elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    b1, b2, b3 = st.columns(3)
    p_df = pd.DataFrame()
    
    # Combined Pending Logic (Standard + OD)
    if b1.button("🔴 Overdue"):
        p_std = master_df[master_df.get('BIS Over Due', 0) != 0].copy() if not master_df.empty else pd.DataFrame()
        p_od = master_od_df[master_od_df.get('Over Due', 0) != 0].copy() if not master_od_df.empty else pd.DataFrame()
        p_df = pd.concat([p_std, p_od.rename(columns={'Customer Name':'CUSTOMER NAME'})], ignore_index=True, sort=False)

    if not p_df.empty:
        st.success(f"Records Found: {len(p_df)}")
        st.download_button("📊 Export Pending List", to_excel(p_df), "Pending_List.xlsx")
        st.dataframe(p_df[['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']], use_container_width=True)
