import streamlit as st
import pandas as pd
import re
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS (Premium Dark Mode) ---
st.markdown("""
<style>
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .main .block-container { animation: fadeIn 0.6s ease-out; }
    
    div[data-testid="stForm"] {
        background: rgba(26, 32, 53, 0.7) !important; backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important; padding: 40px !important;
        border-radius: 20px !important; box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.6) !important;
        max-width: 450px !important; margin: 50px auto !important;
    }
    
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label { color: #60a5fa !important; font-weight: bold !important; letter-spacing: 1px; }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select {
        border-radius: 10px !important; border: 1px solid #334155 !important;
        background-color: #1e293b !important; color: #ffffff !important; 
    }
    
    button[kind="primaryFormSubmit"] { 
        background: linear-gradient(135deg, #2563eb, #0ea5e9) !important; border: none !important; 
        border-radius: 10px !important; color: white !important; font-weight: 700 !important; 
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

# --- FUNGSI DETEKSI LOGO OTOMATIS ---
def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    logo_2 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp"
    if os.path.exists(logo_1): return logo_1
    elif os.path.exists(logo_2): return logo_2
    return None

# --- 3. SISTEM LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        logo_path = get_logo_path()
        if logo_path:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2: st.image(logo_path, use_container_width=True)
            
        st.markdown('<h1 style="color:#60a5fa; text-align:center; font-weight:900; margin-bottom:0px; margin-top:10px;">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:13px; margin-bottom:30px;">System Monitoring Asset Kinarya | Reg Kalimantan</p>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        submit = st.form_submit_button("🚀 MASUK SIMAKIN", use_container_width=True)
    if submit:
        if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF":
            st.session_state.logged_in = True; st.rerun()
        else: st.error("❌ Kredensial Salah!")

if not st.session_state.logged_in:
    login_form(); st.stop() 

# --- 4. SIDEBAR MENU ---
with st.sidebar:
    logo_path = get_logo_path()
    if logo_path: st.image(logo_path, use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #60a5fa; margin-top:20px;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <a href="https://regkalimantan-kut.vercel.app/#sva" target="_blank" style="text-decoration: none;">
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 12px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); font-size: 13px;">
            🌍 Jelajah lebih jauh lagi
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.info("👤 **Aktif:** SIMAKINKUT")
    if st.button("🔄 Refresh Data Server", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Keluar Sistem", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()
    st.markdown("""<div style="text-align: center; font-size: 11px; color: #64748b; margin-top: 30px;">⚡ DEVELOPED BY OKTA PRADIKA<br>© 2026 SYSTEM OPERATIONS</div>""", unsafe_allow_html=True)

# --- 5. LOAD DATA DARI GOOGLE SHEETS ---
@st.cache_data(ttl=60) # Auto refresh setiap 60 detik
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta = load_all_data()

def get_row_by_name(df, target_name):
    if df.empty: return None
    name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
    if not name_col: return None
    matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
    return matched.iloc[0] if not matched.empty else None

# --- 6. DASHBOARD UTAMA ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET</div>', unsafe_allow_html=True)

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
        tools_list = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", "Type Genset", "KVA Genset", "Status Genset", "TANG AMPERE AC / DC", "GROUNDING TESTER", "Aircond rectification tools for dismantle/ install such as piping tools", "Flaring set", "conduits", "pipe benders", "sealant tool", "Steamer Aircond", "Manifold", "freon", "cutting pipe etc", "Full Body Harness", "Double Hooked Lanyard with absorber", "Work Positioning Lanyard", "Sefty Vest", "Sefty shoes", "Safety Civil Gloves", "Safety Electrical Glove", "Safety Climbing Glove", "Rain coat", "Test Pen", "Safety Climbing Helmet", "Safety Ground Helmet", "Safety Glass", "Safety Banner", "Barricade Line", "Safety Boots (For Rainy session/ Flood )", "First aid box", "TOOLS BOX with standard tool set", "portable small Vacuum cleaner", "broom", "canebo", "tarpaulin", "lamp", "Battery Tester", "Mesin Las portable", "Gerinda", "Bor listrik", "KUNCI SABUK (Rantai) FILTER", "VACUM CLEANER", "JET PUMP PEMBERSIH AC", "Mesin Pemotong rumput", "TANG CRIMPING", "LAN TESTER", "TANGGA hidrolic 10 METER", "KOMPAS", "METERAN 50m", "METERAN 100m", "ANGLE METER (Water pass)", "OPTICAL POWER METER", "INFRARED THERMOMETER", "TAMBANG", "KATROL", "KUNCI PASS 32", "Cable & Connector Console", "Power bank Handphone", "Thermal Imager", "Thermal Logger", "Optical splicer single core", "OTDR", "Laptop", "Smartphone", "Printer label", "Genset + Cable Genseat Minimum 100m + COS legrand 3 phase", "Light Source (optical)", "obeng cadik", "tang buaya", "tang kombinasi", "tang potong", "kunci pass set", "kunci L set", "cutter", "Krone LSA", "Krone Wrapping Gun", "Fire Estinguisher portable", "OBD (Car GPS)", "Diagonal Plier", "Wire Stripper", "Electrical Insulation (Solasi Kabel)", "Cable Ties 5mm", "Iron Saw", "Screw stuck drat puller", "Kolor KUT Paste (Fuel Quality tester)", "Tent/ Tarpaulin (Including Lamp)", "Vehicle/ Motorcycle", "Climbing Supporting Tools (Rope, Katrol 7 Etc)", "Feeder Installation Kit", "Portable Ladder", "Car Tracker"]
        tools_data = [{"Nama Tools": t, "Kondisi / Jumlah": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list]
        st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

    with col_mid:
        st.markdown("### 🚗 Data Asset R2/R4")
        asset_fields = ["JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)", "GANTI OLI (TGL TERAKHIR DIGANTI)", "PERGANTIAN BAN (TGL TERAKHIR PERGANTIAN BAN)"]
        asset_data = [{"Parameter Asset R2/R4": f, "Keterangan": str(data_asset_select[f]) if data_asset_select is not None and f in df_asset.columns and str(data_asset_select[f]).strip() not in ["nan", "None"] else "-"} for f in asset_fields]
        st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

    with col_right:
        st.markdown("### ⚡ Data Genset")
        genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
        genset_data = [{"Parameter Genset": f, "Keterangan": str(data_genset_select[f]) if data_genset_select is not None and f in df_genset.columns and str(data_genset_select[f]).strip() not in ["nan", "None"] else "-"} for f in genset_fields]
        st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

    st.write("---")
    
    # --- 7. TOMBOL INPUT VIA GOOGLE FORM ---
    st.markdown("### 📝 Form Laporan & Action Plan")
    st.info("💡 Agar Teks Laporan & Foto Bukti terhubung sempurna di baris yang sama tanpa error, silakan isi laporan Anda melalui form resmi di bawah ini.")
    
    url_gform = "https://forms.gle/dTU9GNtWZcuKqhTv8"
    st.markdown(f"""
    <a href="{url_gform}" target="_blank" style="text-decoration:none;">
        <div style="background: linear-gradient(135deg, #2563eb, #0ea5e9); padding: 20px; border-radius: 15px; color: white; text-align: center; font-weight: bold; font-size: 18px; box-shadow: 0 4px 15px rgba(37,99,235,0.4); margin-bottom: 30px; transition: 0.3s;">
            🚀 KLIK DI SINI UNTUK MENGISI LAPORAN & UPLOAD EVIDANCE
        </div>
    </a>
    """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide Gallery")
    
    tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
        "🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools", "🛠️ Riwayat Bukti Perbaikan", "📄 Fakta Integritas"
    ])

    def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
        with tab_context:
            if data_row is not None:
                photos_exist = False
                cols = st.columns(4)
                idx = 0
                for col_name in df_columns:
                    cell_val = str(data_row[col_name]).strip()
                    if "drive.google.com" in cell_val:
                        match = re.search(r'[-\w]{25,}', cell_val) 
                        if match:
                            photos_exist = True
                            img_url = f"https://drive.google.com/thumbnail?id={match.group(0)}&sz=w1000"
                            html = f"""
                            <div style="background: #1e293b; padding: 12px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.3); text-align: center; margin-bottom: 10px;">
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
        
    # --- TAB RIWAYAT PERBAIKAN (PEMBACA FOTO DARI GOOGLE FORM) ---
    with tab_perbaikan:
        if not df_rekomendasi.empty and selected_nama != "-":
            rec_name_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
            if rec_name_col:
                matched_rek = df_rekomendasi[df_rekomendasi[rec_name_col].astype(str).str.strip().str.lower() == selected_nama.strip().lower()]
                if not matched_rek.empty:
                    st.info("💡 Klik tombol **Refresh Data Server** di menu sebelah kiri untuk melihat data terbaru dari Google Form.")
                    st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Laporan Service: {selected_nama}</h4>", unsafe_allow_html=True)
                    
                    for _, row in matched_rek.iloc[::-1].iterrows():
                        # Mencari teks laporan (Bisa bernama 'Laporan', 'Findings', dsb tergantung nama pertanyaan di Google Form)
                        teks_laporan = row.get('Findings & Action Plan', row.get('Laporan', row.get('Findings', 'Tidak ada deskripsi laporan.')))
                        tanggal = row.get('Timestamp', '-')

                        st.markdown(f"""
                        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 6px solid #3b82f6; border-right: 1px solid #334155; border-top: 1px solid #334155; border-bottom: 1px solid #334155; margin-bottom: 15px; margin-top: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                            <h4 style="color:#60a5fa; margin-top:0;">📅 Update Service: {tanggal}</h4>
                            <p style="color:#e2e8f0; font-size:16px; white-space: pre-wrap; margin-bottom:15px; line-height:1.7;">{teks_laporan}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- PENYEDOT FOTO OTOMATIS DARI GOOGLE FORM ---
                        valid_photos = []
                        for col_name in df_rekomendasi.columns:
                            val = str(row[col_name]).strip()
                            if "drive.google.com" in val:
                                # Pisahkan jika ada beberapa link dalam 1 sel (Bawaan Google Form)
                                urls = val.split(',')
                                for u in urls:
                                    match = re.search(r'[-\w]{25,}', u)
                                    if match: valid_photos.append(match.group(0))

                        # Menampilkan Foto Besar 2 Kolom
                        if valid_photos:
                            cols = st.columns(2) 
                            for i, file_id in enumerate(valid_photos):
                                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200"
                                original_url = f"https://drive.google.com/file/d/{file_id}/view"
                                with cols[i % 2]: 
                                    try:
                                        st.image(thumb_url, use_container_width=True)
                                    except:
                                        st.warning("⚠️ Pratinjau sedang diproses Google.")
                                    st.markdown(f'<div style="text-align:center; margin-bottom: 20px;"><a href="{original_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold; display:inline-block; margin-top:5px; box-shadow: 0 4px 10px rgba(37,99,235,0.3); width:100%;">🔍 Buka Resolusi Penuh</a></div>', unsafe_allow_html=True)
                        st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
                else: st.info("Belum ada riwayat laporan perbaikan untuk karyawan ini.")
            else: st.error("Kolom 'Nama' tidak ditemukan di tabel rekomendasi perbaikan.")
        else: st.info("Belum ada data riwayat perbaikan yang sesuai.")

    with tab_fakta:
        if not df_fakta.empty and selected_nama != "-":
            matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False).any(), axis=1)]
            if not matched_fakta.empty:
                st.markdown(f"<h4 style='color:#60a5fa;'>Arsip Dokumen Fakta Integritas: {selected_nama}</h4>", unsafe_allow_html=True)
                for _, row in matched_fakta.iloc[::-1].iterrows():
                    st.markdown(f"**📅 Diupload pada: {row.get('Timestamp', row.get('TANGGAL', '-'))}**")
                    valid_files = []
                    for c in matched_fakta.columns:
                        val = str(row[c]).strip()
                        if "drive.google.com" in val:
                            urls = val.split(',')
                            for u in urls:
                                match = re.search(r'[-\w]{25,}', u)
                                if match: valid_files.append(match.group(0))
                    
                    if valid_files:
                        cols = st.columns(len(valid_files))
                        for i, file_id in enumerate(valid_files):
                            thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
                            original_url = f"https://drive.google.com/file/d/{file_id}/view"
                            with cols[i]:
                                try: st.image(thumb_url, use_container_width=True)
                                except: st.info("Dokumen PDF")
                                st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="{original_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold; width:100%; display:inline-block; box-shadow: 0 4px 10px rgba(37,99,235,0.3);">📥 BUKA DOKUMEN</a></div>', unsafe_allow_html=True)
                    else: st.info("Tidak ada dokumen PDF/Foto yang terlampir.")
                    st.write("<br><hr style='border-color: #334155;'>", unsafe_allow_html=True)
            else: st.warning(f"Belum ada arsip form Fakta Integritas atas nama: {selected_nama}")
        else: st.info("Data sheet FAKTA INTEGRITAS masih kosong.")
