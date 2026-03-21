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

# --- SIDEBAR ---
st.sidebar.title("🏢 ELGi Global Menu")
page_choice = st.sidebar.radio("Go To Dashboard:", ["1. DPSAC Tracker", "2. INDUSTRIAL Tracker"])

# ==========================================
# 1. DPSAC TRACKER (Standard)
# ==========================================
if page_choice == "1. DPSAC Tracker":
    
    st.title("🛠️ DPSAC Tracker - Standard Machine Data")
    
    # --- BULLETPROOF UNIT STATUS METRICS ---
    if not master_df.empty:
        s_col = next((c for c in master_df.columns if c.lower() == 'unit status'), None)
        if s_col:
            t_total = len(master_df)
            t_active = len(master_df[master_df[s_col].astype(str).str.contains('Active', case=False, na=False)])
            t_shifted = len(master_df[master_df[s_col].astype(str).str.contains('Shifted', case=False, na=False)])
            t_sold = len(master_df[master_df[s_col].astype(str).str.contains('Sold', case=False, na=False)])
            
            # Displaying using Markdown Table (Forces visibility even if metrics fail)
            st.markdown(f"""
            | 📦 Total Units | 🟢 Active | 🔵 Shifted | 🟠 Sold |
            | :--- | :--- | :--- | :--- |
            | **{t_total}** | **{t_active}** | **{t_shifted}** | **{t_sold}** |
            """, unsafe_allow_html=True)
            st.divider()

    tabs = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])
    
    with tabs[0]: # Machine Tracker
        col1, col2 = st.columns(2)
        c_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str)) if not master_df.empty else []
        sel_c = col1.selectbox("Select Customer Name", ["All"] + c_list, key="std_c")
        df_f = master_df if sel_c == "All" else master_df[master_df['CUSTOMER NAME'] == sel_c]
        sel_f = col2.selectbox("Select Fabrication No", ["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()), key="std_f")
        
        if sel_f != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_f].iloc[0]
            curr_h = pd.to_numeric(row.get('HMR Cal.', 0), errors='coerce')
            last_h = pd.to_numeric(row.get('Last Call HMR', 0), errors='coerce')
            elapsed = (curr_h - last_h) if curr_h > last_h else 0
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {row.get('CUSTOMER NAME')}\n**Model:** {row.get('MODEL')}\n**Location:** {row.get('LOCATION', 'None')}")
                st.write(f"**Status:** `{row.get(s_col if s_col else 'Unit Status', 'N/A')}`")
                st.write(f"**Warranty:** {row.get('Warranty Type', 'N/A')}\n**End:** {format_dt(row.get('Warranty End date'))}")
                st.write(f"**Running Hrs:** {curr_h} 🏃‍➡️")
            with c2:
                st.info("📅 Replacement (9 Parts)")
                p_std = {'Oil':'Oil Replacement Date','AFC':'Air filter Compressor Replaced Date','AFE':'Air filter Engine Replaced Date','MOF':'Main Oil filter Replaced Date','ROF':'Return Oil filter Replaced Date','AOS':'AOS Replaced Date','RGT':'Greasing Done Date','1500K':'1500 Valve kit Replaced Date','3000K':'3000 Valve kit Replaced Date'}
                for k, v in p_std.items(): st.write(f"**{k}:** {format_dt(row.get(v))}")
            with c3:
                st.info("⚙️ Live Remaining")
                r_std = {'Oil':'HMR - Oil remaining','AFC':'Air filter replaced - Compressor Remaining Hours','AFE':'Air filter replaced - Engine Remaining Hours','MOF':'Main Oil filter Remaining Hours','ROF':'Return Oil filter Remaining Hours','AOS':'HMR - Separator remaining','RGT':'HMR - Motor regressed remaining','1500K':'1500 Valve kit Remaining Hours','3000K':'3000 Valve kit Remaining Hours'}
                for k, v in r_std.items():
                    val = pd.to_numeric(row.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with c4:
                st.error("🚨 Due Date (9 Parts)")
                d_std = {'OIL':'OIL DUE DATE','AFC':'AFC DUE DATE','AFE':'AFE DUE DATE','MOF':'MOF DUE DATE','ROF':'ROF DUE DATE','AOS':'AOS DUE DATE','RGT':'RGT DUE DATE','1500K':'1500 KIT DUE DATE','3000K':'3000 KIT DUE DATE'}
                for k, v in d_std.items(): st.write(f"**{k}:** {format_dt(row.get(v))}")

            st.divider()
            f_m = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f]
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(f_m[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not f_m.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            h_m = service_df[service_df['Fabrication Number'].astype(str) == sel_f].sort_values(by='Call Logged Date', ascending=False)
            for _, s in h_m.iterrows():
                with st.expander(f"📅 {format_dt(s.get('Call Logged Date'))} | ⚙️ {s.get('Call HMR')} HMR | 🛠️ {s.get('Call Type')}"):
                    st.write(f"**Comments:** {s.get('Service Engineer Comments')}")

    with tabs[1]: # FOC List
        st.subheader("📦 DPSAC Master FOC List")
        std_fabs = master_df['Fabrication No'].astype(str).unique() if not master_df.empty else []
        f_list_std = foc_df[foc_df['FABRICATION NO'].astype(str).isin(std_fabs)]
        st.download_button("📥 Export FOC List", to_excel(f_list_std), "DPSAC_FOC.xlsx")
        st.dataframe(f_list_std, use_container_width=True)

    with tabs[2]: # Service Pending
        st.subheader("⏳ DPSAC Service Pending")
        b1, b2, b3 = st.columns(3)
        p_df = pd.DataFrame()
        if b1.button("🔴 Overdue"): p_df = master_df[master_df['BIS Over Due'] != 0]
        if b2.button("🟡 Current Month"): p_df = master_df[master_df['BIS Current Month Due'] != 0]
        if b3.button("🟢 Next Month"): p_df = master_df[master_df['BIS Next Month Due'] != 0]
        if not p_df.empty:
            st.write(f"**Count:** {len(p_df)}")
            st.download_button("📥 Export Pending List", to_excel(p_df), "DPSAC_Pending.xlsx")
            st.dataframe(p_df, use_container_width=True)

# ==========================================
# 2. INDUSTRIAL TRACKER (Industrial)
# ==========================================
elif page_choice == "2. INDUSTRIAL Tracker":
    st.title("🛡️ INDUSTRIAL Tracker - Industrial Data")
    
    if not master_od_df.empty:
        s_col_i = next((c for c in master_od_df.columns if c.lower() == 'unit status'), None)
        if s_col_i:
            ti_total = len(master_od_df)
            ti_active = len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Active', case=False, na=False)])
            ti_shifted = len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Shifted', case=False, na=False)])
            ti_sold = len(master_od_df[master_od_df[s_col_i].astype(str).str.contains('Sold', case=False, na=False)])
            
            st.markdown(f"| 📦 Total Units | 🟢 Active | 🔵 Shifted | 🟠 Sold |\n| :--- | :--- | :--- | :--- |\n| **{ti_total}** | **{ti_active}** | **{ti_shifted}** | **{ti_sold}** |")
            st.divider()

    tabs_i = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tabs_i[0]: # Machine Tracker
        col1_i, col2_i = st.columns(2)
        c_l_i = sorted(master_od_df['Customer Name'].unique().astype(str)) if not master_od_df.empty else []
        sel_c_i = col1_i.selectbox("Select Customer (IND)", ["All"] + c_l_i, key="ind_c")
        df_f_i = master_od_df if sel_c_i == "All" else master_od_df[master_od_df['Customer Name'] == sel_c_i]
        sel_f_i = col2_i.selectbox("Select Fabrication No (IND)", ["Select"] + sorted(df_f_i['Fabrication No'].astype(str).unique()), key="ind_f")

        if sel_f_i != "Select":
            row_i = df_f_i[df_f_i['Fabrication No'].astype(str) == sel_f_i].iloc[0]
            h_dt = pd.to_datetime(row_i.get('MDA HMR Date'), errors='coerce')
            days = (pd.Timestamp(datetime.now().date()) - h_dt).days if pd.notna(h_dt) else 0
            avg_r = pd.to_numeric(row_i.get('MDA AVG Running Hours Per Day', 0), errors='coerce')
            elapsed_i = days * (avg_r if pd.notna(avg_r) else 0)

            ci1, ci2, ci3, ci4 = st.columns(4)
            with ci1:
                st.info("📋 Info")
                st.write(f"**Customer:** {row_i.get('Customer Name')}\n**Model:** {row_i.get('Model')}\n**Status:** `{row_i.get(s_col_i if s_col_i else 'Unit Status', 'N/A')}`")
                st.write(f"**Running Hrs:** {row_i.get('MDA Total Hours', 'N/A')} 🏃‍➡️")
            with ci2:
                st.info("📅 Replacement (9 Parts)")
                p_ind = {'Oil':'MDA Oil R Date','AF':'MDA AF R Date','OF':'MDA OF R Date','AOS':'MDA AOS R Date','RGT':'MDA RGT R Date','VK':'MDA Valvekit R Date','PF':'MDA PF R DATE','FF':'MDA FF R DATE','CF':'MDA CF R DATE'}
                for k, v in p_ind.items(): st.write(f"**{k}:** {format_dt(row_i.get(v))}")
            with ci3:
                st.info("⚙️ Live Remaining")
                r_ind = {'Oil':'MDA OIL Remaining Hours','AF':'AF Remaining Hours','AOS':'AOS Remaining Hours','VK':'Valve Kit Remaining Hours','PF':'PF DUE','FF':'FF DUE','CF':'CF DUE'}
                for k, v in r_ind.items():
                    val = pd.to_numeric(row_i.get(v, 0), errors='coerce')
                    rem = int((val if pd.notna(val) else 0) - elapsed_i)
                    st.write(f"**{k}:** {rem} Hrs" if rem > 0 else f"**{k}:** 🚨 {rem}")
            with ci4:
                st.error("🚨 Due Date (9 Parts)")
                d_ind = {'Oil':'OIL DUE DATE','AF':'AF DUE DATE','AOS':'AOS DUE DATE','VK':'VALVEKIT DUE DATE','PF':'PF DUE DATE','FF':'FF DUE DATE','CF':'CF DUE DATE'}
                for k, v in d_ind.items(): st.write(f"**{k}:** {format_dt(row_i.get(v))}")

            st.divider()
            f_m_i = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_f_i]
            st.subheader("🎁 Machine FOC Details")
            st.dataframe(f_m_i[['Created On','Part Code','Qty','ELGI IVOICE NO.']] if not f_m_i.empty else pd.DataFrame(), use_container_width=True)
            
            st.subheader("🕒 Service History")
            hi_m_i = service_df[service_df['Fabrication Number'].astype(str) == sel_f_i].sort_values(by='Call Logged Date', ascending=False)
            for _, si in hi_m_i.iterrows():
                with st.expander(f"📅 {format_dt(si.get('Call Logged Date'))} | ⚙️ {si.get('Call HMR')} HMR"):
                    st.info(si.get('Service Engineer Comments'))

    with tabs_i[1]: # Industrial FOC List
        st.subheader("📦 INDUSTRIAL Master FOC List")
        ind_fabs = master_od_df['Fabrication No'].astype(str).unique() if not master_od_df.empty else []
        f_list_i = foc_df[foc_df['FABRICATION NO'].astype(str).isin(ind_fabs)]
        st.download_button("📥 Export FOC List", to_excel(f_list_i), "Industrial_FOC.xlsx")
        st.dataframe(f_list_i, use_container_width=True)

    with tabs_i[2]: # Industrial Pending
        st.subheader("⏳ INDUSTRIAL Service Pending")
        o1, o2, o3 = st.columns(3)
        pi_df = pd.DataFrame()
        if o1.button("🔴 Red Count"): pi_df = master_od_df[master_od_df['Red Count'] != 0]
        if o2.button("🟡 Yellow Count"): pi_df = master_od_df[master_od_df['Yellow Count'] != 0]
        if o3.button("🟢 Green Count"): pi_df = master_od_df[master_od_df['Green Count'] != 0]
        if not pi_df.empty:
            st.write(f"**Count:** {len(pi_df)}")
            st.download_button("📥 Export Pending List", to_excel(pi_df), "Industrial_Pending.xlsx")
            st.dataframe(pi_df, use_container_width=True)
