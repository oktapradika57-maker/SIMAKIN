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
from itertools import zip_longest # Untuk menggabungkan teks dan foto secara berurutan

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SIMAKIN", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS (Animasi Elegan & Premium Dark Mode) ---
st.markdown("""
<style>
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    
    /* Animasi Logo Mengambang & Bercahaya */
    @keyframes pulse-glow {
        0% { filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.4)); }
        100% { filter: drop-shadow(0 0 25px rgba(59, 130, 246, 0.9)); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    .logo-elegant {
        display: block;
        margin: 0 auto;
        border-radius: 10px;
        animation: pulse-glow 2.5s infinite alternate, float 4s infinite ease-in-out;
    }

    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .main .block-container { animation: fadeIn 0.6s ease-out; }
    
    div[data-testid="stForm"] {
        background: rgba(26, 32, 53, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important; padding: 40px !important;
        border-radius: 20px !important; box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.6) !important;
        max-width: 450px !important; margin: 50px auto !important;
    }
    
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label { 
        color: #60a5fa !important; font-weight: bold !important; letter-spacing: 1px; 
    }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {
        border-radius: 10px !important; border: 1px solid #334155 !important;
        background-color: #1e293b !important; color: #ffffff !important; transition: 0.3s;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus { 
        border-color: #3b82f6 !important; box-shadow: 0 0 12px rgba(59, 130, 246, 0.4) !important; 
    }
    
    button[kind="primaryFormSubmit"], .stButton>button { 
        background: linear-gradient(135deg, #2563eb, #0ea5e9) !important; border: none !important; 
        border-radius: 10px !important; color: white !important; font-weight: 700 !important; 
        padding: 10px 0 !important; box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important; transition: 0.3s;
    }
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover {
        transform: scale(1.02); box-shadow: 0 8px 20px rgba(37, 99, 235, 0.6) !important;
    }
    
    .header-style {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); padding: 18px; border-radius: 15px; 
        color: #ffffff; font-weight: 800; font-size: 26px; text-align: center; 
        box-shadow: 0 10px 25px rgba(30, 58, 138, 0.5); margin-bottom: 30px; border: 1px solid #3b82f6;
    }
    
    h1, h2, h3, h4, h5 { color: #f8fafc !important; }
    p, span, div { color: #cbd5e1; }
    hr { border-color: #334155; }
    [data-testid="stDataFrame"] { background-color: #1e293b; border-radius: 10px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI DETEKSI & RENDER LOGO ---
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

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        # Logo Beranimasi Elegan
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(render_logo_html(), unsafe_allow_html=True)
            
        st.markdown('<h1 style="color:#60a5fa; text-align:center; font-weight:900; margin-bottom:0px; margin-top:15px;">SIMAKIN</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:13px; margin-bottom:30px;">System Monitoring Asset Kinarya | Reg Kalimantan</p>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        submit = st.form_submit_button("🚀 MASUK SIMAKIN BIAR YAKIN", use_container_width=True)
    
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True
            st.rerun() # Langsung rerun tanpa jeda agar terasa cepat
        else: st.error("❌ Kredensial Salah!")

if not st.session_state.logged_in:
    login_form(); st.stop() 

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.markdown(render_logo_html(width="80%"), unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #60a5fa; margin-top:20px;'>⚙️ Control SIMAKIN</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <a href="https://regkalimantan-kut.vercel.app/#sva" target="_blank" style="text-decoration: none;">
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 12px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); font-size: 13px;">
            🌍 Jelajah Ekosistem KUT
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.info("👤 **Aktif:** SIMAKINKUT")
    st.markdown("---")
    if st.button("🔄 Refresh Simakin", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Keluar Simakin", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

# --- 5. FUNGSI MENYIMPAN TEKS KE GOOGLE SHEETS ---
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

# --- 6. LOAD DATA DARI GOOGLE SHEETS DENGAN SPINNER (ANTI-DELAY) ---
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
            xls.get("Evidance foto", pd.DataFrame()) # <--- SHEET BARU UNTUK FOTO DITAMBAHKAN
        ) 
    except: 
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sedang menyinkronkan data dari satelit Google..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 7. DASHBOARD UTAMA ---
st.markdown('<div class="header-style">SYSTEM MONITORING ASSET KINARYA</div>', unsafe_allow_html=True)

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
    
    # --- 8. FORM INPUT HYBRID (Teks di Streamlit, Auto-Fill di GForm) ---
    col_chart, col_plan = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("### 📊 Statistik Kondisi Tools")
        st.info("Visualisasi tools tersedia saat data terisi penuh.") 
        
    with col_plan:
        st.markdown("### 📝 1. Form Teks Laporan & Action Plan")
        input_findings = st.text_area("✍️ Ketik deskripsi laporan perbaikan Anda di sini:", height=100)
        
        unit_mobil = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Tidak Ada')) if data_asset_select is not None else "Tidak Ada"
        unit_genset = str(data_genset_select.get('NOMER SERI MESIN', 'Tidak Ada')) if data_genset_select is not None else "Tidak Ada"
        info_gabungan = f"Mobil: {unit_mobil} | Genset: {unit_genset}"
        
        if st.button("🚀 Push Teks Laporan ke Server", use_container_width=True):
            if input_findings:
                with st.spinner("Menyimpan Teks Laporan ke Google Sheets..."):
                    if save_findings_to_sheet(str(dict_karyawan.get('NIK', 'N/A')), selected_nama, info_gabungan, input_findings):
                        st.success("✅ KEREN! Teks Laporan berhasil tersimpan permanen!")
                        time.sleep(2)
                        st.cache_data.clear()
                        st.rerun()
                    else: st.error("❌ GAGAL MENYIMPAN KE GOOGLE SHEETS! Silakan cek koneksi internet.")
            else: st.warning("⚠️ Laporan perbaikan tidak boleh kosong.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📸 2. Upload Evidence (Foto)")
        st.info("Klik tombol di bawah ini. Data Nama dan Kendaraan Anda akan terisi OTOMATIS di Google Form!")
        
        # PRE-FILLED URL GOOGLE FORM
        val_nik = str(dict_karyawan.get('NIK', '-'))
        val_nama = selected_nama
        val_nopol = unit_mobil
        val_jenis = "Asset"
        
        url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
        url_gform_dinamis = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(val_nama)}&entry.1607280297={urllib.parse.quote(val_nopol)}&entry.505680533={urllib.parse.quote(val_jenis)}"
        
        st.markdown(f"""
        <a href="{url_gform_dinamis}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 15px; border-radius: 12px; color: white; text-align: center; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); margin-bottom: 30px; transition: 0.3s;">
                🚀 UPLOAD FOTO (AUTO-FILL GOOGLE FORM)
            </div>
        </a>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide Gallery")
    
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
        "🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Riwayat Bukti Perbaikan", "📄 Fakta Integritas"
    ])
    
    # --- FUNGSI BYPASS KEAMANAN GOOGLE DRIVE ---
    def get_clean_image_url_modern(url):
        if not url: return ""
        match = re.search(r'[-\w]{25,}', url) 
        if match: 
            return f"https://drive.google.com/thumbnail?id={match.group(0)}&sz=w1000"
        return url

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
                        img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                        html = f"""
                        <div style="background: #1e293b; padding: 12px; border-radius: 12px; border: 1px solid #334155; text-align: center; margin-bottom: 10px;">
                            <img src="{img_url}" referrerpolicy="no-referrer" style="width:100%; border-radius:8px; margin-bottom:8px;">
                            <p style="font-size:12px; color:#94a3b8; font-weight:bold; margin:0;">{col_name}</p>
                        </div>
                        """
                        cols[idx % 4].markdown(html, unsafe_allow_html=True)
                        idx += 1
                if not photos_exist: st.info(empty_msg)
            else: st.info(empty_msg)

    render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Tidak ada foto kendaraan R2/R4.")
    render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Tidak ada foto unit Genset.")
    render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Tidak ada foto unit Tools.")
        
    # --- TAB RIWAYAT PERBAIKAN (SINKRONISASI TEKS & EVIDANCE FOTO) ---
    with tab_perbaikan:
        if selected_nama != "-":
            # Siapkan Data Teks dari 'Rekomendasi Perbaikan'
            matched_rek = pd.DataFrame()
            if not df_rekomendasi.empty:
                rek_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
                if rek_name_col:
                    matched_rek = df_rekomendasi[df_rekomendasi[rek_name_col].astype(str).str.strip().str.lower() == selected_nama.strip().lower()]
            
            # Siapkan Data Foto dari 'Evidance foto'
            matched_evid = pd.DataFrame()
            if not df_evidence.empty:
                # Cari baris yang mengandung nama karyawan di kolom mana pun
                matched_evid = df_evidence[df_evidence.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]

            if not matched_rek.empty or not matched_evid.empty:
                st.info("💡 Tekan tombol **Refresh Data Server** di Panel Kiri untuk memuat foto/laporan terbaru.")
                st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Laporan Service & Evidance: {selected_nama}</h4>", unsafe_allow_html=True)
                
                # Menggabungkan Data Teks (matched_rek) dan Data Foto (matched_evid) secara kronologis/berpasangan
                # Karena diambil dari 2 sheet berbeda, kita iterasi secara berpasangan dari yang terbaru
                rek_iter = list(matched_rek.iloc[::-1].iterrows()) if not matched_rek.empty else []
                evid_iter = list(matched_evid.iloc[::-1].iterrows()) if not matched_evid.empty else []
                
                # Iterasi menggunakan zip_longest agar yang satu tidak menghilangkan yang lain
                for (rek_idx, row_rek), (evid_idx, row_evid) in zip_longest(rek_iter, evid_iter, fillvalue=(None, None)):
                    
                    # 1. RENDER TEKS (Dari Sheet Rekomendasi Perbaikan)
                    if row_rek is not None:
                        teks_laporan = row_rek.get('Findings & Action Plan', '')
                        waktu_teks = row_rek.get('Timestamp', '-')
                        if pd.isna(teks_laporan) or teks_laporan.strip() == "":
                            teks_laporan = "- <i>Tidak ada keterangan teks.</i> -"
                            
                        st.markdown(f"""
                        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 6px solid #3b82f6; border-right: 1px solid #334155; margin-bottom: 5px; margin-top: 15px;">
                            <h4 style="color:#60a5fa; margin-top:0;">📅 Update Laporan: {waktu_teks}</h4>
                            <p style="color:#e2e8f0; font-size:16px; white-space: pre-wrap; margin-bottom:0;">{teks_laporan}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 2. RENDER FOTO (Dari Sheet Evidance foto - Kolom B s.d F)
                    if row_evid is not None:
                        waktu_foto = row_evid.iloc[0] if len(row_evid) > 0 else "-" # Ambil kolom pertama sebagai waktu
                        valid_photos = []
                        
                        # Ekstrak seluruh link Google Drive yang ada di baris tersebut
                        for col_val in row_evid.values:
                            val_str = str(col_val).strip()
                            if "drive.google.com" in val_str:
                                urls = val_str.split(',')
                                for u in urls:
                                    match = re.search(r'[-\w]{25,}', u)
                                    if match: valid_photos.append(match.group(0))

                        if valid_photos:
                            st.markdown(f"*(📸 Bukti Foto Evidance - Diupload pada: {waktu_foto})*")
                            cols = st.columns(min(len(valid_photos), 2)) # Tampilan Besar (Maks 2 per baris)
                            for i, file_id in enumerate(valid_photos):
                                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                                original_url = f"https://drive.google.com/file/d/{file_id}/view"
                                with cols[i % 2]: 
                                    html_img = f'<img src="{thumb_url}" referrerpolicy="no-referrer" style="width:100%; border-radius:10px; border: 1px solid #334155;">'
                                    st.markdown(html_img, unsafe_allow_html=True)
                                    st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><a href="{original_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold; display:block; margin-top:5px;">🔍 Buka Resolusi Penuh</a></div>', unsafe_allow_html=True)
                    
                    st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
            else: st.info("Belum ada riwayat laporan perbaikan untuk karyawan ini.")
        else: st.info("Silakan pilih karyawan terlebih dahulu.")

    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Dokumen Fakta Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
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
                                html_img = f'<img src="{thumb_url}" referrerpolicy="no-referrer" style="width:100%; border-radius:10px;">'
                                st.markdown(html_img, unsafe_allow_html=True)
                                st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="{original_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold; width:100%; display:inline-block;">📥 BUKA DOKUMEN</a></div>', unsafe_allow_html=True)
                    else: st.info("Tidak ada dokumen PDF/Foto yang terlampir.")
                    st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
            else: st.warning(f"Belum ada arsip form Fakta Integritas atas nama: {selected_nama}")
        else: st.info("Data sheet FAKTA INTEGRITAS masih kosong.")
