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
        
        # Strip invisible spaces from headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Error or Missing Files: {missing}")
    st.stop()

# --- APP NAVIGATION ---
st.sidebar.title("📌 Menu")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    
    # Customer Selection
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer Select Karein", options=["All"] + customer_list)
    
    filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    # Fabrication Selection
    fab_list = sorted(filtered_df['Fabrication No'].astype(str).unique())
    selected_fab = st.sidebar.selectbox("2. Fabrication No Select Karein", options=["Select"] + fab_list)

    if selected_fab != "Select":
        # Data filtering based on selection
        m_info = filtered_df[filtered_df['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # --- C1 to C4 MACHINE DETAILS ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Machine Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')}")
        with c2:
            st.info("📅 Replacement")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Status")
            st.write(f"**HMR Status:** {m_info.get('Service Status by HMR', 'N/A')}")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # --- FOC PARTS HISTORY (New Section) ---
        st.divider()
        st.subheader("🎁 FOC Parts Details (Free of Cost)")
        
        # Matching fabrication no in FOC file (using headers from your file)
        # Using FABRICATION NO. (with dot) as seen in your CSV snippet
        foc_match = foc_df[foc_df['FABRICATION NO'].astype(str) == selected_fab].copy()
        
        if not foc_match.empty:
            # Columns requested by you
            foc_display = foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']].copy()
            st.dataframe(foc_display, use_container_width=True, hide_index=True)
            st.caption(f"Total {len(foc_match)} FOC items found.")
        else:
            st.info("Is machine ke liye koi FOC parts record nahi mila.")

        # --- SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            for _, row in history.iterrows():
                dt = format_dt(row.get('Call Logged Date'))
                h_hmr = row.get('Call HMR', 'N/A')
                h_type = row.get('Call Type', 'N/A')
                
                header = f"📅 {dt} | ⚙️ {h_hmr} HMR | 🛠️ {h_type}"
                with st.expander(header):
                    st.write(f"**Engineer:** {row.get('Service Engineer', 'N/A')}")
                    st.info(row.get('Service Engineer Comments', 'No comments available.'))
        else:
            st.warning("Is machine ki service history available nahi hai.")

elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    # (Puraana BIS action button logic yahan daal sakte hain)
    st.info("BIS Overdue, Current Month aur Next Month ke buttons yahan kaam karenge.")
