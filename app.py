import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
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
        return None, None, None, ["Files missing. Check Master_Data, Service_Details, Active_FOC."]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

# --- HELPERS ---
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
    p.setFont("Helvetica-Bold", 18); p.drawString(50, height-50, title)
    y = height - 80; p.setFont("Helvetica", 10)
    for k, v in info_dict.items():
        p.drawString(50, y, f"{k}: {v}"); y -= 15
    p.line(50, y, width-50, y); y -= 30
    if table_df is not None and not table_df.empty:
        p.setFont("Helvetica-Bold", 9); cols = table_df.columns.tolist()[:8]
        cur_x = 50
        for c in cols: p.drawString(cur_x, y, str(c)[:15]); cur_x += 95
        y -= 20; p.setFont("Helvetica", 8)
        for _, row in table_df.iterrows():
            if y < 50: p.showPage(); y = height-50; p.setFont("Helvetica", 8)
            cur_x = 50
            for c in cols: p.drawString(cur_x, y, str(row.get(c, "N/A"))[:18]); cur_x += 95
            y -= 15
    p.showPage(); p.save()
    return buffer.getvalue()

master_df, service_df, foc_df, missing = load_data()
if missing: st.error(f"Error: {missing}"); st.stop()

# --- SIDEBAR & SEARCH ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Dashboard:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

# Mapping for 9 Parts (Column names in Excel vs Display Labels)
parts_map = {
    'Oil': {'rem': 'HMR - Oil remaining', 'date': 'Oil Replacement Date', 'due': 'OIL DUE DATE'},
    'AFC': {'rem': 'Air filter replaced - Compressor Remaining Hours', 'date': 'Air filter Compressor Replaced Date', 'due': 'AFC DUE DATE'},
    'AFE': {'rem': 'Air filter replaced - Engine Remaining Hours', 'date': 'Air filter Engine Replaced Date', 'due': 'AFE DUE DATE'},
    'MOF': {'rem': 'Main Oil filter Remaining Hours', 'date': 'Main Oil filter Replaced Date', 'due': 'MOF DUE DATE'},
    'ROF': {'rem': 'Return Oil filter Remaining Hours', 'date': 'Return Oil filter Replaced Date', 'due': 'ROF DUE DATE'},
    'AOS': {'rem': 'HMR - Separator remaining', 'date': 'AOS Replaced Date', 'due': 'AOS DUE DATE'},
    'Greasing': {'rem': 'HMR - Motor regressed remaining', 'date': 'Greasing Done Date', 'due': 'RGT DUE DATE'},
    '1500 Kit': {'rem': '1500 Valve kit Remaining Hours', 'date': '1500 Valve kit Replaced Date', 'due': '1500 KIT DUE DATE'},
    '3000 Kit': {'rem': '3000 Valve kit Remaining Hours', 'date': '3000 Valve kit Replaced Date', 'due': '3000 KIT DUE DATE'}
}

if page == "Machine Tracker":
    st.title("🛠️ Machine Tracker Pro")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("Select Customer", options=["All"] + customer_list)
    cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
    
    # METRICS & CATEGORY
    m1, m2, m3 = st.columns(3)
    t_u = len(cust_filtered)
    w_col = next((c for c in cust_filtered.columns if 'warranty type' in c.lower()), 'Warranty Type')
    n_w = len(cust_filtered[cust_filtered[w_col].astype(str).str.contains('Non', na=False, case=False)])
    m1.metric("Total Units", t_u); m2.metric("In Warranty", t_u - n_w); m3.metric("Non-Warranty", n_w)
    
    cat_col = next((c for c in cust_filtered.columns if 'category' in c.lower()), 'Category')
    with st.expander("📂 View Category Wise Unit Count"):
        counts = cust_filtered[cat_col].value_counts()
        cols = st.columns(4)
        for i, (name, count) in enumerate(counts.items()): cols[i%4].write(f"🔹 **{name}:** `{count}`")
    st.divider()

    selected_fab = st.sidebar.selectbox("Select Fabrication No", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

    if selected_fab != "Select":
        m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
        history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
        
        # Calculations
        curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

        # C1 to C4
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
            st.write(f"**HMR Cal:** {curr_hmr}")
            st.write(f"**Category:** {m_info.get(cat_col, 'N/A')}")
        with c2:
            st.info("📅 Replacement (9 Parts)")
            for p, cols in parts_map.items(): st.write(f"**{p}:** {format_dt(m_info.get(cols['date']))}")
        with c3:
            st.info("⚙️ Live Remaining (9 Parts)")
            for p, cols in parts_map.items():
                val = pd.to_numeric(m_info.get(cols['rem'], 0), errors='coerce')
                rem = int(val - elapsed) if not pd.isna(val) else 0
                st.write(f"**{p}:** {rem} Hrs" if rem > 0 else f"**{p}:** 🚨 {rem} (Due)")
        with c4:
            st.error("🚨 DUE DATES (9 Parts)")
            for p, cols in parts_map.items(): st.write(f"**{p}:** {format_dt(m_info.get(cols['due']))}")

        st.divider()
        ex1, ex2 = st.columns(2)
        ex1.download_button("📊 Export Excel", to_excel(history), f"History_{selected_fab}.xlsx")
        ex2.download_button("📄 Export Full PDF", create_pdf("Report", {"Fab": selected_fab}, history), f"Report_{selected_fab}.pdf")

elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    # SEARCH BAR
    search_query = st.text_input("🔍 Search by Customer Name, FOC No or Part Code", "")
    if search_query:
        foc_display = foc_df[foc_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
    else: foc_display = foc_df
    
    st.download_button("📊 Export Excel", to_excel(foc_display), "FOC_List.xlsx")
    st.dataframe(foc_display, use_container_width=True, hide_index=True)

elif page == "Service Pending List":
    st.title("⏳ Service Pending")
    b1, b2, b3 = st.columns(3)
    p_df = pd.DataFrame()
    if b1.button("🔴 Overdue"): p_df = master_df[master_df.get('BIS Over Due', 0) != 0].copy()
    if b2.button("🟡 Current Month"): p_df = master_df[master_df.get('BIS Current Month Due', 0) != 0].copy()
    if b3.button("🟢 Next Month"): p_df = master_df[master_df.get('BIS Next Month Due', 0) != 0].copy()
    
    if not p_df.empty:
        st.dataframe(p_df[['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']], use_container_width=True)
