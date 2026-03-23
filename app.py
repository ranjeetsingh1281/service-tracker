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
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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

# --- SIDEBAR MENU & SMART METRICS ---
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Dashboard:", ["1. DPSAC Tracker", "2. INDUSTRIAL Tracker"])

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Unit Status (Sidebar)")

# --- SMART METRICS COUNTER (FIXED) ---
def get_sidebar_metrics(df):
    if df.empty: return 0, 0, 0, 0
    # Dynamic column finder
    s_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if not s_col: return len(df), 0, 0, 0
    
    # Cleaning data before counting to avoid 0 results
    status_series = df[s_col].astype(str).str.strip().str.capitalize()
    total = len(df)
    active = len(df[status_series == "Active"])
    shifted = len(df[status_series == "Shifted"])
    sold = len(df[status_series == "Sold"])
    return total, active, shifted, sold

if page_choice == "1. DPSAC Tracker":
    t, a, sh, so = get_sidebar_metrics(master_df)
else:
    t, a, sh, so = get_sidebar_metrics(master_od_df)

st.sidebar.metric("📦 Total Units", t)
st.sidebar.metric("🟢 Active", a)
st.sidebar.metric("🔵 Shifted", sh)
st.sidebar.metric("🟠 Sold", so)

# ==========================================
# 1. DPSAC TRACKER (Standard)
# ==========================================
if page_choice == "1. DPSAC Tracker":
    st.title("🛠️ DPSAC Tracker - Standard Machine Data")
    s_col = next((c for c in master_df.columns if 'status' in c.lower()), "Unit Status")
    
    st.sidebar.markdown("---")
    status_choice = st.sidebar.selectbox("Filter Status List:", ["None", "Active", "Shifted", "Sold"], key="std_filter")
    if status_choice != "None":
        st.subheader(f"📋 {status_choice} Machines")
        f_list = master_df[master_df[s_col].astype(str).str.contains(status_choice, case=False, na=False)]
        st.download_button(f"📥 Export {status_choice}", to_excel(f_list), f"DPSAC_{status_choice}.xlsx")
        st.dataframe(f_list[['Fabrication No', 'CUSTOMER NAME', 'MODEL', s_col]], use_container_width=True)

    tabs = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        sel_c = c1.selectbox("Select Customer", ["All"] + sorted(master_df['CUSTOMER NAME'].unique().astype(str)), key="std_c_sel")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = c2.selectbox("Select Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_f_sel")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            # --- RENDER 4 BLOCKS ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}\n**Model:** {row.get('MODEL')}\n**Status:** `{row.get(s_col, 'N/A')}`\n**Running Hrs:** {curr_h}")
            with col2:
                st.info("📅 Replacement")
                p_std = {'Oil':'Oil Replacement Date','AFC':'Air filter Compressor Replaced Date','AFE':'Air filter Engine Replaced Date','MOF':'Main Oil filter Replaced Date','ROF':'Return Oil filter Replaced Date','AOS':'AOS Replaced Date','RGT':'Greasing Done Date','1500K':'1500 Valve kit Replaced Date','3000K':'3000 Valve kit Replaced Date'}
                for k, v in p_std.items(): st.write(f"**{k}:** {format_dt(row.get(v))}")
            with col3:
                st.info("⚙️ Remaining")
                r_std = {'Oil':'HMR - Oil remaining','AFC':'Air filter replaced - Compressor Remaining Hours','AFE':'Air filter replaced - Engine Remaining Hours','MOF':'Main Oil filter Remaining Hours','ROF':'Return Oil filter Remaining Hours','AOS':'HMR - Separator remaining','RGT':'HMR - Motor regressed remaining','1500K':'1500 Valve kit Remaining Hours','3000K':'3000 Valve kit Remaining Hours'}
                for k, v in r_std.items():
                    val = pd.to_numeric(row.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col4:
                st.error("🚨 Due Date")
                d_std = {'OIL':'OIL DUE DATE','AFC':'AFC DUE DATE','AFE':'AFE DUE DATE','MOF':'MOF DUE DATE','ROF':'ROF DUE DATE','AOS':'AOS DUE DATE','RGT':'RGT DUE DATE','1500K':'1500 KIT DUE DATE','3000K':'3000 KIT DUE DATE'}
                for k, v in d_std.items(): st.write(f"**{k}:** {format_dt(row.get(v))}")

            st.divider()
            f_col = next((c for c in foc_df.columns if 'FABRICATION' in str(c).upper()), "FABRICATION NO")
            f_m = foc_df[foc_df[f_col].astype(str) == sel_f] if not foc_df.empty else pd.DataFrame()
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(f_m[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not f_m.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            h_m = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            for _, s in h_m.iterrows():
                with st.expander(f"📅 {format_dt(s.get('Call Logged Date'))} | ⚙️ {s.get('Call HMR')} HMR"):
                    st.write(f"**Engineer:** {s.get('Service Engineer')}\n**Comments:** {s.get('Service Engineer Comments')}")

# ==========================================
# 2. INDUSTRIAL TRACKER (Industrial)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker - Industrial Data")
    s_col_i = next((c for c in master_od_df.columns if 'status' in c.lower()), "Unit Status")
    
    st.sidebar.markdown("---")
    status_choice_i = st.sidebar.selectbox("Filter Status List:", ["None", "Active", "Shifted", "Sold"], key="ind_filter")
    if status_choice_i != "None":
        st.subheader(f"📋 {status_choice_i} Machines")
        f_list_i = master_od_df[master_od_df[s_col_i].astype(str).str.contains(status_choice_i, case=False, na=False)]
        st.download_button(f"📥 Export {status_choice_i}", to_excel(f_list_i), f"Industrial_{status_choice_i}.xlsx")
        st.dataframe(f_list_i[['Fabrication No', 'Customer Name', 'Model', s_col_i]], use_container_width=True)

    tabs_i = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    with tabs_i[0]:
        ci1, ci2 = st.columns(2)
        sel_ci = ci1.selectbox("Select Customer", ["All"] + sorted(master_od_df['Customer Name'].unique().astype(str)), key="ind_c_sel")
        df_fi = master_od_df if sel_ci == "All" else master_od_df[master_od_df['Customer Name'] == sel_ci]
        sel_fi = ci2.selectbox("Select Fabrication No", ["Select"] + sorted(df_fi['Fabrication No'].astype(str).unique()), key="ind_f_sel")

        if sel_fi != "Select":
            row_i = df_fi[df_fi['Fabrication No'].astype(str) == sel_fi].iloc[0]
            h_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            avg_r = pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_i = days * (avg_r if pd.notna(avg_r) else 0)

            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            with col_i1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}\n**Model:** {row_i.get('Model')}\n**Status:** `{row_i.get(s_col_i, 'N/A')}`\n**Running Hrs:** {row_i.get('MDA Total Hours', 'N/A')}")
            with col_i2:
                st.info("📅 Replacement")
                p_ind = {'Oil':'MDA Oil R Date','AF':'MDA AF R Date','OF':'MDA OF R Date','AOS':'MDA AOS R Date','RGT':'MDA RGT R Date','VK':'MDA Valvekit R Date','PF':'MDA PF R DATE','FF':'MDA FF R DATE','CF':'MDA CF R DATE'}
                for k, v in p_ind.items(): st.write(f"**{k}:** {format_dt(row_i.get(v))}")
            with col_i3:
                st.info("⚙️ Remaining")
                r_ind = {'Oil':'MDA OIL Remaining Hours','AF':'AF Remaining Hours','AOS':'AOS Remaining Hours','RGT':'RGT Remaining Hours','VK':'Valve Kit Remaining Hours','PF':'PF DUE','FF':'FF DUE','CF':'CF DUE'}
                for k, v in r_ind.items():
                    val = pd.to_numeric(row_i.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_i)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col_i4:
                st.error("🚨 Due Date")
                d_ind = {'Oil':'OIL DUE DATE','AF':'AF DUE DATE','AOS':'AOS DUE DATE','VK':'VALVEKIT DUE DATE','RGT':'RGT DUE DATE','PF':'PF DUE DATE','FF':'FF DUE DATE','CF':'CF DUE DATE'}
                for k, v in d_ind.items(): st.write(f"**{k}:** {format_dt(row_i.get(v))}")

            st.divider()
            f_col_i = next((c for c in foc_df.columns if 'FABRICATION' in str(c).upper()), "FABRICATION NO")
            fi_m = foc_df[foc_df[f_col_i].astype(str) == sel_fi] if not foc_df.empty else pd.DataFrame()
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(fi_m[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not fi_m.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            hi_m = service_df[service_df['Fabrication Number'].astype(str) == sel_fi].sort_values(by='Call Logged Date', ascending=False)
            for _, si in hi_m.iterrows():
                with st.expander(f"📅 {format_dt(si.get('Call Logged Date'))} | ⚙️ {si.get('Call HMR')} HMR"):
                    st.write(f"**Engineer:** {si.get('Service Engineer')}\n**Comments:** {si.get('Service Engineer Comments')}")
