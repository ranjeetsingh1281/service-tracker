import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# Data Load Function
@st.cache_data
def load_data():
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    if os.path.exists(m_file) and os.path.exists(s_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        
        # Data Cleaning
        m_df['Warranty Type'] = m_df['Warranty Type'].astype(str).str.strip()
        m_df['CUSTOMER NAME'] = m_df['CUSTOMER NAME'].astype(str).str.strip()
        
        date_cols = [
            'Warranty Start Date', 'Warranty End date', 'Last Call HMR Date',
            'OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'AOS DUE DATE', 
            'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE'
        ]
        for col in date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
        return m_df, s_df
    return None, None

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

def create_pdf(m_info, history):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"Machine Report: {m_info['Fabrication No']}")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, f"Customer: {m_info['CUSTOMER NAME']}")
    p.drawString(50, 715, f"Current HMR: {m_info['HMR Cal.']}")
    p.line(50, 705, 550, 705)
    y = 680
    for _, row in history.head(10).iterrows():
        p.drawString(60, y, f"- {format_dt(row['Call Logged Date'])} | HMR: {row['Call HMR']}")
        y -= 20
    p.showPage()
    p.save()
    return buffer.getvalue()

master_df, service_df = load_data()

if master_df is not None:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("📌 Menu")
    page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

    # --- PAGE 1: MACHINE TRACKER ---
    if page == "Machine Tracker":
        st.title("🛠️ ELGi Compressor Service Tracker")
        
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("1. Select Customer", options=["All Customers"] + customer_list)

        if selected_customer != "All Customers":
            filtered_df = master_df[master_df['CUSTOMER NAME'] == selected_customer].copy()
            st.subheader(f"📊 Summary: {selected_customer}")
            m1, m2, m3 = st.columns(3)
            out_count = len(filtered_df[filtered_df['Warranty Type'].str.contains('Non', na=False, case=False)])
            m1.metric("Total Machines", len(filtered_df))
            m2.metric("In Warranty", len(filtered_df) - out_count)
            m3.metric("Out of Warranty", out_count)
            st.divider()
        else:
            filtered_df = master_df

        selected_fab = st.sidebar.selectbox("2. Select Fabrication No", options=["Select Number"] + sorted(filtered_df['Fabrication No'].unique().astype(str)))

        if selected_fab != "Select Number":
            m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
            history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)

            # Export Buttons
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1: st.download_button("📄 Download PDF Report", create_pdf(m_info, history), f"Report_{selected_fab}.pdf")
            with c_ex2: st.download_button("📊 Download History (Excel)", to_excel(history), f"History_{selected_fab}.xlsx")

            # Details
            current_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
            last_service_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
            elapsed = current_hmr - last_service_hmr
            
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Info")
                st.write(f"**Customer:** {m_info.get('CUSTOMER NAME')}")
                st.write(f"**Current HMR:** {current_hmr}")
            with c2:
                st.info("📅 Replacement")
                st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
            with c3:
                st.info("⚙️ Live Remaining")
                for orig, label in {'HMR - Oil remaining': 'Oil', 'HMR - Separator remaining': 'AOS'}.items():
                    val = pd.to_numeric(m_info.get(orig, 0), errors='coerce') - elapsed
                    st.write(f"**{label}:** {int(val)} Hrs" if val > 0 else f"**{label}:** 🚨 {int(val)} (Due)")
            with c4:
                st.error("🚨 DUE DATES")
                st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")

            st.divider()
            st.subheader("🕒 Service History")
            for _, row in history.iterrows():
                with st.expander(f"📅 {format_dt(row['Call Logged Date'])} | ⚙️ {row.get('Call HMR')} HMR"):
                    st.info(row.get('Service Engineer Comments', 'No comments.'))

    # --- PAGE 2: SERVICE PENDING LIST ---
    elif page == "Service Pending List":
        st.title("⏳ Upcoming Service Pending List")
        st.markdown("Agle 30 dinon mein due hone wali services:")

        # Filter for next 30 days
        today = pd.Timestamp.now()
        next_30_days = today + pd.Timedelta(days=30)
        
        pending_list = master_df[
            (master_df['OIL DUE DATE'] <= next_30_days) | 
            (master_df['AOS DUE DATE'] <= next_30_days)
        ].copy()

        if not pending_list.empty:
            st.warning(f"Total {len(pending_list)} machines ki service aane waali hai.")
            
            # Export Pending List
            st.download_button("📥 Download Pending List (Excel)", to_excel(pending_list), "Pending_Services.xlsx")
            
            # Show Table
            display_cols = ['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AOS DUE DATE', 'HMR Cal.']
            st.dataframe(pending_list[display_cols].sort_values(by='OIL DUE DATE'), use_container_width=True)
        else:
            st.success("Aglo 30 dinon mein koi service pending nahi hai!")

else:
    st.error("Excel files nahi mili!")
