import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# App Title
st.title("🛠️ ELGi Fabrication Service History")
st.markdown("Yeh app BN se BV tak ke saare parts replacement aur due data dikhati hai.")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "master.csv"
    s_file = "service.csv"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        # Master data load karte waqt column types handle karein
        m_df = pd.read_csv(m_file, low_memory=False)
        s_df = pd.read_csv(s_file, low_memory=False)
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

if master_df is not None:
    # Fabrication Number Selection
    fab_list = sorted(master_df['Fabrication Number'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        col1, col2 = st.columns(2)
        
        # Machine Details filter
        m_info = master_df[master_df['Fabrication Number'] == selected_fab].iloc[0]
        
        with col1:
            st.info("📋 Basic Machine Info")
            st.write(f"**Customer:** {m_info.get('Customer Name', 'N/A')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**Status:** {m_info.get('status', 'N/A')}")
            st.write(f"**Model:** {m_info.get('Model', 'N/A')}")

        with col2:
            st.info("📅 Parts Replacement & Due Status")
            # Column BN se BV tak ke columns ki list
            important_cols = [
                'Oil R Date', 'AFC R Date', 'AFE R Date', 'MOF R Date', 
                'ROF R Date', 'AOS R Date', 'RGT R Date', '1500 kit R Date', 
                '3000 kit R Date', 'VK DATE', 'HMR DUE', 'AGEING DUE'
            ]
            
            for col in important_cols:
                if col in m_info:
                    val = m_info[col]
                    # Check if value is empty or 0
                    if pd.isna(val) or val == 0 or val == "0" or val == "No Service":
                        st.write(f"**{col}:** ⚪ N/A")
                    else:
                        st.write(f"**{col}:** ✅ {val}")

        # Service History Section
        st.divider()
        st.subheader(f"🕒 Full History: {selected_fab}")
        
        # Service history fetch karein
        history = service_df[service_df['Fabrication Number'] == selected_fab].sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            st.dataframe(history[['Call Logged Date', 'Call HMR', 'Service Engineer Comments']], use_container_width=True)
        else:
            st.warning("Is Fabrication Number ke liye koi service history record nahi mila.")
else:
    st.error("Error: 'master.csv' aur 'service.csv' files repository mein nahi mili.")
