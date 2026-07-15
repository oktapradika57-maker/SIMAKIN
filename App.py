import streamlit as st
import pandas as pd
import plotly.express as px
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests
import base64
import time
from PIL import Image
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(30, 32, 40, 0.8), rgba(15, 15, 20, 0.9)) !important;
        backdrop-filter: blur(20px) !important; border: 1px solid rgba(255, 82, 82, 0.4) !important;
        padding: 40px !important; border-radius: 20px !important;
        box-shadow: 0px 20px 40px rgba(0,0,0,0.8) !important; max-width: 450px !important; margin: 50px auto !important;
    }
    .header-style {
        background: linear-gradient(135deg, #d32f2f 0%, #9a0007 100%); padding: 15px; border-radius: 12px; 
        color: white; font-weight: 800; font-size: 24px; text-align: center; margin-bottom: 25px;
    }
    .report-card { background: #1e1e24; padding: 20px; border-radius: 12px; border-left: 6px solid #e53935; margin-bottom: 15px; }
    .report-date { color: #ff5252; font-size: 14px; font-weight: bold; margin-bottom: 8px;}
    .report-text { color: #e0e0e0; font-size: 15px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIN & SIDEBAR ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def login_form():
    with st.form("login_form"):
        st.markdown('<h1 style="color:#ff5252; text-align:center;">⚡ SYSTEM PORTAL</h1>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        if st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True):
            if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("❌ Kredensial Salah!")

if not st.session_state.logged_in:
    login_form()
    st.stop()

with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    if st.button("🚪 Keluar"): st.session_state.logged_in = False; st.rerun()

# --- 4. FUNGSI DATA ---
def upload_image_to_gdrive(uploaded_file):
    try:
        GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzDhWqTx4vGoLSkzs8NGu3epuwbZhYPG7wYh5fGIYPxIEAO4uH22Go91-F9xjV4H-sm/exec"
        img = Image.open(uploaded_file).convert('RGB')
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        res = requests.post(GAS_WEB_APP_URL, json={"filename": f"Bukti_{time.time()}.jpg", "base64": b64})
        return res.json().get("url") if res.json().get("status") == "success" else ""
    except: return ""

def get_clean_image_url(url):
    match = re.search(r'([-\w]{25,})', url) 
    return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800" if match else url

@st.cache_data(ttl=120) 
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&cb={time.time()}"
    try:
        xls = pd.read_excel(url, sheet_name=None, engine='openpyxl', dtype=str)
        return xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame())
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi = load_all_data()

# --- 5. TAMPILAN ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET | REG KALIMANTAN</div>', unsafe_allow_html=True)

# (Logika filter karyawan tetap sama di sini)
# ... [Filter Karyawan Anda tetap disini] ...
selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", df_sdm['NAMA'].dropna().unique())
data_asset_select = df_asset[df_asset['NAMA'].str.contains(selected_nama, na=False)] if 'NAMA' in df_asset.columns else None

# --- TAB GALLERY (DIPERBAIKI) ---
tab_r2r4, tab_genset, tab_tools, tab_perbaikan_text, tab_galeri_foto = st.tabs([
    "🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", 
    "📝 Riwayat Teks Laporan", "🖼️ Galeri Foto Perbaikan"
])

# FUNGSI LAMA (JANGAN DISENTUH)
def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
    with tab_context:
        if not data_row.empty:
            cols = st.columns(4)
            for i, col_name in enumerate(df_columns):
                cell_val = str(data_row.iloc[0][col_name])
                if "http" in cell_val:
                    cols[i % 4].image(get_clean_image_url(cell_val), caption=col_name, use_container_width=True)

render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Tidak ada data.")
# ... (render untuk genset & tools sama seperti asli Anda) ...

# --- TAB GALERI FOTO (FIXED) ---
with tab_galeri_foto:
    if selected_nama != "-":
        matched_rek = df_rekomendasi[df_rekomendasi['Nama'].str.contains(selected_nama, na=False, case=False)]
        for index, row in matched_rek.iloc[::-1].iterrows():
            st.markdown(f"**📅 Update Service: {row.get('Timestamp', '-')}**")
            cols = st.columns(3)
            col_idx = 0
            for col in matched_rek.columns:
                if "FOTO" in col.upper() and "http" in str(row[col]):
                    file_id_match = re.search(r'([-\w]{25,})', str(row[col]))
                    if file_id_match:
                        # INI KUNCI FIX-NYA: MENGGUNAKAN ST.IMAGE BUKAN HTML
                        st_img_url = f"https://drive.google.com/thumbnail?id={file_id_match.group(1)}&sz=w800"
                        cols[col_idx % 3].image(st_img_url, use_container_width=True)
                        col_idx += 1
            st.markdown("---")
