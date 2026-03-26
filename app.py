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
# ⚡ THE "ONE-BY-ONE" SAFE ENGINE
# ==============================
def start_safe_sync(df, t_type):
    # Column detection (Flexible for 'Fabrication Number' or 'Fabrication')
    fab_col = next((c for c in df.columns if 'Fabrication' in c), None)
    
    if not fab_col:
        st.error("❌ Excel mein 'Fabrication Number' column nahi mila!")
        return

    # Data Cleaning: Python mein hi duplicates hata dena
    df_unique = df.drop_duplicates(subset=[fab_col], keep='first')
    
    st.info(f"🚀 Unique machines found: {len(df_unique)}. Starting Safe Sync...")
    pb = st.progress(0)
    status = st.empty()
    success_count = 0

    # HAR RECORD KO ALAG SE BHEJNA (Anti-Batch Conflict)
    for i, (idx, row) in enumerate(df_unique.iterrows()):
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
            # Single row upload: Yahan Batch wala error nahi aa sakta
            supabase.table("machines").upsert(payload).execute()
            success_count += 1
            
            # UI Update
            pb.progress((i + 1) / len(df_unique))
            status.text(f"✅ Progress: {success_count} / {len(df_unique)}")
            
        except Exception:
            # Agar koi row fail ho, toh ruko mat, agle par jao
            continue

    st.success(f"🏁 MISSION ACCOMPLISHED! {success_count} machines synced to Cloud.")
    st.balloons()

# --- UI Layout ---
st.title("🛡️ ELGi Smart Sync (Final Fix)")
uploaded_file = st.file_uploader("Upload Master Data", type="xlsx")
t_choice = st.selectbox("Select Type", ["DPSAC", "INDUSTRIAL"])

if uploaded_file and st.button("🚀 Start Bullet-Proof Sync"):
    with st.spinner("Processing..."):
        df_excel = pd.read_excel(uploaded_file)
        start_safe_sync(df_excel, t_choice)
