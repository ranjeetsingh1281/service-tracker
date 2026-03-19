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
main_choice = st.sidebar.radio("Dashboard Chunein:", ["DPSAC Tracker", "INDUSTRIAL Tracker"])

# --- 1. DPSAC SECTION ---
if main_choice == "DPSAC Tracker":
    sub = st.sidebar.selectbox("Standard Options:", ["Machine Tracker", "FOC List", "Service Pending"])
    
    if sub == "Machine Tracker":
        st.title("🛠️ DPSAC Machine Tracker")
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        sel_c = st.sidebar.selectbox("Customer Name", ["All"] + c_list, key="dpsac_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = st.sidebar.selectbox("Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="dpsac_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}")
                st.write(f"**Model:** {row.get('MODEL')}"); st.write(f"**Sl No:** {row.get('SL NO.')}")
                st.write(f"**Location:** {row.get('LOCATION')}"); st.write(f"**HMR Cal:** {curr_h}"); st.write(f"**Avg. Running Hrs:**{row.get('Avg. Hrs')}")
            with c2:
                st.info("📅 Replacement")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['date']))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for p, m in std_parts.items():
                    rem = int(pd.to_numeric(row.get(m['rem'], 0), errors='coerce') - elapsed)
                    st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem}")
            with c4:
                st.error("🚨 DUE DATES")
                for p, m in std_parts.items(): st.write(f"**{p}:** {format_dt(row.get(m['due']))}")

            # --- RESTORED HISTORY & FOC FOR DPSAC ---
            st.divider()
            st.subheader("🎁 FOC Parts History")
            foc_match = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
            st.dataframe(foc_match[['Created On', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not foc_match.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            
            st.subheader("🕒 Service History")
            hist = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            if not hist.empty:
                for _, s_row in hist.iterrows():
                    with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                        st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                        st.info(s_row.get('Service Engineer Comments', 'N/A'))
            else: st.warning("No history found.")

    elif sub == "FOC List":
        st.title("📦 DPSAC FOC Tracker List")
        std_fabs = master_df['Fabrication No'].astype(str).unique()
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)], use_container_width=True)

    elif sub == "Service Pending":
        st.title("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        if b1.button("🔴 Overdue"): st.dataframe(master_df[master_df['BIS Over Due'] != 0])
        if b2.button("🟡 Current Month"): st.dataframe(master_df[master_df['BIS Current Month Due'] != 0])
        if b3.button("🟢 Next Month"): st.dataframe(master_df[master_df['BIS Next Month Due'] != 0])

# --- 2. INDUSTRIAL SECTION ---
elif main_choice == "INDUSTRIAL Tracker (Industrial)":
    sub = st.sidebar.selectbox("Industrial Options:", ["Machine Tracker", "FOC List", "Service Pending"])
    
    if sub == "Machine Tracker":
        st.title("🛡️ INDUSTRIAL Machine Tracker")
        c_list_ind = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_c_ind = st.sidebar.selectbox("Customer Name", ["All"] + c_list_ind, key="ind_c")
        df_f_ind = master_od_df if sel_c_ind == "All" else master_od_df[master_od_df['Customer Name'] == sel_c_ind]
        sel_f_ind = st.sidebar.selectbox("Fabrication No", ["Select"] + sorted(df_f_ind['Fabrication No'].astype(str).unique()), key="ind_f")
        
        if sel_f_ind != "Select":
            row = df_f_ind[df_f_ind['Fabrication No'].astype(str) == sel_f_ind].iloc[0]
            hmr_dt = pd.to_datetime(row.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - hmr_dt).days if pd.notna(hmr_dt) else 0
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

            # --- RESTORED HISTORY & FOC FOR INDUSTRIAL ---
            st.divider()
            st.subheader("🎁 FOC Parts History")
            foc_match_ind = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f_ind]
            st.dataframe(foc_match_ind[['Created On', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not foc_match_ind.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            
            st.subheader("🕒 Service History")
            hist_ind = service_df[service_df['Fabrication Number'].astype(str) == sel_f_ind].sort_values(by='Call Logged Date', ascending=False)
            if not hist_ind.empty:
                for _, s_row in hist_ind.iterrows():
                    with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                        st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                        st.info(s_row.get('Service Engineer Comments', 'N/A'))
            else: st.warning("No history found.")

    elif sub == "FOC List":
        st.title("📦 INDUSTRIAL FOC Tracker List")
        ind_fabs = master_od_df['Fabrication No'].astype(str).unique()
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(ind_fabs)], use_container_width=True)

    elif sub == "Service Pending":
        st.title("⏳ INDUSTRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        if o1.button("🔴 Red Count"): st.dataframe(master_od_df[master_od_df['Red Count'] != 0])
        if o2.button("🟡 Yellow Count"): st.dataframe(master_od_df[master_od_df['Yellow Count'] != 0])
        if o3.button("🟢 Green Count"): st.dataframe(master_od_df[master_od_df['Green Count'] != 0])
