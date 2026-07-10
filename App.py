import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard SDM & Asset", layout="wide", initial_sidebar_state="collapsed")

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
        # Membaca seluruh file Excel (semua tab/sheet)
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl')
        sheet_names = list(xls.keys())
        
        # 3A. Deteksi Sheet SDM
        if "SDM" in xls:
            df_sdm = xls["SDM"]
        else:
            st.error(f"❌ Sheet 'SDM' tidak ditemukan. Sheet yang ada di file Anda: {sheet_names}")
            df_sdm = pd.DataFrame()
            
        # 3B. Deteksi Sheet Asset (Menggunakan nama yang terpotong sesuai sistem)
        asset_target = "ALL ASSET MBP CME TE REG KALIMA"
        actual_asset_name = None
        
        for name in sheet_names:
            if asset_target.replace(" ", "").lower() in name.replace(" ", "").lower():
                actual_asset_name = name
                break
                
        if actual_asset_name:
            df_asset = xls[actual_asset_name]
        else:
            st.error(f"❌ Sheet Asset tidak ditemukan. Sheet yang ada di file Anda: {sheet_names}")
            df_asset = pd.DataFrame()
            
        return df_sdm, df_asset

    except Exception as e:
        st.error(f"❌ Gagal memuat data dari Spreadsheet. Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Panggil fungsi load data
df_sdm, df_asset = load_all_data()

# --- 4. HEADER & KONTEN UTAMA ---
st.markdown('<div class="header-style">🚀 SIMAKIN | REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty and not df_asset.empty:
    
    # 4A. Filter Karyawan
    if 'NAMA' in df_sdm.columns:
        list_nama = df_sdm['NAMA'].dropna().unique()
        selected_nama = st.selectbox("👤 Pilih Nama Karyawan (Dari Sheet SDM):", list_nama)
        
        # Ambil data spesifik 1 orang
        data_karyawan_select = df_sdm[df_sdm['NAMA'] == selected_nama].iloc[0]
        
        # Cek apakah nama ini juga ada di Sheet Asset
        if 'NAMA' in df_asset.columns and selected_nama in df_asset['NAMA'].values:
            data_asset_select = df_asset[df_asset['NAMA'] == selected_nama].iloc[0]
        else:
            data_asset_select = None
            
        # 4B. Data Karyawan (Profil Horizontal)
        st.markdown("### 👤 Data Karyawan (Profil)")
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        
        dict_karyawan = {}
        for field in karyawan_fields:
            if field in df_sdm.columns:
                dict_karyawan[field] = str(data_karyawan_select[field])
            else:
                dict_karyawan[field] = "-"
                
        df_karyawan_profile = pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"])
        st.dataframe(df_karyawan_profile, hide_index=True, use_container_width=True)
        
        st.write("---")

        # 4C. Layout Kolom (Tools vs Asset R2/R4)
        col_left, col_right = st.columns(2)
        
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
                    if str(val).strip() == "nan": val = "-"
                    tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": val})
                    
                    if any(x in val.lower() for x in ['bagus', 'ok', 'ada', '1']): status_bagus += 1
                    elif any(x in val.lower() for x in ['rusak', 'tidak', 'hilang', '0']): status_rusak += 1
                else:
                    tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": "-"})
                    
            df_tools_display = pd.DataFrame(tools_data)
            st.dataframe(df_tools_display, height=450, hide_index=True, use_container_width=True)

        with col_right:
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
                for field in asset_fields:
                    asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": "Belum ada data di Sheet Asset"})
                    
            df_asset_display = pd.DataFrame(asset_data)
            st.dataframe(df_asset_display, height=450, hide_index=True, use_container_width=True)

        # 4D. Grafik & Action Plan
        st.write("---")
        col_chart, col_plan = st.columns([1.5, 2])
        
        with col_chart:
            st.markdown("### 📊 Ringkasan Kondisi Tools Karyawan")
            if status_bagus == 0 and status_rusak == 0:
                st.info("Tidak ada data 'Bagus' atau 'Rusak' yang bisa dihitung untuk grafik.")
            else:
                chart_df = pd.DataFrame({"Kondisi": ["Bagus/Tersedia", "Rusak/Tidak Ada"], "Total": [status_bagus, status_rusak]})
                fig = px.pie(chart_df, values='Total', names='Kondisi', hole=0.4, color='Kondisi',
                             color_discrete_map={'Bagus/Tersedia':'#00b4d8', 'Rusak/Tidak Ada':'#d62828'})
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            
        with col_plan:
            st.markdown("### 📝 Findings & Action Plan")
            st.text_area("Input Rekomendasi perbaikan berkala asset/tools:", height=150)
            st.button("Push Update Data")

        # 4E. Foto Evidence (Dengan Perbaikan Google Drive Link Converter & Debugger)
        st.write("---")
        st.markdown("### 📸 Evidence & Documented Slide (Foto Asset)")
        
        if data_asset_select is not None:
            # Index kolom alfabet: G sd K, S sd U, W sd Z, AA sd AM, AP, AS sd AW
            target_cols = [
                6, 7, 8, 9, 10,       
                18, 19, 20,           
                22, 23, 24, 25,       
                26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 
                41,                   
                44, 45, 46, 47, 48    
            ]
            
            valid_photos = []
            all_detected_values = []
            
            for idx in target_cols:
                if idx < len(df_asset.columns):
                    col_name = df_asset.columns[idx]
                    cell_value = str(data_asset_select[col_name]).strip()
                    
                    if cell_value and cell_value != "nan" and cell_value != "-":
                        all_detected_values.append({"Kolom": col_name, "Isi Data": cell_value})
                        
                        # Ekstraksi tautan URL jika ada di dalam cell
                        urls = re.findall(r'(https?://[^\s"\'\)]+)', cell_value)
                        for url in urls:
                            final_url = url
                            # Jika link berasal dari Google Drive, konversi ke Direct Download Link
                            if "drive.google.com" in url:
                                match_d = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                                if match_d:
                                    final_url = f"https://lh3.googleusercontent.com/d/{match_d.group(1)}"
                                else:
                                    match_id = re.search(r'id=([a-zA-Z0-9-_]+)', url)
                                    if match_id:
                                        final_url = f"https://lh3.googleusercontent.com/d/{match_id.group(1)}"
                            
                            valid_photos.append((col_name, final_url))
            
            if valid_photos:
                photo_cols = st.columns(4) # Menampilkan dalam susunan grid 4 kolom
                for i, (col_label, img_url) in enumerate(valid_photos):
                    with photo_cols[i % 4]:
                        st.image(img_url, caption=f"Kolom: {col_label}", use_container_width=True)
            else:
                st.info("Tidak ada link foto yang valid terdeteksi pada kolom asset karyawan ini.")
            
            # --- PANEL DEBUGGING JIKA FOTO TETAP KOSONG ---
            with st.expander("🔍 Klik di sini jika foto belum muncul (Informasi Isi Kolom G-AW)"):
                if all_detected_values:
                    st.write("Sistem mendeteksi isi data berikut pada kolom foto Anda:")
                    st.json(all_detected_values)
                    st.caption("Catatan: Pastikan isi data di atas berupa link utuh berawalan http:// atau https:// dan file Google Drive diset ke 'Siapa saja dengan link dapat melihat'.")
                else:
                    st.write("Sistem tidak mendeteksi teks apa pun pada kolom G s/d AW untuk karyawan ini. Harap periksa apakah baris data atas nama ini di Google Sheets sudah terisi tautannya.")
        else:
            st.warning("Foto tidak dapat dimuat karena data Asset untuk karyawan ini tidak ditemukan.")

    else:
        st.error("Kolom 'NAMA' tidak ditemukan di Sheet SDM.")
