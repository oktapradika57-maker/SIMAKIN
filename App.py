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
# Mengambil nama karyawan aktif untuk dijadikan generator warna acak yang konsisten
selected_nama_raw = "-"
if 'selected_nama_karyawan' in st.session_state:
    selected_nama_raw = st.session_state.selected_nama_karyawan

# Palet warna premium untuk tema adaptif
themes = [
    {"primary": "#3b82f6", "glow": "rgba(59, 130, 246, 0.6)", "gradient": "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)"}, # Neon Blue
    {"primary": "#10b981", "glow": "rgba(16, 185, 129, 0.6)", "gradient": "linear-gradient(135deg, #064e3b 0%, #10b981 100%)"}, # Emerald Green
    {"primary": "#8b5cf6", "glow": "rgba(139, 92, 246, 0.6)", "gradient": "linear-gradient(135deg, #4c1d95 0%, #8b5cf6 100%)"}, # Royal Purple
    {"primary": "#f59e0b", "glow": "rgba(245, 158, 11, 0.6)", "gradient": "linear-gradient(135deg, #78350f 0%, #f59e0b 100%)"}, # Amber Sunset
    {"primary": "#ec4899", "glow": "rgba(236, 72, 153, 0.6)", "gradient": "linear-gradient(135deg, #831843 0%, #ec4899 100%)"}, # Premium Rose
    {"primary": "#06b6d4", "glow": "rgba(6, 182, 212, 0.6)", "gradient": "linear-gradient(135deg, #164e63 0%, #06b6d4 100%)"}  # Cyber Cyan
]
theme_idx = sum(ord(char) for c in selected_nama_raw) % len(themes) if selected_nama_raw != "-" else 0
active_theme = themes[theme_idx]

# --- 3. CUSTOM ADVANCED CSS DESIGN (3D Luxury & Smooth Animation) ---
st.markdown(f"""
<style>
    /* Definisi CSS Variabel Global sesuai tema aktif */
    :root {{
        --primary-color: {active_theme['primary']};
        --glow-color: {active_theme['glow']};
        --gradient-bg: {active_theme['gradient']};
    }}

    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes pulse-glow {{ 0% {{ filter: drop-shadow(0 0 8px var(--glow-color)); }} 100% {{ filter: drop-shadow(0 0 25px var(--primary-color)); }} }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-8px); }} }}
    
    .stApp {{ background-color: #060913; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, sans-serif; }}
    .main .block-container {{ animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1); }}
    
    /* 3D Glassmorphism Box Login */
    div[data-testid="stForm"] {{
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 40px !important;
        border-radius: 24px !important;
        box-shadow: 0px 25px 50px rgba(0, 0, 0, 0.5), inset 0px 1px 3px rgba(255, 255, 255, 0.1) !important;
        max-width: 460px !important;
        margin: 40px auto !important;
        transition: border-color 0.5s ease, box-shadow 0.5s ease;
    }}
    div[data-testid="stForm"]:hover {{
        border-color: var(--primary-color) !important;
        box-shadow: 0px 25px 60px rgba(0, 0, 0, 0.6), 0 0 30px var(--glow-color) !important;
    }}
    
    /* Animasi Logo Premium */
    .logo-elegant {{
        display: block;
        margin: 0 auto;
        border-radius: 14px;
        animation: pulse-glow 3s infinite alternate, float 4.5s infinite ease-in-out;
    }}
    
    /* Desain Input & Selectbox Presisi */
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label {{ 
        color: #94a3b8 !important; font-weight: 700 !important; letter-spacing: 0.5px; font-size: 13px !important;
        transition: color 0.3s ease;
    }}
    div[data-testid="stTextInput"]:hover label, div[data-testid="stSelectbox"]:hover label, div[data-testid="stTextArea"]:hover label {{
        color: var(--primary-color) !important;
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {{
        border-radius: 12px !important; border: 1px solid #1e293b !important;
        background-color: #0f172a !important; color: #ffffff !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4) !important;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus {{ 
        border-color: var(--primary-color) !important; box-shadow: 0 0 14px var(--glow-color), inset 0 1px 2px rgba(0,0,0,0.2) !important; 
    }}
    
    /* Tombol Interaktif */
    button[kind="primaryFormSubmit"], .stButton>button {{ 
        background: var(--gradient-bg) !important; border: none !important; 
        border-radius: 12px !important; color: white !important; font-weight: 700 !important; 
        padding: 12px 0 !important; box-shadow: 0 4px 15px var(--glow-color) !important; transition: all 0.3s ease;
    }}
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover {{
        transform: translateY(-2px); box-shadow: 0 8px 25px var(--primary-color) !important; filter: brightness(1.1);
    }}
    
    /* Header Utama Aplikasi */
    .header-style {{
        background: var(--gradient-bg); padding: 22px; border-radius: 18px; 
        color: #ffffff; font-weight: 800; font-size: 28px; text-align: center; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4), 0 0 20px var(--glow-color); 
        margin-bottom: 35px; border: 1px solid rgba(255,255,255,0.1);
        text-shadow: 0 2px 4px rgba(0,0,0,0.3); transition: all 0.5s ease;
    }}
    
    /* Desain Galeri 3D Presisi */
    .gallery-card-3d {{
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.05);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin-bottom: 15px;
    }}
    .gallery-card-3d:hover {{
        transform: translateY(-6px) scale(1.02);
        border-color: var(--primary-color);
        box-shadow: 0 18px 35px rgba(0,0,0,0.4), 0 0 20px var(--glow-color);
    }}
    .gallery-card-3d img {{
        width: 100%;
        border-radius: 10px;
        transition: transform 0.4s ease;
    }}
    .gallery-card-3d:hover img {{
        transform: scale(1.01);
    }}
    
    /* Box Riwayat Berpasangan */
    .report-box-premium {{
        background: #0f172a; padding: 22px; border-radius: 16px; 
        border-left: 6px solid var(--primary-color); border-right: 1px solid rgba(255,255,255,0.05);
        border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 15px; margin-top: 15px; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }}
    .report-box-premium:hover {{
        background: #131e35; box-shadow: 0 10px 25px rgba(0,0,0,0.3), 0 0 15px rgba(255,255,255,0.02);
    }}

    h1, h2, h3, h4, h5 {{ color: #ffffff !important; font-weight: 700 !important; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }}
    p, span, div {{ color: #cbd5e1; }}
    hr {{ border-color: #1e293b; }}
    [data-testid="stDataFrame"] {{ background-color: #0f172a; border-radius: 14px; padding: 6px; border: 1px solid rgba(255,255,255,0.05); }}
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
            
        st.markdown('<h1 style="color:#ffffff; text-align:center; font-weight:900; margin-bottom:0px; margin-top:15px; letter-spacing:1px;">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:12px; color:#94a3b8; margin-bottom:30px;">System Monitoring Asset Kinarya | Reg Kalimantan</p>', unsafe_allow_html=True)
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

# --- 5. SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.markdown(render_logo_html(width="80%"), unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top:20px; font-size:20px;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <a href="https://regkalimantan-kut.vercel.app/#sva" target="_blank" style="text-decoration: none;">
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 12px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(16,185,129,0.3); font-size: 13px;">
            🌍 Jelajah Lebih Jauh Lagi
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.info("👤 **Aktif:** SIMAKINKUT")
    st.markdown("---")
    if st.button("🔄 Refresh Data Server", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Keluar Sistem", use_container_width=True):
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
            xls.get("ALL ASSET MBP MBP CME TE REG KALIMA", xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame())), 
            xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), 
            xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), 
            xls.get("Rekomendasi Perbaikan", pd.DataFrame()), 
            xls.get("FAKTA INTERITAR", pd.DataFrame()),
            xls.get("Evidance foto", pd.DataFrame()) 
        ) 
    except: 
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sinkronisasi Mesin Data Visual..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 8. LAYOUT UTAMA DASHBOARD ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET | KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    df_sdm_filtered = df_sdm.copy()
    data_karyawan_select = None; data_asset_select = None; data_genset_select = None; data_tools_asset_select = None
    selected_nama = "-"
    
    st.markdown("### 🔍 Filter Pencarian Karyawan")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4) 
    
    with col_f1:
        list_job = ["SEMUA JABATAN"] + list(df_sdm['JOB'].dropna().unique()) if 'JOB' in df_sdm.columns else ["SEMUA JABATAN"]
        selected_job = st.selectbox("💼 Filter Jabatan:", list_job)
        if selected_job != "SEMUA JABATAN": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]

    with col_f2:
        list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique()) if 'LOKER' in df_sdm_filtered.columns else ["SEMUA LOKER"]
        selected_loker = st.selectbox("📍 Filter Loker Kerja:", list_loker)
        if selected_loker != "SEMUA LOKER": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]

    with col_f3:
        list_nopol = ["SEMUA NOPOL"] + list(df_asset['NOPOL (PLAT NOMOR)'].dropna().unique()) if not df_asset.empty and 'NOPOL (PLAT NOMOR)' in df_asset.columns else ["SEMUA NOPOL"]
        selected_nopol = st.selectbox("🚗 Filter Plat (NOPOL):", list_nopol)
            
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
            selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", list_nama)
            # Simpan state nama agar tema berubah dinamis seketika
            if st.session_state.get('selected_nama_karyawan') != selected_nama:
                st.session_state.selected_nama_karyawan = selected_nama
                st.rerun()
                
            data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
            data_asset_select = get_row_by_name(df_asset, selected_nama)
            data_genset_select = get_row_by_name(df_genset, selected_nama)
            data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)

    st.write("---")
            
    st.markdown("### 👤 Profil & Identitas Karyawan")
    karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
    dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
    st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
    st.write("---")

    col_left, col_mid, col_right = st.columns(3)
    with col_left:
        st.markdown("### 🔧 Data Tools (Alat Kerja)")
        tools_list = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", "Type Genset", "KVA Genset", "Status Genset"]
        tools_data = [{"Nama Tools": t, "Kondisi / Jumlah": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list]
        st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

    with col_mid:
        st.markdown("### 🚗 Data Asset R2/R4")
        asset_fields = ["JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)"]
        asset_data = [{"Parameter Asset R2/R4": f, "Keterangan": str(data_asset_select[f]) if data_asset_select is not None and f in df_asset.columns and str(data_asset_select[f]).strip() not in ["nan", "None"] else "-"} for f in asset_fields]
        st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("### ⚡ Data Genset")
        genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
        genset_data = [{"Parameter Genset": f, "Keterangan": str(data_genset_select[f]) if data_genset_select is not None and f in df_genset.columns and str(data_genset_select[f]).strip() not in ["nan", "None"] else "-"} for f in genset_fields]
        st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

    st.write("---")
    
    # --- 9. FORM INPUT HYBRID (Teks di Streamlit, Auto-Fill di Google Form) ---
    col_chart, col_plan = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("### 📊 Statistik Kondisi Tools")
        st.info("Visualisasi analisis grafik sedang dioptimalkan server.") 
        
    with col_plan:
        st.markdown("### 📝 1. Form Teks Laporan & Action Plan")
        input_findings = st.text_area("✍️ Ketik deskripsi laporan perbaikan Anda di sini:", height=100)
        
        unit_mobil = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Tidak Ada')) if data_asset_select is not None else "Tidak Ada"
        unit_genset = str(data_genset_select.get('NOMER SERI MESIN', 'Tidak Ada')) if data_genset_select is not None else "Tidak Ada"
        info_gabungan = f"Mobil: {unit_mobil} | Genset: {unit_genset}"
        
        if st.button("🚀 Push Teks Laporan ke Server", use_container_width=True):
            if input_findings:
                with st.spinner("Menyimpan Laporan Teks..."):
                    if save_findings_to_sheet(str(dict_karyawan.get('NIK', 'N/A')), selected_nama, info_gabungan, input_findings):
                        st.success("✅ Teks Laporan berhasil terunggah permanen!")
                        time.sleep(1.5)
                        st.cache_data.clear()
                        st.rerun()
                    else: st.error("❌ Gagal menyimpan data. Periksa koneksi internet.")
            else: st.warning("⚠️ Laporan perbaikan tidak boleh kosong.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📸 2. Upload Evidence (Foto)")
        st.info("Klik tombol pintar di bawah. Data NIK, Nama, dan Plat Kendaraan Anda otomatis terisi di Google Form!")
        
        # PRE-FILLED URL LOGIC GOOGLE FORM ASLI ANDA
        val_nik = str(dict_karyawan.get('NIK', '-'))
        val_nama = selected_nama
        val_nopol = unit_mobil
        val_jenis = "Mobil"
        
        url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
        url_gform_dinamis = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(val_nama)}&entry.1607280297={urllib.parse.quote(val_nopol)}&entry.505680533={urllib.parse.quote(val_jenis)}"
        
        st.markdown(f"""
        <a href="{url_gform_dinamis}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 15px; border-radius: 12px; color: white; text-align: center; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); text-align: center; transition: transform 0.2s;">
                🚀 UPLOAD FOTO EVIDANCE (AUTO-FILL GOOGLE FORM)
            </div>
        </a>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide Gallery")
    
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
        "🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Riwayat Bukti Perbaikan", "📄 Fakta Integritas"
    ])
    
    # --- GALERI GRID PREMIUM 3D WITH CORS PENEMBUS BYPASS ---
    def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
        with tab_context:
            if data_row is not None:
                photos_exist = False
                cols = st.columns(4)
                idx = 0
                for col_name in df_columns:
                    cell_val = str(data_row[col_name]).strip()
                    match = re.search(r'[-\w]{25,}', cell_val) 
                    if match:
                        photos_exist = True
                        file_id = match.group(0)
                        # Menggunakan Resolusi Tinggi Thumbnail dengan no-referrer bypass
                        img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                        html = f"""
                        <div class="gallery-card-3d">
                            <img src="{img_url}" referrerpolicy="no-referrer">
                            <p style="font-size:11px; color:#94a3b8; font-weight:bold; margin-top:8px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{col_name}</p>
                        </div>
                        """
                        cols[idx % 4].markdown(html, unsafe_allow_html=True)
                        idx += 1
                if not photos_exist: st.info(empty_msg)
            else: st.info(empty_msg)

    render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Tidak ada foto kendaraan R2/R4.")
    render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Tidak ada foto unit Genset.")
    render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Tidak ada foto unit Tools.")
        
    # --- TAB RIWAYAT PERBAIKAN: SINKRONISASI TOTAL TEKS & FOTO DARI DRIVER SHEET EVIDANCE ---
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
                st.markdown(f"<h4 style='color:var(--primary-color);'>Arsip Laporan Service & Evidance Foto: {selected_nama}</h4>", unsafe_allow_html=True)
                
                rek_iter = list(matched_rek.iloc[::-1].iterrows()) if not matched_rek.empty else []
                evid_iter = list(matched_evid.iloc[::-1].iterrows()) if not matched_evid.empty else []
                
                # Render berurutan kombinasi teks dan foto dari data terbaru
                for (rek_idx, row_rek), (evid_idx, row_evid) in zip_longest(rek_iter, sled_evid := evid_iter, fillvalue=(None, None)):
                    
                    if row_rek is not None:
                        teks_laporan = row_rek.get('Findings & Action Plan', '')
                        waktu_teks = row_rek.get('Timestamp', '-')
                        if pd.isna(teks_laporan) or teks_laporan.strip() == "":
                            teks_laporan = "- <i>Hanya Lampiran Foto Lampiran Evidance</i> -"
                            
                        st.markdown(f"""
                        <div class="report-box-premium">
                            <h4 style="color:var(--primary-color); margin-top:0; font-size:16px;">📅 Update Laporan: {waktu_teks}</h4>
                            <p style="color:#f1f5f9; font-size:15px; white-space: pre-wrap; line-height:1.6; font-weight:500;">{teks_laporan}</p>
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
                            st.markdown(f"<p style='font-size:12px; color:#94a3b8; margin-left:10px;'>📸 <b>Evidance Foto Terkait ({waktu_foto}):</b></p>", unsafe_allow_html=True)
                            cols = st.columns(2) # Tampilan 2 Kolom Raksasa Mewah
                            for i, file_id in enumerate(valid_photos):
                                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
                                original_url = f"https://drive.google.com/file/d/{file_id}/view"
                                with cols[i % 2]: 
                                    html_img = f"""
                                    <div class="gallery-card-3d" style="background: #090f22; border-color: rgba(255,255,255,0.03);">
                                        <img src="{thumb_url}" referrerpolicy="no-referrer">
                                        <div style="text-align:center; margin-top: 10px;">
                                            <a href="{original_url}" target="_blank" style="background: var(--gradient-bg); color: white; padding: 8px 14px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; display: inline-block; box-shadow: 0 4px 10px var(--glow-color); width:90%;">🔍 Lihat Ukuran Penuh</a>
                                        </div>
                                    </div>
                                    """
                                    st.markdown(html_img, unsafe_allow_html=True)
                    st.write("<br>", unsafe_allow_html=True)
            else: st.info("Belum ada riwayat laporan perbaikan untuk karyawan ini.")
        else: st.info("Silakan pilih karyawan terlebih dahulu.")

    # --- TAB FAKTA INTEGRITAS ---
    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:var(--primary-color);'>Arsip Dokumen Fakta Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
                for _, row in matched_fakta.iloc[::-1].iterrows():
                    st.markdown(f"**📅 Diupload pada: {row.get('Timestamp', row.get('TANGGAL', '-'))}**")
                    valid_files = []
                    for c in matched_fakta.columns:
                        if "drive.google.com" in str(row[c]):
                            urls = str(row[c]).split(',')
                            for u in urls:
                                match = re.search(r'[-\w]{25,}', u)
                                if match: valid_files.append(match.group(0))
                    
                    if valid_files:
                        cols = st.columns(len(valid_files))
                        for i, file_id in enumerate(valid_files):
                            thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                            original_url = f"https://drive.google.com/file/d/{file_id}/view"
                            with cols[i]:
                                html_img = f"""
                                <div class="gallery-card-3d">
                                    <img src="{thumb_url}" referrerpolicy="no-referrer">
                                    <div style="text-align:center; margin-top:10px;">
                                        <a href="{original_url}" target="_blank" style="background: var(--gradient-bg); color: white; padding: 8px 15px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; width:100%; display:inline-block;">📥 BUKA DOKUMEN</a>
                                    </div>
                                </div>
                                """
                                st.markdown(html_img, unsafe_allow_html=True)
                    else: st.info("Tidak ada dokumen PDF/Foto yang terlampir.")
                    st.write("<br><hr style='border-color: #1e293b;'>", unsafe_allow_html=True)
            else: st.warning(f"Belum ada arsip form Fakta Integritas atas nama: {selected_nama}")
        else: st.info("Data sheet FAKTA INTEGRITAS masih kosong.")
