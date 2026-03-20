import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# Page Settings
st.set_config_title = "ELGi Global Tracker"
st.set_page_config(layout="wide")

# --- SMART DATA LOADER ---
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

# --- SIDEBAR MENU ---
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Page:", ["1. DPSAC Tracker", "2. EPSAC Tracker"])

# ==========================================
# PAGE 1: DPSAC TRACKER
# ==========================================
if page_choice == "1. DPSAC Tracker":
    st.title("🛠️ DPSAC Tracker - Units Data")
    tabs = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    
    with tabs[0]: # Machine Tracker
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str)) if not master_df.empty else []
        col1, col2 = st.columns(2)
        sel_c = col1.selectbox("Select Customer Name", ["All"] + c_list, key="dpsac_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = col2.selectbox("Select Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="dpsac_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            # Info Cards
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

            # --- History & FOC Details ---
            st.divider()
            col_f, col_h = st.columns(2)
            with col_f:
                st.subheader("🎁 FOC Details")
                f_match = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
                st.dataframe(f_match[['Created On', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not f_match.empty else pd.DataFrame(), use_container_width=True)
            with col_h:
                st.subheader("🕒 Service History")
                h_match = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
                for _, s_row in h_match.iterrows():
                    with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                        st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                        st.info(s_row.get('Service Engineer Comments', 'N/A'))

    with tabs[1]: # FOC List
        st.subheader("📦 DPSAC Master FOC List")
        std_fabs = master_df['Fabrication No'].astype(str).unique() if not master_df.empty else []
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)], use_container_width=True)

    with tabs[2]: # Service Pending
        st.subheader("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        if b1.button("🔴 Overdue"): st.dataframe(master_df[master_df['BIS Over Due'] != 0])
        if b2.button("🟡 Current Month"): st.dataframe(master_df[master_df['BIS Current Month Due'] != 0])
        if b3.button("🟢 Next Month"): st.dataframe(master_df[master_df['BIS Next Month Due'] != 0])

# ==========================================
# PAGE 2: INDUSTRIAL TRACKER (Industrial Data)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker - Industrial Machine Data")
    tabs_i = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tabs_i[0]: # Machine Tracker
        c_list_i = sorted(master_od_df['Customer Name'].unique().astype(str)) if not master_od_df.empty else []
        col1_i, col2_i = st.columns(2)
        sel_c_i = col1_i.selectbox("Select Customer Name", ["All"] + c_list_i, key="ind_c")
        df_f_i = master_od_df if sel_c_i == "All" else master_od_df[master_od_df['Customer Name'] == sel_c_i]
        sel_f_i = col2_i.selectbox("Select Fabrication No", ["Select"] + sorted(df_f_i['Fabrication No'].astype(str).unique()), key="ind_f")

        if sel_f_i != "Select":
            row_i = df_f_i[df_f_i['Fabrication No'].astype(str) == sel_f_i].iloc[0]
            hmr_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - hmr_dt).days if pd.notna(hmr_dt) else 0
            elapsed_i = days * pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')

            # Info Cards
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}\n**Model:** {row_i.get('Model')}\n**Category:** {row_i.get('Category')}")
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

            # --- History & FOC Details ---
            st.divider()
            col_fi, col_hi = st.columns(2)
            with col_fi:
                st.subheader("🎁 FOC Details")
                f_match_i = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f_i]
                st.dataframe(f_match_i[['Created On', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not f_match_i.empty else pd.DataFrame(), use_container_width=True)
            with col_hi:
                st.subheader("🕒 Service History")
                h_match_i = service_df[service_df['Fabrication Number'].astype(str) == sel_f_i].sort_values(by='Call Logged Date', ascending=False)
                for _, si_row in h_match_i.iterrows():
                    with st.expander(f"📅 {format_dt(si_row.get('Call Logged Date'))} | {si_row.get('Call Type', 'N/A')}"):
                        st.info(si_row.get('Service Engineer Comments', 'N/A'))

    with tabs_i[1]: # FOC List
        st.subheader("📦 INDUSTRIAL Master FOC List")
        ind_fabs = master_od_df['Fabrication No'].astype(str).unique() if not master_od_df.empty else []
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(ind_fabs)], use_container_width=True)

    with tabs_i[2]: # Service Pending
        st.subheader("⏳ INDUSTRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        if o1.button("🔴 Red Count"): st.dataframe(master_od_df[master_od_df['Red Count'] != 0])
        if o2.button("🟡 Yellow Count"): st.dataframe(master_od_df[master_od_df['Yellow Count'] != 0])
        if o3.button("🟢 Green Count"): st.dataframe(master_od_df[master_od_df['Green Count'] != 0])
