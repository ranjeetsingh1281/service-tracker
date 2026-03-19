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
st.sidebar.title("📌 Main Menu")
main_choice = st.sidebar.radio("Dashboard Chunein:", 
                                ["DPSAC Tracker (Standard)", "INDUSTRIAL Tracker (OD Data)"])

# --- 1. DPSAC TRACKER (STANDARD DATA) ---
if main_choice == "DPSAC Tracker (Standard)":
    st.sidebar.markdown("---")
    sub_page = st.sidebar.selectbox("Standard Options:", ["Machine Tracker", "FOC List", "Service Pending"])

    if sub_page == "Machine Tracker":
        st.title("🛠️ DPSAC Machine Tracker")
        if master_df.empty: st.warning("Master_Data missing!")
        else:
            cust_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
            sel_cust = st.sidebar.selectbox("Customer", options=["All"] + cust_list, key="std_c")
            df_f = master_df if sel_cust == "All" else master_df[master_df['CUSTOMER NAME'] == sel_cust]
            sel_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_f")
            
            if sel_fab != "Select":
                row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
                # C1-C4 Logic for Standard (As per your requirement)
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.info("📋 Customer Info"); st.write(f"**Customer:** {row.get('CUSTOMER NAME')}")
                # [Standard 9 parts mapping...]
                st.success(f"History for {sel_fab}")
                hist = service_df[service_df['Fabrication Number'].astype(str) == sel_fab].sort_values(by='Call Logged Date', ascending=False)
                for _, s_row in hist.head(5).iterrows():
                    with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                        st.info(s_row.get('Service Engineer Comments', 'N/A'))

    elif sub_page == "FOC List":
        st.title("📦 DPSAC FOC Tracker List")
        std_fabs = master_df['Fabrication No'].astype(str).unique()
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)], use_container_width=True)

    elif sub_page == "Service Pending":
        st.title("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        if b1.button("🔴 Overdue"): st.dataframe(master_df[master_df['BIS Over Due'] != 0])
        if b2.button("🟡 Current Month"): st.dataframe(master_df[master_df['BIS Current Month Due'] != 0])
        if b3.button("🟢 Next Month"): st.dataframe(master_df[master_df['BIS Next Month Due'] != 0])

# --- 2. INDUSTRIAL TRACKER (OD DATA) ---
elif main_choice == "INDUSTRIAL Tracker (OD Data)":
    st.sidebar.markdown("---")
    sub_page = st.sidebar.selectbox("Industrial Options:", ["Machine Tracker", "FOC List", "Service Pending"])

    if sub_page == "Machine Tracker":
        st.title("🛡️ INDUSTRIAL Machine Tracker")
        if master_od_df.empty: st.error("Master_OD_Data missing!")
        else:
            cust_list_od = sorted(master_od_df['Customer Name'].unique().astype(str))
            sel_cust_od = st.sidebar.selectbox("Customer", options=["All"] + cust_list_od, key="od_c")
            df_od_f = master_od_df if sel_cust_od == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust_od]
            sel_fab_od = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(df_od_f['Fabrication No'].astype(str).unique()), key="od_f")

            if sel_fab_od != "Select":
                row_od = df_od_f[df_od_f['Fabrication No'].astype(str) == sel_fab_od].iloc[0]
                # LIVE CALCULATION FOR INDUSTRIAL
                hmr_dt = pd.to_datetime(row_od.get('MDA HMR Date'), errors='coerce')
                days = (pd.Timestamp(datetime.now().date()) - hmr_dt).days if pd.notna(hmr_dt) else 0
                avg = pd.to_numeric(row_od.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
                elapsed_od = days * (avg if pd.notna(avg) else 0)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.info("📋 Customer Info")
                    st.write(f"**Customer:** {row_od.get('Customer Name')}")
                    st.write(f"**Model:** {row_od.get('Model', 'N/A')}")
                    st.write(f"**Category:** {row_od.get('Category', 'N/A')}")
                with c2:
                    st.info("📅 Replacement")
                    # MDA Replacement mapping
                    st.write(f"**Oil:** {format_dt(row_od.get('MDA Oil R Date'))}")
                    st.write(f"**AOS:** {format_dt(row_od.get('MDA AOS R Date'))}")
                with c3:
                    st.info("⚙️ Live Remaining")
                    val = pd.to_numeric(row_od.get('MDA OIL Remaining Hours', 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_od)
                    st.write(f"**Oil Remaining:** {rem} Hrs" if rem > 0 else f"**Oil:** 🚨 {rem}")
                with c4:
                    st.error("🚨 DUE DATES")
                    st.write(f"**Oil Due:** {format_dt(row_od.get('OIL DUE DATE'))}")

    elif sub_page == "FOC List":
        st.title("📦 INDUSTRIAL FOC Tracker List")
        od_fabs = master_od_df['Fabrication No'].astype(str).unique()
        st.dataframe(foc_df[foc_df['FABRICATION NO'].astype(str).isin(od_fabs)], use_container_width=True)

    elif sub_page == "Service Pending":
        st.title("⏳ INDUSTRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        if o1.button("🔴 Red Count"): st.dataframe(master_od_df[master_od_df['Red Count'] != 0])
        if o2.button("🟡 Yellow Count"): st.dataframe(master_od_df[master_od_df['Yellow Count'] != 0])
        if o3.button("🟢 Green Count"): st.dataframe(master_od_df[master_od_df['Green Count'] != 0])
