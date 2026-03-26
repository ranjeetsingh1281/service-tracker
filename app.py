import streamlit as st
import pandas as pd
import os

# --- Page Setup ---
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# --- Function to Load Data Safely ---
@st.cache_data
def load_all_data():
    master_path = "Master_Data.xlsx"
    history_path = "Service_Details.xlsx"
    
    # Check if files exist on GitHub
    if not os.path.exists(master_path) or not os.path.exists(history_path):
        return None, None
        
    try:
        # Loading Excel Files
        m_df = pd.read_excel(master_path, engine='openpyxl')
        h_df = pd.read_excel(history_path, engine='openpyxl')
        
        # Column names clean karna
        m_df.columns = m_df.columns.str.strip()
        h_df.columns = h_df.columns.str.strip()
        
        return m_df, h_df
    except Exception as e:
        st.error(f"Excel Load Error: {e}")
        return None, None

# --- Main Dashboard ---
st.title("🚜 ELGi Smart Service Tracker")
st.info("Status: Running on Local Excel Database (GitHub) ✅")

master, history = load_all_data()

if master is not None:
    # Search Box
    search_id = st.text_input("🔢 Enter Fabrication Number (e.g. 12345)", key="search")

    if search_id:
        # Detect Fabrication Column in Master
        fab_col = next((c for c in master.columns if 'Fabrication' in str(c)), None)
        
        if fab_col:
            # Find the machine
            match = master[master[fab_col].astype(str).str.strip() == str(search_id).strip()]
            
            if not match.empty:
                row = match.iloc[0]
                st.success(f"✅ Machine Found: {row.get('Customer', 'Unknown')}")
                
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current HMR", f"{row.get('CURRENT HMR', 0)} hrs")
                m2.metric("Category", row.get('Category', 'N/A'))
                m3.metric("Status", row.get('Unit Status', 'Active'))
                m4.metric("Avg Running", f"{row.get('Avg. Running', 0)} hrs")

                # --- History Section ---
                st.subheader("🕒 Service History")
                h_fab_col = next((c for c in history.columns if 'Fabrication' in str(c)), None)
                
                if h_fab_col:
                    h_match = history[history[h_fab_col].astype(str).str.strip() == str(search_id).strip()]
                    if not h_match.empty:
                        st.dataframe(h_match, use_container_width=True)
                    else:
                        st.warning("No history found in Service_Details.xlsx for this machine.")
            else:
                st.error("❌ Fabrication Number match nahi hua. Dubara check karein.")
else:
    st.error("🚨 Files load nahi ho rahi hain. GitHub par 'Master_Data.xlsx' check karein.")
