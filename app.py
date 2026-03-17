import streamlit as st
import pandas as pd
import os

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# App Title
st.title("🛠️ ELGi Fabrication Service History")
st.markdown("Service Alerts aur Wrapped Comments ke saath updated version.")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "master.csv"
    s_file = "service.csv"
    
    if os.path.exists(m_file) and os.path.exists(s_file):
        # Master data aur Service data load karein
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
        # Data Filter
        m_info = master_df[master_df['Fabrication Number'] == selected_fab].iloc[0]

        # --- SECTION 1: SERVICE ALERTS (AGEING & HMR) ---
        st.divider()
        st.subheader("⚠️ Service Alerts")
        
        # Ageing Due Alert (Days)
        try:
            ageing = float(m_info.get('AGEING DUE', 100))
            if ageing <= 15 and ageing > 0:
                st.warning(f"🚨 DAYS ALERT: Is machine ki service {int(ageing)} dinon mein due hai!")
            elif ageing <= 0:
                st.error(f"🔴 OVERDUE BY DAYS: Service date nikal chuki hai! ({int(abs(ageing))} din pehle)")
        except:
            pass

        # HMR Due Alert (Hours)
        try:
            hmr_due = float(m_info.get('HMR DUE', 0))
            if hmr_due <= 100 and hmr_due > 0:
                st.warning(f"⚙️ HMR ALERT: Agli service sirf {int(hmr_due)} hours baad due hai!")
            elif hmr_due <= 0:
                st.error(f"🔴 OVERDUE BY HMR: Service hours exceed ho chuke hain! ({int(abs(hmr_due))} hours)")
        except:
            pass

        # --- SECTION 2: MACHINE & PARTS INFO ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("📋 Machine Basic Info")
            st.write(f"**Customer:** {m_info.get('Customer Name', 'N/A')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**Status:** {m_info.get('status', 'N/A')}")
            st.write(f"**Model:** {m_info.get('Model', 'N/A')}")

        with col2:
            st.info("📅 Parts Replacement (BN to BV)")
            # Columns BN to BV from your CSV
            important_cols = [
                'Oil R Date', 'AFC R Date', 'AFE R Date', 'MOF R Date', 
                'ROF R Date', 'AOS R Date', 'RGT R Date', '1500 kit R Date', 
                '3000 kit R Date', 'VK DATE'
            ]
            
            for col in important_cols:
                if col in m_info:
                    val = m_info[col]
                    if pd.isna(val) or val == 0 or val == "0" or str(val).lower() == "no service":
                        st.write(f"**{col}:** ⚪ N/A")
                    else:
                        st.write(f"**{col}:** ✅ {val}")

        # --- SECTION 3: SERVICE HISTORY (WRAP COMMENTS) ---
        st.divider()
        st.subheader(f"🕒 Full History: {selected_fab}")
        
        history = service_df[service_df['Fabrication Number'] == selected_fab].sort_values(by='Call Logged Date', ascending=False)
        
        if not history.empty:
            # Column configuration for wrapping text
            st.dataframe(
                history[['Call Logged Date', 'Call HMR', 'Service Engineer Comments']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Service Engineer Comments": st.column_config.TextColumn(
                        "Service Engineer Comments",
                        width="large",
                    )
                }
            )
        else:
            st.warning("Is Fabrication Number ke liye koi history nahi mili.")
else:
    st.error("Error: 'master.csv' aur 'service.csv' files nahi mili.")
