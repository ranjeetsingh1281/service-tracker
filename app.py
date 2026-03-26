import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="ELGi Service Tracker (Local)", layout="wide", page_icon="🛠️")

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loader (Direct from GitHub Files) ---
@st.cache_data(ttl=600) # 10 min cache taaki bar-bar load na ho
def load_data():
    try:
        # Aapki GitHub par uploaded files ke naam yahan sahi hone chahiye
        df_master = pd.read_excel("Master_Data.xlsx")
        df_history = pd.read_excel("Service_Details.xlsx")
        
        # Cleaning column names (Spaces hatane ke liye)
        df_master.columns = df_master.columns.str.strip()
        df_history.columns = df_history.columns.str.strip()
        
        return df_master, df_history
    except Exception as e:
        st.error(f"⚠️ Excel File Load Nahi Hui: {e}")
        st.info("💡 Tip: Check kijiye ki 'Master_Data.xlsx' GitHub repository mein hai ya nahi.")
        return None, None

# --- Main App ---
st.title("🚜 ELGi Smart Service Tracker")
st.write("Current Database: **Local Excel (GitHub)** ✅")

master, history = load_data()

if master is not None:
    # Sidebar Filters
    st.sidebar.header("🔍 Search & Filter")
    t_choice = st.sidebar.selectbox("Select Tracker Type", ["All", "DPSAC", "INDUSTRIAL"])
    
    # Filter by Type
    if t_choice != "All":
        # Maan lete hain column ka naam 'Type' hai, change as per your excel
        if 'Type' in master.columns:
            master = master[master['Type'] == t_choice]

    # Search Box
    search_query = st.text_input("🔢 Enter Fabrication Number (e.g. 12345)", placeholder="Type number and press Enter...")

    if search_query:
        # Fabrication Number column detect karna
        fab_col = next((c for c in master.columns if 'Fabrication' in c), None)
        
        if fab_col:
            # Match finding
            res = master[master[fab_col].astype(str) == str(search_query).strip()]
            
            if not res.empty:
                row = res.iloc[0]
                st.success(f"✅ Machine Found: **{row.get('Customer', 'Unknown')}**")
                
                # Metrics Row
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Current HMR", f"{row.get('CURRENT HMR', 0)} hrs")
                c2.metric("Category", row.get('Category', 'N/A'))
                c3.metric("Status", row.get('Unit Status', 'Active'))
                c4.metric("Avg Running", f"{row.get('Avg. Running', 0)} hrs")

                # --- Service History Section ---
                st.divider()
                st.subheader("🕒 Service History & Visit Details")
                
                if history is not None:
                    h_fab_col = next((c for c in history.columns if 'Fabrication' in c), None)
                    if h_fab_col:
                        h_res = history[history[h_fab_col].astype(str) == str(search_query).strip()]
                        if not h_res.empty:
                            st.dataframe(h_res, use_container_width=True)
                        else:
                            st.warning("Is machine ki koi purani history nahi mili.")
            else:
                st.error("❌ Machine nahi mili. Please check Fabrication Number.")
        else:
            st.error("Excel mein 'Fabrication' column nahi mila!")

else:
    st.warning("Pehle GitHub par 'Master_Data.xlsx' upload kijiye.")

# --- Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.write("Last Sync: **Live from Excel**")
