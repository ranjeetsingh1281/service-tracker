import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

# Page Settings
st.set_page_config(page_title="ELGi Service Tracker Pro", layout="wide")

# --- DYNAMIC FILE LOADER (With Duplicate & Case Handling) ---
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
        return None, None, None, [f for f in ["Master_Data.xlsx", "Service_Details.xlsx", "Active_FOC.xlsx"] if not find_file(f)]

    try:
        m_df = pd.read_excel(m_name, engine='openpyxl')
        s_df = pd.read_excel(s_name, engine='openpyxl')
        f_df = pd.read_excel(f_name, engine='openpyxl')
        
        # Clean Headers
        m_df.columns = [str(c).strip() for c in m_df.columns]
        s_df.columns = [str(c).strip() for c in s_df.columns]
        
        # FOC Duplicate Header Fix (Handles "ELGI IVOICE NO.")
        new_f_cols = []
        counts = {}
        for col in f_df.columns:
            c = str(col).strip()
            if c in counts:
                counts[c] += 1
                new_f_cols.append(f"{c}_{counts[c]}")
            else:
                counts[c] = 0
                new_f_cols.append(c)
        f_df.columns = new_f_cols
            
        return m_df, s_df, f_df, []
    except Exception as e:
        return None, None, None, [str(e)]

# --- EXPORT HELPERS ---
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
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height-50, title)
    y = height - 80
    p.setFont("Helvetica", 10)
    for k, v in info_dict.items():
        p.drawString(50, y, f"{k}: {v}"); y -= 15
    p.line(50, y, width-50, y); y -= 30
    if table_df is not None and not table_df.empty:
        p.setFont("Helvetica-Bold", 9)
        cols = table_df.columns.tolist()[:8]
        cur_x = 50
        for c in cols: p.drawString(cur_x, y, str(c)[:15]); cur_x += 95
        y -= 20; p.setFont("Helvetica", 8)
        for _, row in table_df.iterrows():
            if y < 50: p.
