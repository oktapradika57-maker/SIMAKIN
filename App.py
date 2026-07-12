import streamlit as st
import pandas as pd
import plotly.express as px
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests
import base64

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SIMAKIN", layout="wide", initial_sidebar_state="collapsed")

# --- 2. LAYAR LOGIN PREMIUM & PROFESIONAL (GLASSMORPHISM COOPERATE THEME) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_form():
    st.markdown("""
        <style>
        /* Desain Card Login */
        .login-box {
            background: #1f2026;
            border: 1px solid #33343d;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            max-width: 420px;
            margin: 80px auto 20px auto;
        }
        .login-title {
            color: #e53935;
            font-size: 24px;
            font-weight: 800;
            text-align: center;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .login-subtitle {
            color: #888894;
            font-size: 13px;
            text-align: center;
            margin-bottom: 30px;
        }
        /* Penyesuaian Style Input Kontainer */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background-color: transparent !important;
        }
        </style>
        <div class="login-box">
            <div class="login-title">🔐 SYSTEM PORTAL LOGIN</div>
            <div class="login-subtitle">Dashboard Operasional, Asset & Genset | Reg Kalimantan</div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form_fields"):
        user = st.text_input("👤 Username", placeholder="Masukkan username anda...")
        pwd = st.text_input("🔑 Password", type="password", placeholder="Masukkan password anda...")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 OTENTIKASI MASUK", width="stretch")
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Kredensial Salah! Silakan periksa kembali Username & Password.")

if not st.session_state.logged_in:
    login_form()
    st.stop() 

# --- 3. CUSTOM CSS DASHBOARD UTAMA ---
st.markdown("""
<style>
    .reportview-container { background: #1e1e24; color: white; }
    .stDataFrame { border-radius: 5px; }
    .header-style {
        background-color: #d32f2f;
        padding: 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. FUNGSI UPLOAD FOTO KE CLOUD (IMGBB) ---
def upload_image_to_imgbb(uploaded_file):
    try:
        api_key = st.secrets["imgbb_api_key"]
        base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": api_key,
            "image": base64_image
        }
        res = requests.post(url, data=payload)
        
        if res.status_code == 200:
            return res.json()["data"]["url"]
        else:
            return ""
    except Exception as e:
        return ""


# --- 5. FUNGSI MENYIMPAN DATA KE GOOGLE SHEETS ---
def get_gspread_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error("Konfigurasi Google Secrets belum diatur di Streamlit Cloud. Fitur 'Push Update Data' dimatikan sementara.")
        return None

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
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")
        return False


# --- 6. FUNGSI LOAD DATA UTAMA (OPTIMASI CACHE) ---
@st.cache_data(ttl=5) 
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        df_sdm = xls.get("SDM", pd.DataFrame())
        df_asset = xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame())
        df_genset = xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame())
        df_tools_asset = xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame())
        df_rekomendasi = xls.get("Rekomendasi Perbaikan", pd.DataFrame())
        return df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi
    except Exception as e:
        st.error(f"❌ Gagal memuat data dari Spreadsheet. Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    clean_target = str(target_name).strip().lower()
    exact_match = df[df[name_col].astype(str).str.strip().str.lower() == clean_target]
    if not exact_match.empty: return exact_match.iloc[0]
    partial_match = df[df[name_col].astype(str).str.strip().str.lower().str.contains(clean_target, regex=False, na=False)]
    if not partial_match.empty: return partial_match.iloc[0]
    return None

def extract_photos_robust(data_row, df_columns, sheet_name=""):
    photos, all_logs = [], []
    if data_row is None: return photos, all_logs

    for idx in range(len(df_columns)):
        col_name = df_columns[idx]
        cell_value = str(data_row[col_name]).strip()
        if cell_value and cell_value not in ["nan", "-", "None"]:
            urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_value)
            for url in urls:
                final_url = url
                if "drive.google.com" in url:
                    match_d = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                    if match_d: final_url = f"https://lh3.googleusercontent.com/d/{match_d.group(1)}"
                    else:
                        match_id = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url)
                        if match_id: final_url = f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
                photos.append((str(col_name), final_url))
    return photos, all_logs


# --- 7. TAMPILAN DASHBOARD ---
st.markdown('<div class="header-style">🚀 SIMAKIN | REG KALIMANTAN</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:right; margin-top:-20px; margin-bottom:20px;"><small>✅ Logged in as: <b>SIMAKINKUT</b></small></div>', unsafe_allow_html=True)

if not df_sdm.empty:
    
    # ==========================================
    # SISTEM FILTER BERTINGKAT (JABATAN -> LOKER)
    # ==========================================
    df_sdm_filtered = df_sdm.copy()
    
    # 1. Filter Job / Jabatan (Paling Atas)
    if 'JOB' in df_sdm.columns:
        list_job = ["SEMUA JOB / JABATAN"] + list(df_sdm['JOB'].dropna().unique())
        selected_job = st.selectbox("💼 Filter Berdasarkan Job / Jabatan:", list_job)
        if selected_job != "SEMUA JOB / JABATAN":
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]

    # 2. Filter Loker (Menyesuaikan dengan Job yang dipilih)
    if 'LOKER' in df_sdm_filtered.columns:
        list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique())
        selected_loker = st.selectbox("📍 Filter Berdasarkan Loker Kerja:", list_loker)
        if selected_loker != "SEMUA LOKER":
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]

    # 3. Pilihan Nama Karyawan Akhir
    if 'NAMA' in df_sdm_filtered.columns:
        list_nama = df_sdm_filtered['NAMA'].dropna().unique()
        selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", list_nama)
        
        data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
        data_asset_select = get_row_by_name(df_asset, selected_nama)
        data_genset_select = get_row_by_name(df_genset, selected_nama)
        data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)
            
        st.markdown("### 👤 Data Karyawan (Profil)")
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
        st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, width="stretch")
        st.write("---")

        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            st.markdown("### 🔧 Data Tools")
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
            st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, width="stretch")

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
            st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, width="stretch")

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
            st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, width="stretch")

        st.write("---")
        col_chart, col_plan = st.columns([1.5, 2])
        
        with col_chart:
            st.markdown("### 📊 Ringkasan Kondisi Tools")
            if status_bagus > 0 or status_rusak > 0:
                fig = px.pie(pd.DataFrame({"Kondisi": ["Bagus/Tersedia", "Rusak/Tidak Ada"], "Total": [status_bagus, status_rusak]}), values='Total', names='Kondisi', hole=0.4, color='Kondisi', color_discrete_map={'Bagus/Tersedia':'#00b4d8', 'Rusak/Tidak Ada':'#d62828'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, width="stretch")
            else: st.info("Kondisi tools bernilai kosong.")
            
        with col_plan:
            st.markdown("### 📝 Findings & Action Plan")
            input_findings = st.text_area("Input Laporan/Rekomendasi perbaikan:", height=100)
            uploaded_files = st.file_uploader("📸 Upload Bukti Nota/Service (Maksimal 5 Foto, .JPG/.PNG)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
            
            unit_mobil = str(data_asset_select['NOPOL (PLAT NOMOR)']) if data_asset_select is not None and 'NOPOL (PLAT NOMOR)' in data_asset_select else "Tidak Ada"
            unit_genset = str(data_genset_select['NOMER SERI MESIN']) if data_genset_select is not None and 'NOMER SERI MESIN' in data_genset_select else "Tidak Ada"
            info_gabungan = f"Mobil/Motor: {unit_mobil} | Genset: {unit_genset}"
            
            if st.button("Push Update Data"):
                if input_findings:
                    if "imgbb_api_key" not in st.secrets:
                        st.error("API Key ImgBB belum dimasukkan di Streamlit Secrets!")
                    else:
                        img_urls = ["", "", "", "", ""]
                        upload_failed = False
                        
                        if uploaded_files:
                            if len(uploaded_files) > 5:
                                st.warning("Hanya 5 foto pertama yang akan disimpan!")
                            
                            with st.spinner("Mengupload foto ke server cloud..."):
                                for idx, file in enumerate(uploaded_files[:5]):
                                    url_hasil = upload_image_to_imgbb(file)
                                    if url_hasil:
                                        img_urls[idx] = url_hasil
                                    else:
                                        upload_failed = True
                                        st.error(f"❌ Foto ke-{idx+1} gagal diupload. Periksa kuota/API Key ImgBB.")
                        
                        with st.spinner("Menyimpan teks laporan ke Spreadsheet..."):
                            sukses = save_findings_to_sheet(
                                str(dict_karyawan.get('NIK', 'N/A')),
                                str(dict_karyawan.get('NAMA', 'N/A')),
                                info_gabungan,
                                input_findings,
                                img_urls[0], img_urls[1], img_urls[2], img_urls[3], img_urls[4]
                            )
                            if sukses:
                                if upload_failed:
                                    st.warning("Data tersimpan, namun ada kegagalan upload foto.")
                                else:
                                    st.success("Data Laporan & Foto berhasil tersimpan!")
                                st.rerun()
                else:
                    st.warning("Mohon isi text area laporan perbaikan sebelum melakukan Push Update.")

        st.write("---")
        st.markdown("### 📸 Evidence & Documented Slide Gallery")
        
        tab_r2r4, tab_genset, tab_tools, tab_perbaikan = st.tabs(["🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Bukti Perbaikan"])
        
        with tab_r2r4:
            photos_r2r4, _ = extract_photos_robust(data_asset_select, df_asset.columns, sheet_name="Asset R2/R4")
            if photos_r2r4:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_r2r4): cols[i % 4].image(url, caption=f"Kolom {lbl}", width="stretch")
            else: st.info("Tidak ada foto kendaraan R2/R4.")

        with tab_genset:
            photos_genset, _ = extract_photos_robust(data_genset_select, df_genset.columns, sheet_name="Genset")
            if photos_genset:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_genset): cols[i % 4].image(url, caption=f"Kolom: {lbl}", width="stretch")
            else: st.info("Tidak ada foto unit Genset.")

        with tab_tools:
            photos_tools, _ = extract_photos_robust(data_tools_asset_select, df_tools_asset.columns, sheet_name="Tools")
            if photos_tools:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_tools): cols[i % 4].image(url, caption=f"Kolom: {lbl}", width="stretch")
            else: st.info("Tidak ada foto unit Tools.")
            
        # ==========================================
        # TAB BUKTI PERBAIKAN DENGAN SMART REGEX DETECTOR (ANTI-BLANK FOTO)
        # ==========================================
        with tab_perbaikan:
            if not df_rekomendasi.empty:
                rec_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
                
                if rec_name_col:
                    clean_target = selected_nama.strip().lower()
                    matched_rek = df_rekomendasi[df_rekomendasi[rec_name_col].astype(str).str.strip().str.lower() == clean_target]
                    
                    if not matched_rek.empty:
                        st.markdown(f"**Riwayat Bukti Perbaikan untuk: {selected_nama}**")
                        foto_columns = [col for col in df_rekomendasi.columns if "FOTO" in str(col).upper()]
                        
                        for index, row in matched_rek.iterrows():
                            st.write(f"📅 **Tanggal:** {row.get('Timestamp', '-')}")
                            st.write(f"📝 **Laporan:** {row.get('Findings & Action Plan', row.get('Findings', '-'))}")
                            
                            foto_cols = st.columns(max(1, len(foto_columns)))
                            col_idx = 0
                            
                            for col_name in foto_columns:
                                cell_raw_value = str(row[col_name]).strip()
                                
                                if cell_raw_value and cell_raw_value not in ["nan", "-", "None", ""]:
                                    # EKSTRAKSI DENGAN REGEX: Bersihkan link dari spasi/karakter rusak tersembunyi
                                    extracted_urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_raw_value)
                                    
                                    # KONDISI 1: Jika lolos deteksi Regex sebagai Link URL Fisik Gambar
                                    if extracted_urls:
                                        valid_img_url = extracted_urls[0]
                                        foto_cols[col_idx].image(valid_img_url, caption=col_name, width="stretch")
                                        col_idx += 1
                                        
                                    # KONDISI 2: Jika terdeteksi sebagai sisa teks Base64 (/9j/...)
                                    elif cell_raw_value.startswith("/9j/") or len(cell_raw_value) > 50:
                                        try:
                                            clean_b64 = cell_raw_value.split(",")[-1] if "," in cell_raw_value else cell_raw_value
                                            missing_padding = len(clean_b64) % 4
                                            if missing_padding:
                                                clean_b64 += '=' * (4 - missing_padding)
                                            
                                            img_bytes = base64.b64decode(clean_b64)
                                            foto_cols[col_idx].image(img_bytes, caption=col_name, width="stretch")
                                            col_idx += 1
                                        except:
                                            pass
                            st.divider()
                    else:
                        st.info(f"Belum ada riwayat laporan perbaikan untuk karyawan ini.")
                else:
                    st.error("Kolom identifikasi 'Nama' tidak ditemukan di tabel rekomendasi perbaikan.")
            else:
                st.info("Belum ada data riwayat perbaikan.")
