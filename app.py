import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DATA LOAD FUNCTION ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(target):
        for f in folder_files:
            if f.lower() == target.lower(): return f
        return None

    m_name = find_file("Master_Data.xlsx")
    s_name = find_file("Service_Details.xlsx")
    f_name = find_file("Active_FOC.xlsx")
    
    if not m_name or not s_name or not f_name:
        return None, None, None, [f for f in ["Master_Data.xlsx", "Service_Details.xlsx", "Active_FOC.xlsx"] if not find_file(f)]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Error or Missing Files: {missing}")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer Select Karein", options=["All"] + customer_list)
    
    filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    selected_fab = st.sidebar.selectbox("2. Fabrication No Select Karein", options=["Select"] + sorted(filtered_df['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = filtered_df[filtered_df['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # Calculations for Live Remaining
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        # Elapsed logic: Aaj ka HMR - Pichla Service HMR
        elapsed = curr_hmr - last_hmr if pd.notna(curr_hmr) and pd.notna(last_hmr) and curr_hmr > last_hmr else 0

        # --- DISPLAY C1 to C4 ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Machine Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**Avg Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')}")
            st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')}")
            st.write(f"**Last Call HMR:** {m_info.get('Last Call HMR', 'N/A')}")
            st.write(f"**Last Call Date:** {format_dt(m_info.get('Last Call HMR Date'))}")
            st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")

        with c2:
            st.info("📅 Replacement Dates")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AFE R-Date:** {format_dt(m_info.get('Air filter Engine Replaced Date'))}")
            st.write(f"**MOF R-Date:** {format_dt(m_info.get('Main Oil filter Replaced Date'))}")
            st.write(f"**ROF R-Date:** {format_dt(m_info.get('Return Oil filter Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
            st.write(f"**Greasing R-Date:** {format_dt(m_info.get('Greasing Done Date'))}")
            st.write(f"**1500 Kit R-Date:** {format_dt(m_info.get('1500 Valve kit Replaced Date'))}")
            st.write(f"**3000 Kit R-Date:** {format_dt(m_info.get('3000 Valve kit Replaced Date'))}")

        with c3:
            st.info("⚙️ Live Remaining Hrs")
            rem_mapping = {
                'HMR - Oil remaining': 'Oil',
                'Air filter replaced - Compressor Remaining Hours': 'AFC',
                'Air filter replaced - Engine Remaining Hours': 'AFE',
                'Main Oil filter Remaining Hours': 'MOF',
                'Return Oil filter Remaining Hours': 'ROF',
                'HMR - Separator remaining': 'AOS',
                'HMR - Motor regressed remaining': 'Greasing',
                '1500 Valve kit Remaining Hours': '1500 Kit',
                '3000 Valve kit Remaining Hours': '3000 Kit'
            }
            for col, label in rem_mapping.items():
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce') - elapsed
                if val <= 0:
                    st.write(f"**{label}:** 🚨 {int(val)} (Due)")
                else:
                    st.write(f"**{label}:** {int(val)} Hrs")

        with c4:
            st.error("🚨 DUE DATES")
            due_cols = ['OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 'AOS DUE DATE', 'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE']
            labels = ['Oil', 'AFC', 'AFE', 'MOF', 'ROF', 'AOS', 'Greasing', '1500 Kit', '3000 Kit']
            for col, label in zip(due_cols, labels):
                st.write(f"**{label} Due:** {format_dt(m_info.get(col))}")

        # --- FOC FOR SPECIFIC MACHINE ---
        st.divider()
        st.subheader("🎁 FOC Parts for this Machine")
        f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
        foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
        if not foc_match.empty:
            st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
        else: st.info("No FOC record.")

        # --- SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                header = f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR | 🛠️ {row.get('Call Type', 'N/A')}"
                with st.expander(header):
                    st.write(f"**Engineer:** {row.get('Service Engineer', 'N/A')}")
                    st.info(row.get('Service Engineer Comments', 'N/A'))

# --- 2. FOC TRACKER LIST (DETAILED) ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    st.write("Yahan aap poori FOC history dekh sakte hain.")
    
    # User requested 14 Columns
    foc_cols = [
        'Created On', 'FOC Number', 'Call Tracking Number', 'Customer Name', 
        'FOC Type', 'FOC Category', 'FOC Status', 'DEALER INVOICE NO./ DATE', 
        'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.', 
        'AO Number', 'LR Number'
    ]
    
    # Filter only available columns from the list
    available_foc_cols = [c for c in foc_cols if c in foc_df.columns]
    
    st.download_button("📥 Download This FOC List (Excel)", to_excel(foc_df[available_foc_cols]), "FOC_Tracker_List.xlsx")
    st.dataframe(foc_df[available_foc_cols], use_container_width=True, hide_index=True)

# --- 3. SERVICE PENDING DASHBOARD (DATE FIXED) ---
elif page == "Service Pending List":
    st.title("⏳ BIS Service Pending Dashboard")
    st.write("Niche diye gaye buttons se filter karein:")
    
    b1, b2, b3 = st.columns(3)
    pending_list = pd.DataFrame()

    if b1.button("🔴 BIS Over Due", use_container_width=True):
        pending_list = master_df[master_df['BIS Over Due'] != 0].copy()
    if b2.button("🟡 BIS Current Month", use_container_width=True):
        pending_list = master_df[master_df['BIS Current Month Due'] != 0].copy()
    if b3.button("🟢 BIS Next Month", use_container_width=True):
        pending_list = master_df[master_df['BIS Next Month Due'] != 0].copy()

    if not pending_list.empty:
        st.success(f"Total Records Found: {len(pending_list)}")
        st.download_button("📥 Download Pending List (Excel)", to_excel(pending_list), "Pending_List.xlsx")
        
        # Columns to display in table
        disp_cols = ['CUSTOMER NAME', 'Fabrication No', 'HMR Cal.', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE', '3000 KIT DUE DATE']
        table_df = pending_list[disp_cols].copy()
        
        # Applying dd-mmm-yy format to all date columns in table
        for c in ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE', '3000 KIT DUE DATE']:
            table_df[c] = table_df[c].apply(format_dt)
            
        st.dataframe(table_df, use_container_width=True, hide_index=True)
    else:
        st.info("Kripya filter karne ke liye upar diye gaye buttons mein se ek select karein.")
