import streamlit as st
import pandas as pd
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import os
import urllib.parse 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
    .header-style { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); padding: 18px; border-radius: 15px; color: white; font-weight: 800; font-size: 26px; text-align: center; margin-bottom: 30px; border: 1px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNGSI LOGO & LOGIN ---
def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    return logo_1 if os.path.exists(logo_1) else None

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login"):
        st.markdown('<h1 style="color:#60a5fa; text-align:center;">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("MASUK"):
            if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
                st.session_state.logged_in = True; st.rerun()
            else: st.error("❌ Salah!")
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    if get_logo_path(): st.image(get_logo_path(), use_container_width=True)
    if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Keluar"): st.session_state.logged_in = False; st.rerun()

# --- 5. FUNGSI GOOGLE SHEETS ---
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds)
    except: return None

def save_findings_to_sheet(nik, nama, unit_info, findings):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        worksheet = sh.worksheet("Rekomendasi Perbaikan")
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nik, nama, unit_info, findings])
        return True
    except: return False

# --- 6. LOAD DATA ---
@st.cache_data(ttl=60)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta = load_all_data()

# --- 7. DASHBOARD UTAMA ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET</div>', unsafe_allow_html=True)

# Logic Filter
selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", df_sdm['NAMA'].unique() if 'NAMA' in df_sdm.columns else [])
data_karyawan = df_sdm[df_sdm['NAMA'] == selected_nama].iloc[0] if not df_sdm[df_sdm['NAMA'] == selected_nama].empty else None
data_asset = df_asset[df_asset['NAMA'] == selected_nama].iloc[0] if not df_asset[df_asset['NAMA'] == selected_nama].empty else None

# --- 8. INPUT HYBRID (Teks di Streamlit, Foto di Form) ---
col_plan, col_upload = st.columns([1, 1])

with col_plan:
    st.markdown("### 📝 Input Teks Laporan")
    input_findings = st.text_area("✍️ Ketik deskripsi laporan perbaikan:", height=150)
    if st.button("🚀 Simpan Teks ke Server"):
        if input_findings and data_karyawan is not None:
            nik = str(data_karyawan.get('NIK', '-'))
            unit = str(data_asset.get('NOPOL (PLAT NOMOR)', 'Mobil')) if data_asset is not None else "Asset"
            if save_findings_to_sheet(nik, selected_nama, unit, input_findings):
                st.success("✅ Teks berhasil disimpan!")
        else: st.error("Mohon pilih karyawan dan isi laporan.")

with col_upload:
    st.markdown("### 📸 Upload Evidence (Otomatis)")
    # Data untuk Auto-Fill
    val_nik = str(data_karyawan.get('NIK', '-')) if data_karyawan is not None else "-"
    val_nama = selected_nama
    val_nopol = str(data_asset.get('NOPOL (PLAT NOMOR)', '-')) if data_asset is not None else "-"
    val_jenis = "Mobil" # Bisa disesuaikan
    
    # URL Auto-Fill
    url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
    url_gform = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(val_nama)}&entry.1607280297={urllib.parse.quote(val_nopol)}&entry.505680533={urllib.parse.quote(val_jenis)}"
    
    st.markdown(f"""
    <a href="{url_gform}" target="_blank" style="text-decoration:none;">
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; border-radius: 15px; color: white; text-align: center; font-weight: bold; font-size: 16px;">
            🚀 KLIK UNTUK UPLOAD FOTO (Data sudah terisi)
        </div>
    </a>
    """, unsafe_allow_html=True)

# --- 9. GALERI RIWAYAT ---
st.markdown("### 📸 Galeri Riwayat Perbaikan")
if not df_rekomendasi.empty:
    matched = df_rekomendasi[df_rekomendasi['Nama'].astype(str).str.strip().str.lower() == selected_nama.lower()]
    for _, row in matched.iloc[::-1].iterrows():
        st.markdown(f"---")
        st.markdown(f"**📅 {row.get('Timestamp')}** | {row.get('Findings & Action Plan')}")
        # Mencari foto di seluruh kolom
        photos = []
        for col in df_rekomendasi.columns:
            if "drive.google.com" in str(row[col]):
                match = re.search(r'[-\w]{25,}', str(row[col]))
                if match: photos.append(match.group(0))
        
        if photos:
            cols = st.columns(min(len(photos), 4))
            for i, pid in enumerate(photos):
                cols[i%4].image(f"https://drive.google.com/thumbnail?id={pid}&sz=w800", use_container_width=True)
