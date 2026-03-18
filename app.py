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
        return None, None, None, ["Files Missing"]

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

# --- PDF EXPORT (FULL LIST) ---
def create_pdf(title, info_dict, table_df=None):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, title)
    p.setFont("Helvetica", 10)
    y = height - 70
    for key, val in info_dict.items():
        p.drawString(50, y, f"{key}: {val}")
        y -= 15
    
    p.line(50, y, width - 50, y)
    y -= 30
    
    if table_df is not None and not table_df.empty:
        p.setFont("Helvetica-Bold", 9)
        display_cols = table_df.columns.tolist()[:7]
        curr_x = 50
        for col in display_cols:
            p.drawString(curr_x, y, str(col)[:15])
            curr_x += 100
        
        y -= 20
        p.setFont("Helvetica", 8)
        for _, row in table_df.iterrows():
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 8)
            curr_x = 50
            for col in display_cols:
                p.drawString(curr_x, y, str(row.get(col, "N/A"))[:18])
                curr_x += 100
            y -= 15
            
    p.showPage()
    p.save()
    return buffer.getvalue()

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return str(dt)

master_df, service_df, foc_df, missing = load_data()

if master_df is not None:
    st.sidebar.title("📌 Navigation")
    page = st.sidebar.radio("Go to:", ["Machine Tracker", "FOC Tracker List", "Service Pending List"])

    if page == "Machine Tracker":
        st.title("🛠️ Machine Tracker Pro")
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("Customer", options=["All"] + customer_list)
        cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
        
        selected_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

        if selected_fab != "Select":
            m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
            history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy()
            
            # Export Buttons
            ex1, ex2 = st.columns(2)
            ex1.download_button("📊 Export Excel", to_excel(history), f"History_{selected_fab}.xlsx")
            ex2.download_button("📄 Export PDF", create_pdf("Machine Detail Report", {"Fab": selected_fab, "Customer": m_info['CUSTOMER NAME']}, history), f"Report_{selected_fab}.pdf")

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            
            curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
            last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
            elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

            with c1:
                st.info("📋 Customer Info")
                st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
                st.write(f"**Current HMR:** {curr_hmr}")
                st.write(f"**Last Service HMR:** {last_hmr}")

            with c2:
                st.info("📅 Replacement")
                # Flexible column check
                st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
                st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
                st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")

            with c3:
                st.info("⚙️ Live Remaining")
                rem_items = {'HMR - Oil remaining': 'Oil', 'Main Oil filter Remaining Hours': 'MOF', 'HMR - Separator remaining': 'AOS'}
                for col, lbl in rem_items.items():
                    val = pd.to_numeric(m_info.get(col, 0), errors='coerce')
                    rem = int(val - elapsed) if not pd.isna(val) else 0
                    st.write(f"**{lbl}:** {rem} Hrs" if rem > 0 else f"**{lbl}:** 🚨 {rem} (Due)")

            with c4:
                st.error("🚨 DUE DATES")
                st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
                st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
                st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

            # FOC Section
            st.divider()
            st.subheader("🎁 FOC Parts")
            f_col = 'FABRICATION NO' if 'FABRICATION NO' in foc_df.columns else 'FABRICATION NO.'
            foc_match = foc_df[foc_df[f_col].astype(str) == selected_fab].copy()
            if not foc_match.empty:
                st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)

else:
    st.error("Data Load Failed!")
