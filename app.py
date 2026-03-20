import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DATA LOAD ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(base):
        for f in folder_files:
            if f.lower().startswith(base.lower()): return f
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
            if not df.empty: df.columns = [str(c).strip() for c in df.columns]
        return m_df, m_od_df, s_df, f_df
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

master_df, master_od_df, service_df, foc_df = load_data()

# --- MAPPINGS ---
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

ind_parts = {
    'Oil': {'rem': 'MDA OIL Remaining Hours', 'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'rem': 'AF Remaining Hours', 'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'rem': 'OF Remaining Hours', 'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'rem': 'AOS Remaining Hours', 'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'rem': 'RGT Remaining Hours', 'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'VK': {'rem': 'Valve Kit Remaining Hours', 'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'rem': 'PF DUE', 'date': 'MDA PF R DATE', 'due': 'PF DUE DATE'},
    'FF': {'rem': 'FF DUE', 'date': 'MDA FF R DATE', 'due': 'FF DUE DATE'},
    'CF': {'rem': 'CF DUE', 'date': 'MDA CF R DATE', 'due': 'CF DUE DATE'}
}

# --- SIDEBAR ---
st.sidebar.title("📌 Main Menu")
main_choice = st.sidebar.radio("Dashboard Chunein:", ["DPSAC Tracker (Standard)", "INDUSTRIAL Tracker (Industrial)"])

# --- 1. DPSAC SECTION ---
if main_choice == "DPSAC Tracker (Standard)":
    sub = st.sidebar.selectbox("Standard Options:", ["Machine Tracker", "FOC List", "Service Pending"])
    
    if sub == "Machine Tracker":
        st.title("🛠️ DPSAC Machine Tracker")
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_c = st.sidebar.selectbox("Customer Name", ["All"] + c_list, key="d_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = st.sidebar.selectbox("Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="d_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}")
                st.write(f"**Model:** {row.get('MODEL')}"); st.write(f"**Location:** {row.get('LOCATION')}")
                st.write(f"**Last Call HMR:** {row.get('Last Call HMR')}")
                st.write(f"**Last Call Date:** {format_dt(row.get('Last Call HMR Date'))}")
                st.write(f"**Avg. Run Hrs:** {row.get('Avg. Hrs')} 🕧")
                st.write(f"**Running Hrs:** {row.get('HMR Cal.')} 🏃‍➡️")
                
            with c2:
                st.info("📅 Replacement")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['date']))}")
            with c3:
                st.info("🕧 Live Remaining")
                for p, m in std_parts.items():
                    rem = int(pd.to_numeric(row.get(m['rem'], 0), errors='coerce') - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 DUE DATES")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['due']))}")

            # --- DPSAC History & FOC ---
            st.divider()
            st.subheader("🎁 FOC Parts History")
            f_match = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
            st.dataframe(f_match[['Created On', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not f_match.empty else pd.DataFrame(), hide_index=True)
            
            st.subheader("🕒 Service History")
            h_match = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            for _, s_row in h_match.iterrows():
                with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | ⏱️ {s_row.get('Call HMR')} | 📝 {s_row.get('Call Type', 'N/A')}"):
                    st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                    st.info(s_row.get('Service Engineer Comments', 'N/A'))

# --- 2. INDUSTRIAL SECTION ---
elif main_choice == "INDUSTRIAL Tracker (Industrial)":
    sub = st.sidebar.selectbox("Industrial Options:", ["Machine Tracker", "FOC List", "Service Pending"])
    
    if sub == "Machine Tracker":
        st.title("🛡️ INDUSTRIAL Machine Tracker")
        c_list_i = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_c_i = st.sidebar.selectbox("Customer Name", ["All"] + c_list_i, key="i_c")
        df_f_i = master_od_df if sel_c_i == "All" else master_od_df[master_od_df['Customer Name'] == sel_c_i]
        sel_f_i = st.sidebar.selectbox("Fabrication No", ["Select"] + sorted(df_f_i['Fabrication No'].astype(str).unique()), key="i_f")
        
        if sel_f_i != "Select":
            row = df_f_i[df_f_i['Fabrication No'].astype(str) == sel_f_i].iloc[0]
            h_dt = pd.to_datetime(row.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            elapsed = days * pd.to_numeric(row.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('Customer Name')}")
                st.write(f"**Model:** {row.get('Model')}"); st.write(f"**Category:** {row.get('Category')}")
            with c2:
                st.info("📅 Replacement")
                for p, m in ind_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, m in ind_parts.items():
                    rem = int(pd.to_numeric(row.get(m['rem'], 0), errors='coerce') - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 DUE DATES")
                for p, m in ind_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['due']))}")

            # --- INDUSTRIAL History & FOC ---
            st.divider()
            st.subheader("🎁 FOC Parts History")
            f_match_i = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f_i]
            st.dataframe(f_match_i[['Created On', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not f_match_i.empty else pd.DataFrame(), hide_index=True)
            
            st.subheader("🕒 Service History")
            h_match_i = service_df[service_df['Fabrication Number'].astype(str) == sel_f_i].sort_values(by='Call Logged Date', ascending=False)
            for _, s_row in h_match_i.iterrows():
                with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                    st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                    st.info(s_row.get('Service Engineer Comments', 'N/A'))

# --- FOC & PENDING (Logic Remains same as before for both) ---
