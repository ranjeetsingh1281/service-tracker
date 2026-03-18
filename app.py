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
    m_file = "Master_Data.xlsx"
    s_file = "Service_Details.xlsx"
    f_file = "Active_FOC.xlsx"
    
    if os.path.exists(m_file) and os.path.exists(s_file) and os.path.exists(f_file):
        m_df = pd.read_excel(m_file, engine='openpyxl')
        s_df = pd.read_excel(s_file, engine='openpyxl')
        f_df = pd.read_excel(f_file, engine='openpyxl')
        
        # Clean Headers (Invisible spaces hatana)
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
        
        # Data Cleaning
        m_df['Warranty Type'] = m_df['Warranty Type'].astype(str).str.strip()
        m_df['CUSTOMER NAME'] = m_df['CUSTOMER NAME'].astype(str).str.strip()
        
        # Date Conversion
        date_cols = [
            'Warranty Start Date', 'Warranty End date', 'OIL DUE DATE', 
            'AFC DUE DATE', 'AFE DUE DATE', 'MOF DUE DATE', 'ROF DUE DATE', 
            'AOS DUE DATE', 'RGT DUE DATE', '1500 KIT DUE DATE', '3000 KIT DUE DATE',
            'Oil Replacement Date', 'Air filter Compressor Replaced Date', 
            'Air filter Engine Replaced Date', 'Main Oil filter Replaced Date', 
            'Return Oil filter Replaced Date', 'AOS Replaced Date', 'Greasing Done Date', 
            '1500 Valve kit Replaced Date', '3000 Valve kit Replaced Date'
        ]
        for col in date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        
        if 'Call Logged Date' in s_df.columns:
            s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
            
        return m_df, s_df, f_df
    return None, None, None

# Helper Functions
def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def create_pdf(m_info, history):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"ELGi Machine Report: {m_info['Fabrication No']}")
    p.setFont("Helvetica", 10)
    p.drawString(50, 735, f"Customer: {m_info['CUSTOMER NAME']}")
    p.line(50, 725, 550, 725)
    y = 700
    p.drawString(50, y, "Service History:")
    y -= 20
    for _, row in history.head(10).iterrows():
        ct = row.get('Call Type', 'N/A')
        p.drawString(60, y, f"- {format_dt(row['Call Logged Date'])} | HMR: {row.get('Call HMR','N/A')} | Type: {ct}")
        y -= 15
    p.showPage()
    p.save()
    return buffer.getvalue()

master_df, service_df, foc_df = load_data()

if master_df is not None:
    st.sidebar.title("📌 Menu")
    page = st.sidebar.radio("Option Chunein:", ["Machine Tracker", "Service Pending List"])

    # --- PAGE 1: MACHINE TRACKER ---
    if page == "Machine Tracker":
        st.title("🛠️ Machine Tracker Pro")
        
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("1. Select Customer", options=["All"] + customer_list)
        
        filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
        selected_fab = st.sidebar.selectbox("2. Select Fabrication No", options=["Select"] + sorted(filtered_df['Fabrication No'].unique().astype(str)))

        if selected_fab != "Select":
            m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
            history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)

            # Export Buttons
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1: st.download_button("📄 PDF Report", create_pdf(m_info, history), f"Report_{selected_fab}.pdf")
            with c_ex2: st.download_button("📊 History Excel", to_excel(history), f"History_{selected_fab}.xlsx")

            # Calc HMR
            curr_hmr = pd.to_numeric(m_info.get('HMR Cal.', 0), errors='coerce')
            last_hmr = pd.to_numeric(m_info.get('Last Call HMR', 0), errors='coerce')
            elapsed = curr_hmr - last_hmr if pd.notna(curr_hmr) and pd.notna(last_hmr) else 0

            # --- DISPLAY DATA (C1-C4) ---
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Machine Info")
                st.write(f"**Avg. Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')}")
                st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')}")
                st.write(f"**Current HMR:** {curr_hmr}")
                st.write(f"**Since Last Service:** {int(elapsed)} Hrs")

            with c2:
                st.info("📅 Replacement")
                st.write(f"**Oil R-Date:** {format_dt(m_info.get('Oil Replacement Date'))}")
                st.write(f"**AFC R-Date:** {format_dt(m_info.get('Air filter Compressor Replaced Date'))}")
                st.write(f"**AOS R-Date:** {format_dt(m_info.get('AOS Replaced Date'))}")

            with c3:
                st.info("⚙️ Live Remaining")
                rem_cols = {'HMR - Oil remaining': 'Oil', 'HMR - Separator remaining': 'AOS'}
                for orig, label in rem_cols.items():
                    val = pd.to_numeric(m_info.get(orig, 0), errors='coerce') - elapsed
                    st.write(f"**{label}:** {int(val)} Hrs" if val > 0 else f"**{label}:** 🚨 {int(val)} (Due)")

            with c4:
                st.error("🚨 DUE DATES")
                st.write(f"**Oil Due:** {format_dt(m_info.get('OIL DUE DATE'))}")
                st.write(f"**AFC Due:** {format_dt(m_info.get('AFC DUE DATE'))}")
                st.write(f"**AOS Due:** {format_dt(m_info.get('AOS DUE DATE'))}")

            # --- NAYA SECTION: FOC PARTS ---
            st.divider()
            st.subheader("🎁 FOC Parts History (Free of Cost)")
            foc_record = foc_df[foc_df['FABRICATION NO.'] == selected_fab].copy()
            if not foc_record.empty:
                st.dataframe(foc_record[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
            else:
                st.info("No FOC records found for this machine.")

            # --- SERVICE HISTORY ---
            st.divider()
            st.subheader("🕒 Service History")
            if not history.empty:
                for _, row in history.iterrows():
                    c_type = row.get('Call Type', 'N/A')
                    header = f"📅 {format_dt(row['Call Logged Date'])} | ⚙️ {row.get('Call HMR','N/A')} HMR | 🛠️ {c_type}"
                    with st.expander(header):
                        st.write(f"**Type:** {c_type} | **Engineer:** {row.get('Service Engineer', 'N/A')}")
                        st.info(row.get('Service Engineer Comments', 'No comments.'))
            else: st.warning("No history found.")

    # --- PAGE 2: SERVICE PENDING LIST ---
    elif page == "Service Pending List":
        st.title("⏳ BIS Service Dashboard")
        b1, b2, b3 = st.columns(3)
        pending_list = pd.DataFrame()

        if b1.button("🔴 BIS Over Due"):
            pending_list = master_df[master_df['BIS Over Due'] != 0].copy()
        if b2.button("🟡 BIS Current Month"):
            pending_list = master_df[master_df['BIS Current Month Due'] != 0].copy()
        if b3.button("🟢 BIS Next Month"):
            pending_list = master_df[master_df['BIS Next Month Due'] != 0].copy()

        if not pending_list.empty:
            st.write(f"Records: {len(pending_list)}")
            st.download_button("📥 Download Excel", to_excel(pending_list), "Pending_List.xlsx")
            cols = ['CUSTOMER NAME', 'Fabrication No', 'OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']
            df_disp = pending_list[cols].copy()
            for c in ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE']: df_disp[c] = df_disp[c].apply(format_dt)
            st.dataframe(df_disp, use_container_width=True)

else:
    st.error("Excel files (Master, Service, FOC) not found!")
