import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Compressor Service Tracker Pro")
st.markdown("Advanced Machine Details (with PDF & Excel Export)")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Clean data
        m_df['Warranty Type'] = m_df['Warranty Type'].astype(str).str.strip()
        m_df['CUSTOMER NAME'] = m_df['CUSTOMER NAME'].astype(str).str.strip()
        
        date_cols = ['Warranty Start Date', 'Warranty End date', 'Last Call HMR Date', 'Oil Replacement Date', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']
        for col in date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

# --- EXCEL EXPORT FUNCTION ---
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- PDF EXPORT FUNCTION (Simple Version) ---
def create_pdf(m_info, history):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Service Report: {m_info['Fabrication No']}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Customer: {m_info['CUSTOMER NAME']}")
    p.drawString(100, 715, f"Current HMR: {m_info['HMR Cal.']}")
    p.drawString(100, 700, f"Warranty Status: {m_info['Warranty Type']}")
    
    p.drawString(100, 670, "Latest Service History:")
    y = 650
    for _, row in history.head(5).iterrows():
        date_str = format_dt(row['Call Logged Date'])
        p.drawString(100, y, f"- {date_str} | HMR: {row['Call HMR']}")
        y -= 20
        if y < 50: break # Page break simple logic
        
    p.showPage()
    p.save()
    return buffer.getvalue()

if master_df is not None:
    # SIDEBAR FILTERS
    st.sidebar.header("🔍 Filters")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Select Customer", options=["All Customers"] + customer_list)

    if selected_customer != "All Customers":
        filtered_df = master_df[master_df['CUSTOMER NAME'] == selected_customer].copy()
        
        # SUMMARY METRICS
        st.subheader(f"📊 Summary: {selected_customer}")
        m1, m2, m3 = st.columns(3)
        total_count = len(filtered_df)
        out_of_warranty_count = len(filtered_df[filtered_df['Warranty Type'].str.contains('Non', na=False, case=False)])
        m1.metric("Total Machines", total_count)
        m2.metric("In Warranty", total_count - out_of_warranty_count)
        m3.metric("Out of Warranty", out_of_warranty_count)

        # DOWNLOAD BUTTON FOR FULL CUSTOMER LIST
        excel_data = to_excel(filtered_df)
        st.download_button(label="📥 Download Customer Machine List (Excel)", data=excel_data, file_name=f"{selected_customer}_Machines.xlsx")
        st.divider()
    else:
        filtered_df = master_df

    selected_fab = st.sidebar.selectbox("2. Select Fabrication Number", options=["Select Number"] + sorted(filtered_df['Fabrication No'].unique().astype(str)))

    if selected_fab != "Select Number":
        m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)

        # BUTTONS FOR INDIVIDUAL MACHINE REPORT
        st.subheader("📋 Export Reports")
        c1, c2 = st.columns(2)
        with c1:
            pdf_data = create_pdf(m_info, history)
            st.download_button(label="📄 Download Machine PDF Report", data=pdf_data, file_name=f"Report_{selected_fab}.pdf", mime="application/pdf")
        with c2:
            hist_excel = to_excel(history)
            st.download_button(label="📊 Download Service History (Excel)", data=hist_excel, file_name=f"History_{selected_fab}.xlsx")

        # ... (Rest of your original layout code for Section 1, 2, 3 remains same)
        st.info(f"Yahan aapki machine {selected_fab} ki baaki details pehle ki tarah dikhengi...")

else:
    st.error("Excel files nahi mili!")
