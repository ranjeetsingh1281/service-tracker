import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Compressor Service Tracker Pro")
st.markdown("Customer Summary & Live Machine Details")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Date columns conversion
        date_columns = [
            'Warranty Start Date', 'Warranty End date', 'Last Call HMR Date',
            'Oil Replacement Date', 'Air filter Compressor Replaced Date', 
            'Air filter Engine Replaced Date', 'Main Oil filter Replaced Date', 
            'Return Oil filter Replaced Date', 'AOS Replaced Date', 
            'Greasing Done Date', '1500 Valve kit Replaced Date', 
            '3000 Valve kit Replaced Date', 'OIL DUE DATE', 'AFC DUE DATE', 
            'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 'AOS DUE DATE', 
            'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE'
        ]
        for col in date_columns:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: 
        return "N/A"
    try:
        return dt.strftime('%d-%b-%y')
    except:
        return str(dt)

if master_df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filters")
    
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Select Customer", options=["All Customers"] + customer_list)

    if selected_customer != "All Customers":
        filtered_df = master_df[master_df['CUSTOMER NAME'] == selected_customer]
        
        # --- FIXED COUNT LOGIC ---
        st.subheader(f"📊 Summary for {selected_customer}")
        m1, m2, m3 = st.columns(3)
        
        total_count = len(filtered_df)
        # Check for 'Non' or 'Out' for Out of Warranty
        out_of_warranty_count = len(filtered_df[filtered_df['Warranty Type'].str.contains('Non|Out', na=False, case=False)])
        # Warranty count = Total - Non Warranty
        warranty_count = total_count - out_of_warranty_count
        
        m1.metric("Total Fabrications", total_count)
        m2.metric("In Warranty", warranty_count)
        m3.metric("Out of Warranty", out_of_warranty_count)
        st.divider()
    else:
        filtered_df = master_df

    fab_list = sorted(filtered_df['Fabrication No'].unique().astype(str))
    selected_fab = st.sidebar.selectbox("2. Select Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication No'] == selected_fab].iloc[0]

        # Machine Header
        st.subheader(f"🛡️ Obligation: {m_info.get('Warranty Type', 'N/A')}")
        st.write(f"📅 **Warranty Start:** {format_dt(m_info.get('Warranty Start Date'))} | **End:** {format_dt(m_info.get('Warranty End date'))}")

        # Live Calculation
        current_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_service_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed_hours = current_hmr - last_service_hmr if pd.notna(current_hmr) and pd.notna(last_service_hmr) else 0

        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Current HMR:** {current_hmr}")
            st.write(f"**Hours since Last Service:** {int(elapsed_hours)} Hrs")

        with col2:
            st.info("📅 Replacement Dates")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")

        with col3:
            st.info("⚙️ Live Remaining Hours")
            rem_cols = {
                'HMR - Oil remaining': 'Oil',
                'Air filter replaced - Compressor Remaining Hours': 'AFC',
                'HMR - Separator remaining': 'AOS'
            }
            for orig, label in rem_cols.items():
                orig_rem = pd.to_numeric(m_info.get(orig, 0), errors='coerce')
                live_rem = orig_rem - elapsed_hours if pd.notna(orig_rem) else 0
                st.write(f"**{label}:** {int(live_rem)} Hrs" if live_rem > 0 else f"**{label}:** 🚨 {int(live_rem)} (Due)")

        with col4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # Service History
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                with st.expander(f"📅 {format_dt(row['Call Logged Date'])} | ⚙️ {row.get('Call HMR', 'N/A')} HMR"):
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
    else:
        st.info("👈 Sidebar se Customer aur machine select karein.")
else:
    st.error("Excel files nahi mili!")
