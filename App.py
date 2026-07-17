import streamlit as st
import pandas as pd
import requests
import base64
import io
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from PIL import Image

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS "HAPPY & CLEAN" (Light Theme, Profesional, Nyaman) ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stForm"] { background: #ffffff !important; border-radius: 20px !important; padding: 30px !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .header-style { background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); padding: 20px; border-radius: 15px; color: white; font-weight: 800; font-size: 26px; text-align: center; margin-bottom: 30px; }
    button[kind="primaryFormSubmit"], .stButton>button { background: #2563eb !important; color: white !important; font-weight: bold !important; border-radius: 10px !important; transition: 0.3s; }
    button[kind="primaryFormSubmit"]:hover { background: #1d4ed8 !important; }
    h1, h2, h3 { color: #1e293b !important; }
    .stInfo { background-color: #eff6ff !important; color: #1e40af !important; }
    /* Memperbaiki tampilan tabel agar clean */
    .stDataFrame { border-radius: 10px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI UPLOAD FOTO (URL WEB APP ANDA) ---
def upload_image_to_gdrive(uploaded_file):
    # URL TERBARU ANDA
    GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzkNRhVe-T2L-ol4bBnPK-CiJp189GH9F4PutYnUszIZ1lLV_RxWcX124UmU16Aa9M4/exec"
    
    try:
        img = Image.open(uploaded_file).convert('RGB')
        img.thumbnail((600, 600))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        b64_string = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        payload = {"filename": f"Bukti_{int(time.time())}.jpg", "base64": b64_string}
        response = requests.post(GAS_WEB_APP_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("url")
            else:
                return f"ERROR: {result.get('message')}"
        return f"HTTP_ERROR: {response.status_code}"
    except Exception as e:
        return f"NETWORK_ERROR: {str(e)}"

# --- 4. FUNGSI DATA ---
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds)
    except: return None

def save_findings_to_sheet(nik, nama, unit_info, findings, f1, f2, f3, f4, f5):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        worksheet = sh.worksheet("Rekomendasi Perbaikan")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, nik, nama, unit_info, findings, f1, f2, f3, f4, f5])
        return True
    except Exception as e:
        st.error(f"Gagal simpan ke Sheet: {e}")
        return False

@st.cache_data(ttl=600)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
    return xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame())

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 5. TAMPILAN UTAMA ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    with st.form("login"):
        st.write("### Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk"):
            if u == "SIMAKINKUT" and p == "2026KUTPOSITIF":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET</div>', unsafe_allow_html=True)

# Filter Karyawan
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f4:
    list_nama = df_sdm['NAMA'].dropna().unique() if 'NAMA' in df_sdm.columns else []
    selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", list_nama)

data_karyawan_select = get_row_by_name(df_sdm, selected_nama)
data_asset_select = get_row_by_name(df_asset, selected_nama)
data_genset_select = get_row_by_name(df_genset, selected_nama)
data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)

# Profil
st.markdown("### 👤 Profil Karyawan")
if data_karyawan_select is not None:
    st.dataframe(pd.DataFrame(list(data_karyawan_select.items()), columns=["Parameter", "Info"]), use_container_width=True)

# Form & Gallery
tab1, tab2 = st.tabs(["📝 Input Laporan", "🖼️ Galeri & Arsip"])
with tab1:
    input_findings = st.text_area("✍️ Laporan Perbaikan:", height=100)
    uploaded_files = st.file_uploader("📸 Upload Foto (Maks 5):", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    if st.button("🚀 Push Update"):
        img_urls = ["", "", "", "", ""]
        with st.spinner("Mengupload..."):
            for idx, file in enumerate(uploaded_files[:5]):
                url = upload_image_to_gdrive(file)
                if url and "ERROR" not in url: img_urls[idx] = url
                else: st.error(f"Foto {idx+1} gagal: {url}")
        
        unit_info = f"Mobil: {data_asset_select.get('NOPOL (PLAT NOMOR)', '-')}" if data_asset_select is not None else "N/A"
        if save_findings_to_sheet(str(data_karyawan_select.get('NIK', 'N/A')), selected_nama, unit_info, input_findings, *img_urls):
            st.success("✅ Data tersimpan!")
            st.rerun()

with tab2:
    st.markdown("### 🛠️ Riwayat Perbaikan")
    if not df_rekomendasi.empty:
        matched_rek = df_rekomendasi[df_rekomendasi['Nama'].str.contains(selected_nama, na=False)]
        for _, row in matched_rek.iterrows():
            st.write(f"**{row['Timestamp']}**: {row['Findings & Action Plan']}")
            # Tampilkan foto jika ada
            cols = st.columns(5)
            for i in range(1, 6):
                if row.get(f'Foto {i}'): cols[i-1].image(row[f'Foto {i}'], width=100)
