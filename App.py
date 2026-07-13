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

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SIMAKIN", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS & ANIMASI KORPORAT PREMIUM ---
st.markdown("""
<style>
    .reportview-container { background: #121212; color: #ffffff; }
    @keyframes slideUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    
    .header-style {
        background: linear-gradient(135deg, #d32f2f 0%, #9a0007 100%);
        padding: 15px; border-radius: 12px; color: white; font-weight: 800; font-size: 24px;
        text-align: center; box-shadow: 0 10px 20px rgba(211, 47, 47, 0.3); margin-bottom: 25px;
        animation: slideUp 0.8s ease-out; border: 1px solid #ff6659;
    }
    
    .login-box {
        background: rgba(30, 32, 40, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px; border-radius: 20px;
        box-shadow: 0 25px 45px rgba(0,0,0,0.5); max-width: 450px; margin: 80px auto; animation: fadeIn 1s ease-out;
    }
    .login-title { color: #ff5252; font-size: 28px; font-weight: 900; text-align: center; margin-bottom: 10px; }
    .login-subtitle { color: #b0bec5; font-size: 14px; text-align: center; margin-bottom: 35px; }
    
    .stButton>button { transition: all 0.3s ease; border-radius: 8px; font-weight: bold; }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(229, 57, 53, 0.4); border-color: #ff5252; color: #ff5252; }

    .report-card {
        background: #1e1e24; padding: 20px; border-radius: 12px; border-left: 6px solid #e53935;
        margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); animation: slideUp 0.5s ease-out;
    }
    .report-date { color: #ff5252; font-size: 14px; font-weight: bold; margin-bottom: 8px;}
    .report-text { color: #e0e0e0; font-size: 15px; line-height: 1.6; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_form():
    st.markdown("""
        <div class="login-box">
            <div class="login-title">⚡ SYSTEM PORTAL SIMAKIN</div>
            <div class="login-subtitle">SYSTEM MONITORING ASSET KINARYA | SIMAKIN Reg Kalimantan</div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("👤 Username", placeholder="Ketik username Anda...")
        pwd = st.text_input("🔑 Password", type="password", placeholder="Ketik password Anda...")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 MAU MAKIN YAKIN LOGIN SIMAKIN", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Kredensial Salah! Silakan periksa Username & Password.")

if not st.session_state.logged_in:
    login_form()
    st.stop() 

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #ff5252;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    st.info("👤 **Aktif:** SIMAKINKUT")
    st.markdown("---")
    if st.button("🔄 Refresh Data Server", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Keluar Sistem", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- 5. FUNGSI UPLOAD FOTO KE IMGBB (MULTIPART FILE UPLOAD) ---
# Diperbarui menggunakan files payload asli (anti-blokir)
def upload_image_to_imgbb(uploaded_file):
    try:
        api_key = st.secrets["imgbb_api_key"]
        url = "https://api.imgbb.com/1/upload"
        
        # Kirim sebagai file mentah, bukan base64 string
        payload = {"key": api_key}
        files = {"image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
        res = requests.post(url, data=payload, files=files)
        if res.status_code == 200:
            return res.json()["data"]["url"]
        else:
            st.error(f"Pesan Error ImgBB: {res.text}")
            return ""
    except Exception as e:
        st.error(f"Error Sistem: {e}")
        return ""

# --- 6. FUNGSI MENYIMPAN DATA KE GOOGLE SHEETS ---
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict)
        return gspread.authorize(creds)
    except: return None

def save_findings_to_sheet(nik, nama, unit_info, findings, f1, f2, f3, f4, f5):
    try:
        client = get_gspread_client()
        if client is None: return False
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        try: worksheet = sh.worksheet("Rekomendasi Perbaikan")
        except:
            worksheet = sh.add_worksheet(title="Rekomendasi Perbaikan", rows="1000", cols="10")
            worksheet.append_row(["Timestamp", "NIK", "Nama", "Unit Asset (Mobil & Genset)", "Findings & Action Plan", "Foto 1", "Foto 2", "Foto 3", "Foto 4", "Foto 5"])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, nik, nama, unit_info, findings, f1, f2, f3, f4, f5])
        return True
    except: return False

# --- 7. FUNGSI LOAD DATA UTAMA (ANTI-CACHE GOOGLE) ---
@st.cache_data(ttl=2) 
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    cb = int(time.time())
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx&cb={cb}"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), 
                xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), 
                xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), 
                xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), 
                xls.get("Rekomendasi Perbaikan", pd.DataFrame()))
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    clean_target = str(target_name).strip().lower()
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(clean_target, regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

def extract_photos_robust(data_row, df_columns):
    photos = []
    if data_row is None: return photos
    for col_name in df_columns:
        cell_val = str(data_row[col_name]).strip()
        if cell_val and cell_val not in ["nan", "-", "None"]:
            urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_val)
            for url in urls:
                final_url = url
                if "drive.google.com" in url:
                    match_d = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                    if match_d: final_url = f"https://lh3.googleusercontent.com/d/{match_d.group(1)}"
                    else:
                        match_id = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url)
                        if match_id: final_url = f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
                photos.append((str(col_name), final_url))
    return photos

# --- 8. TAMPILAN DASHBOARD UTAMA ---
st.markdown('<div class="header-style">🚀 SYSTEM MONITORING ASSET KINARYA | SIMAKIN REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    df_sdm_filtered = df_sdm.copy()
    
    st.markdown("### 🔍 Filter Pencarian Karyawan")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if 'JOB' in df_sdm.columns:
            list_job = ["SEMUA JABATAN"] + list(df_sdm['JOB'].dropna().unique())
            selected_job = st.selectbox("💼 Filter Jabatan:", list_job)
            if selected_job != "SEMUA JABATAN":
                df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]

    with col_f2:
        if 'LOKER' in df_sdm_filtered.columns:
            list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique())
            selected_loker = st.selectbox("📍 Filter Loker Kerja:", list_loker)
            if selected_loker != "SEMUA LOKER":
                df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]

    with col_f3:
        if 'NAMA' in df_sdm_filtered.columns:
            list_nama = df_sdm_filtered['NAMA'].dropna().unique()
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
        status_bagus, status_rusak = 0, 0
        for tool in tools_list:
            if data_karyawan_select is not None and tool in df_sdm.columns:
                val = str(data_karyawan_select[tool])
                if val.strip() in ["nan", "None"]: val = "-"
                tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": val})
                if any(x in val.lower() for x in ['bagus', 'ok', 'ada', '1']): status_bagus += 1
                elif any(x in val.lower() for x in ['rusak', 'tidak', 'hilang', '0']): status_rusak += 1
            else: tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": "-"})
        st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

    with col_mid:
        st.markdown("### 🚗 Data Asset R2/R4")
        asset_fields = ["JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)", "GANTI OLI (TGL TERAKHIR DIGANTI)", "PERGANTIAN BAN (TGL TERAKHIR PERGANTIAN BAN)"]
        asset_data = []
        if data_asset_select is not None:
            for field in asset_fields:
                val = str(data_asset_select[field]) if field in df_asset.columns else "-"
                if val.strip() in ["nan", "None"]: val = "-"
                asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": val})
        else: asset_data = [{"Parameter": f, "Keterangan": "-"} for f in asset_fields]
        st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("### ⚡ Data Genset")
        genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
        genset_data = []
        if data_genset_select is not None:
            for field in genset_fields:
                val = str(data_genset_select[field]) if field in df_genset.columns else "-"
                if val.strip() in ["nan", "None"]: val = "-"
                genset_data.append({"Parameter Genset": field, "Keterangan": val})
        else: genset_data = [{"Parameter": f, "Keterangan": "-"} for f in genset_fields]
        st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

    st.write("---")
    col_chart, col_plan = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("### 📊 Statistik Kondisi Tools")
        if status_bagus > 0 or status_rusak > 0:
            fig = px.pie(pd.DataFrame({"Kondisi": ["Bagus/Tersedia", "Rusak/Tidak Ada"], "Total": [status_bagus, status_rusak]}), values='Total', names='Kondisi', hole=0.4, color='Kondisi', color_discrete_map={'Bagus/Tersedia':'#00b4d8', 'Rusak/Tidak Ada':'#e53935'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Kondisi tools bernilai kosong.")
        
    with col_plan:
        st.markdown("### 📝 Form Laporan & Action Plan")
        input_findings = st.text_area("✍️ Ketik Laporan Perbaikan Unit/Kendaraan:", height=100)
        uploaded_files = st.file_uploader("📸 Upload Nota / Foto Perbaikan (Maks 5 Foto)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        
        unit_mobil = str(data_asset_select['NOPOL (PLAT NOMOR)']) if data_asset_select is not None and 'NOPOL (PLAT NOMOR)' in data_asset_select else "Tidak Ada"
        unit_genset = str(data_genset_select['NOMER SERI MESIN']) if data_genset_select is not None and 'NOMER SERI MESIN' in data_genset_select else "Tidak Ada"
        info_gabungan = f"Mobil/Motor: {unit_mobil} | Genset: {unit_genset}"
        
        if st.button("🚀 Push Update Data ke Server", use_container_width=True):
            if input_findings:
                if "imgbb_api_key" not in st.secrets:
                    st.error("API Key ImgBB belum dimasukkan di Streamlit Secrets!")
                else:
                    img_urls = ["", "", "", "", ""]
                    upload_failed = False
                    if uploaded_files:
                        with st.spinner("Mengupload foto ke Cloud ImgBB..."):
                            for idx, file in enumerate(uploaded_files[:5]):
                                url_hasil = upload_image_to_imgbb(file)
                                if url_hasil: 
                                    img_urls[idx] = url_hasil
                                else: 
                                    upload_failed = True
                    
                    if not upload_failed or not uploaded_files:
                        with st.spinner("Menyimpan teks laporan ke GSheet..."):
                            sukses = save_findings_to_sheet(
                                str(dict_karyawan.get('NIK', 'N/A')), str(dict_karyawan.get('NAMA', 'N/A')),
                                info_gabungan, input_findings,
                                img_urls[0], img_urls[1], img_urls[2], img_urls[3], img_urls[4]
                            )
                            if sukses:
                                st.success("✅ Data Laporan & Foto berhasil tersimpan!")
                                st.cache_data.clear()
                                st.rerun()
            else:
                st.warning("⚠️ Mohon isi text area laporan perbaikan terlebih dahulu.")

    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide Gallery")
    
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan = st.tabs(["🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Riwayat Bukti Perbaikan"])
    
    with tab_r2r4:
        photos_r2r4 = extract_photos_robust(data_asset_select, df_asset.columns)
        if photos_r2r4:
            cols = st.columns(4)
            for i, (lbl, url) in enumerate(photos_r2r4): 
                cols[i % 4].markdown(f'<img src="{url}" style="width:100%; border-radius:10px; margin-bottom:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><p style="text-align:center; font-size:12px;">Kolom {lbl}</p>', unsafe_allow_html=True)
        else: st.info("Tidak ada foto kendaraan R2/R4.")

    with tab_genset:
        photos_genset = extract_photos_robust(data_genset_select, df_genset.columns)
        if photos_genset:
            cols = st.columns(4)
            for i, (lbl, url) in enumerate(photos_genset): 
                cols[i % 4].markdown(f'<img src="{url}" style="width:100%; border-radius:10px; margin-bottom:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><p style="text-align:center; font-size:12px;">Kolom {lbl}</p>', unsafe_allow_html=True)
        else: st.info("Tidak ada foto unit Genset.")

    with tab_tools:
        photos_tools = extract_photos_robust(data_tools_asset_select, df_tools_asset.columns)
        if photos_tools:
            cols = st.columns(4)
            for i, (lbl, url) in enumerate(photos_tools): 
                cols[i % 4].markdown(f'<img src="{url}" style="width:100%; border-radius:10px; margin-bottom:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><p style="text-align:center; font-size:12px;">Kolom {lbl}</p>', unsafe_allow_html=True)
        else: st.info("Tidak ada foto unit Tools.")
        
    with tab_perbaikan:
        if not df_rekomendasi.empty:
            rec_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
            
            if rec_name_col:
                clean_target = selected_nama.strip().lower()
                matched_rek = df_rekomendasi[df_rekomendasi[rec_name_col].astype(str).str.strip().str.lower() == clean_target]
                
                if not matched_rek.empty:
                    st.markdown(f"<h4 style='color:#ff5252;'>Arsip Laporan Service: {selected_nama}</h4>", unsafe_allow_html=True)
                    foto_columns = [col for col in df_rekomendasi.columns if "FOTO" in str(col).upper()]
                    
                    for index, row in matched_rek.iloc[::-1].iterrows():
                        tanggal_laporan = row.get('Timestamp', '-')
                        teks_laporan = row.get('Findings & Action Plan', row.get('Findings', '-'))
                        
                        st.markdown(f"""
                        <div class="report-card">
                            <div class="report-date">🕒 Diposting pada: {tanggal_laporan}</div>
                            <div class="report-text">{teks_laporan}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        foto_cols = st.columns(max(1, len(foto_columns)))
                        col_idx = 0
                        
                        for col_name in foto_columns:
                            cell_raw_value = str(row[col_name]).strip()
                            if cell_raw_value and cell_raw_value not in ["nan", "-", "None", ""]:
                                extracted_urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_raw_value)
                                
                                if extracted_urls:
                                    valid_img_url = extracted_urls[0]
                                    html_img = f'''
                                    <img src="{valid_img_url}" style="width:100%; border-radius:8px; border: 1px solid #444; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-top:5px; margin-bottom:5px;">
                                    <div style="text-align: center; margin-bottom: 10px;">
                                        <a href="{valid_img_url}" target="_blank" style="color: #64b5f6; font-size: 13px; text-decoration: none;">🔍 Lihat Ukuran Penuh</a>
                                    </div>
                                    '''
                                    foto_cols[col_idx].markdown(html_img, unsafe_allow_html=True)
                                    col_idx += 1
                        st.write("<br><hr style='border-color: #333;'>", unsafe_allow_html=True)
                else:
                    st.info(f"Belum ada riwayat laporan perbaikan untuk karyawan ini.")
            else:
                st.error("Kolom identifikasi 'Nama' tidak ditemukan di tabel rekomendasi perbaikan.")
        else:
            st.info("Belum ada data riwayat perbaikan di dalam server.")
