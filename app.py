import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

st.title("🛠️ ELGi Compressor Service Tracker Pro")
st.markdown("Advanced Machine Details (Reports + Live Data)")

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
        
        date_columns = [
            'Warranty Start Date', 'Warranty End date', 'Last Call HMR Date',
            'Oil Replacement Date', 'Air filter Compressor Replaced Date', 
            'Air filter Engine Replaced Date', 'Main Oil filter Replaced Date', 
            'Return Oil filter Replaced Date', 'AOS Replaced Date', 
            'Greasing Done Date', '1500 Valve kit Replaced Date', 
            '3000 Valve kit Replaced Date', 'OIL DUE DATE', 'AFC DUE DATE', 
            'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 'AOS DUE DATE', 
            'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE'
        ]
        for col in date_columns:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

master_df, service_df = load_data()

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

# Export Functions
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

def create_pdf(m_info, history):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"ELGi Machine Report: {m_info['Fabrication No']}")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, f"Customer: {m_info['CUSTOMER NAME']}")
    p.drawString(50, 715, f"Current HMR: {m_info['HMR Cal.']}")
    p.line(50, 705, 550, 705)
    
    y = 680
    p.drawString(50, y, "Latest Service History:")
    y -= 20
    for _, row in history.head(10).iterrows():
        p.drawString(60, y, f"- {format_dt(row['Call Logged Date'])} | HMR: {row['Call HMR']} | {str(row['Service Engineer Comments'])[:50]}...")
        y -= 20
    p.showPage()
    p.save()
    return buffer.getvalue()

if master_df is not None:
    # SIDEBAR
    st.sidebar.header("🔍 Filters")
    customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
    selected_customer = st.sidebar.selectbox("1. Select Customer", options=["All Customers"] + customer_list)

    if selected_customer != "All Customers":
        filtered_df = master_df[master_df['CUSTOMER NAME'] == selected_customer].copy()
        
        # Summary Metrics
        st.subheader(f"📊 Summary: {selected_customer}")
        m1, m2, m3 = st.columns(3)
        total_count = len(filtered_df)
        out_of_warranty_count = len(filtered_df[filtered_df['Warranty Type'].str.contains('Non', na=False, case=False)])
        m1.metric("Total Machines", total_count)
        m2.metric("In Warranty", total_count - out_of_warranty_count)
        m3.metric("Out of Warranty", out_of_warranty_count)

        st.download_button(label="📥 Download Customer Machine List (Excel)", data=to_excel(filtered_df), file_name=f"{selected_customer}_List.xlsx")
        st.divider()
    else:
        filtered_df = master_df

    selected_fab = st.sidebar.selectbox("2. Select Fabrication Number", options=["Select Number"] + sorted(filtered_df['Fabrication No'].unique().astype(str)))

    if selected_fab != "Select Number":
        m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
        history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)

        # --- SECTION: EXPORT BUTTONS ---
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button(label="📄 Download PDF Report", data=create_pdf(m_info, history), file_name=f"Report_{selected_fab}.pdf")
        with col_ex2:
            st.download_button(label="📊 Download History (Excel)", data=to_excel(history), file_name=f"History_{selected_fab}.xlsx")

        # --- SECTION 1: WARRANTY ---
        st.divider()
        st.subheader(f"🛡️ Obligation (Warranty): {m_info.get('Warranty Type', 'N/A')}")
        st.write(f"📅 **Start:** {format_dt(m_info.get('Warranty Start Date'))} | **End:** {format_dt(m_info.get('Warranty End date'))}")

        # Live Calculation
        current_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
        last_service_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
        elapsed_hours = current_hmr - last_service_hmr if pd.notna(current_hmr) and pd.notna(last_service_hmr) else 0

        # --- SECTION 2: 4-COLUMN DETAILS ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("📋 Machine Info")
            st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
            st.write(f"**Current HMR:** {current_hmr}")
            st.write(f"**Since Last Service:** {int(elapsed_hours)} Hrs")
        with c2:
            st.info("📅 Replacement Dates")
            st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
            st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
        with c3:
            st.info("⚙️ Live Remaining Hours")
            rem_cols = {'HMR - Oil remaining': 'Oil', 'Air filter replaced - Compressor Remaining Hours': 'AFC', 'HMR - Separator remaining': 'AOS'}
            for orig, label in rem_cols.items():
                val = pd.to_numeric(m_info.get(orig, 0), errors='coerce') - elapsed_hours
                st.write(f"**{label}:** {int(val)} Hrs" if val > 0 else f"**{label}:** 🚨 {int(val)} (Due)")
        with c4:
            st.error("🚨 DUE DATES")
            st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
            st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
            st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

        # --- SECTION 3: HISTORY ---
        st.divider()
        st.subheader("🕒 Service History")
        if not history.empty:
            for _, row in history.iterrows():
                with st.expander(f"📅 {format_dt(row['Call Logged Date'])} | ⚙️ {row.get('Call HMR', 'N/A')} HMR"):
                    st.info(row.get('Service Engineer Comments', 'No comments.'))
    else:
        st.info("👈 Sidebar se Customer aur Machine select karein.")
else:
    st.error("Files nahi mili!")
