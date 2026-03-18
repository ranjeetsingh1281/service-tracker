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
        
        # Clean Headers & Handle Duplicates in FOC
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        
        # FOC Duplicate Header Fix
        new_cols = []
        counts = {}
        for col in f_df.columns:
            c = str(col).strip()
            if c in counts:
                counts[c] += 1
                new_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_cols.append(c)
        f_df.columns = new_cols
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Error or Missing Files: {missing}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer Select Karein", options=["All"] + customer_list)
    
    # Filter by Customer
    cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    # --- DASHBOARD METRICS (TOTAL, WARRANTY, NON-WARRANTY) ---
    st.subheader(f"📊 Dashboard Summary: {selected_customer}")
    m1, m2, m3 = st.columns(3)
    total_units = len(cust_filtered)
    # Checking Warranty Type (assuming 'Non' means Non-Warranty)
    non_warranty = len(cust_filtered[cust_filtered['Warranty Type'].str.contains('Non', na=False, case=False)])
    in_warranty = total_units - non_warranty
    
    m1.metric("Total Units", total_units)
    m2.metric("In Warranty", in_warranty)
    m3.metric("Non-Warranty", non_warranty)
    st.divider()

    # Fabrication Selection
    selected_fab = st.sidebar.selectbox("2. Fabrication No Select Karein", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # Live Remaining Calculation
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if pd.notna(curr_hmr) and pd.notna(last_hmr) and curr_hmr > last_hmr else 0

        # --- MACHINE DETAILS C1 to C4 ---
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**Avg Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')}")
            st.write(f"**HMR Cal:** {curr_hmr}")
            st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")
        with c2:
            st.info("📅 Replacement Dates")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Live Remaining Hrs")
            rem_mapping = {'HMR - Oil remaining': 'Oil', 'Air filter replaced - Compressor Remaining Hours': 'AFC', 'HMR - Separator remaining': 'AOS'}
            for col, label in rem_mapping.items():
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce') - elapsed
                st.write(f"**{label}:** {int(val)} Hrs" if val > 0 else f"**{label}:** 🚨 {int(val)} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")


        # --- SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                header = f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR | 🛠️ {row.get('Call Type', 'N/A')}"
                with st.expander(header):
                    st.info(row.get('Service Engineer Comments', 'N/A'))

        # --- FOC SECTION ---
        st.divider()
        st.subheader("🎁 FOC Parts for this Machine")
        f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
        foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
        if not foc_match.empty:
            st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
        else: st.info("No FOC record.")


# --- 2. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    foc_cols = ['Created On', 'FOC Number', 'Customer Name', 'FOC Status', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']
    available = [c for c in foc_cols if c in foc_df.columns]
    st.dataframe(foc_df[available], use_container_width=True)

# --- 3. SERVICE PENDING DASHBOARD ---
elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    b1, b2, b3 = st.columns(3)
    pending_df = pd.DataFrame()
    if b1.button("🔴 BIS Over Due"): pending_df = master_df[master_df['BIS Over Due'] != 0].copy()
    if b2.button("🟡 BIS Current Month"): pending_df = master_df[master_df['BIS Current Month Due'] != 0].copy()
    if b3.button("🟢 BIS Next Month"): pending_df = master_df[master_df['BIS Next Month Due'] != 0].copy()

    if not pending_df.empty:
        st.success(f"Records: {len(pending_df)}")
        disp_cols = ['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']
        table = pending_df[disp_cols].copy()
        for c in ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']: table[c] = table[c].apply(format_dt)
        st.dataframe(table, use_container_width=True)
