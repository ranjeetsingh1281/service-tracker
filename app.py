import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Compressor Service Tracker Pro")
st.markdown("Advanced Machine Details (Industrial)")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_OD_Data.xlsx"
    s_file = "Service_Details.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Date columns conversion
        date_columns = [
            'Warranty Start Date', 'MDA HMR Date',
            'MDA Oil R Date', 'MDA AF R Date', 
            'MDA OF R Date', 'MDA AOS R Date', 
            'MDA RGT R Date', 'MDA Valvekit R Date', 
            'MDA PF R DATE', 'MDA FF R DATE', 
            'MDA CF R DATE', 'AF Next Due Date', 'OF Next Due Date', 
            'Oil Next Due Date', 'AOS Next Due Date', 'VALVE Next Due Date', 'RGT Next Due Date', 
            'PF Next Due date', 'CF Next Due Date', 'FF Next Due Date', 'Last Sch Date'
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
    fab_list = sorted(master_df['Fabrication No'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication No'] == selected_fab].iloc[0]

        # --- SECTION 1: WARRANTY ---
        st.divider()
        st.subheader(f"🛡️ Obligation (Warranty): {m_info.get('Warranty Type', 'N/A')}")
        st.write(f"📅 **Start:** {format_dt(m_info.get('Warranty Start Date'))}")

        # --- PRE-CALCULATION FOR LIVE REMAINING HOURS ---
        # Current HMR vs Last Service HMR difference
        current_hmr = pd.to_numeric(m_info.get('CURRENT HMR', 0), errors='coerce')
        last_service_hmr = pd.to_numeric(m_info.get('Last Sch HMR', 0), errors='coerce')
        
        # Kitne hours machine chal chuki hai pichli service ke baad
        elapsed_hours = current_hmr - last_service_hmr if pd.notna(current_hmr) and pd.notna(last_service_hmr) else 0

        # --- SECTION 2: 4-COLUMN LAYOUT ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**City:** {m_info.get('City', 'N/A')}")
            st.write(f"**Sate:** {m_info.get('State', 'N/A')}")
            st.write(f"**Category:** {m_info.get('Category', 'N/A')}")
            st.write(f"**Avg. Running Hrs:** {m_info.get('MDA AVG Running Hours Per Day', 'N/A')}👈")
            st.write(f"**Last Call HMR:** {m_info.get('Last Sch HMR')}")
            st.write(f"**Last Call HMR Date:** {format_dt(m_info.get('Last Sch Date'))}")
            st.write(f"**Hours since Last Service:** {int(elapsed_hours)}👈")

        with col2:
            st.info("📅 Replacement Dates")
             # Sabhi Replacement dates par format_dt apply kiya gaya hai
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('MDA Oil R Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AFE R-Date:** {format_dt(m_info.get('Air filter Engine Replaced Date'))}")
            st.write(f"**MOF R-Date:** {format_dt(m_info.get('Main Oil filter Replaced Date'))}")
            st.write(f"**ROF R-Date:** {format_dt(m_info.get('Return Oil filter Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
            st.write(f"**Greasing R-Date:** {format_dt(m_info.get('Greasing Done Date'))}")
            st.write(f"**1500 Kit R-Date:** {format_dt(m_info.get('1500 Valve kit Replaced Date'))}")
            st.write(f"**3000 Kit R-Date:** {format_dt(m_info.get('3000 Valve kit Replaced Date'))}")

        with col3:
            st.info("⚙️ Live Remaining Hours")
            # Logic: Last Service Remaining - Elapsed Hours
            rem_cols = {
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
            
            for original_col, label in rem_cols.items():
                orig_rem = pd.to_numeric(m_info.get(original_col, 0), errors='coerce')
                live_rem = orig_rem - elapsed_hours if pd.notna(orig_rem) else 0
                
                # Agar hours khatam ho gaye hain toh minus ki jagah 0 ya Warning dikhayein
                if live_rem <= 0:
                    st.write(f"**{label}:** 🚨 {int(live_rem)} (Due Now)")
                else:
                    st.write(f"**{label}:** {int(live_rem)} Hrs")

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
                    st.write(f"**Status:** {row.get('Call Status', 'N/A')}")
                    st.write("**Engineer Comments:**")
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
        else:
            st.warning("No history found.")
else:
    st.error("Excel files nahi mili!")
