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
        
        # Saari Date Columns ko convert karna
        date_cols = [
            'Warranty Start Date', 'Warranty End date', 'Last Call HMR Date',
            'OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'MOF DUE DATE', 
            'ROF DUE DATE', 'AOS DUE DATE', 'RGT DUE DATE', '1500 KIT DUE DATE', 
            '3000 KIT DUE DATE', 'Oil Replacement Date', 'Air filter Compressor Replaced Date', 
            'Air filter Engine Replaced Date', 'Main Oil filter Replaced Date', 
            'Return Oil filter Replaced Date', 'AOS Replaced Date', 'Greasing Done Date', 
            '1500 Valve kit Replaced Date', '3000 Valve kit Replaced Date'
        ]
        for col in date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        
        if 'Call Logged Date' in s_df.columns:
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
    p.drawString(50, 750, f"ELGi Machine Report: {m_info['Fabrication No']}")
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
    st.sidebar.title("📌 Navigation Menu")
    page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

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

            # Calculations
            current_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
            last_service_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
            elapsed = current_hmr - last_service_hmr if pd.notna(current_hmr) and pd.notna(last_service_hmr) else 0
            
            # --- SECTION 1: MACHINE HEADER ---
            st.divider()
            st.subheader(f"🛡️ Obligation: {m_info.get('Warranty Type', 'N/A')}")
            st.write(f"📅 **Warranty Start:** {format_dt(m_info.get('Warranty Start Date'))} | **End:** {format_dt(m_info.get('Warranty End date'))}")

            # --- DISPLAY DATA (Updated Sections) ---
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.info("📋 Machine Info")
                st.write(f"**Avg. Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')} 👈")
                st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')} 👈")
                st.write(f"**Due Remarks:** {m_info.get('Due remarks', 'N/A')}")
                st.write(f"**Last Call HMR:** {m_info.get('Last Call HMR', 'N/A')}")
                st.write(f"**Last Call HMR Date:** {format_dt(m_info.get('Last Call HMR Date'))}")
                st.write(f"**Current HMR:** {current_hmr}")
                st.write(f"**Since Last Service:** {int(elapsed)} Hrs")
            
            with c2:
                st.info("📅 Replacement")
                st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
                st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
                st.write(f"**AFE R-Date:** {format_dt(m_info.get('Air filter Engine Replaced Date'))}")
                st.write(f"**MOF R-Date:** {format_dt(m_info.get('Main Oil filter Replaced Date'))}")
                st.write(f"**ROF R-Date:** {format_dt(m_info.get('Return Oil filter Replaced Date'))}")
                st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")
                st.write(f"**Greasing R-Date:** {format_dt(m_info.get('Greasing Done Date'))}")
                st.write(f"**1500 Kit R-Date:** {format_dt(m_info.get('1500 Valve kit Replaced Date'))}")
                st.write(f"**3000 Kit R-Date:** {format_dt(m_info.get('3000 Valve kit Replaced Date'))}")
            
            with c3:
                st.info("⚙️ Live Remaining")
                # Parts mapping for live deduction
                rem_cols = {
                    'HMR - Oil remaining': 'Oil', 
                    'Air filter replaced - Compressor Remaining Hours': 'AFC',
                    'Air filter replaced - Engine Remaining Hours': 'AFE',
                    'Main Oil filter Remaining Hours': 'MOF',
                    'Return Oil filter Remaining Hours': 'ROF',
                    'HMR - Separator remaining': 'AOS',
                    'HMR - Motor regressed remaining': 'Greasing',
                    '1500 Valve kit Remaining Hours': '1500 Kit',
                    '3000 Valve kit Remaining Hours': '3000 Kit'
                }
                for orig, label in rem_cols.items():
                    val = pd.to_numeric(m_info.get(orig, 0), errors='coerce') - elapsed
                    if val <= 0:
                        st.write(f"**{label}:** 🚨 {int(val)} (Due)")
                    else:
                        st.write(f"**{label}:** {int(val)} Hrs")
            
            with c4:
                st.error("🚨 DUE DATES")
                st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
                st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
                st.write(f"**AFE Due:** {format_dt(m_info.get('AFE DUE DATE'))}")
                st.write(f"**MOF Due:** {format_dt(m_info.get('MOF DUE DATE'))}")
                st.write(f"**ROF Due:** {format_dt(m_info.get('ROF DUE DATE'))}")
                st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")
                st.write(f"**Greasing Due:** {format_dt(m_info.get('RGT DUE DATE'))}")
                st.write(f"**1500 Kit Due:** {format_dt(m_info.get('1500 KIT DUE DATE'))}")
                st.write(f"**3000 Kit Due:** {format_dt(m_info.get('3000 KIT DUE DATE'))}")

            st.divider()
            st.subheader("🕒 Service History")
            if not history.empty:
                for _, row in history.iterrows():
                    with st.expander(f"📅 {format_dt(row['Call Logged Date'])} | ⚙️ {row.get('Call HMR')} HMR"):
                        st.info(row.get('Service Engineer Comments', 'No comments.'))
            else: st.warning("No history found.")
        else: st.info("👈 Sidebar se Customer aur Machine select karein.")
# --- SECTION 2: SERVICE PENDING LIST (WITH ACTION BUTTONS) ---
    elif page == "Service Pending List":
        st.title("⏳ Service Pending Dashboard")
        st.markdown("Niche diye gaye buttons par click karke due list generate karein:")

        # Action Buttons Layout
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        # Session state to keep track of filter
        if 'filter_type' not in st.session_state:
            st.session_state.filter_type = None

        with btn_col1:
            if st.button("🔴 1. BIS Over Due", use_container_width=True):
                st.session_state.filter_type = "Over Due"
        
        with btn_col2:
            if st.button("🟡 2. BIS Current Month Due", use_container_width=True):
                st.session_state.filter_type = "Current Month"
        
        with btn_col3:
            if st.button("🟢 3. BIS Next Month Due", use_container_width=True):
                st.session_state.filter_type = "Next Month"

        # Logic to filter based on button click
        pending_list = pd.DataFrame() # Khali dataframe

        if st.session_state.filter_type == "Over Due":
            st.subheader("🚨 List: BIS Over Due")
            # Logic: Jinka 'BIS Over Due' column 0 se bada ho ya 'Yes' ho
            pending_list = master_df[master_df['BIS Over Due'].notna() & (master_df['BIS Over Due'] != 0)].copy()

        elif st.session_state.filter_type == "Current Month":
            st.subheader("📅 List: BIS Current Month Due")
            pending_list = master_df[master_df['BIS Current Month Due'].notna() & (master_df['BIS Current Month Due'] != 0)].copy()

        elif st.session_state.filter_type == "Next Month":
            st.subheader("🗓️ List: BIS Next Month Due")
            pending_list = master_df[master_df['BIS Next Month Due'].notna() & (master_df['BIS Next Month Due'] != 0)].copy()

        # Display Result
        if not pending_list.empty:
            st.write(f"Total Records Found: **{len(pending_list)}**")
            
            # Download Button
            st.download_button("📥 Download This List (Excel)", to_excel(pending_list), f"BIS_{st.session_state.filter_type}_List.xlsx")
            
            # Display Columns
            check_cols = ['OIL DUE DATE', 'AFC DUE DATE', 'AFE DUE DATE', 'AOS DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE']
            display_cols = ['CUSTOMER NAME', 'Fabrication No', 'Contact No. 1'] + check_cols
            
            # Formatting and Display
            display_df = pending_list[display_cols].copy()
            for col in check_cols:
                display_df[col] = display_df[col].apply(format_dt)
            
            st.dataframe(display_df, use_container_width=True)
        elif st.session_state.filter_type is not None:
            st.info(f"Is category ({st.session_state.filter_type}) mein koi data nahi mila.")
        else:
            st.info("Upar diye gaye buttons mein se ek select karein list dekhne ke liye.")
