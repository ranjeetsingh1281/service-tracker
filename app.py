import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Compressor Service Tracker Pro")
st.markdown("Advanced Machine Details")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # In sabhi columns ko datetime mein convert karein taaki format change ho sake
        all_date_cols = [
            'Warranty Start Date', 'Warranty End date', 
            'Oil Replacement Date', 'Air filter Compressor Replaced Date', 
            'Air filter Engine Replaced Date', 'Main Oil filter Replaced Date', 
            'Return Oil filter Replaced Date', 'AOS Replaced Date', 
            'Greasing Done Date', '1500 Valve kit Replaced Date', 
            '3000 Valve kit Replaced Date', 'OIL DUE DATE', 'AFC DUE DATE', 
            'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 'AOS DUE DATE', 
            'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE'
        ]
        
        for col in all_date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')

        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

# Date formatting helper function (dd-mmm-yy)
def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() == "nan": 
        return "N/A"
    try:
        return dt.strftime('%d-%b-%y')
    except:
        return str(dt) # Agar conversion fail ho toh original value dikhaye

if master_df is not None:
    fab_list = sorted(master_df['Fabrication No'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication No'] == selected_fab].iloc[0]

        # --- SECTION 1: WARRANTY HEADER ---
        st.divider()
        st.subheader(f"🛡️ Obligation (Warranty): {m_info.get('Warranty Type', 'N/A')}")
        st.write(f"📅 **Start:** {format_dt(m_info.get('Warranty Start Date'))}  |  **End:** {format_dt(m_info.get('Warranty End date'))}")

        # --- SECTION 2: 4-COLUMN LAYOUT ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Address:** {m_info.get('Address', 'N/A')}")
            st.write(f"**Contact No 1:** {m_info.get('Contact No. 1', 'N/A')}")
            st.write(f"**Category:** {m_info.get('Category', 'N/A')}")
            st.write(f"**Avg. Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')} 👈")
            st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')} 👈")
            st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")
            st.write(f"**Last Call HMR:** {m_info.get('Last Call HMR', 'N/A')}")
            st.write(f"**Last Call HMR Date:** {format_dt(m_info.get('Last Call HMR Date', 'N/A'))}")

        with col2:
            st.info("📅 Replacement Dates")
            # Replacement Dates with format_dt
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AFE R-Date:** {format_dt(m_info.get('Air filter Engine Replaced Date'))}")
            st.write(f"**MOF R-Date:** {format_dt(m_info.get('Main Oil filter Replaced Date'))}")
            st.write(f"**ROF R-Date:** {format_dt(m_info.get('Return Oil filter Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
            st.write(f"**Greasing:** {format_dt(m_info.get('Greasing Done Date'))}")
            st.write(f"**1500 Kit:** {format_dt(m_info.get('1500 Valve kit Replaced Date'))}")
            st.write(f"**3000 Kit:** {format_dt(m_info.get('3000 Valve kit Replaced Date'))}")

        with col3:
            st.info("⚙️ Remaining Hours")
            st.write(f"**Oil Rem:** {m_info.get('HMR - Oil remaining', 'N/A')}")
            st.write(f"**AFC Rem:** {m_info.get('Air filter replaced - Compressor Remaining Hours', 'N/A')}")
            st.write(f"**AFE Rem:** {m_info.get('Air filter replaced - Engine Remaining Hours', 'N/A')}")
            st.write(f"**MOF Rem:** {m_info.get('Main Oil filter Remaining Hours','N/A')}")
            st.write(f"**ROF Rem:** {m_info.get('Return Oil filter Remaining Hours','N/A')}")
            st.write(f"**AOS Rem:** {m_info.get('HMR - Separator remaining', 'N/A')}")
            st.write(f"**RGT Rem:** {m_info.get('HMR - Motor regressed remaining','N/A')}")
            st.write(f"**1500 Kit Rem:** {m_info.get('1500 Valve kit Remaining Hours','N/A')}")
            st.write(f"**3000 Kit Rem:** {m_info.get('3000 Valve kit Remaining Hours', 'N/A')}")

        with col4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AFE Due:** {format_dt(m_info.get('AFE DUE DATE'))}")
            st.write(f"**MOF Due:** {format_dt(m_info.get('MOF DUE DATE'))}")
            st.write(f"**ROF Due:** {format_dt(m_info.get('ROF DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")
            st.write(f"**Greasing Due:** {format_dt(m_info.get('RGT DUE DATE'))}")
            st.write(f"**1500 Kit Due:** {format_dt(m_info.get('1500 KIT DUE DATE'))}")
            st.write(f"**3000 Kit Due:** {format_dt(m_info.get('3000 KIT DUE DATE'))}")

        # --- SECTION 3: SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History (Newest First)")
        
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy()
        history = history.sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            for index, row in history.iterrows():
                d_str = format_dt(row['Call Logged Date'])
                header = f"📅 {d_str} | ⚙️ {row.get('Call HMR', 'N/A')} HMR | {row.get('Call Type', 'N/A')}"
                
                with st.expander(header):
                    st.write(f"**Tracking No:** {row.get('Call Tracking Number', 'N/A')}")
                    st.write(f"**Status:** {row.get('Call Status', 'N/A')}")
                    st.write("**Engineer Comments:**")
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
        else:
            st.warning("No history found.")
else:
    st.error("Excel files nahi mili! Check GitHub repository.")
