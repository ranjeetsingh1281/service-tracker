import streamlit as st
import pandas as pd
import os
from datetime import datetime

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

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Dashboard:", ["Standard Tracker", "OD Machine Tracker", "FOC Tracker List"])

# Mapping for OD 9 Parts (Revised for Live Calc)
od_parts_map = {
    'Oil': {'rem': 'MDA OIL Remaining Hours', 'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'rem': 'AF Remaining Hours', 'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'rem': 'OF Remaining Hours', 'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'rem': 'AOS Remaining Hours', 'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'rem': 'RGT Remaining Hours', 'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'Valvekit': {'rem': 'Valve Kit Remaining Hours', 'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'rem': 'MDA PF R DATE', 'due': 'MDA PF R DATE', 'due_alt': 'PF DUE DATE'}, # Using date as base if rem missing
    'FF': {'rem': 'MDA FF R DATE', 'due': 'MDA FF R DATE', 'due_alt': 'FF DUE DATE'},
    'CF': {'rem': 'MDA CF R DATE', 'due': 'MDA CF R DATE', 'due_alt': 'CF DUE DATE'}
}

# --- 1. STANDARD TRACKER (Existing Logic) ---
if page == "Standard Tracker":
    st.title("🛠️ Standard Machine Tracker")
    if master_df.empty:
        st.warning("Master_Data file load nahi hui.")
    else:
        # (Standard Tracker Logic remains same as previous working version)
        cust_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("Customer", options=["All"] + cust_list)
        df_f = master_df if sel_cust == "All" else master_df[master_df['CUSTOMER NAME'] == sel_cust]
        sel_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()))
        
        if sel_fab != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
            st.header(f"Machine: {sel_fab}")
            # ... (C1-C4 display as per previous iron-clad version)

# --- 2. OD MACHINE TRACKER (FIXED LIVE CALC) ---
elif page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker (Live Hours)")
    if master_od_df.empty:
        st.error("Master_OD_Data file detect nahi hui.")
    else:
        cust_list_od = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust_od = st.sidebar.selectbox("Customer (OD)", options=["All"] + cust_list_od)
        df_od_f = master_od_df if sel_cust_od == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust_od]
        sel_fab_od = st.sidebar.selectbox("Fabrication No (OD)", options=["Select"] + sorted(df_od_f['Fabrication No'].astype(str).unique()))

        if sel_fab_od != "Select":
            row_od = df_od_f[df_od_f['Fabrication No'].astype(str) == sel_fab_od].iloc[0]
            
            # --- LIVE CALCULATION LOGIC FOR OD ---
            # 1. HMR Date se aaj tak kitne din huye
            hmr_date = pd.to_datetime(row_od.get('MDA HMR Date'), errors='coerce')
            today = pd.Timestamp(datetime.now().date())
            days_passed = (today - hmr_date).days if pd.notna(hmr_date) else 0
            
            # 2. Avg Running Hrs per day se multiply karke elapsed hrs nikalein
            avg_hrs = pd.to_numeric(row_od.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            if pd.isna(avg_hrs): avg_hrs = 0
            elapsed_od = days_passed * avg_hrs

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row_od.get('Customer Name')}")
                st.write(f"**Model:** {row_od.get('Model', 'N/A')}")
                st.write(f"**Category:** {row_od.get('Category', 'N/A')}")
            
            with c2:
                st.info("📅 Replacement")
                for label, cols in od_parts_map.items():
                    st.write(f"**{label}:** {format_dt(row_od.get(cols['date']))}")

            with c3:
                st.info("⚙️ Live Remaining")
                for label, cols in od_parts_map.items():
                    # Excel se base remaining value uthayein
                    base_rem = pd.to_numeric(row_od.get(cols['rem'], 0), errors='coerce')
                    if pd.isna(base_rem): base_rem = 0
                    
                    # Live subtraction
                    final_rem = int(base_rem - elapsed_od)
                    
                    if final_rem <= 0:
                        st.write(f"**{label}:** 🚨 {final_rem} (Due)")
                    else:
                        st.write(f"**{label}:** {final_rem} Hrs")
                
                st.divider()
                st.write(f"*(Based on {avg_hrs} hrs/day since {format_dt(hmr_date)})*")

            with c4:
                st.error("🚨 DUE DATES")
                for label, cols in od_parts_map.items():
                    due_col = cols.get('due')
                    st.write(f"**{label} Due:** {format_dt(row_od.get(due_col))}")

# --- 3. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    st.dataframe(foc_df, use_container_width=True, hide_index=True)
    
            # Service History for OD
            st.divider()
            st.subheader("🕒 Service History")
            hist_od = service_df[service_df['Fabrication Number'].astype(str) == sel_fab_od].sort_values(by='Call Logged Date', ascending=False)
            for _, s_row in hist_od.head(5).iterrows():
                with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                    st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                    st.info(s_row.get('Service Engineer Comments', 'N/A'))
