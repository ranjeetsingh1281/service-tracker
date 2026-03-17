import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# App Title
st.title("🛠️ ELGi Fabrication Service History")
st.markdown("Service Alerts aur Wrapped Comments (Mobile Friendly) ke saath.")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "master.csv"
    s_file = "service.csv"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_csv(m_file, low_memory=False)
        s_df = pd.read_csv(s_file, low_memory=False)
        # Date conversion for sorting
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

if master_df is not None:
    fab_list = sorted(master_df['Fabrication Number'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        m_info = master_df[master_df['Fabrication Number'] == selected_fab].iloc[0]

        # --- SECTION 1: SERVICE ALERTS ---
        st.divider()
        st.subheader("⚠️ Service Alerts")
        
        # Ageing & HMR Logic
        try:
            ageing = float(m_info.get('AGEING DUE', 100))
            if ageing <= 15 and ageing > 0:
                st.warning(f"🚨 DAYS ALERT: Service {int(ageing)} dinon mein due hai!")
            elif ageing <= 0:
                st.error(f"🔴 OVERDUE: {int(abs(ageing))} din pehle service due thi!")
        except: pass

        # --- SECTION 2: MACHINE & PARTS INFO ---
        col1, col2 = st.columns(2)
        with col1:
            st.info("📋 Machine Info")
            st.write(f"**Customer:** {m_info.get('Customer Name', 'N/A')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**Model:** {m_info.get('Model', 'N/A')}")

        with col2:
            st.info("📅 Parts Status (BN to BV)")
            important_cols = ['Oil R Date', 'AFC R Date', 'AFE R Date', 'MOF R Date', 'ROF R Date', 'AOS R Date', 'RGT R Date', '1500 kit R Date', '3000 kit R Date', 'VK DATE']
            for col in important_cols:
                if col in m_info:
                    val = m_info[col]
                    st.write(f"**{col}:** {val if pd.notna(val) and val != '0' else '⚪ N/A'}")

        # --- SECTION 3: SERVICE HISTORY (DESCENDING & WRAPPED) ---
        st.divider()
        st.subheader(f"🕒 Full History: {selected_fab}")
        
        # Filtering & Sorting (Descending Order)
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy()
        history = history.sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            st.write("Niche har date par click karein poora comment padhne ke liye:")
            
            for index, row in history.iterrows():
                # Display date in a readable format
                date_str = row['Call Logged Date'].strftime('%d-%b-%Y') if pd.notna(row['Call Logged Date']) else "N/A"
                
                # Using Expander for automatic text wrapping on mobile
                with st.expander(f"📅 {date_str} | ⚙️ HMR: {row['Call HMR']}"):
                    st.markdown(f"**Service Engineer Comments:**")
                    st.write(row['Service Engineer Comments'])
        else:
            st.warning("Is machine ke liye koi history nahi mili.")
else:
    st.error("Error: Files nahi mili.")
