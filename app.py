import streamlit as st
import pandas as pd
import os
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
        
        # Clean Headers
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
page = st.sidebar.radio("Select Dashboard:", ["Standard Tracker", "OD Machine Tracker", "FOC Tracker List"])

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
od_parts = {
    'Oil': {'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'Valvekit': {'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'date': 'MDA PF R DATE', 'due': 'PF DUE DATE'},
    'FF': {'date': 'MDA FF R DATE', 'due': 'FF DUE DATE'},
    'CF': {'date': 'MDA CF R DATE', 'due': 'CF DUE DATE'}
}

# --- 1. STANDARD TRACKER (RESTORED) ---
if page == "Standard Tracker":
    st.title("🛠️ Standard Machine Tracker")
    if master_df.empty:
        st.warning("Master_Data.xlsx load nahi hui.")
    else:
        cust_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("Customer", options=["All"] + cust_list)
        df_f = master_df if sel_cust == "All" else master_df[master_df['CUSTOMER NAME'] == sel_cust]
        
        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        t_u = len(df_f)
        n_w = len(df_f[df_f['Warranty Type'].astype(str).str.contains('Non', na=False, case=False)])
        m1.metric("Total Units", t_u); m2.metric("In Warranty", t_u - n_w); m3.metric("Non-Warranty", n_w)
        
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
                st.write(f"**HMR Cal:** {curr_hmr}")
            with c2:
                st.info("📅 Replacement")
                for p, cols in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(cols['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, cols in std_parts.items():
                    val = pd.to_numeric(row.get(cols['rem'], 0), errors='coerce')
                    rem = int(val - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 DUE DATES")
                for p, cols in std_parts.items(): st.write(f"**{p} Due:** {format_dt(row.get(cols['due']))}")

# --- 2. OD MACHINE TRACKER ---
elif page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker (Master_OD_Data)")
    if master_od_df.empty:
        st.error("Master_OD_Data nahi mili.")
    else:
        cust_list_od = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust_od = st.sidebar.selectbox("Customer (OD)", options=["All"] + cust_list_od)
        df_od_f = master_od_df if sel_cust_od == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust_od]
        
        sel_fab_od = st.sidebar.selectbox("Fabrication No (OD)", options=["Select"] + sorted(df_od_f['Fabrication No'].astype(str).unique()))

        if sel_fab_od != "Select":
            row_od = df_od_f[df_od_f['Fabrication No'].astype(str) == sel_fab_od].iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row_od.get('Customer Name')}")
                st.write(f"**Model:** {row_od.get('Model', 'N/A')}")
                st.write(f"**Sub Group:** {row_od.get('Product Sub Group', 'N/A')}")
                st.write(f"**Category:** {row_od.get('Category', 'N/A')}")
            with c2:
                st.info("📅 Replacement (9 Parts)")
                for label, cols in od_parts.items(): st.write(f"**{label}:** {format_dt(row_od.get(cols['date']))}")
            with c3:
                st.info("⚙️ Live Tracking")
                st.write(f"**Avg Hrs/Day:** {row_od.get('MDA AVG Running Hours Per Day', 'N/A')}")
                st.write(f"**HMR Date:** {format_dt(row_od.get('MDA HMR Date'))}")
            with c4:
                st.error("🚨 DUE DATES (9 Parts)")
                for label, cols in od_parts.items(): st.write(f"**{label} Due:** {format_dt(row_od.get(cols['due']))}")

# --- 3. FOC TRACKER LIST (COMMON) ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    query = st.text_input("🔍 Search FOC Number or Customer", "")
    if not foc_df.empty:
        f_disp = foc_df[foc_df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)] if query else foc_df
        st.dataframe(f_disp, use_container_width=True, hide_index=True)
