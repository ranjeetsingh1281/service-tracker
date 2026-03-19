import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- SMART FILE LOADER ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(target_base):
        # Yeh function .xlsx aur .xlxs dono formats check karega
        for f in folder_files:
            if f.lower().startswith(target_base.lower()):
                return f
        return None

    m_name = find_file("Master_Data")
    m_od_name = find_file("Master_OD_Data")
    s_name = find_file("Service_Details")
    f_name = find_file("Active_FOC")
    
    try:
        m_df = pd.read_excel(m_name, engine='openpyxl') if m_name else pd.DataFrame()
        m_od_df = pd.read_excel(m_od_name, engine='openpyxl') if m_od_name else pd.DataFrame()
        s_df = pd.read_excel(s_name, engine='openpyxl') if s_name else pd.DataFrame()
        f_df = pd.read_excel(f_name, engine='openpyxl') if f_name else pd.DataFrame()
        
        # Clean Headers
        for df in [m_df, m_od_df, s_df, f_df]:
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
        
        return m_df, m_od_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

master_df, master_od_df, service_df, foc_df, errors = load_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Dashboard:", ["Standard Tracker", "OD Machine Tracker", "FOC Tracker List"])

# Mapping for OD 9 Parts
od_parts = {
    'Oil': {'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'Valvekit': {'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'date': 'MDA PF R DATE', 'due': 'PF DUE DATE'},
    'FF': {'date': 'MDA FF R DATE', 'due': 'FF DUE DATE'},
    'CF': {'date': 'MDA CF R DATE', 'due': 'CF DUE DATE'}
}

# --- OD MACHINE TRACKER LOGIC ---
if page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker")
    if master_od_df.empty:
        st.error("❌ Master_OD_Data detect nahi hui. Kripya GitHub par file name check karein.")
    else:
        cust_list = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("1. Customer", options=["All"] + cust_list)
        df_f = master_od_df if sel_cust == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust]
        
        sel_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()))

        if sel_fab != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
            
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row.get('Customer Name')}")
                st.write(f"**Model:** {row.get('Model', 'N/A')}")
                st.write(f"**Sub Group:** {row.get('Product Sub Group', 'N/A')}")
                st.write(f"**Category:** {row.get('Category', 'N/A')}")
                st.write(f"**Location:** {row.get('Location', 'N/A')}")

            with c2:
                st.info("📅 Replacement (9 Parts)")
                for label, cols in od_parts.items():
                    st.write(f"**{label}:** {format_dt(row.get(cols['date']))}")

            with c3:
                st.info("⚙️ Live Tracking")
                st.write(f"**Avg Hrs/Day:** {row.get('MDA AVG Running Hours Per Day', 'N/A')}")
                st.write(f"**HMR Date:** {format_dt(row.get('MDA HMR Date'))}")
                st.write(f"**Total Hours:** {row.get('MDA Total Hours', 'N/A')}")

            with c4:
                st.error("🚨 DUE DATES (9 Parts)")
                for label, cols in od_parts.items():
                    st.write(f"**{label} Due:** {format_dt(row.get(cols['due']))}")

            # History & FOC (Common Logic)
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🎁 FOC History")
                foc_match = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_fab]
                st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']] if not foc_match.empty else pd.DataFrame(), hide_index=True)
            
            with col_b:
                st.subheader("🕒 Service History")
                hist = service_df[service_df['Fabrication Number'].astype(str) == sel_fab].sort_values(by='Call Logged Date', ascending=False)
                if not hist.empty:
                    for _, s_row in hist.head(5).iterrows():
                        with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | {s_row.get('Call Type', 'N/A')}"):
                            st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                            st.info(s_row.get('Service Engineer Comments', 'N/A'))

# --- REMAINDING PAGES (Standard Tracker, etc.) ---
elif page == "Standard Tracker":
    st.title("🛠️ Standard Machine Tracker")
    st.write("Yahan aapka purana Master_Data load hoga.")
    # (Purana logic yahan add karein...)

elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker")
    st.dataframe(foc_df, use_container_width=True)
