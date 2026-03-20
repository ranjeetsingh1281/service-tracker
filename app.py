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
            if not d.empty: d.columns = [str(c).strip() for c in d.columns]
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

# --- SIDEBAR ---
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Dashboard:", ["1. DPSAC Tracker", "2. INDUSTRIAL Tracker"])

# ==========================================
# 1. DPSAC TRACKER (Standard)
# ==========================================
if page_choice == "1. DPSAC Tracker":
    st.title("🛠️ DPSAC Tracker")
    
    # Status Metrics
    if not master_df.empty and 'Unit Status' in master_df.columns:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Units", len(master_df))
        m2.metric("🟢 Active", len(master_df[master_df['Unit Status'] == 'Active']))
        m3.metric("🔵 Shifted", len(master_df[master_df['Unit Status'] == 'Shifted']))
        m4.metric("🟠 Sold", len(master_df[master_df['Unit Status'] == 'Sold']))

    t1, t2, t3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with t1:
        c1, c2 = st.columns(2)
        sel_c = c1.selectbox("Customer", ["All"] + sorted(master_df['CUSTOMER NAME'].unique().astype(str)), key="std_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = c2.selectbox("Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            # C1-C4 Layout
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}\n**Model:** {row.get('MODEL')}\n**Status:** `{row.get('Unit Status')}`")
                st.write(f"**Warr End:** {format_dt(row.get('Warranty End date'))}\n**HMR:** {curr_h}")
            with col2:
                st.info("📅 Replacement")
                p_l = {'Oil':'Oil Replacement Date','AFC':'Air filter Compressor Replaced Date','AOS':'AOS Replaced Date'}
                for k, v in p_l.items(): st.write(f"**{k}:** {format_dt(row.get(v))}")
            with col3:
                st.info("⚙️ Live Remaining")
                r_l = {'Oil':'HMR - Oil remaining','AFC':'Air filter replaced - Compressor Remaining Hours','AOS':'HMR - Separator remaining'}
                for k, v in r_l.items():
                    rem = int(pd.to_numeric(row.get(v, 0), errors='coerce') - elapsed)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col4:
                st.error("🚨 Due Date")
                for k in ['OIL', 'AFC', 'AOS']: st.write(f"**{k} Due:** {format_dt(row.get(f'{k} DUE DATE'))}")

            # Machine History & FOC
            st.divider()
            f_m = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(f_m[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not f_m.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            h_m = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            for _, s in h_m.iterrows():
                with st.expander(f"📅 {format_dt(s.get('Call Logged Date'))} | ⚙️ {s.get('Call HMR')} HMR | {s.get('Call Type')}"):
                    st.write(f"**Comments:** {s.get('Service Engineer Comments')}")

    with t2:
        st.subheader("📦 DPSAC FOC List")
        std_fabs = master_df['Fabrication No'].astype(str).unique()
        f_list = foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)]
        st.download_button("📥 Export FOC", to_excel(f_list), "DPSAC_FOC.xlsx")
        st.dataframe(f_list, use_container_width=True)

    with t3:
        st.subheader("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        p_df = pd.DataFrame()
        if b1.button("🔴 Overdue"): p_df = master_df[master_df['BIS Over Due'] != 0]
        if b2.button("🟡 Current Month"): p_df = master_df[master_df['BIS Current Month Due'] != 0]
        if b3.button("🟢 Next Month"): p_df = master_df[master_df['BIS Next Month Due'] != 0]
        if not p_df.empty:
            st.write(f"**Count:** {len(p_df)}")
            st.download_button("📥 Export Pending", to_excel(p_df), "Pending.xlsx")
            st.dataframe(p_df, use_container_width=True)

# ==========================================
# 2. INDUSTRIAL TRACKER (Industrial)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker")
    
    if not master_od_df.empty and 'Unit Status' in master_od_df.columns:
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Total Units", len(master_od_df))
        i2.metric("🟢 Active", len(master_od_df[master_od_df['Unit Status'] == 'Active']))
        i3.metric("🔵 Shifted", len(master_od_df[master_od_df['Unit Status'] == 'Shifted']))
        i4.metric("🟠 Sold", len(master_od_df[master_od_df['Unit Status'] == 'Sold']))

    ti1, ti2, ti3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with ti1:
        ci1, ci2 = st.columns(2)
        sel_ci = ci1.selectbox("Customer", ["All"] + sorted(master_od_df['Customer Name'].unique().astype(str)), key="ind_c")
        df_fi = master_od_df if sel_ci == "All" else master_od_df[master_od_df['Customer Name'] == sel_ci]
        sel_fi = ci2.selectbox("Fabrication No", ["Select"] + sorted(df_fi['Fabrication No'].astype(str).unique()), key="ind_f")

        if sel_fi != "Select":
            row_i = df_fi[df_fi['Fabrication No'].astype(str) == sel_fi].iloc[0]
            h_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            avg_r = pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_i = days * (avg_r if pd.notna(avg_r) else 0)

            # C1-C4 Layout
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            with col_i1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}\n**Model:** {row_i.get('Model')}")
                st.write(f"**Status:** `{row_i.get('Unit Status')}`\n**Running Hrs:** {row_i.get('MDA Total Hours')}")
            with col_i2:
                st.info("📅 Replacement")
                p_i = {'Oil':'MDA Oil R Date','AF':'MDA AF R Date','AOS':'MDA AOS R Date'}
                for k, v in p_i.items(): st.write(f"**{k}:** {format_dt(row_i.get(v))}")
            with col_i3:
                st.info("⚙️ Live Remaining")
                r_i = {'Oil':'MDA OIL Remaining Hours','AF':'AF Remaining Hours','AOS':'AOS Remaining Hours'}
                for k, v in r_i.items():
                    val = pd.to_numeric(row_i.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_i)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with col_i4:
                st.error("🚨 Due Date")
                for k in ['OIL', 'AF', 'AOS']: st.write(f"**{k} Due:** {format_dt(row_i.get(f'{k} DUE DATE'))}")

            # Machine History & FOC
            st.divider()
            f_match_ind = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_fi]
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(f_match_ind[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not f_match_ind.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            hi_m_ind = service_df[service_df['Fabrication Number'].astype(str) == sel_fi].sort_values(by='Call Logged Date', ascending=False)
            for _, si in hi_m_ind.iterrows():
                with st.expander(f"📅 {format_dt(si.get('Call Logged Date'))} | ⚙️ {si.get('Call HMR')} HMR | {si.get('Call Type')}"):
                    st.info(si.get('Service Engineer Comments'))

    with ti2:
        st.subheader("📦 INDUSTRIAL FOC List")
        ind_fabs = master_od_df['Fabrication No'].astype(str).unique()
        f_list_i = foc_df[foc_df['FABRICATION NO'].astype(str).isin(ind_fabs)]
        st.download_button("📥 Export FOC", to_excel(f_list_i), "Industrial_FOC.xlsx")
        st.dataframe(f_list_i, use_container_width=True)

    with ti3:
        st.subheader("⏳ INDUSTRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        pi_df = pd.DataFrame()
        if o1.button("🔴 Red Count"): pi_df = master_od_df[master_od_df['Red Count'] != 0]
        if o2.button("🟡 Yellow Count"): pi_df = master_od_df[master_od_df['Yellow Count'] != 0]
        if o3.button("🟢 Green Count"): pi_df = master_od_df[master_od_df['Green Count'] != 0]
        if not pi_df.empty:
            st.write(f"**Count:** {len(pi_df)}")
            st.download_button("📥 Export Pending", to_excel(pi_df), "Ind_Pending.xlsx")
            st.dataframe(pi_df, use_container_width=True)
