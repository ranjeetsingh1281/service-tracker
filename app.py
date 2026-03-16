Python 3.9.13 (tags/v3.9.13:6de2ca5, May 17 2022, 16:36:42) [MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# App Title
st.title("🛠️ ELGi Fabrication Service History")
st.markdown("Yeh app automatic data load karti hai.")

# Data Load Function
@st.cache_data
def load_data():
    # File names (GitHub folder mein yahi naam rakhein)
    m_file = "master.csv"
    s_file = "service.csv"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_csv(m_file)
        s_df = pd.read_csv(s_file)
        return m_df, s_df
    else:
        return None, None

master_df, service_df = load_data()

if master_df is not None:
    # Fabrication Number Selection
    fab_list = sorted(master_df['Fabrication Number'].unique().astype(str))
    selected_fab = st.selectbox("🔍 Search Fabrication Number", options=["Select Number"] + fab_list)

    if selected_fab != "Select Number":
        # Split screen into two parts
        col1, col2 = st.columns(2)
        
        # Machine Details
        m_info = master_df[master_df['Fabrication Number'] == selected_fab].iloc[0]
        
        with col1:
            st.info("📋 Machine Info")
            st.write(f"**Customer:** {m_info.get('Customer Name', 'N/A')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**Status:** {m_info.get('status', 'N/A')}")

        with col2:
            st.info("📅 Replacement Dates")
            # Jo columns humne lookup kiye thhe
            dates = ['Oil R Date', 'AFC R Date', 'AFE R Date', 'AOS R Date']
            for d in dates:
                if d in m_info:
                    st.write(f"**{d}:** {m_info[d]}")

        # Service History
        st.divider()
        st.subheader(f"🕒 Full History: {selected_fab}")
        history = service_df[service_df['Fabrication Number'] == selected_fab].sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            st.dataframe(history[['Call Logged Date', 'Call HMR', 'Service Engineer Comments']], use_container_width=True)
        else:
            st.warning("Koi service history nahi mili.")
else:
    st.error("Error: 'master.csv' aur 'service.csv' files nahi mili. Inhein GitHub repository mein upload karein.")