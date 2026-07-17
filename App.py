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
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS (Modern Premium Dark Mode + 3D Smooth Animations) ---
st.markdown("""
<style>
    /* Animasi Transisi Halus */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Background Utama App */
    .stApp { 
        background-color: #0b0f19; 
        color: #e2e8f0; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Efek Fade In ke seluruh blok container utama saat filter diganti */
    .main .block-container {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Box Login 3D Glassmorphism Premium */
    div[data-testid="stForm"] {
        background: rgba(26, 32, 53, 0.7) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        padding: 40px !important;
        border-radius: 20px !important;
        box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.6), inset 0px 0px 20px rgba(59, 130, 246, 0.1) !important;
        max-width: 450px !important;
        margin: 50px auto !important;
        transform: perspective(1000px) rotateX(2deg);
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    div[data-testid="stForm"]:hover {
        transform: perspective(1000px) rotateX(0deg) translateY(-5px);
        box-shadow: 0px 25px 45px rgba(59, 130, 246, 0.2), inset 0px 0px 30px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* Input Form (Jelas dan Terbaca) */
    div[data-testid="stTextInput"] label { color: #60a5fa !important; font-weight: bold !important; letter-spacing: 1px; }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select {
        border-radius: 10px !important; 
        border: 1px solid #334155 !important;
        background-color: #1e293b !important; 
        color: #ffffff !important; 
        font-size: 15px !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus { 
        border-color: #3b82f6 !important; 
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.4) !important; 
    }
    
    /* Tombol Utama (Gradient Blue Elegan) */
    button[kind="primaryFormSubmit"], .stButton>button { 
        background: linear-gradient(135deg, #2563eb, #0ea5e9) !important; 
        border: none !important; 
        border-radius: 10px !important; 
        color: white !important; 
        font-size: 15px !important; 
        font-weight: 700 !important; 
        padding: 10px 0 !important; 
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; 
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.4) !important; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
    }
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover { 
        transform: translateY(-3px) scale(1.02) !important; 
        box-shadow: 0 12px 25px rgba(37, 99, 235, 0.6) !important;
    }
    
    /* Header Utama */
    .header-style {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); 
        padding: 18px; 
        border-radius: 15px; 
        color: #ffffff; 
        font-weight: 800; 
        font-size: 26px; 
        text-align: center; 
        box-shadow: 0 10px 25px rgba(30, 58, 138, 0.5); 
        margin-bottom: 30px; 
        border: 1px solid #3b82f6;
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Warna Teks Global agar kontras */
    h1, h2, h3, h4, h5 { color: #f8fafc !important; }
    p, span, div { color: #cbd5e1; }
    hr { border-color: #334155; }
    
    /* Custom Styling untuk DataFrame */
    [data-testid="stDataFrame"] { background-color: #1e293b; border-radius: 10px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown('<h1 style="color:#60a5fa; text-align:center; font-weight:900; letter-spacing:2px; margin-bottom:0px;">⚡ SYSTEM PORTAL</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8; text-align:center; font-size:13px; margin-bottom:30px; letter-spacing:1px; text-transform:uppercase;">Operational, Asset & Genset | Reg Kalimantan</p>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME", placeholder="Ketik username Anda...")
        pwd = st.text_input("🔑 PASSWORD", type="password", placeholder="Ketik password Anda...")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True)
    
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Kredensial Salah! Silakan periksa Username & Password.")

if not st.session_state.logged_in:
    login_form()
    st.stop() 

# --- 4. SIDEBAR MENU & FOOTER ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    st.info("👤 **Aktif:** SIMAKINKUT")
    st.markdown("---")
    if st.button("🔄 Refresh Data Server", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Keluar Sistem", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("""
    <style>
        .footer-sidebar {
            text-align: center; font-size: 11px; color: #64748b; letter-spacing: 1.5px; margin-top: 30px; transition: all 0.3s ease;
        }
        .footer-sidebar:hover { color: #3b82f6; text-shadow: 0 0 8px rgba(59, 130, 246, 0.5); cursor: default; }
    </style>
    <div class="footer-sidebar">
        ⚡ DEVELOPED BY OKTA PRADIKA<br>
        © 2026 SYSTEM OPERATIONS
    </div>
    """, unsafe_allow_html=True)

# --- 5. FUNGSI UPLOAD MENGGUNAKAN GOOGLE APPS SCRIPT (URL BARU ANDA) ---
def upload_image_to_gdrive(uploaded_file):
    # INI ADALAH URL TERBARU YANG ANDA BERIKAN
    GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycby5I3Yz8xFqc9ZmhS8EPj6UCB9iBeEqeuil_TgAf4KkQCsFVl4HcGUVzlGwIKcEzdQB/exec"
    
    try:
        # Kompres gambar agar lebih cepat diupload dan tidak ditolak server
        img = Image.open(uploaded_file).convert('RGB')
        img.thumbnail((600, 600)) 
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        b64_string = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        payload = {
            "filename": f"Bukti_{int(time.time())}.jpg", 
            "base64": b64_string
        }
        
        # Kirim ke Apps Script (Time out diperpanjang menjadi 60 detik)
        response = requests.post(GAS_WEB_APP_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("url") # Berhasil mengembalikan URL Foto
            else:
                return f"ERROR: {result.get('message')}"
        else:
            return f"ERROR_HTTP: {response.status_code}"
    except Exception as e:
        return f"ERROR_NETWORK: {e}"

# --- 6. FUNGSI MENYIMPAN DATA KE GOOGLE SHEETS ---
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        return gspread.authorize(creds)
    except: return None

def save_findings_to_sheet(nik, nama, unit_info, findings, f1, f2, f3, f4, f5):
    try:
        client = get_gspread_client()
        if client is None: return False
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        try: 
            worksheet = sh.worksheet("Rekomendasi Perbaikan")
        except:
            worksheet = sh.add_worksheet(title="Rekomendasi Perbaikan", rows="1000", cols="10")
            worksheet.append_row(["Timestamp", "NIK", "Nama", "Unit Asset (Mobil & Genset)", "Findings & Action Plan", "Foto 1", "Foto 2", "Foto 3", "Foto 4", "Foto 5"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, nik, nama, unit_info, findings, f1, f2, f3, f4, f5])
        return True
    except: return False

# --- 7. FUNGSI LOAD DATA UTAMA ---
@st.cache_data(ttl=600) 
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), 
                xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), 
                xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), 
                xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), 
                xls.get("Rekomendasi Perbaikan", pd.DataFrame()),
                xls.get("FAKTA INTERITAR", pd.DataFrame())) 
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    clean_target = str(target_name).strip().lower()
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(clean_target, regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 8. TAMPILAN DASHBOARD UTAMA ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET | REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    df_sdm_filtered = df_sdm.copy()
    
    data_karyawan_select = None; data_asset_select = None; data_genset_select = None; data_tools_asset_select = None
    selected_nama = "-"
    
    st.markdown("### 🔍 Filter Pencarian Karyawan")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4) 
    
    with col_f1:
        if 'JOB' in df_sdm.columns:
            list_job = ["SEMUA JABATAN"] + list(df_sdm['JOB'].dropna().unique())
            selected_job = st.selectbox("💼 Filter Jabatan:", list_job)
            if selected_job != "SEMUA JABATAN": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]

    with col_f2:
        if 'LOKER' in df_sdm_filtered.columns:
            list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique())
            selected_loker = st.selectbox("📍 Filter Loker Kerja:", list_loker)
            if selected_loker != "SEMUA LOKER": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]

    with col_f3:
        if not df_asset.empty and 'NOPOL (PLAT NOMOR)' in df_asset.columns:
            list_nopol = ["SEMUA NOPOL"] + list(df_asset['NOPOL (PLAT NOMOR)'].dropna().unique())
            selected_nopol = st.selectbox("🚗 Filter Plat (NOPOL):", list_nopol)
        else:
            selected_nopol = "SEMUA NOPOL"
            
    if selected_nopol != "SEMUA NOPOL":
        asset_filtered = df_asset[df_asset['NOPOL (PLAT NOMOR)'] == selected_nopol]
        nama_col_asset = next((col for col in asset_filtered.columns if "NAMA" in str(col).upper()), None)
        if nama_col_asset:
            valid_names = asset_filtered[nama_col_asset].astype(str).str.strip().str.lower().unique()
            nama_col_sdm = next((col for col in df_sdm_filtered.columns if "NAMA" in str(col).upper()), None)
            if nama_col_sdm:
                df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[nama_col_sdm].astype(str).str.strip().str.lower().isin(valid_names)]

    with col_f4:
        if 'NAMA' in df_sdm_filtered.columns:
            list_nama = df_sdm_filtered['NAMA'].dropna().unique()
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
        tools_list = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", "Type Genset", "KVA Genset", "Status Genset", "TANG AMPERE AC / DC", "GROUNDING TESTER", "Aircond rectification tools for dismantle/ install such as piping tools", "Flaring set", "conduits", "pipe benders", "sealant tool", "Steamer Aircond", "Manifold", "freon", "cutting pipe etc", "Full Body Harness", "Double Hooked Lanyard with absorber", "Work Positioning Lanyard", "Sefty Vest", "Sefty shoes", "Safety Civil Gloves", "Safety Electrical Glove", "Safety Climbing Glove", "Rain coat", "Test Pen", "Safety Climbing Helmet", "Safety Ground Helmet", "Safety Glass", "Safety Banner", "Barricade Line", "Safety Boots (For Rainy session/ Flood )", "First aid box", "TOOLS BOX with standard tool set", "portable small Vacuum cleaner", "broom", "canebo", "tarpaulin", "lamp", "Battery Tester", "Mesin Las portable", "Gerinda", "Bor listrik", "KUNCI SABUK (Rantai) FILTER", "VACUM CLEANER", "JET PUMP PEMBERSIH AC", "Mesin Pemotong rumput", "TANG CRIMPING", "LAN TESTER", "TANGGA hidrolic 10 METER", "KOMPAS", "METERAN 50m", "METERAN 100m", "ANGLE METER (Water pass)", "OPTICAL POWER METER", "INFRARED THERMOMETER", "TAMBANG", "KATROL", "KUNCI PASS 32", "Cable & Connector Console", "Power bank Handphone", "Thermal Imager", "Thermal Logger", "Optical splicer single core", "OTDR", "Laptop", "Smartphone", "Printer label", "Genset + Cable Genseat Minimum 100m + COS legrand 3 phase", "Light Source (optical)", "obeng cadik", "tang buaya", "tang kombinasi", "tang potong", "kunci pass set", "kunci L set", "cutter", "Krone LSA", "Krone Wrapping Gun", "Fire Estinguisher portable", "OBD (Car GPS)", "Diagonal Plier", "Wire Stripper", "Electrical Insulation (Solasi Kabel)", "Cable Ties 5mm", "Iron Saw", "Screw stuck drat puller", "Kolor KUT Paste (Fuel Quality tester)", "Tent/ Tarpaulin (Including Lamp)", "Vehicle/ Motorcycle", "Climbing Supporting Tools (Rope, Katrol 7 Etc)", "Feeder Installation Kit", "Portable Ladder", "Car Tracker"]
        tools_data = []
        for tool in tools_list:
            if data_karyawan_select is not None and tool in df_sdm.columns:
                val = str(data_karyawan_select[tool])
                tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": val if val.strip() not in ["nan", "None"] else "-"})
            else: tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": "-"})
        st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

    with col_mid:
        st.markdown("### 🚗 Data Asset R2/R4")
        asset_fields = ["JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)", "GANTI OLI (TGL TERAKHIR DIGANTI)", "PERGANTIAN BAN (TGL TERAKHIR PERGANTIAN BAN)"]
        asset_data = []
        if data_asset_select is not None:
            for field in asset_fields:
                val = str(data_asset_select[field]) if field in df_asset.columns else "-"
                asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": val if val.strip() not in ["nan", "None"] else "-"})
        else: asset_data = [{"Parameter": f, "Keterangan": "-"} for f in asset_fields]
        st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("### ⚡ Data Genset")
        genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
        genset_data = []
        if data_genset_select is not None:
            for field in genset_fields:
                val = str(data_genset_select[field]) if field in df_genset.columns else "-"
                genset_data.append({"Parameter Genset": field, "Keterangan": val if val.strip() not in ["nan", "None"] else "-"})
        else: genset_data = [{"Parameter": f, "Keterangan": "-"} for f in genset_fields]
        st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

    st.write("---")
    col_chart, col_plan = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("### 📊 Statistik Kondisi Tools")
        st.info("Visualisasi tools tersedia saat data terisi penuh.") 
        
    with col_plan:
        st.markdown("### 📝 Form Laporan & Action Plan")
        input_findings = st.text_area("✍️ Ketik Laporan Perbaikan Unit/Kendaraan:", height=100)
        uploaded_files = st.file_uploader("📸 Upload Nota / Foto Perbaikan (Maks 5 Foto)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        
        unit_mobil = str(data_asset_select['NOPOL (PLAT NOMOR)']) if data_asset_select is not None and 'NOPOL (PLAT NOMOR)' in data_asset_select else "Tidak Ada"
        unit_genset = str(data_genset_select['NOMER SERI MESIN']) if data_genset_select is not None and 'NOMER SERI MESIN' in data_genset_select else "Tidak Ada"
        info_gabungan = f"Mobil/Motor: {unit_mobil} | Genset: {unit_genset}"
        
        if st.button("🚀 Push Update Data ke Server", use_container_width=True):
            if input_findings:
                img_urls = ["", "", "", "", ""]
                ada_foto_gagal = False
                pesan_gagal = ""
                
                if uploaded_files:
                    with st.spinner("🚀 Sedang mengupload foto ke Drive Anda... (Mohon tunggu beberapa saat)"):
                        for idx, file in enumerate(uploaded_files[:5]):
                            url_hasil = upload_image_to_gdrive(file)
                            if url_hasil and not url_hasil.startswith("ERROR"): 
                                img_urls[idx] = url_hasil
                            else: 
                                ada_foto_gagal = True
                                pesan_gagal = url_hasil if url_hasil else "Gagal tidak diketahui"
                                st.error(f"Peringatan Upload Foto ke-{idx+1}: {pesan_gagal}")
                
                with st.spinner("Menyimpan Laporan Teks ke Spreadsheet..."):
                    sukses_simpan = save_findings_to_sheet(
                        str(dict_karyawan.get('NIK', 'N/A')), str(dict_karyawan.get('NAMA', 'N/A')),
                        info_gabungan, input_findings, img_urls[0], img_urls[1], img_urls[2], img_urls[3], img_urls[4]
                    )
                    
                    if sukses_simpan:
                        if ada_foto_gagal:
                            st.warning("⚠️ Laporan Teks Berhasil Masuk! Tetapi foto gagal masuk, silakan cek pengaturan Apps Script Anda.")
                        else:
                            st.success("✅ KEREN! Laporan & Link Foto berhasil tersimpan permanen!")
                        
                        time.sleep(2)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ GAGAL MENYIMPAN KE GOOGLE SHEETS! Silakan cek koneksi.")
            else:
                st.warning("⚠️ Laporan perbaikan tidak boleh kosong.")

    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide Gallery")
    
    # -------------------------------------------------------------------------
    # TAB GALLERY (5 TAB TERMASUK FAKTA INTEGRITAS)
    # -------------------------------------------------------------------------
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
        "🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Riwayat Bukti Perbaikan", "📄 Fakta Integritas"
    ])
    
    def get_clean_image_url_legacy(url):
        match = re.search(r'([-\w]{25,})', url) 
        if match and ("drive.google" in url or "docs.google" in url):
            return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w800"
        return url

    def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
        with tab_context:
            if data_row is not None:
                photos_exist = False
                cols = st.columns(4)
                idx = 0
                for col_name in df_columns:
                    cell_val = str(data_row[col_name]).strip()
                    if cell_val and cell_val not in ["nan", "-", "None"]:
                        urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_val)
                        if urls:
                            photos_exist = True
                            img_url = get_clean_image_url_legacy(urls[0])
                            html = f"""
                            <div style="background: #1e293b; padding: 12px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.3); text-align: center; margin-bottom: 10px; transition: transform 0.3s;">
                                <img src="{img_url}" style="width:100%; border-radius:8px; margin-bottom:8px;">
                                <p style="font-size:12px; color:#94a3b8; font-weight:bold; margin:0;">Kolom {col_name}</p>
                            </div>
                            """
                            cols[idx % 4].markdown(html, unsafe_allow_html=True)
                            idx += 1
                if not photos_exist: st.info(empty_msg)
            else: st.info(empty_msg)

    render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Tidak ada foto kendaraan R2/R4.")
    render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Tidak ada foto unit Genset.")
    render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Tidak ada foto unit Tools.")
        
    
    # --- TAB 4: RIWAYAT BUKTI PERBAIKAN ---
    with tab_perbaikan:
        if not df_rekomendasi.empty and selected_nama != "-":
            rec_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
            if rec_name_col:
                clean_target = selected_nama.strip().lower()
                matched_rek = df_rekomendasi[df_rekomendasi[rec_name_col].astype(str).str.strip().str.lower() == clean_target]
                
                if not matched_rek.empty:
                    st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Laporan Service: {selected_nama}</h4>", unsafe_allow_html=True)
                    
                    foto_columns = [col for col in df_rekomendasi.columns if "FOTO" in str(col).upper()]
                    
                    for index, row in matched_rek.iloc[::-1].iterrows():
                        tanggal_laporan = row.get('Timestamp', '-')
                        teks_laporan = row.get('Findings & Action Plan', row.get('Findings', '-'))
                        
                        st.markdown(f"""
                        <div style="background: #1e293b; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; border-right: 1px solid #334155; border-top: 1px solid #334155; border-bottom: 1px solid #334155; margin-bottom: 20px; margin-top: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                            <h5 style="color:#60a5fa; margin-top:0;">📅 Update Service: {tanggal_laporan}</h5>
                            <p style="color:#e2e8f0; font-size:14px; white-space: pre-wrap; margin-bottom:0; line-height:1.6;">{teks_laporan}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        valid_photos = []
                        for col_name in foto_columns:
                            val = str(row[col_name]).strip()
                            if val and val not in ["nan", "-", "None", ""]:
                                valid_photos.append(val)
                        
                        if valid_photos:
                            cols = st.columns(len(valid_photos))
                            for i, raw_url in enumerate(valid_photos):
                                match = re.search(r'([-\w]{25,})', raw_url)
                                if match and ("drive.google" in raw_url or "docs.google" in raw_url):
                                    file_id = match.group(1)
                                    safe_image_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                                    
                                    with cols[i]:
                                        st.image(safe_image_url, use_container_width=True)
                                        st.markdown(f'<div style="text-align:center;"><a href="{raw_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: bold; display:inline-block; margin-top:5px; box-shadow: 0 4px 10px rgba(37,99,235,0.3);">🔍 Buka Foto Asli</a></div>', unsafe_allow_html=True)
                                else:
                                    if "http" in raw_url:
                                        with cols[i]:
                                            st.image(raw_url, use_container_width=True)
                                            
                        st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
                else: st.info(f"Belum ada riwayat laporan perbaikan untuk karyawan ini.")
            else: st.error("Kolom 'Nama' tidak ditemukan di tabel rekomendasi perbaikan.")
        else: st.info("Belum ada data riwayat perbaikan yang sesuai.")

    # --- TAB 5: FAKTA INTEGRITAS DARI GOOGLE FORM ---
    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Dokumen Fakta Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
                
                for index, row in matched_fakta.iloc[::-1].iterrows():
                    tanggal = row.get('Timestamp', row.get('TANGGAL', 'Tanggal Tidak Diketahui'))
                    st.markdown(f"**📅 Diupload pada: {tanggal}**")
                    
                    valid_files = []
                    for col_name in matched_fakta.columns:
                        val = str(row[col_name]).strip()
                        if "drive.google.com" in val:
                            urls = re.findall(r'(https?://[^\s,]+)', val)
                            for u in urls:
                                if u not in valid_files:
                                    valid_files.append(u)
                                    
                    if valid_files:
                        cols = st.columns(len(valid_files))
                        for i, raw_url in enumerate(valid_files):
                            match = re.search(r'([-\w]{25,})', raw_url)
                            with cols[i]:
                                if match:
                                    file_id = match.group(1)
                                    safe_image_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                                    try:
                                        st.image(safe_image_url, use_container_width=True)
                                    except:
                                        st.info("Dokumen PDF (Klik tombol di bawah)")
                                        
                                    st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="{raw_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold; width:100%; display:inline-block; box-shadow: 0 4px 10px rgba(37,99,235,0.3);">📥 BUKA DOKUMEN / FOTO</a></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="{raw_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold; width:100%; display:inline-block; box-shadow: 0 4px 10px rgba(37,99,235,0.3);">📥 BUKA LINK FILE</a></div>', unsafe_allow_html=True)
                    else:
                        st.info("Tidak ada dokumen PDF/Foto yang terlampir pada laporan ini.")
                    st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
            else:
                st.warning(f"Belum ada arsip form Fakta Integritas atas nama: {selected_nama}")
        else:
            st.info("Data sheet FAKTA INTERITAR masih kosong atau belum dimuat.")
