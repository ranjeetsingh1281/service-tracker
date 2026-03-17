import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Data Cleaning
        m_df['Warranty Type'] = m_df['Warranty Type'].astype(str).str.strip()
        m_df['CUSTOMER NAME'] = m_df['CUSTOMER NAME'].astype(str).str.strip()
        
        # Zaroori Date Columns ko convert karna
        date_cols = [
            'Warranty Start Date', 'Warranty End date', 'Last Call HMR Date',
            'OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'AOS DUE DATE', 
            'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE'
        ]
        for col in date_cols:
            if col in m_df.columns:
                # errors='coerce' se galat dates NaT (Not a Time) ban jayengi
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pending_Services')
    return output.getvalue()

master_df, service_df = load_data()

if master_df is not None:
    st.sidebar.title("📌 Navigation Menu")
    page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

    # --- PAGE 1: MACHINE TRACKER (Wahi purana logic) ---
    if page == "Machine Tracker":
        st.title("🛠️ ELGi Compressor Service Tracker")
        # ... (Yahan aapka purana machine tracker ka code rahega)
        st.info("Sidebar se customer select karein.")

    # --- PAGE 2: SERVICE PENDING LIST (FIXED) ---
    elif page == "Service Pending List":
        st.title("⏳ Service Pending Dashboard")
        
        # Filter Days Selection
        days_to_check = st.select_slider(
            "Kitne dinon ki pending list dekhni hai?",
            options=[7, 15, 30, 60, 90],
            value=30
        )

        today = pd.Timestamp.now().normalize() # Aaj ki date bina samay ke
        future_date = today + pd.Timedelta(days=days_to_check)
        
        # Logic: Jo date 'aaj' se badi ho aur 'future_date' se choti ho
        # Ya phir jo Overdue ho (aaj se purani date)
        pending_list = master_df[
            (master_df['OIL DUE DATE'] <= future_date) | 
            (master_df['AFC DUE DATE'] <= future_date) |
            (master_df['AOS DUE DATE'] <= future_date)
        ].copy()

        # Remove rows where all due dates are NaT (N/A)
        pending_list = pending_list.dropna(subset=['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE'], how='all')

        if not pending_list.empty:
            st.warning(f"Total {len(pending_list)} machines ki service agle {days_to_check} dinon mein pending hai.")
            
            # Download Button
            st.download_button("📥 Download This List (Excel)", to_excel(pending_list), f"Pending_List_{days_to_check}days.xlsx")
            
            # Formatting table for display
            display_df = pending_list[['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE', 'HMR Cal.']].copy()
            
            # Dates ko sundar dikhane ke liye formatting
            display_df['OIL DUE DATE'] = display_df['OIL DUE DATE'].apply(format_dt)
            display_df['AFC DUE DATE'] = display_df['AFC DUE DATE'].apply(format_dt)
            display_df['AOS DUE DATE'] = display_df['AOS DUE DATE'].apply(format_dt)
            
            st.dataframe(display_df.sort_values(by='CUSTOMER NAME'), use_container_width=True)
            
        else:
            st.success(f"Agle {days_to_check} dinon mein koi service pending nahi mili!")
            st.info("Tip: Agar list khali hai, toh slider ko badha kar 60 ya 90 din karke dekhein.")

else:
    st.error("Data load nahi ho pa raha hai. Check files on GitHub.")
