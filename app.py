import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Fabrication Service Tracker Pro")
st.markdown("Advanced Machine Details & Service History (Excel Version)")

# Data Load Function
@st.cache_data
def load_data():
    # Naye file names ke mutabik
    m_file = "Master_Data.xlsx"
    s_file = "Service_Detail.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        # Excel files read karne ke liye engine='openpyxl' ka use
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Service date conversion
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

if master_df is not None:
    # Search Fabrication No (Column - C)
    fab_list = sorted(master_df['Fabrication No'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication No'] == selected_fab].iloc[0]

        # --- SECTION 1: WARRANTY HEADER (Column M & O) ---
        st.divider()
        warranty_status = m_info.get('Warranty Type', 'N/A')
        w_start = m_info.get('Warranty Start Date', 'N/A')
        w_end = m_info.get('Warranty End date', 'N/A')
        
        st.subheader(f"🛡️ Warranty: {warranty_status}")
        st.write(f"📅 **Start:** {w_start}  |  **End:** {w_end}")

        # --- SECTION 2: 4-COLUMN LAYOUT ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Address:** {m_info.get('Address', 'N/A')}")
            st.write(f"**Email:** {m_info.get('Email ID', 'N/A')}")
            st.write(f"**Contact 1:** {m_info.get('Contact No. 1', 'N/A')}")
            st.write(f"**Contact 2:** {m_info.get('Contact No. 2', 'N/A')}")
            st.write(f"**Category:** {m_info.get('Category', 'N/A')}")

        with col2:
            st.info("📅 Replacement Dates")
            # Columns DR to DZ
            st.write(f"**Oil R-Date:** {m_info.get('Oil Replacement Date', 'N/A')}")
            st.write(f"**AFC R-Date:** {m_info.get('Air filter Compressor Replaced Date', 'N/A')}")
            st.write(f"**AFE R-Date:** {m_info.get('Air filter Engine Replaced Date', 'N/A')}")
            st.write(f"**MOF R-Date:** {m_info.get('Main Oil filter Replaced Date', 'N/A')}")
            st.write(f"**ROF R-Date:** {m_info.get('Return Oil filter Replaced Date', 'N/A')}")
            st.write(f"**AOS R-Date:** {m_info.get('AOS Replaced Date', 'N/A')}")
            st.write(f"**Greasing Date:** {m_info.get('Greasing Done Date', 'N/A')}")
            st.write(f"**1500 Kit R-Date:** {m_info.get('1500 Valve kit Replaced Date', 'N/A')}")
            st.write(f"**3000 Kit R-Date:** {m_info.get('3000 Valve kit Replaced Date', 'N/A')}")

        with col3:
            st.info("⚙️ Remaining Hours")
            # Columns EA to EI
            st.write(f"**Oil Rem:** {m_info.get('HMR - Oil remaining', 'N/A')}")
            st.write(f"**AFC Rem:** {m_info.get('Air filter replaced - Compressor Remaining Hours', 'N/A')}")
            st.write(f"**AFE Rem:** {m_info.get('Air filter replaced - Engine Remaining Hours', 'N/A')}")
            st.write(f"**MOF Rem:** {m_info.get('Main Oil filter Remaining Hours', 'N/A')}")
            st.write(f"**ROF Rem:** {m_info.get('Return Oil filter Remaining Hours', 'N/A')}")
            st.write(f"**AOS Rem:** {m_info.get('HMR - Separator remaining', 'N/A')}")
            st.write(f"**Grease Rem:** {m_info.get('HMR - Motor regressed remaining', 'N/A')}")
            st.write(f"**1500 Kit Rem:** {m_info.get('1500 Valve kit Remaining Hours', 'N/A')}")
            st.write(f"**3000 Kit Rem:** {m_info.get('3000 Valve kit Remaining Hours', 'N/A')}")

        with col4:
            st.error("🚨 DUE DATES")
            # Columns CU to DC
            st.write(f"**Oil Due:** {m_info.get('OIL DUE DATE', 'N/A')}")
            st.write(f"**AFC Due:** {m_info.get('AFC DUE DATE', 'N/A')}")
            st.write(f"**AFE Due:** {m_info.get('AFE DUE DATE', 'N/A')}")
            st.write(f"**MOF Due:** {m_info.get('MOF DUE DATE', 'N/A')}")
            st.write(f"**ROF Due:** {m_info.get('ROF DUE DATE', 'N/A')}")
            st.write(f"**AOS Due:** {m_info.get('AOS DUE DATE', 'N/A')}")
            st.write(f"**RGT Due:** {m_info.get('RGT DUE DATE', 'N/A')}")
            st.write(f"**1500 Kit Due:** {m_info.get('1500 KIT DUE DATE', 'N/A')}")
            st.write(f"**3000 Kit Due:** {m_info.get('3000 KIT DUE DATE', 'N/A')}")

        # --- SECTION 3: SERVICE HISTORY (DESCENDING) ---
        st.divider()
        st.subheader("🕒 Service/Call History (Newest First)")
        
        # Filtering Service_Detail (Column R is Fabrication Number)
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy()
        history = history.sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            for index, row in history.iterrows():
                d_str = row['Call Logged Date'].strftime('%d-%b-%Y') if pd.notna(row['Call Logged Date']) else "N/A"
                header = f"📅 {d_str} | ⚙️ {row.get('Call HMR', 'N/A')} HMR | {row.get('Call Type', 'N/A')}"
                
                with st.expander(header):
                    st.write(f"**Tracking No:** {row.get('Call Tracking Number', 'N/A')}")
                    st.write(f"**Status:** {row.get('Call Status', 'N/A')}")
                    st.write(f"**Customer:** {row.get('Customer', 'N/A')}")
                    st.write("**Engineer Comments:**")
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
        else:
            st.warning("No history found.")
else:
    st.error("Excel files (Master_Data.xlsx / Service_Detail.xlsx) nahi mili!")
