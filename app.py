import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DYNAMIC FILE LOADER ---
@st.cache_data
def load_data():
    # Folder mein jo bhi files hain unki list lein
    folder_files = os.listdir('.')
    
    def find_file(target_name):
        for f in folder_files:
            if f.lower() == target_name.lower():
                return f
        return None

    # Target files dhoondein (Case-Insensitive)
    m_name = find_file("Master_Data.xlsx")
    s_name = find_file("Service_Details.xlsx")
    f_name = find_file("Active_FOC.xlsx")
    
    missing = []
    if not m_name: missing.append("Master_Data.xlsx")
    if not s_name: missing.append("Service_Details.xlsx")
    if not f_name: missing.append("Active_FOC.xlsx")
    
    if missing:
        return None, None, None, missing

    # Load Files
    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        f_df.columns = [str(c).strip() for c in f_df.columns]
        
        # Clean Values
        m_df['CUSTOMER NAME'] = m_df['CUSTOMER NAME'].astype(str).str.strip()
        
        # Date Conversion
        date_cols = ['OIL DUE DATE', 'AFC DUE DATE', 'AOS DUE DATE', 'Warranty End date']
        for col in date_cols:
            if col in m_df.columns:
                m_df[col] = pd.to_datetime(m_df[col], errors='coerce')
        
        if 'Call Logged Date' in s_df.columns:
            s_df['Call Logged Date'] = pd.to_datetime(s_df['Call Logged Date'], errors='coerce')
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [f"Error reading files: {e}"]

def format_dt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    return dt.strftime('%d-%b-%y')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

master_df, service_df, foc_df, missing = load_data()

# --- ERROR DISPLAY ---
if missing:
    st.error("❌ Files Not Found or Error Loading:")
    for m in missing: st.write(f"- {m}")
    st.info("Check karein ki GitHub par teeno Excel files uploaded hain.")
    st.stop()

# --- MAIN APP ---
if master_df is not None:
    st.sidebar.title("📌 Menu")
    page = st.sidebar.radio("Go to:", ["Machine Tracker", "Service Pending List"])

    if page == "Machine Tracker":
        st.title("🛠️ Machine Tracker Pro")
        
        customer_list = sorted(master_df['CUSTOMER NAME'].unique().astype(str))
        selected_customer = st.sidebar.selectbox("Select Customer", options=["All"] + customer_list)
        
        filtered_df = master_df if selected_customer == "All" else master_df[master_df['CUSTOMER NAME'] == selected_customer]
        selected_fab = st.sidebar.selectbox("Select Fabrication No", options=["Select"] + sorted(filtered_df['Fabrication No'].unique().astype(str)))

        if selected_fab != "Select":
            m_info = filtered_df[filtered_df['Fabrication No'] == selected_fab].iloc[0]
            
            # Details Layout
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.info("📋 Machine Info")
                st.write(f"**Customer:** {m_info.get('CUSTOMER NAME', 'N/A')}")
                st.write(f"**Model:** {m_info.get('MODEL', 'N/A')}")
                st.write(f"**Avg. Running Hrs:** {m_info.get('Avg. Hrs', 'N/A')} 👈")
                st.write(f"**Calculated Avg Hrs:** {m_info.get('HMR Cal.', 'N/A')} 👈")
                st.write(f"**Last Call HMR:** {m_info.get('Last Call HMR', 'N/A')}")
                st.write(f"**Last Call HMR Date:** {format_dt(m_info.get('Last Call HMR Date'))}")
                st.write(f"**Since Last Service:** {int(elapsed)} Hrs 🛠️")
            
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
            if st.button("🔴 1. Over Due", use_container_width=True):
                st.session_state.filter_type = "Over Due"
        
        with btn_col2:
            if st.button("🟡 2. Current Month Due", use_container_width=True):
                st.session_state.filter_type = "Current Month"
        
        with btn_col3:
            if st.button("🟢 3. Next Month Due", use_container_width=True):
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
# --- SERVICE HISTORY SECTION ---
            st.divider()
            st.subheader("🕒 Service History")
            if not history.empty:
                for _, row in history.iterrows():
                    # Using the new helper function to find Call Type
                    c_type = get_col_val(row, 'Call Type')
                    c_hmr = row.get('Call HMR', 'N/A')
                    c_dt = format_dt(row.get('Call Logged Date'))
                    
                    with st.expander(f"📅 {c_dt} | ⚙️ {c_hmr} HMR | 🛠️ {c_type}"):
                        st.write(f"**Call Type:** {c_type}")
                        st.write(f"**Engineer:** {get_col_val(row, 'Service Engineer')}")
                        st.info(f"**Comments:** {get_col_val(row, 'Service Engineer Comments')}")
            else:
                st.warning("No records found.")

    elif page == "Service Pending List":
        st.title("⏳ Service Pending Dashboard")
        # Pending buttons logic remains same...
        st.write("Buttons use karein.")
            
            # FOC Section
            st.divider()
            st.subheader("🎁 FOC Parts History")
            # FOC file ke fabrication column ka naam check karein
            f_col = 'FABRICATION NO.' if 'FABRICATION NO.' in foc_df.columns else 'Fabrication No'
            foc_match = foc_df[foc_df[f_col] == selected_fab].copy()
            if not foc_match.empty:
                st.dataframe(foc_match[['Failure Material Details', 'Part Code', 'Qty', 'ELGI IVOICE NO.']], use_container_width=True, hide_index=True)
            else:
                st.info("No FOC records found.")

            # Service History
            st.divider()
            st.subheader("🕒 Service History")
            history = service_df[service_df['Fabrication Number'] == selected_fab].copy().sort_values(by='Call Logged Date', ascending=False)
            if not history.empty:
                for _, row in history.iterrows():
                    header = f"📅 {format_dt(row.get('Call Logged Date'))} | ⚙️ {row.get('Call HMR')} HMR | 🛠️ {row.get('Call Type', 'N/A')}"
                    with st.expander(header):
                        st.info(row.get('Service Engineer Comments', 'No comments.'))
            else:
                st.warning("No history found.")

    elif page == "Service Pending List":
        st.title("⏳ Service Pending Dashboard")
        st.write("Action buttons use karke list generate karein.")
        b1, b2, b3 = st.columns(3)
        # Add your BIS Button Logic here...

else:
    st.error("Data loading failed.")
