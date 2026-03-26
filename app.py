import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==============================
# 🔐 CLOUD CONFIG
# ==============================
URL = st.secrets["SUPABASE_URL"].strip()
KEY = st.secrets["SUPABASE_KEY"].strip()
supabase: Client = create_client(URL, KEY)

# ==============================
# ⚡ ROBUST SYNC ENGINE
# ==============================
def upload_master_data(df, tracker_type):
    # 1. Clean Duplicates in Excel (Fabrication ID must be unique)
    # Column names check karein jo aapke excel mein hain
    fab_col = 'Fabrication Number' if 'Fabrication Number' in df.columns else 'Fabrication'
    
    st.info(f"Checking for duplicates in {len(df)} records...")
    df_clean = df.drop_duplicates(subset=[fab_col], keep='first')
    
    diff = len(df) - len(df_clean)
    if diff > 0:
        st.warning(f"⚠️ {diff} Duplicate Fabrication IDs found and removed.")

    st.info(f"🚀 Uploading {len(df_clean)} unique records...")
    pb = st.progress(0)
    
    # Batch processing ki jagah stability ke liye single upsert with error handling
    for i, row in df_clean.iterrows():
        try:
            data = {
                "fabrication_id": str(row.get(fab_col, '')).strip(),
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": float(pd.to_numeric(row.get('Avg. Running', 0), errors='coerce') or 0),
                "current_hmr": float(pd.to_numeric(row.get('CURRENT HMR', 0), errors='coerce') or 0),
                "total_hours_dn": float(pd.to_numeric(row.get('MDA Total Hours', 0), errors='coerce') or 0),
                "last_service_date": str(pd.to_datetime(row.get('Last Call Date', '2024-01-01')).date()),
                "tracker_type": tracker_type
            }
            supabase.table("machines").upsert(data).execute()
        except Exception as e:
            st.error(f"❌ Error at row {i}: {e}")
            continue
            
        pb.progress((i + 1) / len(df_clean))
    
    st.success(f"✅ Sync Successful! {len(df_clean)} machines are now on Cloud.")

# --- Streamlit UI ---
st.title("⚡ ELGi Smart Sync (No Duplicates)")
m_file = st.file_uploader("Upload Master Data", type="xlsx")
t_type = st.selectbox("Select Type", ["DPSAC", "INDUSTRIAL"])

if m_file and st.button("Sync Master Data"):
    df_excel = pd.read_excel(m_file)
    upload_master_data(df_excel, t_type)
