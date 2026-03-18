import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DATA LOAD FUNCTION WITH ERROR TRACKING ---
@st.cache_data
def load_data():
    files = {
        "Master": "Master_Data.xlsx",
        "Service": "Service_Details.xlsx",
        "FOC": "Active_FOC.xlsx"
    }
    
    missing_files = []
    for key, name in files.items():
        if not os.path.exists(name):
            missing_files.append(name)
            
    if missing_files:
        return None, None, None, missing_files

    # Agar saari files hain, tab load karein
    m_df = pd.read_excel(files["Master"], engine='openpyxl')
    s_df = pd.read_excel(files["Service"], engine='openpyxl')
    f_df = pd.read_excel(files["FOC"], engine='openpyxl')
    
    # Clean Headers
    m_df.columns = [str(c).strip() for c in m_df.columns]
    s_df.columns = [str(c).strip() for c in s_df.columns]
    f_df.columns = [str(c).strip() for c in f_df.columns]
    
    return m_df, s_df, f_df, []

# Helper Functions
def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

master_df, service_df, foc_df, missing = load_data()

# --- MISSING FILE WARNING ---
if missing:
    st.error(f"❌ Files Not Found: {', '.join(missing)}")
    st.info("Check karein ki GitHub repository mein ye files exact isi naam (Capital/Small letters) ke saath uploaded hain.")
    st.stop() # App ko yahi rok dega jab tak file na mile

# --- AGAR FILES MIL GAYI TOH BAAKI CODE ---
if master_df is not None:
    st.sidebar.title("📌 Menu")
    page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

    if page == "Machine Tracker":
        st.title("🛠️ Machine Tracker Pro")
        
        # Customer Filter
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("1. Customer", options=["All"] + customer_list)
        
        filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
        
        # Fabrication Filter
        fab_list = sorted(filtered_df['Fabrication No'].unique().astype(str))
        selected_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + fab_list)

        if selected_fab != "Select":
            m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
            
            # --- DETAILS C1 to C4 ---
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Machine Info")
                st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
                st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.')}")

            # --- FOC SECTION ---
            st.divider()
            st.subheader("🎁 FOC Parts History")
            # FOC file ke fabrication column ka naam 'FABRICATION NO.' hai
            foc_match = foc_df[foc_df['FABRICATION NO.'] == selected_fab].copy()
            if not foc_match.empty:
                st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
            else:
                st.info("No FOC records found.")

            # --- SERVICE HISTORY ---
            st.divider()
            st.subheader("🕒 Service History")
            history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
            if not history.empty:
                for _, row in history.iterrows():
                    dt = format_dt(row.get('Call Logged Date'))
                    header = f"📅 {dt} | ⚙️ {row.get('Call HMR', 'N/A')} HMR | 🛠️ {row.get('Call Type', 'N/A')}"
                    with st.expander(header):
                        st.info(row.get('Service Engineer Comments', 'No comments.'))
            else:
                st.warning("No service history found.")

    elif page == "Service Pending List":
        st.title("⏳ BIS Pending List")
        # (Yahan aapka BIS logic rahega...)
