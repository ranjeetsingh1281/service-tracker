import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Fabrication Service Tracker Pro")
st.markdown("Advanced Machine Details (Excel Version with Formatted Dates)")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Detail.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Sabhi date columns ko convert karein taaki format change ho sake
        date_cols_m = ['Warranty Start Date', 'Warranty End date', 'OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 'AOS DUE DATE', 'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE']
        for col in date_cols_m:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')

        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

# Date formatting helper function
def format_dt(dt):
    if pd.isna(dt): return "N/A"
    return dt.strftime('%d-%b-%y')

if master_df is not None:
    fab_list = sorted(master_df['Fabrication No'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication No'] == selected_fab].iloc[0]

        # --- SECTION 1: WARRANTY HEADER ---
        st.divider()
        w_start = format_dt(m_info.get('Warranty Start Date'))
        w_end = format_dt(m_info.get('Warranty End date'))
        st.subheader(f"🛡️ Warranty: {m_info.get('Warranty Type', 'N/A')}")
        st.write(f"📅 **Start:** {w_start}  |  **End:** {w_end}")

        # --- SECTION 2: 4-COLUMN LAYOUT ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Address:** {m_info.get('Address', 'N/A')}")
            st.write(f"**Contact 1:** {m_info.get('Contact No. 1', 'N/A')}")
            st.write(f"**Category:** {m_info.get('Category', 'N/A')}")

        with col2:
            st.info("📅 Replacement Dates")
            # In dates ko bhi format_dt se pass karein agar ye Excel mein date type hain
            st.write(f"**Oil R-Date:** {m_info.get('Oil Replacement Date', 'N/A')}")
            st.write(f"**AFC R-Date:** {m_info.get('Air filter Compressor Replaced Date', 'N/A')}")
            st.write(f"**AFE R-Date:** {m_info.get('Air filter Engine Replaced Date', 'N/A')}")
            st.write(f"**AOS R-Date:** {m_info.get('AOS Replaced Date', 'N/A')}")
            st.write(f"**3000 Kit R-Date:** {m_info.get('3000 Valve kit Replaced Date', 'N/A')}")

        with col3:
            st.info("⚙️ Remaining Hours")
            st.write(f"**Oil Rem:** {m_info.get('HMR - Oil remaining', 'N/A')}")
            st.write(f"**AFC Rem:** {m_info.get('Air filter replaced - Compressor Remaining Hours', 'N/A')}")
            st.write(f"**AFE Rem:** {m_info.get('Air filter replaced - Engine Remaining Hours', 'N/A')}")
            st.write(f"**AOS Rem:** {m_info.get('HMR - Separator remaining', 'N/A')}")

        with col4:
            st.error("🚨 DUE DATES")
            # DUE DATES ko dd-mmm-yy format mein dikhana
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AFE Due:** {format_dt(m_info.get('AFE DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")
            st.write(f"**3000 Kit Due:** {format_dt(m_info.get('3000 KIT DUE DATE'))}")

        # --- SECTION 3: SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History (Descending)")
        
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy()
        history = history.sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            for index, row in history.iterrows():
                # Service history ki date format karna
                d_str = format_dt(row['Call Logged Date'])
                header = f"📅 {d_str} | ⚙️ {row.get('Call HMR', 'N/A')} HMR | {row.get('Call Type', 'N/A')}"
                
                with st.expander(header):
                    st.write(f"**Status:** {row.get('Call Status', 'N/A')}")
                    st.write(f"**Engineer Comments:**")
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
        else:
            st.warning("No history found.")
else:
    st.error("Files nahi mili! Check 'Master_Data.xlsx' & 'Service_Detail.xlsx' on GitHub.")
