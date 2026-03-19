import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

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
        return None, None, None, ["Files Missing"]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

# --- EXPORT TOOLS ---
def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Files Missing: {missing}"); st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List","FOC Tracker List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer Select Karein", options=["All"] + customer_list)
    cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    # MAIN METRICS
    st.subheader(f"📊 Dashboard Summary: {selected_customer}")
    m1, m2, m3 = st.columns(3)
    t_u = len(cust_filtered)
    n_w = len(cust_filtered[cust_filtered['Warranty Type'].astype(str).str.contains('Non', na=False, case=False)])
    m1.metric("Total Units", t_u)
    m2.metric("In Warranty", t_u - n_w)
    m3.metric("Non-Warranty", n_w)

    # --- NAYA UPDATE: CATEGORY WISE UNIT COUNT ---
    st.write("---")
    st.markdown("#### 📂 Category Wise Unit Count")
    if 'Category' in cust_filtered.columns:
        cat_counts = cust_filtered['Category'].value_counts()
        # Displaying in 4 columns for better look
        cat_cols = st.columns(4)
        for i, (cat_name, count) in enumerate(cat_counts.items()):
            with cat_cols[i % 4]:
                st.write(f"🔹 **{cat_name}:** `{count}`")
    else:
        st.warning("Master Data mein 'Category' column nahi mila. Kripya check karein.")
    
    st.divider()

    # Fabrication Selection
    selected_fab = st.sidebar.selectbox("2. Fabrication No Select Karein", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
        
        # --- MACHINE DETAILS (C1 to C4) ---
        c1, c2, c3, c4 = st.columns(4)
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

        with c1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**Location:** {m_info.get('Location', 'N/A')}")
            st.write(f"**Avg. Running Hrs:** {m_info.get('MDA AVG Running Hours Per Day', 'N/A')}👈")
            st.write(f"**Current Load HMR (Cal.):** {CURRENT LOAD HMR}👈")
            st.write(f"**Current Unload HMR (Cal.):** {CURRENT UNLOAD HMR}👈")
            st.write(f"**Last Call HMR:** {Last Sch HMR}")
            st.write(f"**Last Call HMR Date:** {format_dt(m_info.get('Last Sch Date'))}")
            st.write(f"**Hours since Last Service:** {int(elapsed_hours)}👈")
            
        with c2:
            st.info("📅 Replacement")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AFE R-Date:** {format_dt(m_info.get('Air filter Engine Replaced Date'))}")
            st.write(f"**MOF R-Date:** {format_dt(m_info.get('Main Oil filter Replaced Date'))}")
            st.write(f"**ROF R-Date:** {format_dt(m_info.get('Return Oil filter Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
            st.write(f"**Greasing R-Date:** {format_dt(m_info.get('Greasing Done Date'))}")
            st.write(f"**1500 Kit R-Date:** {format_dt(m_info.get('1500 Valve kit Replaced Date'))}")
            st.write(f"**3000 Kit R-Date:** {format_dt(m_info.get('3000 Valve kit Replaced Date'))}")
            
        with c3:
            st.info("⚙️ Live Remaining")
            # Safe remaining calculation
            for col, lbl in [('HMR - Oil remaining', 'Oil'), ('Air filter replaced - Compressor Remaining Hours', 'AFC'),
                ('Air filter replaced - Engine Remaining Hours', 'AFE'),
                ('Main Oil filter Remaining Hours' 'MOF'),
                ('Return Oil filter Remaining Hours', 'ROF'),('HMR - Separator remaining', 'AOS'), ('HMR - Motor regressed remaining', 'Greasing'),
                ('1500 Valve kit Remaining Hours', '1500 Kit'),
                ('3000 Valve kit Remaining Hours', '3000 Kit']
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce')
                rem = int(val - elapsed) if not pd.isna(val) else 0
                st.write(f"**{lbl}:** {rem} Hrs" if rem > 0 else f"**{lbl}:** 🚨 {rem} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AFE Due:** {format_dt(m_info.get('AFE DUE DATE'))}")
            st.write(f"**MOF Due:** {format_dt(m_info.get('MOF DUE DATE'))}")
            st.write(f"**ROF Due:** {format_dt(m_info.get('ROF DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")
            st.write(f"**Greasing Due:** {format_dt(m_info.get('RGT DUE DATE'))}")
            st.write(f"**1500 Kit Due:** {format_dt(m_info.get('1500 KIT DUE DATE'))}")
            st.write(f"**3000 Kit Due:** {format_dt(m_info.get('3000 KIT DUE DATE'))}")

        # Service History Expanders
        st.divider(); st.subheader("🕒 Service History")
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        if not history.empty:
            for _, row in history.iterrows():
                with st.expander(f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR"):
                    st.write(f"**Type:** {row.get('Call Type', 'N/A')}")
                    st.info(row.get('Service Engineer Comments', 'N/A'))
        else: st.warning("No history found.")

elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    # Buttons logic...

# --- BAAKI PAGES (FOC Tracker & Pending List) SAME RAHENGE ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    st.dataframe(foc_df, use_container_width=True, hide_index=True)
