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
    m_od_name = find_file("Master_OD_Data.xlsx")
    s_name = find_file("Service_Details.xlsx")
    f_name = find_file("Active_FOC.xlsx")
    
    if not s_name or not f_name:
        return None, None, None, None, ["Required Service/FOC files missing."]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl') if m_name else pd.DataFrame()
        m_od_df = pd.read_excel(m_od_name, engine='openpyxl') if m_od_name else pd.DataFrame()
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        for df in [m_df, m_od_df, s_df, f_df]:
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
        
        return m_df, m_od_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, None, [str(e)]

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

master_df, master_od_df, service_df, foc_df, errors = load_data()
if errors: st.error(f"Error: {errors}"); st.stop()

# --- SIDEBAR ---
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Dashboard Chunein:", ["Machine Tracker", "OD Machine Tracker", "FOC Tracker List", "Service Pending List"])

# Mapping for Parts (OD Dashboard logic)
od_parts = {
    'Oil': {'date': 'MDA Oil R Date', 'due': 'OIL DUE DATE'},
    'AF': {'date': 'MDA AF R Date', 'due': 'AF DUE DATE'},
    'OF': {'date': 'MDA OF R Date', 'due': 'OF DUE DATE'},
    'AOS': {'date': 'MDA AOS R Date', 'due': 'AOS DUE DATE'},
    'RGT': {'date': 'MDA RGT R Date', 'due': 'RGT DUE DATE'},
    'Valvekit': {'date': 'MDA Valvekit R Date', 'due': 'VALVEKIT DUE DATE'},
    'PF': {'date': 'MDA PF R DATE', 'due': 'PF DUE DATE'},
    'FF': {'date': 'MDA FF R DATE', 'due': 'FF DUE DATE'},
    'CF': {'date': 'MDA CF R DATE', 'due': 'CF DUE DATE'}
}

# --- RENDER DASHBOARDS ---

if page == "Machine Tracker":
    # (Purana standard machine tracker code yahan rahega)
    st.title("🛠️ Standard Machine Tracker")
    # ... Same logic as previous version ...
    st.info("Puraana data dashboard yahan dikhega.")

elif page == "OD Machine Tracker":
    st.title("🛡️ OD Machine Tracker (Master_OD_Data)")
    if master_od_df.empty:
        st.warning("Master_OD_Data.xlsx file load nahi hui.")
    else:
        cust_list = sorted(master_od_df['Customer Name'].unique().astype(str))
        sel_cust = st.sidebar.selectbox("1. Customer", options=["All"] + cust_list)
        df_f = master_od_df if sel_cust == "All" else master_od_df[master_od_df['Customer Name'] == sel_cust]
        
        sel_fab = st.sidebar.selectbox("2. Fabrication No", options=["Select"] + sorted(df_f['Fabrication No'].astype(str).unique()))

        if sel_fab != "Select":
            row = df_f[df_f['Fabrication No'].astype(str) == sel_fab].iloc[0]
            
            # --- SECTION C1 to C4 ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer Name:** {row.get('Customer Name')}")
                st.write(f"**Model:** {row.get('Model', 'N/A')}")
                st.write(f"**Sub Group:** {row.get('Product Sub Group', 'N/A')}")
                st.write(f"**Category:** {row.get('Category', 'N/A')}")
            with c2:
                st.info("📅 Replacement (OD)")
                for label, cols in od_parts.items():
                    st.write(f"**{label} R-Date:** {format_dt(row.get(cols['date']))}")
            with c3:
                st.info("⚙️ Live Remaining / Status")
                st.write(f"**AVG Running Hrs/Day:** {row.get('MDA AVG Running Hours Per Day', 'N/A')}")
                st.write(f"**HMR Date:** {format_dt(row.get('MDA HMR Date'))}")
            with c4:
                st.error("🚨 DUE DATES (OD)")
                for label, cols in od_parts.items():
                    st.write(f"**{label} Due:** {format_dt(row.get(cols['due']))}")

            # --- FOC & SERVICE HISTORY MATCHING ---
            st.divider()
            foc_match = foc_df[foc_df['FABRICATION NO'].astype(str) == sel_fab].copy()
            if not foc_match.empty:
                st.subheader("🎁 FOC Parts for this Machine")
                st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)

            st.subheader("🕒 Service History")
            hist = service_df[service_df['Fabrication Number'].astype(str) == sel_fab].copy().sort_values(by='Call Logged Date', ascending=False)
            if not hist.empty:
                for _, s_row in hist.iterrows():
                    with st.expander(f"📅 {format_dt(s_row.get('Call Logged Date'))} | ⚙️ {s_row.get('Call HMR')} HMR | 🛠️ {s_row.get('Call Type','N/A')}"):
                        st.write(f"**Call Type:** `{s_row.get('Call Type', 'N/A')}`")
                        st.write(f"**Engineer:** {s_row.get('Service Engineer', 'N/A')}")
                        st.info(s_row.get('Service Engineer Comments', 'N/A'))
            else: st.warning("Service history nahi mili.")

elif page == "FOC Tracker List":
    st.title("📦 Master FOC Tracker List")
    query = st.text_input("🔍 Search Customer, Part or FOC No", "")
    f_disp = foc_df[foc_df.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)] if query else foc_df
    st.download_button("📊 Export Excel", to_excel(f_disp), "FOC_Master_List.xlsx")
    st.dataframe(f_disp, use_container_width=True, hide_index=True)

elif page == "Service Pending List":
    st.title("⏳ Service Pending")
    # (Pending list logic with buttons as before)
    st.info("Pending Dashboard filter yahan kaam karenge.")
