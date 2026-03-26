import streamlit as st
import pandas as pd
import os

# --- Page Setup ---
st.set_page_config(page_title="ELGi Service Tracker", layout="wide")

# --- Function to Load Data (Direct from GitHub Files) ---
@st.cache_data
def load_excel_db():
    # In files ka naam wahi hona chahiye jo GitHub par hai
    m_path = "Master_Data.xlsx"
    h_path = "Service_Details.xlsx"
    
    if os.path.exists(m_path) and os.path.exists(h_path):
        try:
            m_df = pd.read_excel(m_path, engine='openpyxl').fillna("N/A")
            h_df = pd.read_excel(h_path, engine='openpyxl').fillna("N/A")
            # Cleaning columns
            m_df.columns = m_df.columns.str.strip()
            h_df.columns = h_df.columns.str.strip()
            return m_df, h_df
        except Exception as e:
            st.error(f"Error reading Excel: {e}")
            return None, None
    return None, None

# --- UI Layout ---
st.title("🚜 ELGi Smart Service Tracker")
st.subheader("Database Mode: Excel Direct (No Cloud) ✅")

master, history = load_excel_db()

if master is not None:
    # --- SEARCH SECTION ---
    st.divider()
    search_id = st.text_input("🔍 Enter Fabrication Number (e.g. 12345)", placeholder="Type and press Enter...")

    if search_id:
        # Detect Fabrication Column
        fab_col = next((c for c in master.columns if 'Fabrication' in str(c)), None)
        
        if fab_col:
            # Find Match
            res = master[master[fab_col].astype(str).str.strip() == str(search_id).strip()]
            
            if not res.empty:
                row = res.iloc[0]
                st.success(f"✅ Customer: **{row.get('Customer', 'Unknown')}**")
                
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current HMR", f"{row.get('CURRENT HMR', 0)} hrs")
                m2.metric("Category", row.get('Category', 'N/A'))
                m3.metric("Status", row.get('Unit Status', 'Active'))
                m4.metric("Avg Running", f"{row.get('Avg. Running', 0)} hrs")

                # --- History Section ---
                st.divider()
                st.subheader("🕒 Service History Details")
                h_fab_col = next((c for c in history.columns if 'Fabrication' in str(c)), None)
                
                if h_fab_col:
                    h_res = history[history[h_fab_col].astype(str).str.strip() == str(search_id).strip()]
                    if not h_res.empty:
                        st.dataframe(h_res, use_container_width=True)
                    else:
                        st.info("Is machine ki koi history history file mein nahi mili.")
            else:
                st.error("❌ Fabrication Number match nahi hua. Excel mein check karein.")
else:
    st.warning("🚨 Files 'Master_Data.xlsx' aur 'Service_Details.xlsx' GitHub par nahi mili!")
