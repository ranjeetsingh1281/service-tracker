import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="ELGi Global Tracker Pro", layout="wide")

# --- SMART DATA LOADER ---
@st.cache_data
def load_data():
    f_list = os.listdir('.')
    def find_f(base):
        for f in f_list:
            if f.lower().startswith(base.lower()): return f
        return None

    m_n, m_od_n, s_n, f_n = find_f("Master_Data"), find_f("Master_OD_Data"), find_f("Service_Details"), find_f("Active_FOC")
    
    try:
        m_df = pd.read_excel(m_n, engine='openpyxl') if m_n else pd.DataFrame()
        m_od_df = pd.read_excel(m_od_n, engine='openpyxl') if m_od_n else pd.DataFrame()
        s_df = pd.read_excel(s_n, engine='openpyxl') if s_n else pd.DataFrame()
        f_df = pd.read_excel(f_n, engine='openpyxl') if f_n else pd.DataFrame()
        for d in [m_df, m_od_df, s_df, f_df]:
            if not d.empty: 
                d.columns = [str(c).strip() for c in d.columns]
        return m_df, m_od_df, s_df, f_df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, master_od_df, service_df, foc_df = load_data()

# --- SIDEBAR MENU ---
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Dashboard:", ["1. DPSAC Tracker", "2. INDUSTRIAL Tracker"])

# ==========================================
# 1. DPSAC TRACKER (Standard)
# ==========================================
if page_choice == "1. DPSAC Tracker":
    st.title("🛠️ DPSAC Tracker - Standard Machine Data")
    
    # Smart Column Finder for Status
    s_col = next((c for c in master_df.columns if 'status' in c.lower()), None)
    
    if not master_df.empty and s_col:
        st.markdown("### 📊 Unit Status Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Total Units", len(master_df))
        m2.metric("🟢 Active", len(master_df[master_df[s_col].astype(str).str.contains('Active', case=False, na=False)]))
        m3.metric("🔵 Shifted", len(master_df[master_df[s_col].astype(str).str.contains('Shifted', case=False, na=False)]))
        m4.metric("🟠 Sold", len(master_df[master_df[s_col].astype(str).str.contains('Sold', case=False, na=False)]))
        st.divider()

    # SIDEBAR FILTER
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filter by Status")
    status_choice = st.sidebar.selectbox("Generate Detailed List:", ["None", "Active", "Shifted", "Sold"], key="std_status")
    if status_choice != "None" and s_col:
        st.subheader(f"📋 {status_choice} Machines List")
        f_list = master_df[master_df[s_col].astype(str).str.contains(status_choice, case=False, na=False)]
        st.download_button(f"📥 Export {status_choice} List", to_excel(f_list), f"DPSAC_{status_choice}.xlsx")
        st.dataframe(f_list[['Fabrication No', 'CUSTOMER NAME', 'MODEL', s_col]], use_container_width=True)
        st.divider()

    tabs = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str)) if not master_df.empty else []
        sel_c = c1.selectbox("Select Customer Name", ["All"] + c_list, key="std_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = c2.selectbox("Select Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}\n**Model:** {row.get('MODEL')}\n**Status:** `{row.get(s_col, 'N/A')}`")
                st.write(f"**Running Hrs:** {curr_h} 🏃‍➡️")
            with col2:
                st.info("📅 Replacement")
                for k, v in {'Oil':'Oil Replacement Date','AFC':'Air filter Compressor Replaced Date','AOS':'AOS Replaced Date'}.items(): 
                    st.write(f"**{k}:** {format_dt(row.get(v))}")
            with col3:
                st.info("⚙️ Live Remaining")
                for k, v in {'Oil':'HMR - Oil remaining','AFC':'Air filter replaced - Compressor Remaining Hours','AOS':'HMR - Separator remaining'}.items():
                    val = pd.to_numeric(row.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col4:
                st.error("🚨 Due Date")
                for k in ['OIL', 'AFC', 'AOS']: st.write(f"**{k} Due:** {format_dt(row.get(f'{k} DUE DATE'))}")

    # (DPSAC FOC & Pending logic remains same as per last complete version)

# ==========================================
# 2. INDUSTRIAL TRACKER (Industrial)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker - OD Master Data")
    
    # Smart Column Finder for Industrial Status
    s_col_i = next((c for c in master_od_df.columns if 'status' in c.lower()), None)
    
    if not master_od_df.empty and s_col_i:
        st.markdown("### 📊 Unit Status Overview")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("📦 Total Units", len(master_od_df))
        i2.metric("🟢 Active", len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Active', case=False, na=False)]))
        i3.metric("🔵 Shifted", len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Shifted', case=False, na=False)]))
        i4.metric("🟠 Sold", len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Sold', case=False, na=False)]))
        st.divider()

    # SIDEBAR FILTER (INDUSTRIAL)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filter by Status")
    status_choice_i = st.sidebar.selectbox("Generate Detailed List:", ["None", "Active", "Shifted", "Sold"], key="ind_status")
    if status_choice_i != "None" and s_col_i:
        st.subheader(f"📋 {status_choice_i} Machines List")
        f_list_i = master_od_df[master_od_df[s_col_i].astype(str).str.contains(status_choice_i, case=False, na=False)]
        st.download_button(f"📥 Export {status_choice_i} List", to_excel(f_list_i), f"Industrial_{status_choice_i}.xlsx")
        st.dataframe(f_list_i[['Fabrication No', 'Customer Name', 'Model', s_col_i]], use_container_width=True)
        st.divider()

    ti1, ti2, ti3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    with ti1:
        ci1, ci2 = st.columns(2)
        c_l_i = sorted(master_od_df['Customer Name'].unique().astype(str)) if not master_od_df.empty else []
        sel_ci = ci1.selectbox("Select Customer (IND)", ["All"] + c_l_i, key="ind_c_sel")
        df_fi = master_od_df if sel_ci == "All" else master_od_df[master_od_df['Customer Name'] == sel_ci]
        sel_fi = ci2.selectbox("Select Fabrication No (IND)", ["Select"] + sorted(df_fi['Fabrication No'].astype(str).unique()), key="ind_f_sel")

        if sel_fi != "Select":
            row_i = df_fi[df_fi['Fabrication No'].astype(str) == sel_fi].iloc[0]
            h_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            avg_r = pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_i = days * (avg_r if pd.notna(avg_r) else 0)

            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            with col_i1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}\n**Model:** {row_i.get('Model')}\n**Status:** `{row_i.get(s_col_i, 'N/A')}`")
                st.write(f"**Running Hrs:** {row_i.get('MDA Total Hours')} 🏃‍➡️")
            with col_i2:
                st.info("📅 Replacement")
                for k, v in {'Oil':'MDA Oil R Date','AF':'MDA AF R Date','AOS':'MDA AOS R Date'}.items():
                    st.write(f"**{k}:** {format_dt(row_i.get(v))}")
            with col_i3:
                st.info("⚙️ Live Remaining")
                for k, v in {'Oil':'MDA OIL Remaining Hours','AF':'AF Remaining Hours','AOS':'AOS Remaining Hours'}.items():
                    val = pd.to_numeric(row_i.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_i)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col_i4:
                st.error("🚨 Due Date")
                for k in ['OIL', 'AF', 'AOS']: st.write(f"**{k} Due:** {format_dt(row_i.get(f'{k} DUE DATE'))}")
