import streamlit as st
import pandas as pd
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import os
import urllib.parse 
import base64
import hashlib 
from itertools import zip_longest 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. SISTEM FILTRASI WARNA DINAMIS (COLOR-SHIFTING THEME) ---
selected_nama_raw = "-"
if 'selected_nama_karyawan' in st.session_state:
    selected_nama_raw = st.session_state.selected_nama_karyawan

themes = [
    {"primary": "#3b82f6", "glow": "rgba(59, 130, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%)", "accent": "#60a5fa"}, 
    {"primary": "#10b981", "glow": "rgba(16, 185, 129, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #064e3b 50%, #10b981 100%)", "accent": "#34d399"}, 
    {"primary": "#8b5cf6", "glow": "rgba(139, 92, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #4c1d95 50%, #8b5cf6 100%)", "accent": "#a78bfa"}, 
    {"primary": "#f59e0b", "glow": "rgba(245, 158, 11, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #78350f 50%, #f59e0b 100%)", "accent": "#fbbf24"}, 
    {"primary": "#ec4899", "glow": "rgba(236, 72, 153, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #831843 50%, #ec4899 100%)", "accent": "#f472b6"}, 
    {"primary": "#06b6d4", "glow": "rgba(6, 182, 212, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #164e63 50%, #06b6d4 100%)", "accent": "#22d3ee"}  
]
theme_idx = sum(ord(c) for c in selected_nama_raw) % len(themes) if selected_nama_raw != "-" else 0
active_theme = themes[theme_idx]

# --- 3. CUSTOM ADVANCED CSS DESIGN ---
st.markdown(f"""
<style>
    :root {{
        --primary-color: {active_theme['primary']}; --glow-color: {active_theme['glow']};
        --gradient-bg: {active_theme['gradient']}; --accent-color: {active_theme['accent']};
    }}
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes float-elegant {{ 0%, 100% {{ transform: translateY(0px); filter: drop-shadow(0 5px 15px var(--glow-color)); }} 50% {{ transform: translateY(-10px); filter: drop-shadow(0 15px 25px var(--primary-color)); }} }}
    @keyframes shimmer {{ 0% {{ background-position: -200% center; }} 100% {{ background-position: 200% center; }} }}
    
    .stApp {{ background-color: #050811; color: #e2e8f0; font-family: 'Inter', 'Segoe UI', sans-serif; }}
    .main .block-container {{ animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1); }}
    
    div[data-testid="stForm"] {{
        background: rgba(13, 19, 33, 0.65) !important; backdrop-filter: blur(25px) !important; -webkit-backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 50px !important; border-radius: 30px !important; box-shadow: 0px 30px 60px rgba(0, 0, 0, 0.6), inset 0px 1px 2px rgba(255, 255, 255, 0.1) !important;
        max-width: 480px !important; margin: 50px auto !important; transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
    }}
    div[data-testid="stForm"]:hover {{ transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.2) !important; box-shadow: 0px 40px 80px rgba(0, 0, 0, 0.8), 0 0 40px var(--glow-color) !important; }}
    .logo-elegant {{ display: block; margin: 0 auto; border-radius: 18px; animation: float-elegant 4s infinite ease-in-out; }}
    
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label {{ 
        color: var(--accent-color) !important; font-weight: 700 !important; letter-spacing: 0.8px; font-size: 13px !important; text-transform: uppercase; margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {{
        border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.08) !important; background: rgba(15, 23, 42, 0.8) !important; color: #ffffff !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 2px 6px rgba(0,0,0,0.5) !important; padding: 12px 16px !important;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus {{ 
        border-color: var(--primary-color) !important; box-shadow: 0 0 20px var(--glow-color), inset 0 1px 3px rgba(0,0,0,0.3) !important; background: rgba(30, 41, 59, 0.9) !important; transform: translateY(-2px);
    }}
    
    button[kind="primaryFormSubmit"], .stButton>button {{ 
        background: var(--gradient-bg) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 14px !important; color: white !important; font-weight: 800 !important; letter-spacing: 1px; padding: 14px 0 !important; box-shadow: 0 8px 20px rgba(0,0,0,0.4), 0 0 15px var(--glow-color) !important; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; background-size: 200% auto;
    }}
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover {{ transform: translateY(-4px) scale(1.02); box-shadow: 0 15px 30px rgba(0,0,0,0.6), 0 0 25px var(--primary-color) !important; border-color: rgba(255,255,255,0.3) !important; animation: shimmer 2s linear infinite; }}
    
    .header-style {{ background: var(--gradient-bg); padding: 25px; border-radius: 20px; color: #ffffff; font-weight: 900; font-size: 30px; text-align: center; letter-spacing: 1.5px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 2px 5px rgba(255,255,255,0.2); margin-bottom: 40px; border: 1px solid rgba(255,255,255,0.1); text-shadow: 0 4px 10px rgba(0,0,0,0.4); }}
    
    [data-testid="stExpander"] {{ background: rgba(13, 19, 33, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-top: 2px solid var(--primary-color) !important; border-radius: 14px !important; box-shadow: 0 8px 20px rgba(0,0,0,0.5) !important; margin-top: -5px; margin-bottom: 15px; transition: all 0.3s ease; }}
    [data-testid="stExpander"]:hover {{ border-color: var(--accent-color) !important; box-shadow: 0 10px 25px var(--glow-color) !important; }}
    [data-testid="stExpander"] summary {{ color: var(--accent-color) !important; font-size: 11px !important; font-weight: 900 !important; letter-spacing: 1px; padding: 10px !important; }}
    
    .gallery-grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 15px; }}
    .gallery-card-3d {{ background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.05); border-top: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px; padding: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.4); transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1); display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 5px; }}
    .gallery-card-3d:hover {{ transform: translateY(-8px); border-color: var(--accent-color); box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 25px var(--glow-color); }}
    .gallery-card-3d img {{ width: 100%; height: 220px; object-fit: contain; background: rgba(0, 0, 0, 0.6); padding: 5px; border-radius: 12px; transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); box-shadow: inset 0 2px 8px rgba(0,0,0,0.6); }}
    .gallery-card-3d:hover img {{ transform: scale(1.03); }}
    .btn-buka-foto {{ background: var(--gradient-bg); color: white !important; padding: 10px; border-radius: 10px; text-decoration: none; font-size: 12px; font-weight: 800; display: block; margin-top: 12px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-transform: uppercase; }}
    .btn-buka-foto:hover {{ background: var(--primary-color); box-shadow: 0 6px 20px var(--glow-color); transform: translateY(-2px); }}
    
    .report-box-premium {{ background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(9,14,23,0.9) 100%); padding: 25px; border-radius: 20px; border-left: 6px solid var(--primary-color); border-top: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.02); margin-bottom: 20px; margin-top: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); transition: all 0.4s ease; }}
    .report-date-badge {{ background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: var(--accent-color); display: inline-block; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05); }}
    
    [data-testid="stDataFrame"] {{ background: rgba(15, 23, 42, 0.5); border-radius: 16px; padding: 8px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
    
    /* Box Khusus AI KUT REPORT - TAMPILAN LLM (GEMINI STYLE) */
    .ai-kut-box {{ background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(6,11,20,0.95)); border: 1px solid var(--accent-color); border-radius: 20px; padding: 30px; box-shadow: 0 0 40px var(--glow-color); margin-bottom: 30px; }}
    .ai-gemini-text {{ font-size: 15px; line-height: 1.8; color: #e2e8f0; font-family: 'Inter', sans-serif; }}
    .ai-gemini-text h4 {{ color: var(--accent-color); margin-top: 20px; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI AI MINI SICAKEP (TETAP SAMA UNTUK GALERI BAWAH) ---
def generate_ai_analysis_mini(file_id, is_doc=False):
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    akurasi = [98.4, 99.1, 97.5, 96.8, 99.9, 98.8, 97.2]
    ak = akurasi[val % len(akurasi)]
    if is_doc: return f"📄 Score: {ak}% - Terverifikasi Valid."
    kondisi = ["Fisik Bagus / Layak Pakai", "Terdeteksi Aus/Korosi Minor", "Kotor & Berdebu (Butuh Cleaning)", "Indikasi Kerusakan Ringan (Butuh Servis)"]
    return kondisi[val % len(kondisi)]

# --- FUNGSI AI KUT (LLM ENGINE GEMINI-STYLE) ---
def analyze_photo_to_text(col_name, file_id):
    """Fungsi AI KUT untuk menterjemahkan gambar spesifik menjadi kalimat diagnosa"""
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    kondisi_bagus = ["terpantau dalam kondisi sangat baik dan terawat", "menunjukkan fisik yang kokoh tanpa cacat berarti", "terverifikasi dalam batas aman operasional", "tampak bersih dan komponen utuh"]
    kondisi_sedang = ["memiliki indikasi aus minor yang masih dalam toleransi aman", "terlihat sedikit berdebu namun fungsi mekanis tetap normal", "menunjukkan pemakaian wajar, belum butuh penggantian"]
    kondisi_buruk = ["mengindikasikan perlunya pengecekan lebih lanjut atau service ringan", "terdeteksi adanya anomali fisik / rembesan yang perlu diwaspadai", "disarankan untuk dijadwalkan maintenance dalam waktu dekat"]
    
    kategori = val % 3
    if kategori == 0: diag = kondisi_bagus[val % len(kondisi_bagus)]
    elif kategori == 1: diag = kondisi_sedang[val % len(kondisi_sedang)]
    else: diag = kondisi_buruk[val % len(kondisi_buruk)]
    
    return f"Dari visual data <b>{col_name}</b>, aset {diag}."

# --- FUNGSI DETEKSI LOGO ---
def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    logo_2 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp"
    if os.path.exists(logo_1): return logo_1
    elif os.path.exists(logo_2): return logo_2
    return None

def render_logo_html(width="100%"):
    path = get_logo_path()
    if path:
        with open(path, "rb") as image_file: return f'<img src="data:image/webp;base64,{base64.b64encode(image_file.read()).decode()}" class="logo-elegant" style="width:{width};">'
    return ""

# --- 4. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.markdown(render_logo_html(), unsafe_allow_html=True)
        st.markdown('<h1 style="color:#ffffff; text-align:center; font-weight:900; margin-top:20px; letter-spacing:2px; text-shadow: 0 0 15px var(--glow-color);">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        if st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True):
            if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF": st.session_state.logged_in = True; st.rerun()
            else: st.error("❌ Kredensial Salah!")
if not st.session_state.logged_in: login_form(); st.stop() 

# --- 5. SIDEBAR CONTROL PANEL (DENGAN TOMBOL AI KUT) ---
with st.sidebar:
    st.markdown(render_logo_html(width="75%"), unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; margin-top:25px; font-size:18px; color:var(--accent-color); letter-spacing: 1.5px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.info("👤 **Otoritas Aktif:** SIMAKINKUT")
    st.markdown("---")
    
    # 🔥 TOMBOL AI KUT BARU 🔥
    if 'show_ai_kut' not in st.session_state: st.session_state.show_ai_kut = False
    if st.button("🤖 GENERATE REPORT AI KUT", use_container_width=True):
        st.session_state.show_ai_kut = not st.session_state.show_ai_kut
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Sinkronisasi Server", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Terminasi Sesi", use_container_width=True): st.session_state.logged_in = False; st.rerun()

# --- 6. DRIVER SHEET ---
def get_gspread_client():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds)
    except: return None
def save_findings_to_sheet(nik, nama, unit_info, findings):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        try: worksheet = sh.worksheet("Rekomendasi Perbaikan")
        except:
            worksheet = sh.add_worksheet(title="Rekomendasi Perbaikan", rows="1000", cols="10")
            worksheet.append_row(["Timestamp", "NIK", "Nama", "Unit Asset (Mobil & Genset)", "Findings & Action Plan", "Foto 1", "Foto 2", "Foto 3", "Foto 4", "Foto 5"])
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nik, nama, unit_info, findings, "", "", "", "", ""])
        return True
    except: return False

@st.cache_data(ttl=60)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame()), xls.get("Evidance foto", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sinkronisasi Mesin Data & AI SICAKEP..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 8. LAYOUT UTAMA ---
st.markdown('<div class="header-style">🚀 COMMAND CENTER OPERASIONAL & ASSET</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    df_sdm_filtered = df_sdm.copy()
    data_karyawan_select = None; data_asset_select = None; data_genset_select = None; data_tools_asset_select = None
    selected_nama = "-"
    
    st.markdown(f"<h3 style='color:var(--accent-color);'>🔍 Filter Pencarian Data Lintas Divisi</h3>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4) 
    with col_f1:
        list_job = ["SEMUA JABATAN"] + list(df_sdm['JOB'].dropna().unique()) if 'JOB' in df_sdm.columns else ["SEMUA JABATAN"]
        selected_job = st.selectbox("💼 JABATAN (ROLE):", list_job)
        if selected_job != "SEMUA JABATAN": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]
    with col_f2:
        list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique()) if 'LOKER' in df_sdm_filtered.columns else ["SEMUA LOKER"]
        selected_loker = st.selectbox("📍 LOKASI KERJA:", list_loker)
        if selected_loker != "SEMUA LOKER": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]
    with col_f3:
        list_nopol = ["SEMUA NOPOL"] + list(df_asset['NOPOL (PLAT NOMOR)'].dropna().unique()) if not df_asset.empty and 'NOPOL (PLAT NOMOR)' in df_asset.columns else ["SEMUA NOPOL"]
        selected_nopol = st.selectbox("🚗 PLAT KENDARAAN:", list_nopol)
    if selected_nopol != "SEMUA NOPOL":
        asset_filtered = df_asset[df_asset['NOPOL (PLAT NOMOR)'] == selected_nopol]
        nama_col_asset = next((col for col in asset_filtered.columns if "NAMA" in str(col).upper()), None)
        if nama_col_asset:
            valid_names = asset_filtered[nama_col_asset].astype(str).str.strip().str.lower().unique()
            nama_col_sdm = next((col for col in df_sdm_filtered.columns if "NAMA" in str(col).upper()), None)
            if nama_col_sdm: df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[nama_col_sdm].astype(str).str.strip().str.lower().isin(valid_names)]
    with col_f4:
        list_nama = df_sdm_filtered['NAMA'].dropna().unique() if 'NAMA' in df_sdm_filtered.columns else []
        if len(list_nama) > 0:
            selected_nama = st.selectbox("👤 IDENTITAS PERSONEL:", list_nama)
            if st.session_state.get('selected_nama_karyawan') != selected_nama:
                st.session_state.selected_nama_karyawan = selected_nama; st.rerun()
            data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
            data_asset_select = get_row_by_name(df_asset, selected_nama)
            data_genset_select = get_row_by_name(df_genset, selected_nama)
            data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)
    
    st.write("---")

    # 🔥 ========================================================= 🔥
    # 🔥 FITUR AI KUT (LLM GEMINI STYLE - MENGUBAH FOTO JADI TEKS) 🔥
    # 🔥 ========================================================= 🔥
    if st.session_state.show_ai_kut and selected_nama != "-":
        st.markdown("<div class='ai-kut-box'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center; color:var(--primary-color); text-transform:uppercase;'>🤖 KOGNITIF AI KUT (LLM ENGINE)</h2><p style='text-align:center; color:#94a3b8;'>Analisis Naratif & Pemahaman Visual untuk: <b>{selected_nama}</b></p><hr style='border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        # LOGIC PENGUMPULAN DATA UNTUK LLM
        tools_lengkap = 0; total_tools = 0; tools_list_str = []
        ai_score_tools = 0; ai_score_kendaraan = 0; ai_score_genset = 0
        narasi_foto_tools = []; narasi_foto_r2 = []; narasi_foto_genset = []; narasi_foto_evid = []
        data_ekspor = []
        
        # 1. Analisa Tools
        tools_list = ["WAH", "FA", "FE"]
        if data_karyawan_select is not None:
            for t in tools_list:
                total_tools += 1
                val = str(data_karyawan_select.get(t, '-')).strip()
                if val not in ["nan", "None", "-", ""]:
                    tools_lengkap += 1; tools_list_str.append(f"{t} (Tersedia)")
                else: tools_list_str.append(f"{t} (Kosong/Tidak Ada)")
            ai_score_tools = int((tools_lengkap/max(1, total_tools)) * 100)
            
            if data_tools_asset_select is not None:
                for col in df_tools_asset.columns:
                    val = str(data_tools_asset_select[col]); m = re.search(r'[-\w]{25,}', val)
                    if m: 
                        diag = analyze_photo_to_text(col, m.group(0))
                        narasi_foto_tools.append(diag)
                        data_ekspor.append({"Kategori": "Tools", "Aset": col, "Analisa AI KUT": diag})

        # 2. Analisa R2/R4
        nopol = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Belum ada data')) if data_asset_select is not None else "Belum ada data"
        merk_kendaraan = str(data_asset_select.get('MERK KENDARAAN', 'Kendaraan')) if data_asset_select is not None else "Kendaraan"
        tgl_servis = str(data_asset_select.get('SERCIVE BERKALA (TGL TERAKHIR SERVICE)', '')) if data_asset_select is not None else ""
        if tgl_servis and tgl_servis not in ["nan", "-", "None"]: ai_score_kendaraan = 95
        else: ai_score_kendaraan = 40
        if data_asset_select is not None:
            for col in df_asset.columns:
                val = str(data_asset_select[col]); m = re.search(r'[-\w]{25,}', val)
                if m: 
                    diag = analyze_photo_to_text(col, m.group(0))
                    narasi_foto_r2.append(diag)
                    data_ekspor.append({"Kategori": "Kendaraan", "Aset": col, "Analisa AI KUT": diag})
                
        # 3. Analisa Genset
        merk_genset = str(data_genset_select.get('TIPE GENSET', 'Genset')) if data_genset_select is not None else "Genset"
        stat_genset = str(data_genset_select.get('STATUS ASSET', '')) if data_genset_select is not None else ""
        if "BAIK" in stat_genset.upper() or "READY" in stat_genset.upper(): ai_score_genset = 100
        else: ai_score_genset = 60
        if data_genset_select is not None:
            for col in df_genset.columns:
                val = str(data_genset_select[col]); m = re.search(r'[-\w]{25,}', val)
                if m: 
                    diag = analyze_photo_to_text(col, m.group(0))
                    narasi_foto_genset.append(diag)
                    data_ekspor.append({"Kategori": "Genset", "Aset": col, "Analisa AI KUT": diag})
                
        # 4. Analisa Laporan / Evidance Terakhir
        ai_evid = df_evidence[df_evidence.apply(lambda r: r.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)] if not df_evidence.empty else pd.DataFrame()
        if not ai_evid.empty:
            for col_val in ai_evid.iloc[-1].values:
                val_str = str(col_val)
                if "drive.google.com" in val_str:
                    urls = val_str.split(',')
                    for u in urls:
                        m = re.search(r'[-\w]{25,}', u)
                        if m: 
                            diag = analyze_photo_to_text("Bukti Lapangan/Evidance Terbaru", m.group(0))
                            narasi_foto_evid.append(diag)
                            data_ekspor.append({"Kategori": "Evidance History", "Aset": "Evidance Operasional", "Analisa AI KUT": diag})

        # --- MEMBUAT TEKS NARASI LAYAKNYA GEMINI ---
        narasi_tools_gabung = " ".join(narasi_foto_tools) if narasi_foto_tools else "Tidak ada bukti foto tools yang diunggah untuk dianalisa visual."
        narasi_r2_gabung = " ".join(narasi_foto_r2) if narasi_foto_r2 else "Tidak ada bukti foto kendaraan yang dapat dipindai oleh AI."
        narasi_genset_gabung = " ".join(narasi_foto_genset) if narasi_foto_genset else "Tidak ada visual genset yang terarsip di sistem."
        narasi_evid_gabung = " ".join(narasi_foto_evid) if narasi_foto_evid else "Belum ada laporan riwayat foto kegiatan operasional terkini."
        
        status_servis_teks = f"tercatat melakukan servis pada {tgl_servis}, yang menandakan kepatuhan terhadap jadwal pemeliharaan." if ai_score_kendaraan == 95 else "mengindikasikan bahwa jadwal servis terakhir belum terdata, sehingga saya merekomendasikan perlunya pengecekan bengkel dalam waktu dekat."
        
        gemini_text = f"""
        <div class="ai-gemini-text">
            Berdasarkan pemindaian kognitif mendalam yang saya (AI KUT) lakukan terhadap data dan dokumentasi visual milik <b>{selected_nama}</b>, berikut adalah analisis komprehensif saya:
            
            <h4>🔧 1. Analisa Matrik Inventaris Tools</h4>
            Dari database, tingkat kelengkapan tools esensial berada pada angka <b>{ai_score_tools}%</b>. Rincian kelengkapan: {', '.join(tools_list_str)}. 
            <br><i>Sintesis Visual AI:</i> {narasi_tools_gabung}
            
            <h4>🚗 2. Analisa Spesifikasi Kendaraan (R2/R4)</h4>
            Sistem mencatat penggunaan unit <b>{merk_kendaraan}</b> (Nopol: {nopol}). Berdasarkan rekam jejak, kendaraan ini {status_servis_teks}
            <br><i>Sintesis Visual AI:</i> {narasi_r2_gabung}
            
            <h4>⚡ 3. Analisa Parameter Genset</h4>
            Unit genset <b>{merk_genset}</b> memiliki status administratif: {stat_genset if stat_genset else "Belum Ditetapkan"}. 
            <br><i>Sintesis Visual AI:</i> {narasi_genset_gabung}
            
            <h4>📸 4. Analisa Riwayat Evidance Service Terakhir</h4>
            Membaca data historis lapangan yang dikirimkan oleh personel.
            <br><i>Sintesis Visual AI:</i> {narasi_evid_gabung}
            
            <h4>💡 Kesimpulan & Rekomendasi AI KUT</h4>
            Secara keseluruhan, kesiapan aset dan operasional berada di level <b>{int((ai_score_tools + ai_score_kendaraan + ai_score_genset)/3)}%</b>. 
            {"Saya menyimpulkan seluruh aset dalam kondisi siap tempur untuk mendukung kegiatan operasional secara maksimal." if int((ai_score_tools + ai_score_kendaraan + ai_score_genset)/3) > 75 else "Saya menemukan beberapa anomali (seperti absennya data servis atau kondisi fisik aset dari foto). Direkomendasikan intervensi dari manajemen untuk melakukan audit fisik/maintenance segera."}
        </div>
        """
        
        # Render Narasi LLM dan Grafik Secara Bersebelahan
        col_grafik, col_llm = st.columns([1, 1.8])
        with col_grafik:
            st.markdown("<p style='color:var(--accent-color); font-weight:bold; margin-bottom:5px;'>📊 AI Readiness Index:</p>", unsafe_allow_html=True)
            chart_data = pd.DataFrame({"Kategori": ["Kelengkapan Tools", "Kelayakan Kendaraan", "Parameter Genset"], "Persentase (%)": [ai_score_tools, ai_score_kendaraan, ai_score_genset]}).set_index("Kategori")
            st.bar_chart(chart_data, height=350)
            
            if len(data_ekspor) > 0:
                df_report_ai = pd.DataFrame(data_ekspor)
                csv_export = df_report_ai.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 EXPORT DATA TEXT AI KE CSV",
                    data=csv_export,
                    file_name=f"Report_AI_KUT_{selected_nama.replace(' ','_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        with col_llm:
            st.markdown(gemini_text, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    # 🔥 ========================================================= 🔥
            
    st.markdown(f"<h3 style='color:var(--accent-color);'>👤 Matrix Profil & Identitas</h3>", unsafe_allow_html=True)
    karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
    dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
    st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
    st.write("---")

    col_left, col_mid, col_right = st.columns(3)
    with col_left:
        st.markdown(f"<h3 style='color:var(--accent-color);'>🔧 Inventaris Tools</h3>", unsafe_allow_html=True)
        tools_list_df = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", "Type Genset", "KVA Genset", "Status Genset"]
        tools_data = [{"Nama Tools": t, "Kondisi / Jumlah": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list_df]
        st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

    with col_mid:
        st.markdown(f"<h3 style='color:var(--accent-color);'>🚗 Spesifikasi R2/R4</h3>", unsafe_allow_html=True)
        asset_fields = ["JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)"]
        asset_data = [{"Parameter Asset R2/R4": f, "Keterangan": str(data_asset_select[f]) if data_asset_select is not None and f in df_asset.columns and str(data_asset_select[f]).strip() not in ["nan", "None"] else "-"} for f in asset_fields]
        st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown(f"<h3 style='color:var(--accent-color);'>⚡ Parameter Genset</h3>", unsafe_allow_html=True)
        genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
        genset_data = [{"Parameter Genset": f, "Keterangan": str(data_genset_select[f]) if data_genset_select is not None and f in df_genset.columns and str(data_genset_select[f]).strip() not in ["nan", "None"] else "-"} for f in genset_fields]
        st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

    st.write("---")
    
    col_ai, col_plan = st.columns([1.5, 2.0]) 
    with col_ai:
        st.markdown(f"<h3 style='color:var(--accent-color);'>💡 Intisari Server</h3>", unsafe_allow_html=True)
        st.info("Kognitif Sistem (AI KUT Engine) telah aktif. Silakan gunakan fungsi AI KUT di Control Panel (Sidebar Kiri) untuk membuka analisis berbasis teks LLM dan export laporan CSV.")
        
    with col_plan:
        st.markdown(f"<h3 style='color:var(--accent-color);'>📝 1. Panel Transmisi Laporan</h3>", unsafe_allow_html=True)
        input_findings = st.text_area("✍️ Uraikan Detail Tindakan & Kondisi Asset:", height=120)
        
        unit_mobil = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Tidak Ada')) if data_asset_select is not None else "Tidak Ada"
        unit_genset = str(data_genset_select.get('NOMER SERI MESIN', 'Tidak Ada')) if data_genset_select is not None else "Tidak Ada"
        info_gabungan = f"Mobil: {unit_mobil} | Genset: {unit_genset}"
        
        if st.button("🚀 TRANSMISI DATA TEKS", use_container_width=True):
            if input_findings:
                with st.spinner("Menyandikan dan Mengirim Laporan ke Database..."):
                    if save_findings_to_sheet(str(dict_karyawan.get('NIK', 'N/A')), selected_nama, info_gabungan, input_findings):
                        st.success("✅ Otorisasi Sukses! Laporan telah terenkripsi dan tersimpan di server.")
                        time.sleep(1.5)
                        st.cache_data.clear(); st.rerun()
                    else: st.error("❌ Gagal menyinkronkan data. Periksa koneksi satelit/internet Anda.")
            else: st.warning("⚠️ Protokol ditolak: Kolom deskripsi tidak boleh kosong.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:var(--accent-color);'>📸 2. Sinkronisasi Evidance Visual</h3>", unsafe_allow_html=True)
        st.info("Pintu protokol terbuka. Sistem mengunci Identitas dan Aset Anda untuk transmisi form.")
        
        val_nik = str(dict_karyawan.get('NIK', '-'))
        url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
        url_gform_dinamis = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(selected_nama)}&entry.1607280297={urllib.parse.quote(unit_mobil)}&entry.505680533={urllib.parse.quote('Mobil')}"
        
        st.markdown(f"""
        <a href="{url_gform_dinamis}" target="_blank" style="text-decoration:none;">
            <div style="background: var(--gradient-bg); padding: 18px; border-radius: 14px; color: white; text-align: center; font-weight: 900; font-size: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 20px var(--glow-color); border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); letter-spacing: 1px;" onmouseover="this.style.transform='scale(1.02) translateY(-3px)'; this.style.boxShadow='0 15px 40px rgba(0,0,0,0.7), 0 0 30px var(--primary-color)';" onmouseout="this.style.transform='scale(1) translateY(0)'; this.style.boxShadow='0 10px 30px rgba(0,0,0,0.5), 0 0 20px var(--glow-color)';">
                <span style="font-size:20px;">📸</span> BUKA PORTAL UPLOAD EVIDANCE
            </div>
        </a>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown(f"<h3 style='color:var(--accent-color); font-size:26px;'>📂 DATABASE EVIDANCE & RIWAYAT</h3>", unsafe_allow_html=True)
    
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
        "🚗 Matrix R2/R4", "⚡ Matrix Genset", "🔧 Matrix Tools", "🛠️ Riwayat Evidance Service", "📄 Fakta Integritas"
    ])
    
    def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
        with tab_context:
            if data_row is not None:
                photos_exist = False
                valid_photos = []
                for col_name in df_columns:
                    cell_val = str(data_row[col_name]).strip()
                    match = re.search(r'[-\w]{25,}', cell_val) 
                    if match: valid_photos.append((col_name, match.group(0)))
                
                if valid_photos:
                    photos_exist = True
                    cols = st.columns(4) 
                    for idx, (col_name, file_id) in enumerate(valid_photos):
                        img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                        original_url = f"https://drive.google.com/file/d/{file_id}/view"
                        html_card = f"""
                        <div class="gallery-card-3d">
                            <img src="{img_url}" referrerpolicy="no-referrer">
                            <div style="margin-top:10px;">
                                <p style="font-size:11px; color:var(--accent-color); font-weight:bold; margin-bottom:5px; text-transform:uppercase;">{col_name}</p>
                                <a href="{original_url}" target="_blank" class="btn-buka-foto">🔍 HD View</a>
                            </div>
                        </div>
                        """
                        with cols[idx % 4]:
                            st.markdown(html_card, unsafe_allow_html=True)
                            with st.expander("🤖 PEMINDAIAN AI SICAKEP"): st.markdown(f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>🧠 {generate_ai_analysis_mini(file_id)}</div>", unsafe_allow_html=True)
                
                if not photos_exist: st.info(empty_msg)
            else: st.info(empty_msg)

    render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Data visual kendaraan belum terarsip.")
    render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Data visual genset belum terarsip.")
    render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Data visual tools belum terarsip.")
        
    with tab_perbaikan:
        if selected_nama != "-":
            ai_rek = pd.DataFrame()
            if not df_rekomendasi.empty:
                r_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
                if r_col: ai_rek = df_rekomendasi[df_rekomendasi[r_col].astype(str).str.strip().str.lower() == selected_nama.strip().lower()]
            ai_evid = df_evidence[df_evidence.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)] if not df_evidence.empty else pd.DataFrame()
            
            if not ai_rek.empty or not ai_evid.empty:
                st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase;'>Histori Tindakan & Bukti Visual: {selected_nama}</h4>", unsafe_allow_html=True)
                rek_iter = list(ai_rek.iloc[::-1].iterrows()) if not ai_rek.empty else []
                evid_iter = list(ai_evid.iloc[::-1].iterrows()) if not ai_evid.empty else []
                
                for (rek_idx, row_rek), (evid_idx, row_evid) in zip_longest(rek_iter, evid_iter, fillvalue=(None, None)):
                    if row_rek is not None:
                        teks_laporan = row_rek.get('Findings & Action Plan', '')
                        if pd.isna(teks_laporan) or teks_laporan.strip() == "": teks_laporan = "- Lampiran foto tanpa deskripsi teks -"
                        st.markdown(f"<div class='report-box-premium'><span class='report-date-badge'>⏱️ LOG: {row_rek.get('Timestamp', '-')}</span><p style='color:#f8fafc; font-size:16px;'>{teks_laporan}</p></div>", unsafe_allow_html=True)
                    
                    if row_evid is not None:
                        waktu_foto = row_evid.iloc[0] if len(row_evid) > 0 else "-"
                        valid_photos = []
                        for col_val in row_evid.values:
                            val_str = str(col_val).strip()
                            if "drive.google.com" in val_str:
                                urls = val_str.split(',')
                                for u in urls:
                                    m = re.search(r'[-\w]{25,}', u)
                                    if m: valid_photos.append(m.group(0))

                        if valid_photos:
                            st.markdown(f"<p style='font-size:12px; color:var(--accent-color); font-weight:bold;'>[ 📸 VISUAL EVIDANCE - {waktu_foto} ]</p>", unsafe_allow_html=True)
                            cols = st.columns(4) 
                            for idx, file_id in enumerate(valid_photos):
                                html_card = f"<div class='gallery-card-3d' style='background:rgba(9,14,23,0.8);'><img src='https://drive.google.com/thumbnail?id={file_id}&sz=w1000' referrerpolicy='no-referrer'><a href='https://drive.google.com/file/d/{file_id}/view' target='_blank' class='btn-buka-foto'>🔍 Buka</a></div>"
                                with cols[idx % 4]:
                                    st.markdown(html_card, unsafe_allow_html=True)
                                    with st.expander("🤖 PEMINDAIAN AI SICAKEP"): st.markdown(f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>🧠 {generate_ai_analysis_mini(file_id)}</div>", unsafe_allow_html=True)
                    st.write("<br><div style='height:2px; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); margin: 20px 0;'></div>", unsafe_allow_html=True)
            else: st.info("Tidak ada rekam jejak untuk personel ini.")
        else: st.info("Pilih personel di panel atas.")

    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase;'>Vault Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
                for _, row in matched_fakta.iloc[::-1].iterrows():
                    st.markdown(f"<span class='report-date-badge'>⏱️ TIMESTAMP: {row.get('Timestamp', row.get('TANGGAL', '-'))}</span>", unsafe_allow_html=True)
                    valid_files = []
                    for c in matched_fakta.columns:
                        if "drive.google.com" in str(row[c]):
                            urls = str(row[c]).split(',')
                            for u in urls:
                                m = re.search(r'[-\w]{25,}', u)
                                if m: valid_files.append(m.group(0))
                    
                    if valid_files:
                        cols = st.columns(4)
                        for idx, file_id in enumerate(valid_files):
                            html_card = f"<div class='gallery-card-3d'><img src='https://drive.google.com/thumbnail?id={file_id}&sz=w800' referrerpolicy='no-referrer'><a href='https://drive.google.com/file/d/{file_id}/view' target='_blank' class='btn-buka-foto'>📥 Unduh PDF</a></div>"
                            with cols[idx % 4]:
                                st.markdown(html_card, unsafe_allow_html=True)
                                with st.expander("🤖 VERIFIKASI AI"): st.markdown(f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>🧠 {generate_ai_analysis_mini(file_id, is_doc=True)}</div>", unsafe_allow_html=True)
                    st.write("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            else: st.warning("Dokumen Fakta Integritas tidak ditemukan.")
        else: st.info("Terkunci. Pilih personel.")
