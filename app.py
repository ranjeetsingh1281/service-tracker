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
        return None, None, None, [f for f in ["Master_Data.xlsx", "Service_Details.xlsx", "Active_FOC.xlsx"] if not find_file(f)]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        
        # FOC Duplicate Header Fix
        new_f_cols = []
        counts = {}
        for col in f_df.columns:
            c = str(col).strip()
            if c in counts:
                counts[c] += 1
                new_f_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_f_cols.append(c)
        f_df.columns = new_f_cols
            
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

def create_pdf(title, info_dict, table_df=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height-50, title)
    y = height - 80
    p.setFont("Helvetica", 10)
    for k, v in info_dict.items():
        p.drawString(50, y, f"{k}: {v}"); y -= 15
    p.line(50, y, width-50, y); y -= 30
    if table_df is not None and not table_df.empty:
        p.setFont("Helvetica-Bold", 9)
        cols = table_df.columns.tolist()[:8]
        cur_x = 50
        for c in cols: p.drawString(cur_x, y, str(c)[:15]); cur_x += 90
        y -= 20; p.setFont("Helvetica", 8)
        for _, row in table_df.iterrows():
            if y < 50: p.showPage(); y = height-50; p.setFont("Helvetica", 8)
            cur_x = 50
            for c in cols: p.drawString(cur_x, y, str(row.get(c, "N/A"))[:18]); cur_x += 90
            y -= 15
    p.showPage(); p.save()
    return buffer.getvalue()

master_df, service_df, foc_df, missing = load_data()

if missing:
    st.error(f"❌ Files Missing: {missing}"); st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# --- 1. MACHINE TRACKER ---
if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Customer Select Karein", options=["All"] + customer_list)
    cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    # METRICS SECTION
    st.subheader(f"📊 Summary: {selected_customer}")
    m1, m2, m3 = st.columns(3)
    t_u = len(cust_filtered)
    n_w = len(cust_filtered[cust_filtered['Warranty Type'].str.contains('Non', na=False, case=False)])
    m1.metric("Total Units", t_u)
    m2.metric("In Warranty", t_u - n_w)
    m3.metric("Non-Warranty", n_w)

    # --- NAYA UPDATE: CATEGORY WISE COUNT ---
    with st.expander("📂 View Category Wise Unit Count"):
        if 'Warranty Type' in cust_filtered.columns:
            cat_counts = cust_filtered['Warranty Type'].value_counts()
            c_cols = st.columns(len(cat_counts) if len(cat_counts) > 0 else 1)
            for i, (cat_name, count) in enumerate(cat_counts.items()):
                c_cols[i % len(c_cols)].write(f"**{cat_name}:** {count}")
        else:
            st.warning("Warranty Type column nahi mila.")
    
    st.divider()

    selected_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        
        # Export Buttons
        ex1, ex2 = st.columns(2)
        ex1.download_button("📊 Export Excel", to_excel(history), f"History_{selected_fab}.xlsx")
        ex2.download_button("📄 Export PDF Report", create_pdf("Machine Detail Report", {"Fab": selected_fab, "Customer": m_info['CUSTOMER NAME']}, history), f"Report_{selected_fab}.pdf")

        # C1 to C4
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

        with c1:
            st.info("📋 Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**HMR Cal:** {curr_hmr}")
            st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")
        with c2:
            st.info("📅 Replacement")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Live Remaining")
            items = {'HMR - Oil remaining': 'Oil', 'Main Oil filter Remaining Hours': 'MOF', 'HMR - Separator remaining': 'AOS'}
            for col, lbl in items.items():
                val = pd.to_numeric(m_info.get(col, 0), errors='coerce')
                rem = int(val - elapsed) if not pd.isna(val) else 0
                st.write(f"**{lbl}:** {rem} Hrs" if rem > 0 else f"**{lbl}:** 🚨 {rem} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # FOC
        st.divider(); st.subheader("🎁 FOC Parts History")
        f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
        foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
        if not foc_match.empty:
            st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)

        # History
        st.divider(); st.subheader("🕒 Service History")
        if not history.empty:
            for _, row in history.iterrows():
                with st.expander(f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR | 🛠️ {row.get('Call Type','N/A')}"):
                    st.write(f"**Engineer:** {row.get('Service Engineer', 'N/A')}")
                    st.info(row.get('Service Engineer Comments', 'N/A'))

# --- 2. FOC TRACKER LIST ---
elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    f_cols = ['Created On', 'FOC Number', 'Call Tracking Number', 'Customer Name', 'FOC Type', 'FOC Category', 'FOC Status', 'DEALER INVOICE NO./ DATE', 'Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.', 'AO Number', 'LR Number']
    available = [c for c in f_cols if c in foc_df.columns]
    st.download_button("📊 Export FOC Excel", to_excel(foc_df[available]), "FOC_Master.xlsx")
    st.dataframe(foc_df[available], use_container_width=True, hide_index=True)

# --- 3. SERVICE PENDING LIST ---
elif page == "Service Pending List":
    st.title("⏳ Service Pending Dashboard")
    b1, b2, b3 = st.columns(3)
    p_df = pd.DataFrame()
    if b1.button("🔴 Overdue", use_container_width=True): p_df = master_df[master_df['BIS Over Due'] != 0].copy()
    if b2.button("🟡 Current Month", use_container_width=True): p_df = master_df[master_df['BIS Current Month Due'] != 0].copy()
    if b3.button("🟢 Next Month", use_container_width=True): p_df = master_df[master_df['BIS Next Month Due'] != 0].copy()

    if not p_df.empty:
        st.success(f"Records Found: {len(p_df)}")
        st.download_button("📊 Export Pending Excel", to_excel(p_df), "Pending.xlsx")
        disp = ['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']
        table = p_df[disp].copy()
        for c in ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']: table[c] = table[c].apply(format_dt)
        st.dataframe(table, use_container_width=True, hide_index=True)
