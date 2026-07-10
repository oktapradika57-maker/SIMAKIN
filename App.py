import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CUSTOM CSS ---
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

# --- 3. FUNGSI UTAS: KONVERSI ABJAD KOLOM EXCEL KE INDEX ANGKA ---
def col_letter_to_index(col_str):
    exp = 0
    idx = 0
    for char in reversed(col_str.upper().strip()):
        idx += (ord(char) - ord('A') + 1) * (26 ** exp)
        exp += 1
    return idx - 1

# --- 4. FUNGSI LOAD DATA DARI SEMUA SHEET ---
@st.cache_data(ttl=600)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl')
        
        df_sdm = xls.get("SDM", pd.DataFrame())
        df_asset = xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame())
        df_genset = xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame())
        df_tools_asset = xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame())
        
        return df_sdm, df_asset, df_genset, df_tools_asset
    except Exception as e:
        st.error(f"❌ Gagal memuat data dari Spreadsheet. Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset, df_genset, df_tools_asset = load_all_data()

# --- 5. FUNGSI PENCARIAN BARIS DATA BERDASARKAN NAMA (TOLERAN TYPO & SPASI) ---
def get_row_by_name(df, name):
    if df.empty or 'NAMA' not in df.columns:
        return None
    clean_target_name = str(name).strip().lower()
    # Mencocokkan nama dengan mengabaikan spasi berlebih dan huruf besar/kecil
    matched = df[df['NAMA'].astype(str).str.strip().str.lower() == clean_target_name]
    if not matched.empty:
        return matched.iloc[0]
    return None

# --- 6. FUNGSI EKSTRAKSI & KONVERSI LINK FOTO GOOGLE DRIVE ---
def extract_valid_photos(data_row, df_columns, target_indices):
    photos = []
    all_logs = []
    if data_row is None or len(df_columns) == 0:
        return photos, all_logs
        
    for idx in target_indices:
        if idx < len(df_columns):
            col_name = df_columns[idx]
            cell_value = str(data_row[col_name]).strip()
            
            if cell_value and cell_value != "nan" and cell_value != "-":
                all_logs.append({"Kolom": col_name, "Isi Teks Sel": cell_value})
                urls = re.findall(r'(https?://[^\s"\'\)]+)', cell_value)
                for url in urls:
                    final_url = url
                    # Perbaikan format konversi direct link Google Drive agar stabil di Streamlit
                    if "drive.google.com" in url:
                        match_d = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                        if match_d:
                            final_url = f"https://lh3.googleusercontent.com/d/{match_d.group(1)}"
                        else:
                            match_id = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url)
                            if match_id:
                                final_url = f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
                    photos.append((col_name, final_url))
    return photos, all_logs

# --- 7. HEADER DASHBOARD ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL, ASSET & GENSET | REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    
    # ==========================================
    # FILTER BERTINGKAT: LOKER & NAMA KARYAWAN
    # ==========================================
    if 'LOKER' in df_sdm.columns:
        list_loker = ["SEMUA LOKER"] + list(df_sdm['LOKER'].dropna().unique())
        selected_loker = st.selectbox("📍 Pilih Loker Kerja (Filter Atas):", list_loker)
        
        if selected_loker != "SEMUA LOKER":
            df_sdm_filtered = df_sdm[df_sdm['LOKER'] == selected_loker]
        else:
            df_sdm_filtered = df_sdm
    else:
        df_sdm_filtered = df_sdm

    if 'NAMA' in df_sdm_filtered.columns:
        list_nama = df_sdm_filtered['NAMA'].dropna().unique()
        selected_nama = st.selectbox("👤 Pilih Nama Karyawan (Dari Sheet SDM):", list_nama)
        
        # Ambil data spesifik menggunakan Smart Name Matching
        data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
        data_asset_select = get_row_by_name(df_asset, selected_nama)
        data_genset_select = get_row_by_name(df_genset, selected_nama)
        data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)
            
        # --- DATA PROFIL KARYAWAN ---
        st.markdown("### 👤 Data Karyawan (Profil)")
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        dict_karyawan = {field: str(data_karyawan_select[field]) if field in data_karyawan_select else "-" for field in karyawan_fields}
        df_karyawan_profile = pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"])
        st.dataframe(df_karyawan_profile, hide_index=True, use_container_width=True)
        
        st.write("---")

        # ==========================================
        # LAYOUT 3 KOLOM BERDAMPINGAN (Tools, Asset, Genset)
        # ==========================================
        col_left, col_mid, col_right = st.columns(3)
        
        with col_left:
            st.markdown("### 🔧 Data Tools (Kondisi & Jumlah)")
            tools_list = [
                "WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", 
                "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", 
                "Type Genset", "KVA Genset", "Status Genset", "TANG AMPERE AC / DC", "GROUNDING TESTER", 
                "Aircond rectification tools for dismantle/ install such as piping tools", "Flaring set", 
                "conduits", "pipe benders", "sealant tool", "Steamer Aircond", "Manifold", "freon", 
                "cutting pipe etc", "Full Body Harness", "Double Hooked Lanyard with absorber", 
                "Work Positioning Lanyard", "Sefty Vest", "Sefty shoes", "Safety Civil Gloves", 
                "Safety Electrical Glove", "Safety Climbing Glove", "Rain coat", "Test Pen", 
                "Safety Climbing Helmet", "Safety Ground Helmet", "Safety Glass", "Safety Banner", 
                "Barricade Line", "Safety Boots (For Rainy session/ Flood )", "First aid box", 
                "TOOLS BOX with standard tool set", "portable small Vacuum cleaner", "broom", "canebo", 
                "tarpaulin", "lamp", "Battery Tester", "Mesin Las portable", "Gerinda", "Bor listrik", 
                "KUNCI SABUK (Rantai) FILTER", "VACUM CLEANER", "JET PUMP PEMBERSIH AC", "Mesin Pemotong rumput", 
                "TANG CRIMPING", "LAN TESTER", "TANGGA hidrolic 10 METER", "KOMPAS", "METERAN 50m", 
                "METERAN 100m", "ANGLE METER (Water pass)", "OPTICAL POWER METER", "INFRARED THERMOMETER", 
                "TAMBANG", "KATROL", "KUNCI PASS 32", "Cable & Connector Console", "Power bank Handphone", 
                "Thermal Imager", "Thermal Logger", "Optical splicer single core", "OTDR", "Laptop", 
                "Smartphone", "Printer label", "Genset + Cable Genseat Minimum 100m + COS legrand 3 phase", 
                "Light Source (optical)", "obeng cadik", "tang buaya", "tang kombinasi", "tang potong", 
                "kunci pass set", "kunci L set", "cutter", "Krone LSA", "Krone Wrapping Gun", 
                "Fire Estinguisher portable", "OBD (Car GPS)", "Diagonal Plier", "Wire Stripper", 
                "Electrical Insulation (Solasi Kabel)", "Cable Ties 5mm", "Iron Saw", "Screw stuck drat puller", 
                "Kolor KUT Paste (Fuel Quality tester)", "Tent/ Tarpaulin (Including Lamp)", "Vehicle/ Motorcycle", 
                "Climbing Supporting Tools (Rope, Katrol 7 Etc)", "Feeder Installation Kit", "Portable Ladder", "Car Tracker"
            ]
            
            tools_data = []
            status_bagus, status_rusak = 0, 0
            for tool in tools_list:
                if tool in df_sdm.columns:
                    val = str(data_karyawan_select[tool])
                    if val.strip() == "nan": val = "-"
                    tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": val})
                    if any(x in val.lower() for x in ['bagus', 'ok', 'ada', '1']): status_bagus += 1
                    elif any(x in val.lower() for x in ['rusak', 'tidak', 'hilang', '0']): status_rusak += 1
                else:
                    tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": "-"})
            st.dataframe(pd.DataFrame(tools_data), height=450, hide_index=True, use_container_width=True)

        with col_mid:
            st.markdown("### 🚗 Data Asset R2/R4 (Logistik)")
            asset_fields = [
                "JABATAN/ROLE", "LOKASI KERJA", "KATEGORI KENDARAAN", "STATUS KEPEMILIKAN ASSET", 
                "NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", 
                "OLI MESIN (TGL TERAKHIR DIGANTI)", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)", 
                "GANTI OLI (TGL TERAKHIR DIGANTI)", "PERGANTIAN BAN (TGL TERAKHIR PERGANTIAN BAN)"
            ]
            asset_data = []
            if data_asset_select is not None:
                for field in asset_fields:
                    val = str(data_asset_select[field]) if field in df_asset.columns else "-"
                    if val.strip() == "nan": val = "-"
                    asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": val})
            else:
                asset_data = [{"Parameter Asset R2/R4": f, "Keterangan": "Belum ada data Asset"} for f in asset_fields]
            st.dataframe(pd.DataFrame(asset_data), height=450, hide_index=True, use_container_width=True)

        with col_right:
            st.markdown("### ⚡ Data Genset")
            genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STSTUS KEPEMILIKAN", "STATUS ASSET"]
            genset_data = []
            if data_genset_select is not None:
                for field in genset_fields:
                    val = str(data_genset_select[field]) if field in df_genset.columns else "-"
                    if val.strip() == "nan": val = "-"
                    genset_data.append({"Parameter Genset": field, "Keterangan": val})
            else:
                genset_data = [{"Parameter Genset": f, "Keterangan": "Belum ada data Genset"} for f in genset_fields]
            st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

        # --- GRAFIK KONDISI ---
        st.write("---")
        col_chart, col_plan = st.columns([1.5, 2])
        with col_chart:
            st.markdown("### 📊 Ringkasan Kondisi Tools Karyawan")
            if status_bagus > 0 or status_rusak > 0:
                chart_df = pd.DataFrame({"Kondisi": ["Bagus/Tersedia", "Rusak/Tidak Ada"], "Total": [status_bagus, status_rusak]})
                fig = px.pie(chart_df, values='Total', names='Kondisi', hole=0.4, color='Kondisi', color_discrete_map={'Bagus/Tersedia':'#00b4d8', 'Rusak/Tidak Ada':'#d62828'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Kondisi tools bernilai kosong.")
        with col_plan:
            st.markdown("### 📝 Findings & Action Plan")
            st.text_area("Input Rekomendasi perbaikan berkala:", height=150)
            st.button("Push Update Data")

        # ==========================================
        # SEKSI FOTO EVIDENCE (GALLERY VIA TABS & DEBUGGER)
        # ==========================================
        st.write("---")
        st.markdown("### 📸 Evidence & Documented Slide Gallery")
        
        tab_r2r4, tab_genset, tab_tools = st.tabs(["🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools (Kalimantan)"])
        
        # 1. Tab Foto Asset R2/R4
        with tab_r2r4:
            letters_r2r4 = ["G","H","I","J","K","S","T","U","W","X","Y","Z","AA","AB","AC","AD","AE","AF","AG","AH","AI","AJ","AK","AL","AM","AP","AS","AT","AU","AV","AW"]
            idx_r2r4 = [col_letter_to_index(l) for l in letters_r2r4]
            photos_r2r4, logs_r2r4 = extract_valid_photos(data_asset_select, df_asset.columns, idx_r2r4)
            
            if photos_r2r4:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_r2r4):
                    cols[i % 4].image(url, caption=f"Kolom {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto kendaraan R2/R4 terdeteksi untuk karyawan ini.")
            
            with st.expander("🔍 Debug Link Kolom R2/R4"):
                st.write(logs_r2r4 if logs_r2r4 else "Kolom-kolom di GSheet kosong.")

        # 2. Tab Foto Genset
        with tab_genset:
            letters_genset = ["F","G","H","M","N","O","P","Q","S","T","U","V","W","X","Z","AA","AB","AC","AD","AE","AF","AG","AH"]
            idx_genset = [col_letter_to_index(l) for l in letters_genset]
            photos_genset, logs_genset = extract_valid_photos(data_genset_select, df_genset.columns, idx_genset)
            
            if photos_genset:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_genset):
                    cols[i % 4].image(url, caption=f"Kolom {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto unit Genset terdeteksi untuk karyawan ini.")
                
            with st.expander("🔍 Debug Link Kolom Genset"):
                st.write(logs_genset if logs_genset else "Kolom-kolom di GSheet kosong.")

        # 3. Tab Foto Tools
        with tab_tools:
            # Generate indeks alfabet otomatis dari E sampai DB
            start_idx = col_letter_to_index("E")
            end_idx = col_letter_to_index("DB")
            idx_tools = list(range(start_idx, end_idx + 1))
            
            photos_tools, logs_tools = extract_valid_photos(data_tools_asset_select, df_tools_asset.columns, idx_tools)
            
            if photos_tools:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_tools):
                    cols[i % 4].image(url, caption=f"Kolom {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto unit Tools terdeteksi untuk karyawan ini.")
                
            with st.expander("🔍 Debug Link Kolom Tools"):
                st.write(logs_tools if logs_tools else "Kolom-kolom di GSheet kosong.")

    else:
        st.error("Kolom 'NAMA' tidak terdeteksi.")
