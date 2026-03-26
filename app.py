import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="ELGi Service Tracker (Excel)", layout="wide")

# --- Data Loader (Direct from Excel) ---
@st.cache_data
def load_excel_data():
    try:
        # Aapki files ke naam yahan check kar lijiye
        df_master = pd.read_excel("Master_Data.xlsx")
        df_history = pd.read_excel("Service_Details.xlsx")
        return df_master, df_history
    except Exception as e:
        st.error(f"Excel File Missing: {e}")
        return None, None

# --- UI ---
st.title("🛠️ ELGi Service Tracker (Local Excel Mode)")

master, history = load_excel_data()

if master is not None:
    # Search Box
    search_id = st.text_input("🔍 Search Fabrication Number (e.g. 12345)")
    
    if search_id:
        # Filter Master Data
        machine = master[master['Fabrication Number'].astype(str) == search_id]
        
        if not machine.empty:
            st.success(f"Machine Found: {machine.iloc[0]['Customer']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current HMR", machine.iloc[0]['CURRENT HMR'])
            col2.metric("Category", machine.iloc[0]['Category'])
            col3.metric("Unit Status", machine.iloc[0]['Unit Status'])
            
            # Show History
            st.subheader("🕒 Service History")
            machine_history = history[history['Fabrication Number'].astype(str) == search_id]
            st.table(machine_history)
        else:
            st.warning("Machine nahi mili. Please check Fabrication Number.")
else:
    st.info("💡 Tip: 'Master_Data.xlsx' aur 'Service_Details.xlsx' ko GitHub repository mein upload karein.")
