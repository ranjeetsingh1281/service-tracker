import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DATA LOAD FUNCTION ---
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
        
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        
        # FOC Duplicate Header Fix
        new_cols = []
        counts = {}
        for col in f_df.columns:
            c = str(col).strip()
            if c in counts:
                counts[c] += 1
                new_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_cols.append(c)
        f_df.columns = new_cols
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

# --- EXPORT FUNCTIONS ---
def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def create_pdf(title, info_dict, table_df=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, title)
    p.setFont("Helvetica", 10)
    y = 730
    for key, val in info_dict.items():
        p.drawString(50, y, f"{key}: {val}")
        y -= 15
    p.line(50, y, 550, y)
    y -= 20
    if table_df is not None:
        p.drawString(50, y, "Recent Records:")
        y -= 20
        for _, row in table_df.head(10).iterrows():
            p.drawString(60, y, f"- {row.iloc[0]} | {row.iloc[1]}")
            y -= 15
            if y < 50: break
    p.showPage()
    p.save()
    return buffer.getvalue()

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Missing Files: {missing}"); st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer", options=["All"] + customer_list)
    cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    st.subheader(f"📊 Summary: {selected_customer}")
    m1, m2, m3 = st.columns(3)
    t_u = len(cust_filtered)
    n_w = len(cust_filtered[cust_filtered['Warranty Type'].str.contains('Non', na=False, case=False)])
    m1.metric("Total Units", t_u); m2.metric("In Warranty", t_u - n_w); m3.metric("Non-Warranty", n_w)
    st.divider()

    selected_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        
        # Export Row
        ex_c1, ex_c2 = st.columns(2)
        pdf_data = {"Customer": m_info['CUSTOMER NAME'], "Fabrication No": selected_fab, "HMR": m_info.get('HMR Cal.','N/A')}
        ex_c1.download_button("📄 Export to PDF", create_pdf("Machine Report", pdf_data, history), f"Report_{selected_fab}.pdf")
        ex_c2.download_button("📊 Export History to Excel", to_excel(history), f"History_{selected_fab}.xlsx")

        # C1 to C4 Display
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if pd.notna(curr_hmr) and pd.notna(last_hmr) and curr_hmr > last_hmr else 0
        
        with c1:
            st.info("📋 Customer Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**HMR Cal:** {curr_hmr}")
            st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")
        with c2:
            st.info("📅 Replacement")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Live Remaining")
            for col, lbl in [('HMR - Oil remaining', 'Oil'), ('HMR - Separator remaining', 'AOS')]:
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce') - elapsed
                st.write(f"**{lbl}:** {int(val)} Hrs" if val > 0 else f"**{lbl}:** 🚨 {int(val)} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # FOC & History (Same as before)
        st.divider(); st.subheader("🎁 FOC Parts")
        f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
        foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
        if not foc_match.empty: st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
        
        st.divider(); st.subheader("🕒 Service History")
        for _, row in history.iterrows():
            with st.expander(f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR"):
                st.info(row.get('Service Engineer Comments', 'N/A'))

# --- 2. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    f_cols = ['Created On', 'FOC Number', 'Call Tracking Number', 'Customer Name', 'FOC Type', 'FOC Category', 'FOC Status', 'DEALER INVOICE NO./ DATE', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.', 'AO Number', 'LR Number']
    available = [c for c in f_cols if c in foc_df.columns]
    
    c1, c2 = st.columns(2)
    c1.download_button("📊 Export FOC to Excel", to_excel(foc_df[available]), "FOC_Master_List.xlsx")
    c2.download_button("📄 Export FOC to PDF", create_pdf("FOC Master List", {"Total Records": len(foc_df)}), "FOC_Master.pdf")
    
    st.dataframe(foc_df[available], use_container_width=True, hide_index=True)

# --- 3. SERVICE PENDING LIST ---
elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    b1, b2, b3 = st.columns(3)
    p_df = pd.DataFrame()
    if b1.button("🔴 BIS Over Due", use_container_width=True): p_df = master_df[master_df['BIS Over Due'] != 0].copy()
    if b2.button("🟡 BIS Current Month", use_container_width=True): p_df = master_df[master_df['BIS Current Month Due'] != 0].copy()
    if b3.button("🟢 BIS Next Month", use_container_width=True): p_df = master_df[master_df['BIS Next Month Due'] != 0].copy()

    if not p_df.empty:
        st.success(f"Records: {len(p_df)}")
        ex_c1, ex_c2 = st.columns(2)
        ex_c1.download_button("📊 Export Pending to Excel", to_excel(p_df), "Pending_List.xlsx")
        ex_c2.download_button("📄 Export Pending to PDF", create_pdf("Pending Service List", {"Count": len(p_df)}), "Pending_List.pdf")
        
        disp = ['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']
        table = p_df[disp].copy()
        for c in ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']: table[c] = table[c].apply(format_dt)
        st.dataframe(table, use_container_width=True, hide_index=True)
