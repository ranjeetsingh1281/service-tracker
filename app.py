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
# ⚡ DUPLICATE-PROOF SYNC
# ==============================
def start_sync(df, t_type):
    # 1. Column detection
    fab_col = next((c for c in df.columns if 'Fabrication' in c), None)
    
    if not fab_col:
        st.error("❌ Excel mein 'Fabrication Number' column nahi mila!")
        return

    # 2. Duplicate Removal Logic
    st.info(f"Checking {len(df)} records for duplicates...")
    df_unique = df.drop_duplicates(subset=[fab_col], keep='first')
    
    removed = len(df) - len(df_unique)
    if removed > 0:
        st.warning(f"⚠️ {removed} Duplicate IDs mile aur unhe hata diya gaya.")

    # 3. Uploading Unique Records
    st.info(f"🚀 Uploading {len(df_unique)} Unique Records...")
    pb = st.progress(0)
    
    for i, row in df_unique.iterrows():
        try:
            payload = {
                "fabrication_id": str(row.get(fab_col, '')).strip(),
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": float(pd.to_numeric(row.get('Average Running Hours', row.get('Avg. Running', 0)), errors='coerce') or 0),
                "current_hmr": float(pd.to_numeric(row.get('Current Hours', row.get('CURRENT HMR', 0)), errors='coerce') or 0),
                "total_hours_dn": float(pd.to_numeric(row.get('Total Hours', row.get('MDA Total Hours', 0)), errors='coerce') or 0),
                "last_service_date": str(pd.to_datetime(row.get('Last Call Date', '2024-01-01')).date()),
                "tracker_type": t_type
            }
            # Single row upload taaki koi duplicate conflict na ho
            supabase.table("machines").upsert(payload).execute()
        except Exception as e:
            st.error(f"Row {i} Error: {e}")
            continue
            
        pb.progress((i + 1) / len(df_unique))
    
    st.success(f"🏁 DONE! {len(df_unique)} Unique records synced successfully.")

# --- UI ---
st.title("⚡ ELGi Smart Sync (No Duplicates)")
uploaded_file = st.file_uploader("Upload Master Data", type="xlsx")
t_choice = st.selectbox("Type", ["DPSAC", "INDUSTRIAL"])

if uploaded_file and st.button("🚀 Start Safe Sync"):
    df_excel = pd.read_excel(uploaded_file)
    start_sync(df_excel, t_choice)
