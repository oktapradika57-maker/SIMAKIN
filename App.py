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

# --- 3. FUNGSI LOAD DATA ---
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

# --- 4. FUNGSI PENCARIAN BARIS DATA BERDASARKAN NAMA (FUZZY MATCHING / ANTI-GAGAL) ---
def get_row_by_name(df, target_name):
    if df.empty:
        return None
    
    # Cari nama kolom yang mengandung kata "NAMA" (Bisa 'NAMA', 'NAMA KARYAWAN', dll)
    name_col = None
    for col in df.columns:
        if "NAMA" in str(col).upper():
            name_col = col
            break
            
    if not name_col:
        return None
        
    clean_target = str(target_name).strip().lower()
    
    # Coba cocokkan 100% presisi (setelah dibersihkan spasinya)
    exact_match = df[df[name_col].astype(str).str.strip().str.lower() == clean_target]
    if not exact_match.empty:
        return exact_match.iloc[0]
        
    # Jika gagal, coba cocokkan sebagian (Misal "Budi" terbaca di dalam "Budi Santoso")
    partial_match = df[df[name_col].astype(str).str.strip().str.lower().str.contains(clean_target, regex=False, na=False)]
    if not partial_match.empty:
        return partial_match.iloc[0]
        
    return None

# --- 5. FUNGSI ULTRA-ROBUST: EKSTRAKSI FOTO DENGAN AUTOMATIC FAILSAFE SCAN & DEEP LOG ---
def extract_photos_robust(data_row, df_columns, range_letters=None, sheet_name=""):
    photos = []
    all_logs = []
    
    # Cek apakah baris nama karyawan tersebut berhasil ditemukan di sheet ini
    if data_row is None:
        all_logs.append({"Status": "❌ GAGAL DITEMUKAN", "Pesan": f"Data atas nama ini TIDAK ADA di sheet {sheet_name}. Pastikan namanya terdaftar dan nama kolom memuat kata 'NAMA'.", "Data Mentah": "-"})
        return photos, all_logs

    # Jika nama ditemukan, kita log semua isi datanya agar Anda bisa melihat apa yang dibaca sistem
    raw_dict = {}
    for col in df_columns:
        val = str(data_row[col]).strip()
        if val and val not in ["nan", "-", "None"]:
            raw_dict[col] = val
    all_logs.append({"Status": "✅ NAMA DITEMUKAN", "Pesan": f"Baris data karyawan ditemukan. Ini isi teks mentah yang dibaca komputer dari GSheet Anda:", "Data Mentah": str(raw_dict)})

    def letter_to_idx(s):
        val = 0
        for char in s.upper().strip():
            val = val * 26 + (ord(char) - ord('A') + 1)
        return val - 1

    target_indices = []
    if range_letters:
        for item in range_letters:
            if "-" in item:
                start, end = item.split("-")
                target_indices.extend(list(range(letter_to_idx(start), letter_to_idx(end) + 1)))
            else:
                target_indices.append(letter_to_idx(item))
    else:
        target_indices = list(range(len(df_columns)))

    # Scan Link pada Semua Kolom (Failsafe)
    for idx in range(len(df_columns)):
        col_name = df_columns[idx]
        cell_value = str(data_row[col_name]).strip()
        
        if cell_value and cell_value not in ["nan", "-", "None"]:
            urls = re.findall(r'(https?://[^\s"\'\)<>]+)', cell_value)
            for url in urls:
                final_url = url
                if "drive.google.com" in url:
                    match_d = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                    if match_d:
                        final_url = f"https://lh3.googleusercontent.com/d/{match_d.group(1)}"
                    else:
                        match_id = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url)
                        if match_id:
                            final_url = f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
                photos.append((str(col_name), final_url))
                all_logs.append({"Status": "🔗 LINK DITEMUKAN", "Pesan": f"Terdapat link gambar pada kolom: {col_name}", "Data Mentah": final_url})
                
    return photos, all_logs

# --- 6. HEADER DASHBOARD ---
st.markdown('<div class="header-style">🚀 SIMAKIN | REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    
    # ==========================================
    # FILTER BERTINGKAT
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
        
        data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
        data_asset_select = get_row_by_name(df_asset, selected_nama)
        data_genset_select = get_row_by_name(df_genset, selected_nama)
        data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)
            
        # --- DATA PROFIL KARYAWAN ---
        st.markdown("### 👤 Data Karyawan (Profil)")
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
        st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
        
        st.write("---")

        # ==========================================
        # LAYOUT 3 KOLOM BERDAMPINGAN
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
                if data_karyawan_select is not None and tool in df_sdm.columns:
                    val = str(data_karyawan_select[tool])
                    if val.strip() in ["nan", "None"]: val = "-"
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
                    if val.strip() in ["nan", "None"]: val = "-"
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
                    if val.strip() in ["nan", "None"]: val = "-"
                    genset_data.append({"Parameter Genset": field, "Keterangan": val})
            else:
                genset_data = [{"Parameter Genset": f, "Keterangan": "Belum ada data Genset"} for f in genset_fields]
            st.dataframe(pd.DataFrame(genset_data), height=450, hide_index=True, use_container_width=True)

        # --- GRAFIK ---
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
        # GALLERY EVIDENCE (DENGAN SMART DEBUGGER)
        # ==========================================
        st.write("---")
        st.markdown("### 📸 Evidence & Documented Slide Gallery")
        
        tab_r2r4, tab_genset, tab_tools = st.tabs(["🚗 Foto Asset R2/R4", "⚡ Foto Genset", "🔧 Foto Tools (Kalimantan)"])
        
        # 1. Tab Foto Asset R2/R4
        with tab_r2r4:
            photos_r2r4, logs_r2r4 = extract_photos_robust(
                data_asset_select, df_asset.columns, range_letters=["G-K", "S-U", "W-Z", "AA-AM", "AP", "AS-AW"], sheet_name="Asset R2/R4"
            )
            if photos_r2r4:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_r2r4):
                    cols[i % 4].image(url, caption=f"Kolom {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto kendaraan R2/R4 terdeteksi.")

        # 2. Tab Foto Genset
        with tab_genset:
            photos_genset, logs_genset = extract_photos_robust(
                data_genset_select, df_genset.columns, range_letters=["F-H", "M-Q", "S-X", "Z-AH"], sheet_name="Genset"
            )
            if photos_genset:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_genset):
                    cols[i % 4].image(url, caption=f"Kolom: {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto unit Genset terdeteksi.")
                
            with st.expander("🔍 Cek Analisis Masalah Sheet Genset"):
                for log in logs_genset:
                    st.write(f"**{log['Status']}**: {log['Pesan']}")
                    st.code(log['Data Mentah'])

        # 3. Tab Foto Tools
        with tab_tools:
            photos_tools, logs_tools = extract_photos_robust(
                data_tools_asset_select, df_tools_asset.columns, range_letters=["E-DB"], sheet_name="Tools"
            )
            if photos_tools:
                cols = st.columns(4)
                for i, (lbl, url) in enumerate(photos_tools):
                    cols[i % 4].image(url, caption=f"Kolom: {lbl}", use_container_width=True)
            else:
                st.info("Tidak ada foto unit Tools terdeteksi.")
                
            with st.expander("🔍 Cek Analisis Masalah Sheet Tools"):
                for log in logs_tools:
                    st.write(f"**{log['Status']}**: {log['Pesan']}")
                    st.code(log['Data Mentah'])

    else:
        st.error("Kolom 'NAMA' tidak terdeteksi.")
