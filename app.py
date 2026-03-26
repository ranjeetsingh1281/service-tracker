import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="ELGi Service Tracker", layout="wide", page_icon="🚜")

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loader (Direct from GitHub Files) ---
@st.cache_data
def load_data():
    try:
        # 1. Master Data Load
        m_df = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        # 2. History Data Load
        h_df = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        
        # Column names se extra spaces hatana
        m_df.columns = m_df.columns.str.strip()
        h_df.columns = h_df.columns.str.strip()
        
        return m_df, h_df
    except Exception as e:
        st.error(f"⚠️ Error: Files nahi mil rahi hain! Check karein ki GitHub par 'Master_Data.xlsx' aur 'Service_Details.xlsx' uploaded hain.")
        return None, None

# --- Main App Logic ---
st.title("🚜 ELGi Smart Service Tracker (Offline Mode)")
st.write("Current Status: **Excel Database Active** ✅")

master, history = load_data()

if master is not None:
    # Sidebar Search
    st.sidebar.header("🔍 Search Machine")
    search_id = st.sidebar.text_input("Enter Fabrication Number", placeholder="e.g. 12345")

    if search_id:
        # Detect Fabrication Column
        fab_col = next((c for c in master.columns if 'Fabrication' in c), None)
        
        if fab_col:
            # Finding exact match
            res = master[master[fab_col].astype(str) == str(search_id).strip()]
            
            if not res.empty:
                machine = res.iloc[0]
                st.success(f"✅ Machine Found: **{machine.get('Customer', 'N/A')}**")
                
                # --- Quick Metrics ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current HMR", f"{machine.get('CURRENT HMR', 0)} hrs")
                m2.metric("Category", machine.get('Category', 'N/A'))
                m3.metric("Status", machine.get('Unit Status', 'Active'))
                m4.metric("Avg Running", f"{machine.get('Avg. Running', 0)} hrs")

                # --- Service History Section ---
                st.divider()
                st.subheader("📜 Detailed Service History")
                
                if history is not None:
                    h_fab_col = next((c for c in history.columns if 'Fabrication' in c), None)
                    if h_fab_col:
                        # Filter history for this machine
                        h_res = history[history[h_fab_col].astype(str) == str(search_id).strip()]
                        if not h_res.empty:
                            st.dataframe(h_res, use_container_width=True)
                        else:
                            st.info("Is machine ki koi purani history Service_Details.xlsx mein nahi mili.")
            else:
                st.error("❌ Fabrication Number match nahi hua. Dubara check karein.")
        else:
            st.error("Excel mein 'Fabrication' column nahi mil raha.")
    else:
        st.info("💡 Sidebar mein Fabrication Number daalein machine ki history dekhne ke liye.")

# Footer Check
st.sidebar.markdown("---")
st.sidebar.caption("💡 Tip: Excel file update karne par GitHub par 'Commit' zaroori hai.")
