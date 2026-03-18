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

# --- ROBUST PDF EXPORT FUNCTION (Full List) ---
def create_pdf(title, info_dict, table_df=None):
    buffer = BytesIO()
    # Landscape orientation taaki zyada columns fit ho sakein
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, title)
    
    p.setFont("Helvetica", 10)
    y = height - 80
    for key, val in info_dict.items():
        p.drawString(50, y, f"{key}: {val}")
        y -= 15
    
    p.line(50, y, width - 50, y)
    y -= 30
    
    # Table Content
    if table_df is not None and not table_df.empty:
        p.setFont("Helvetica-Bold", 10)
        # Displaying first 7-8 columns in landscape
        display_cols = table_df.columns.tolist()[:8]
        
        curr_x = 50
        for col in display_cols:
            p.drawString(curr_x, y, str(col)[:15])
            curr_x += 90
        
        y -= 20
        p.setFont("Helvetica", 8)
        for _, row in table_df.iterrows():
            if y < 50: # Page break logic
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 8)
            
            curr_x = 50
            for col in display_cols:
                val = str(row.get(col, "N/A"))
                p.drawString(curr_x, y, val[:18])
                curr_x += 90
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

    # --- 1. MACHINE TRACKER ---
    if page == "Machine Tracker":
        st.title("🛠️ Machine Tracker")
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("Customer", options=["All"] + customer_list)
        cust_filtered = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
        
        selected_fab = st.sidebar.selectbox("Fabrication No", options=["Select"] + sorted(cust_filtered['Fabrication No'].astype(str).unique()))

        if selected_fab != "Select":
            m_info = cust_filtered[cust_filtered['Fabrication No'].astype(str) == selected_fab].iloc[0]
            history = service_df[service_df['Fabrication Number'].astype(str) == selected_fab].copy()
            
            # Export Buttons Row
            ex1, ex2 = st.columns(2)
            ex1.download_button("📊 Export History to Excel", to_excel(history), f"History_{selected_fab}.xlsx")
            ex2.download_button("📄 Export Machine PDF", create_pdf("Service History Report", {"Fab No": selected_fab, "Customer": m_info['CUSTOMER NAME']}, history), f"Report_{selected_fab}.pdf")

            # Machine Details Display
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
            last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
            elapsed = curr_hmr - last_hmr if curr_hmr > last_hmr else 0

            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
                st.write(f"**HMR:** {curr_hmr}")
            
            with c3:
                st.info("⚙️ Live Remaining")
                # KEYERROR FIX: Using .get()
                items = {'HMR - Oil remaining': 'Oil', 'Main Oil filter Remaining Hours': 'MOF', 'HMR - Separator remaining': 'AOS'}
                for col, lbl in items.items():
                    val = pd.to_numeric(m_info.get(col, 0), errors='coerce')
                    rem = int(val - elapsed)
                    st.write(f"**{lbl}:** {rem} Hrs" if rem > 0 else f"**{lbl}:** 🚨 {rem} (Due)")

    # --- 2. FOC TRACKER LIST ---
    elif page == "FOC Tracker List":
        st.title("📦 FOC Tracker List")
        c1, c2 = st.columns(2)
        c1.download_button("📊 Download FOC Excel", to_excel(foc_df), "FOC_Master.xlsx")
        c2.download_button("📄 Download FOC PDF (Full List)", create_pdf("FOC Master List", {"Total Items": len(foc_df)}, foc_df), "FOC_List.pdf")
        st.dataframe(foc_df, use_container_width=True)

    # --- 3. SERVICE PENDING LIST ---
    elif page == "Service Pending List":
        st.title("⏳ Service Pending")
        b1, b2, b3 = st.columns(3)
        p_df = pd.DataFrame()
        if b1.button("🔴 Overdue"): p_df = master_df[master_df['BIS Over Due'] != 0].copy()
        
        if not p_df.empty:
            st.download_button("📄 Download Pending PDF", create_pdf("Service Pending List", {"Count": len(p_df)}, p_df), "Pending.pdf")
            st.dataframe(p_df, use_container_width=True)

else:
    st.error("Data Load Failed!")
