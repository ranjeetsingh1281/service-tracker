import streamlit as st
import pd as pd
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="ELGi Global Tracker Pro", layout="wide")

# --- SMART DATA LOADER ---
@st.cache_data
def load_data():
    f_list = os.listdir('.')
    def find_f(base):
        for f in f_list:
            if f.lower().startswith(base.lower()): return f
        return None

    m_n = find_f("Master_Data")
    m_od_n = find_f("Master_OD_Data")
    s_n = find_f("Service_Details")
    f_n = find_f("Active_FOC")
    
    try:
        m_df = pd.read_excel(m_n, engine='openpyxl') if m_n else pd.DataFrame()
        m_od_df = pd.read_excel(m_od_n, engine='openpyxl') if m_od_n else pd.DataFrame()
        s_df = pd.read_excel(s_n, engine='openpyxl') if s_n else pd.DataFrame()
        f_df = pd.read_excel(f_n, engine='openpyxl') if f_n else pd.DataFrame()
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
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Dashboard:", ["1. DPSAC Tracker", "2. INDUSTRIAL Tracker"])

# ==========================================
# PAGE 1: DPSAC TRACKER (Standard)
# ==========================================
if page_choice == "1. DPSAC Tracker":
    st.title("🛠️ DPSAC Tracker")
    tabs = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    
    with tabs[0]: # Machine Tracker
        col1, col2 = st.columns(2)
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str)) if not master_df.empty else []
        sel_c = col1.selectbox("Customer Name", ["All"] + c_list, key="d_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = col2.selectbox("Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="d_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0

            # C1-C4 SPACIOUS LOOK
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}")
                st.write(f"**Model:** {row.get('MODEL', 'N/A')}")
                st.write(f"**Location:** {row.get('LOCATION', 'None')}")
                st.write(f"**Last Call HMR:** {last_h}")
                st.write(f"**Last Call Date:** {format_dt(row.get('Last Call HMR Date'))}")
                st.write(f"**Running Hrs:** {curr_h} 🏃‍➡️")
            with c2:
                st.info("📅 Replacement Date")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, m in std_parts.items():
                    rem = int(pd.to_numeric(row.get(m['rem'], 0), errors='coerce') - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 Due Date")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['due']))}")

            # History & FOC
            st.divider()
            f_m = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
            if not f_m.empty:
                st.subheader("🎁 FOC Details")
                st.dataframe(f_m[['Created On', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True)
            
            st.subheader("🕒 Service History")
            h_m = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            for _, s_row in h_m.iterrows():
                with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | ⚙️ {s_row.get('Call HMR')} HMR"):
                    st.write(f"**Engineer:** {s_row.get('Service Engineer')}")
                    st.info(s_row.get('Service Engineer Comments'))

# ==========================================
# PAGE 2: INDUSTRIAL TRACKER (OD)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker")
    tabs_i = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tabs_i[0]: # Machine Tracker
        col1_i, col2_i = st.columns(2)
        c_l_i = sorted(master_od_df['Customer Name'].unique().astype(str)) if not master_od_df.empty else []
        sel_c_i = col1_i.selectbox("Customer Name", ["All"] + c_l_i, key="i_c")
        df_f_i = master_od_df if sel_c_i == "All" else master_od_df[master_od_df['Customer Name'] == sel_c_i]
        sel_f_i = col2_i.selectbox("Fabrication No", ["Select"] + sorted(df_f_i['Fabrication No'].astype(str).unique()), key="i_f")

        if sel_f_i != "Select":
            row_i = df_f_i[df_f_i['Fabrication No'].astype(str) == sel_f_i].iloc[0]
            h_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            avg_r = pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_i = days * (avg_r if pd.notna(avg_r) else 0)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}")
                st.write(f"**Model:** {row_i.get('Model', 'N/A')}")
                st.write(f"**Location:** {row_i.get('Location', 'None')}")
                st.write(f"**Last Call Date:** {format_dt(h_dt)}")
                st.write(f"**Avg. Run Hrs:** {avg_r} 🕧")
                st.write(f"**Running Hrs:** {row_i.get('MDA Total Hours', 'N/A')} 🏃‍➡️")
            with c2:
                st.info("📅 Replacement Date")
                for p, m in ind_parts.items(): st.write(f"**{p}:** {format_dt(row_i.get(m['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, m in ind_parts.items():
                    val = pd.to_numeric(row_i.get(m['rem'], 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_i)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 Due Date")
                for p, m in ind_parts.items(): st.write(f"**{p}:** {format_dt(row_i.get(m['due']))}")

            # History & FOC
            st.divider()
            fi_m = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f_i]
            if not fi_m.empty:
                st.subheader("🎁 FOC Details")
                st.dataframe(fi_m[['Created On', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True)
            
            st.subheader("🕒 Service History")
            hi_m = service_df[service_df['Fabrication Number'].astype(str) == sel_f_i].sort_values(by='Call Logged Date', ascending=False)
            for _, si_row in hi_m.iterrows():
                with st.expander(f"📅 {format_dt(si_row.get('Call Logged Date'))} | ⚙️ {si_row.get('Call HMR')} HMR"):
                    st.write(f"**Engineer:** {si_row.get('Service Engineer')}")
                    st.info(si_row.get('Service Engineer Comments'))
