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
from itertools import zip_longest 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. SISTEM FILTRASI WARNA DINAMIS (COLOR-SHIFTING THEME) ---
selected_nama_raw = "-"
if 'selected_nama_karyawan' in st.session_state:
    selected_nama_raw = st.session_state.selected_nama_karyawan

# Palet warna Ultra-Premium
themes = [
    {"primary": "#3b82f6", "glow": "rgba(59, 130, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%)", "accent": "#60a5fa"}, # Neon Blue
    {"primary": "#10b981", "glow": "rgba(16, 185, 129, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #064e3b 50%, #10b981 100%)", "accent": "#34d399"}, # Emerald Green
    {"primary": "#8b5cf6", "glow": "rgba(139, 92, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #4c1d95 50%, #8b5cf6 100%)", "accent": "#a78bfa"}, # Royal Purple
    {"primary": "#f59e0b", "glow": "rgba(245, 158, 11, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #78350f 50%, #f59e0b 100%)", "accent": "#fbbf24"}, # Amber Sunset
    {"primary": "#ec4899", "glow": "rgba(236, 72, 153, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #831843 50%, #ec4899 100%)", "accent": "#f472b6"}, # Premium Rose
    {"primary": "#06b6d4", "glow": "rgba(6, 182, 212, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #164e63 50%, #06b6d4 100%)", "accent": "#22d3ee"}  # Cyber Cyan
]
theme_idx = sum(ord(c) for c in selected_nama_raw) % len(themes) if selected_nama_raw != "-" else 0
active_theme = themes[theme_idx]

# --- 3. CUSTOM ADVANCED CSS DESIGN (Ultra 3D Luxury & Precision Layout) ---
st.markdown(f"""
<style>
    :root {{
        --primary-color: {active_theme['primary']};
        --glow-color: {active_theme['glow']};
        --gradient-bg: {active_theme['gradient']};
        --accent-color: {active_theme['accent']};
    }}

    /* Global Animations */
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes float-elegant {{ 0%, 100% {{ transform: translateY(0px); filter: drop-shadow(0 5px 15px var(--glow-color)); }} 50% {{ transform: translateY(-10px); filter: drop-shadow(0 15px 25px var(--primary-color)); }} }}
    @keyframes shimmer {{ 0% {{ background-position: -200% center; }} 100% {{ background-position: 200% center; }} }}
    
    .stApp {{ background-color: #050811; color: #e2e8f0; font-family: 'Inter', 'Segoe UI', sans-serif; }}
    .main .block-container {{ animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1); }}
    
    /* 3D Glassmorphism Login Box */
    div[data-testid="stForm"] {{
        background: rgba(13, 19, 33, 0.65) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 50px !important;
        border-radius: 30px !important;
        box-shadow: 0px 30px 60px rgba(0, 0, 0, 0.6), inset 0px 1px 2px rgba(255, 255, 255, 0.1) !important;
        max-width: 480px !important;
        margin: 50px auto !important;
        transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
    }}
    div[data-testid="stForm"]:hover {{
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0px 40px 80px rgba(0, 0, 0, 0.8), 0 0 40px var(--glow-color) !important;
    }}
    
    /* Floating Logo */
    .logo-elegant {{
        display: block; margin: 0 auto; border-radius: 18px;
        animation: float-elegant 4s infinite ease-in-out;
    }}
    
    /* Ultra-Premium Input Fields (Mewah & Tidak Monoton) */
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label {{ 
        color: var(--accent-color) !important; font-weight: 700 !important; letter-spacing: 0.8px; font-size: 13px !important;
        text-transform: uppercase; margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {{
        border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(15, 23, 42, 0.8) !important; color: #ffffff !important; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: inset 0 2px 6px rgba(0,0,0,0.5) !important;
        padding: 12px 16px !important;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus {{ 
        border-color: var(--primary-color) !important; 
        box-shadow: 0 0 20px var(--glow-color), inset 0 1px 3px rgba(0,0,0,0.3) !important; 
        background: rgba(30, 41, 59, 0.9) !important;
        transform: translateY(-2px);
    }}
    
    /* Tombol Interaktif Premium (Shimmer Effect) */
    button[kind="primaryFormSubmit"], .stButton>button {{ 
        background: var(--gradient-bg) !important; border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 14px !important; color: white !important; font-weight: 800 !important; letter-spacing: 1px;
        padding: 14px 0 !important; box-shadow: 0 8px 20px rgba(0,0,0,0.4), 0 0 15px var(--glow-color) !important; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        background-size: 200% auto;
    }}
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover {{
        transform: translateY(-4px) scale(1.02); 
        box-shadow: 0 15px 30px rgba(0,0,0,0.6), 0 0 25px var(--primary-color) !important; 
        border-color: rgba(255,255,255,0.3) !important;
        animation: shimmer 2s linear infinite;
    }}
    
    /* Header Utama */
    .header-style {{
        background: var(--gradient-bg); padding: 25px; border-radius: 20px; 
        color: #ffffff; font-weight: 900; font-size: 30px; text-align: center; letter-spacing: 1.5px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 2px 5px rgba(255,255,255,0.2); 
        margin-bottom: 40px; border: 1px solid rgba(255,255,255,0.1);
        text-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }}
    
    /* =========================================================
       FIX GALERI HORIZONTAL: Menggunakan Kolom Streamlit + Card CSS
       ========================================================= */
    .gallery-card-3d {{
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 18px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 15px; /* Jarak antar baris ke bawah */
    }}
    .gallery-card-3d:hover {{
        transform: translateY(-8px);
        border-color: var(--accent-color);
        box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 25px var(--glow-color);
    }}
    /* Gambar Presisi (Tidak Penuh Layar) & UTUH */
    .gallery-card-3d img {{
        width: 100%;
        height: 220px; /* Tinggi seragam agar sejajar rapi */
        object-fit: contain; /* FOTO TAMPIL UTUH/FULL, TIDAK TERPOTONG */
        background: rgba(0, 0, 0, 0.4); 
        padding: 5px;
        border-radius: 12px;
        transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.6);
    }}
    .gallery-card-3d:hover img {{
        transform: scale(1.03); 
    }}
    .btn-buka-foto {{
        background: var(--gradient-bg); color: white !important; padding: 10px; 
        border-radius: 10px; text-decoration: none; font-size: 12px; font-weight: 800; 
        display: block; margin-top: 12px; border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-transform: uppercase;
    }}
    .btn-buka-foto:hover {{
        background: var(--primary-color); box-shadow: 0 6px 20px var(--glow-color); transform: translateY(-2px);
    }}
    
    /* Box Teks Laporan Premium */
    .report-box-premium {{
        background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(9,14,23,0.9) 100%);
        padding: 25px; border-radius: 20px; 
        border-left: 6px solid var(--primary-color);
        border-top: 1px solid rgba(255,255,255,0.08);
        border-right: 1px solid rgba(255,255,255,0.02);
        border-bottom: 1px solid rgba(255,255,255,0.02);
        margin-bottom: 20px; margin-top: 20px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
        transition: all 0.4s ease;
    }}
    .report-box-premium:hover {{
        transform: translateX(5px);
        border-left-color: var(--accent-color);
        box-shadow: 0 20px 40px rgba(0,0,0,0.5), -5px 0 20px var(--glow-color);
    }}
    .report-date-badge {{
        background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: bold; color: var(--accent-color);
        display: inline-block; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05);
    }}

    /* Tabel DataFrame Modern */
    [data-testid="stDataFrame"] {{ 
        background: rgba(15, 23, 42, 0.5); border-radius: 16px; padding: 8px; 
        border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI DETEKSI LOGO UTAMA ---
def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    logo_2 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp"
    if os.path.exists(logo_1): return logo_1
    elif os.path.exists(logo_2): return logo_2
    return None

def render_logo_html(width="100%"):
    path = get_logo_path()
    if path:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f'<img src="data:image/webp;base64,{encoded_string}" class="logo-elegant" style="width:{width};">'
    return ""

# --- 4. SISTEM PORTAL LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.markdown(render_logo_html(), unsafe_allow_html=True)
            
        st.markdown('<h1 style="color:#ffffff; text-align:center; font-weight:900; margin-bottom:0px; margin-top:20px; letter-spacing:2px; text-shadow: 0 0 15px var(--glow-color);">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:13px; color:#94a3b8; margin-bottom:35px; letter-spacing: 1px;">SYSTEM MONITORING ASSET KINARYA | REG KALIMANTAN</p>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        submit = st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True)
    
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("❌ Kredensial Salah!")

if not st.session_state.logged_in:
    login_form(); st.stop() 

# --- 5. SIDEBAR CONTROL PANEL MEWAH ---
with st.sidebar:
    st.markdown(render_logo_html(width="75%"), unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; margin-top:25px; font-size:18px; color:var(--accent-color); letter-spacing: 1.5px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <a href="https://regkalimantan-kut.vercel.app/#sva" target="_blank" style="text-decoration: none;">
        <div style="background: var(--gradient-bg); padding: 14px; border-radius: 12px; text-align: center; color: white; font-weight: 800; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.4); font-size: 13px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px;" onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 10px 25px var(--glow-color)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 20px rgba(0,0,0,0.4)';">
            🌍 Jelajah Ruang Kinerja
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.info("👤 **Otoritas Aktif:** SIMAKINKUT")
    st.markdown("---")
    if st.button("🔄 Sinkronisasi Server", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Terminasi Sesi", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

# --- 6. FUNGSI DRIVER SHEET & BACKEND ---
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
        try: worksheet = sh.worksheet("Rekomendasi Perbaikan")
        except:
            worksheet = sh.add_worksheet(title="Rekomendasi Perbaikan", rows="1000", cols="10")
            worksheet.append_row(["Timestamp", "NIK", "Nama", "Unit Asset (Mobil & Genset)", "Findings & Action Plan", "Foto 1", "Foto 2", "Foto 3", "Foto 4", "Foto 5"])
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nik, nama, unit_info, findings, "", "", "", "", ""])
        return True
    except: return False

# --- 7. INGEST DATA SERVER SHEET ---
@st.cache_data(ttl=60)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (
            xls.get("SDM", pd.DataFrame()), 
            xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), 
            xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), 
            xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), 
            xls.get("Rekomendasi Perbaikan", pd.DataFrame()), 
            xls.get("FAKTA INTERITAR", pd.DataFrame()),
            xls.get("Evidance foto", pd.DataFrame()) 
        ) 
    except: 
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sinkronisasi Mesin Data Visual 3D..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 8. LAYOUT UTAMA DASHBOARD ---
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
                st.session_state.selected_nama_karyawan = selected_nama
                st.rerun()
                
            data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
            data_asset_select = get_row_by_name(df_asset, selected_nama)
            data_genset_select = get_row_by_name(df_genset, selected_nama)
            data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)

    st.write("---")
            
    st.markdown(f"<h3 style='color:var(--accent-color);'>👤 Matrix Profil & Identitas</h3>", unsafe_allow_html=True)
    karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
    dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
    st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
    st.write("---")

    col_left, col_mid, col_right = st.columns(3)
    with col_left:
        st.markdown(f"<h3 style='color:var(--accent-color);'>🔧 Inventaris Tools</h3>", unsafe_allow_html=True)
        tools_list = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", "Type Genset", "KVA Genset", "Status Genset"]
        tools_data = [{"Nama Tools": t, "Kondisi / Jumlah": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list]
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
    
    # --- 9. FORM INPUT HYBRID (Teks di Streamlit, Auto-Fill di GForm) ---
    col_chart, col_plan = st.columns([1.2, 2.3]) 
    
    with col_chart:
        st.markdown(f"<h3 style='color:var(--accent-color);'>📊 Analitik Visual</h3>", unsafe_allow_html=True)
        st.info("Render grafik 3D sedang dioptimalkan oleh sistem server.") 
        
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
                        st.cache_data.clear()
                        st.rerun()
                    else: st.error("❌ Gagal menyinkronkan data. Periksa koneksi satelit/internet Anda.")
            else: st.warning("⚠️ Protokol ditolak: Kolom deskripsi tidak boleh kosong.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:var(--accent-color);'>📸 2. Sinkronisasi Evidance Visual</h3>", unsafe_allow_html=True)
        st.info("Pintu protokol terbuka. Sistem telah mengunci NIK, Nama, dan Aset Anda untuk transmisi form.")
        
        val_nik = str(dict_karyawan.get('NIK', '-'))
        val_nama = selected_nama
        val_nopol = unit_mobil
        val_jenis = "Mobil"
        
        url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
        url_gform_dinamis = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(val_nama)}&entry.1607280297={urllib.parse.quote(val_nopol)}&entry.505680533={urllib.parse.quote(val_jenis)}"
        
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
    
    # --- FUNGSI GALERI HORIZONTAL PAKAI KOLOM STREAMLIT (TIDAK TUMPUK KE BAWAH) ---
    def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
        with tab_context:
            if data_row is not None:
                photos_exist = False
                valid_photos = []
                for col_name in df_columns:
                    cell_val = str(data_row[col_name]).strip()
                    match = re.search(r'[-\w]{25,}', cell_val) 
                    if match:
                        valid_photos.append((col_name, match.group(0)))
                
                if valid_photos:
                    photos_exist = True
                    # MEMAKSA LAYOUT 4 KOLOM MENYAMPING SECARA HORIZONTAL (TIDAK TUMPUK)
                    cols = st.columns(4) 
                    for idx, (col_name, file_id) in enumerate(valid_photos):
                        img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
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
                        # Memasukkan ke kolom secara bergantian (menyamping)
                        cols[idx % 4].markdown(html_card, unsafe_allow_html=True)
                
                if not photos_exist: st.info(empty_msg)
            else: st.info(empty_msg)

    render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Data visual kendaraan belum terarsip di server.")
    render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Data visual genset belum terarsip di server.")
    render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Data visual tools belum terarsip di server.")
        
    # --- TAB RIWAYAT PERBAIKAN: HORIZONTAL PRESISI ---
    with tab_perbaikan:
        if selected_nama != "-":
            matched_rek = pd.DataFrame()
            if not df_rekomendasi.empty:
                rek_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
                if rek_name_col:
                    matched_rek = df_rekomendasi[df_rekomendasi[rek_name_col].astype(str).str.strip().str.lower() == selected_nama.strip().lower()]
            
            matched_evid = pd.DataFrame()
            if not df_evidence.empty:
                matched_evid = df_evidence[df_evidence.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]

            if not matched_rek.empty or not matched_evid.empty:
                st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase; letter-spacing:1px;'>Histori Tindakan & Bukti Visual: {selected_nama}</h4>", unsafe_allow_html=True)
                
                rek_iter = list(matched_rek.iloc[::-1].iterrows()) if not matched_rek.empty else []
                evid_iter = list(matched_evid.iloc[::-1].iterrows()) if not matched_evid.empty else []
                
                for (rek_idx, row_rek), (evid_idx, row_evid) in zip_longest(rek_iter, evid_iter, fillvalue=(None, None)):
                    
                    if row_rek is not None:
                        teks_laporan = row_rek.get('Findings & Action Plan', '')
                        waktu_teks = row_rek.get('Timestamp', '-')
                        if pd.isna(teks_laporan) or teks_laporan.strip() == "":
                            teks_laporan = "- Sistem mendeteksi lampiran foto tanpa deskripsi teks -"
                            
                        st.markdown(f"""
                        <div class="report-box-premium">
                            <span class="report-date-badge">⏱️ LOG SERVER: {waktu_teks}</span>
                            <p style="color:#f8fafc; font-size:16px; white-space: pre-wrap; line-height:1.7; font-weight:500; margin-bottom:0;">{teks_laporan}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if row_evid is not None:
                        waktu_foto = row_evid.iloc[0] if len(row_evid) > 0 else "-"
                        valid_photos = []
                        
                        for col_val in row_evid.values:
                            val_str = str(col_val).strip()
                            if "drive.google.com" in val_str:
                                urls = val_str.split(',')
                                for u in urls:
                                    match = re.search(r'[-\w]{25,}', u)
                                    if match: valid_photos.append(match.group(0))

                        if valid_photos:
                            st.markdown(f"<p style='font-size:12px; color:var(--accent-color); margin-left:15px; font-weight:bold; letter-spacing:0.5px;'>[ 📸 DATA VISUAL EVIDANCE - {waktu_foto} ]</p>", unsafe_allow_html=True)
                            
                            # MEMAKSA LAYOUT 4 KOLOM MENYAMPING SECARA HORIZONTAL (TIDAK TUMPUK)
                            cols = st.columns(4) 
                            for idx, file_id in enumerate(valid_photos):
                                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                                original_url = f"https://drive.google.com/file/d/{file_id}/view"
                                html_card = f"""
                                <div class="gallery-card-3d" style="background: rgba(9,14,23,0.8); border: 1px solid rgba(255,255,255,0.02);">
                                    <img src="{thumb_url}" referrerpolicy="no-referrer">
                                    <a href="{original_url}" target="_blank" class="btn-buka-foto">🔍 Expand Resolusi</a>
                                </div>
                                """
                                cols[idx % 4].markdown(html_card, unsafe_allow_html=True)
                            
                    st.write("<br><div style='height:2px; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); margin: 20px 0;'></div>", unsafe_allow_html=True)
            else: st.info("Sistem belum mendeteksi rekam jejak untuk personel ini.")
        else: st.info("Otorisasi Identitas: Pilih personel di panel atas.")

    # --- TAB FAKTA INTEGRITAS HORIZONTAL PRESISI ---
    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase;'>Vault Dokumen Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
                for _, row in matched_fakta.iloc[::-1].iterrows():
                    st.markdown(f"<span class='report-date-badge' style='margin-left:5px;'>⏱️ TIMESTAMP: {row.get('Timestamp', row.get('TANGGAL', '-'))}</span>", unsafe_allow_html=True)
                    valid_files = []
                    for c in matched_fakta.columns:
                        if "drive.google.com" in str(row[c]):
                            urls = str(row[c]).split(',')
                            for u in urls:
                                match = re.search(r'[-\w]{25,}', u)
                                if match: valid_files.append(match.group(0))
                    
                    if valid_files:
                        # MEMAKSA LAYOUT 4 KOLOM MENYAMPING SECARA HORIZONTAL (TIDAK TUMPUK)
                        cols = st.columns(4)
                        for idx, file_id in enumerate(valid_files):
                            thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                            original_url = f"https://drive.google.com/file/d/{file_id}/view"
                            html_card = f"""
                            <div class="gallery-card-3d">
                                <img src="{thumb_url}" referrerpolicy="no-referrer">
                                <a href="{original_url}" target="_blank" class="btn-buka-foto" style="background:linear-gradient(135deg, #0f172a, #1e293b);">📥 Unduh / Buka PDF</a>
                            </div>
                            """
                            cols[idx % 4].markdown(html_card, unsafe_allow_html=True)
                    else: st.info("Tidak ada dokumen yang dilampirkan.")
                    st.write("<br><hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            else: st.warning(f"Dokumen Fakta Integritas tidak ditemukan untuk: {selected_nama}")
        else: st.info("Data Vault FAKTA INTEGRITAS terkunci. Pilih personel.")
