import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DYNAMIC FILE LOADER ---
@st.cache_data
def load_data():
    folder_files = os.listdir('.')
    def find_file(target):
        for f in folder_files:
            if f.lower() == target.lower(): return f
        return None

    m_name = find_file("Master_Data.xlsx")
    s_name = find_file("Service_Details.xlsx")
    f_name = find_file("Active_FOC.xlsx")
    
    if not m_name or not s_name or not f_name:
        return None, None, None, [f for f in ["Master_Data.xlsx", "Service_Details.xlsx", "Active_FOC.xlsx"] if not find_file(f)]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers (Invisible spaces hatana)
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        
        # FOC Headers Fix for Duplicates
        f_cols = []
        for i, col in enumerate(f_df.columns):
            c_name = str(col).strip()
            if c_name in f_cols:
                f_cols.append(f"{c_name}_{i}")
            else:
                f_cols.append(c_name)
        f_df.columns = f_cols
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Error or Missing Files: {missing}")
    st.stop()

# --- APP NAVIGATION ---
st.sidebar.title("📌 Menu")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer", options=["All"] + customer_list)
    
    filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    selected_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(filtered_df['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = filtered_df[filtered_df['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # --- SECTION 1: C1 to C4 DETAILS ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**HMR Cal:** {m_info.get('HMR Cal.', 'N/A')}")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")

        # --- SECTION 2: FOC PARTS HISTORY (SMART MAPPING) ---
        st.divider()
        st.subheader("🎁 FOC Parts History")
        
        # Fabrication column check (Handle with and without dot)
        foc_fab_col = None
        for col in ['FABRICATION NO', 'FABRICATION NO.', 'Fabrication No']:
            if col in foc_df.columns:
                foc_fab_col = col
                break
        
        if foc_fab_col:
            foc_match = foc_df[foc_df[foc_fab_col].astype(str) == selected_fab].copy()
            
            if not foc_match.empty:
                # Sirf wahi columns jo dikhane hain
                target_cols = ['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']
                # Check agar columns exist karte hain
                valid_cols = [c for c in target_cols if c in foc_match.columns]
                
                st.dataframe(foc_match[valid_cols], use_container_width=True, hide_index=True)
            else:
                st.info("Is machine ke liye koi FOC record nahi mila.")
        else:
            st.error("FOC file mein Fabrication column nahi mila!")

        # --- SECTION 3: SERVICE HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                dt = format_dt(row.get('Call Logged Date'))
                header = f"📅 {dt} | ⚙️ {row.get('Call HMR','N/A')} HMR | 🛠️ {row.get('Call Type','N/A')}"
                with st.expander(header):
                    st.write(f"**Engineer:** {row.get('Service Engineer', 'N/A')}")
                    st.info(row.get('Service Engineer Comments', 'N/A'))
        else:
            st.warning("No history records.")

elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    st.info("Action buttons logic yahan continue rahega.")
