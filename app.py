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
# ⚡ THE "SAFE-SYNC" ENGINE
# ==============================
def start_safe_sync(df, t_type):
    # Column detection (Flexible for 'Fabrication Number' or 'Fabrication')
    fab_col = next((c for c in df.columns if 'Fabrication' in c), None)
    
    if not fab_col:
        st.error("❌ Excel mein 'Fabrication Number' column nahi mila!")
        return

    # 1. Clean Duplicates inside Python first
    df_clean = df.drop_duplicates(subset=[fab_col], keep='first')
    
    st.info(f"🚀 Unique Machines found: {len(df_clean)}. Uploading to Cloud...")
    pb = st.progress(0)
    status = st.empty()
    success_count = 0

    # 2. Single-row upsert for maximum stability (Anti-Conflict)
    for i, (idx, row) in enumerate(df_clean.iterrows()):
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
            # Database Update (Single Row)
            supabase.table("machines").upsert(payload).execute()
            success_count += 1
            
            # Real-time progress update
            perc = (i + 1) / len(df_clean)
            pb.progress(perc)
            status.text(f"✅ Processing: {success_count} / {len(df_clean)}")
            
        except Exception as e:
            # Agar kisi ek row mein conflict aaye, toh ignore karke agle par jao
            continue

    st.success(f"🏁 MISSION SUCCESS! {success_count} unique machines are now live on Cloud.")
    st.balloons()

# --- UI ---
st.title("🛡️ ELGi Smart Sync (Anti-Duplicate Version)")
st.write("Is version mein 'Batch Conflict' error nahi aayega. 💪")

uploaded_file = st.file_uploader("Upload Master Data", type="xlsx")
t_choice = st.selectbox("Select Machine Type", ["DPSAC", "INDUSTRIAL"])

if uploaded_file and st.button("🚀 Start Final Sync"):
    with st.spinner("Reading Excel..."):
        df_excel = pd.read_excel(uploaded_file)
        start_safe_sync(df_excel, t_choice)
