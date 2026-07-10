import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard SDM & Asset", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Tema Gelap Dashboard) ---
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
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI LOAD DATA DARI MULTIPLE SHEETS ---
@st.cache_data(ttl=600)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    # Menggunakan format export xlsx agar bisa membaca multi-sheet berdasarkan nama
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    try:
        df_sdm = pd.read_excel(excel_url, sheet_name="SDM")
        df_asset = pd.read_excel(excel_url, sheet_name="ALL ASSET MBP CME TE REG KALIMANTAN")
        return df_sdm, df_asset
    except Exception as e:
        st.error(f"Gagal memuat data dari Spreadsheet. Pastikan akses GSheet sudah Public (Anyone with link can view). Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_sdm, df_asset = load_all_data()

# --- HEADER DASHBOARD ---
st.markdown('<div class="header-style">🚀 DASHBOARD OPERASIONAL & ASSET | REG KALIMANTAN</div>', unsafe_allow_html=True)

if not df_sdm.empty and not df_asset.empty:
    
    # ==========================================
    # PILIH KARYAWAN (FILTER UTAMA)
    # ==========================================
    # Kita gunakan kolom NAMA yang ada di kedua sheet sebagai penyambung relasi data
    list_nama = df_sdm['NAMA'].dropna().unique()
    selected_nama = st.selectbox("👤 Pilih Nama Karyawan:", list_nama)
    
    # Filter data berdasarkan nama terpilih
    data_karyawan_select = df_sdm[df_sdm['NAMA'] == selected_nama].iloc[0]
    
    # Cek apakah nama tersebut memiliki data di sheet Asset
    has_asset = selected_nama in df_asset['NAMA'].values
    if has_asset:
        data_asset_select = df_asset[df_asset['NAMA'] == selected_nama].iloc[0]
    else:
        data_asset_select = None

    # ==========================================
    # BARIS 1: DATA RINGKAS KARYAWAN (Profil Utama)
    # ==========================================
    st.markdown("### 👤 Data Karyawan (Profil)")
    karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
    dict_karyawan = {field: data_karyawan_select[field] if field in df_sdm.columns else "-" for field in karyawan_fields}
    df_karyawan_profile = pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"])
    st.dataframe(df_karyawan_profile, hide_index=True, use_container_width=True)
    
    st.write("---")

    # ==========================================
    # BARIS 2: DATA TOOLS DAN ASSET R2/R4 (BERDAMPINGAN)
    # ==========================================
    col_left, col_right = st.columns(2)
    
    # --- KOLOM KIRI: DATA TOOLS (Kondisi & Jumlah) ---
    with col_left:
        st.markdown("### 🔧 Data Tools (Kondisi & Jumlah)")
        
        tools_list = [
            "WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", 
            "Safety Driving License", "Type Kendaraan", "Jenis Kendaraan", "Nopol", "Status Asset Kendaraan", 
            "Type Genset", "KVA Genset", "Status Genset", "TANG AMPERE AC / DC", "GROUNDING TESTER",
            "Flaring set", "conduits", "pipe benders", "sealant tool", "Steamer Aircond", "Manifold", "freon",
            "Full Body Harness", "Sefty Vest", "Sefty shoes", "Test Pen", "Safety Climbing Helmet", "First aid box",
            "TOOLS BOX with standard tool set", "Laptop", "Smartphone", "Genset + Cable Genseat Minimum 100m + COS legrand 3 phase"
            # ... Anda bisa menambahkan list tools lengkap Anda di sini ...
        ]
        
        tools_data = []
        status_bagus, status_rusak = 0, 0
        
        for tool in tools_list:
            if tool in df_sdm.columns:
                val = str(data_karyawan_select[tool])
                tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": val})
                if any(x in val.lower() for x in ['bagus', 'ok', 'ada', '1']): status_bagus += 1
                elif any(x in val.lower() for x in ['rusak', 'tidak', '0']): status_rusak += 1
            else:
                tools_data.append({"Nama Tools": tool, "Kondisi / Jumlah": "-"})
                
        df_tools_display = pd.DataFrame(tools_data)
        st.dataframe(df_tools_display, height=400, hide_index=True, use_container_width=True)

    # --- KOLOM KANAN: DATA ASSET R2/R4 (Sheet: ALL ASSET MBP CME...) ---
    with col_right:
        st.markdown("### 🚗 Data Asset R2/R4 (Logistik & Kendaraan)")
        
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
                asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": val})
        else:
            for field in asset_fields:
                asset_data.append({"Parameter Asset R2/R4": field, "Keterangan": "Data Asset Tidak Ditemukan"})
                
        df_asset_display = pd.DataFrame(asset_data)
        # Dibuat list bentuk scrollable sama persis dengan height=400
        st.dataframe(df_asset_display, height=400, hide_index=True, use_container_width=True)

    # ==========================================
    # BARIS 3: GRAFIK & ANALISA
    # ==========================================
    st.write("---")
    col_chart, col_plan = st.columns([1.5, 2])
    
    with col_chart:
        st.markdown("### 📊 Ringkasan Kondisi Tools Karyawan")
        chart_df = pd.DataFrame({"Kondisi": ["Bagus/OK", "Rusak/Tidak Ada"], "Total": [status_bagus, status_rusak]})
        fig = px.pie(chart_df, values='Total', names='Kondisi', hole=0.4, color='Kondisi',
                     color_discrete_map={'Bagus/OK':'#00b4d8', 'Rusak/Tidak Ada':'#d62828'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_plan:
        st.markdown("### 📝 Findings & Action Plan")
        st.text_area("Input Rekomendasi perbaikan berkala asset/tools:", height=120)
        st.button("Push Update Data Asset & Tools")

    # ==========================================
    # BARIS 4: FOTO EVIDENCE BERDASARKAN INDEKS KOLOM GSHEET
    # ==========================================
    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide (Foto Asset Terkait)")
    
    if data_asset_select is not None:
        # Konversi nama kolom alfabet GSheet menjadi indeks angka Python (0-indexed)
        # G=6, H=7, I=8, J=9, K=10, S=18, T=19, U=20, W=22, X=23, Y=24, Z=25
        # AA=26, AB=27, AC=28, AD=29, AE=30, AF=31, AG=32, AH=33, AI=34, AJ=35, AK=36, AL=37, AM=38
        # AP=41, AS=44, AT=45, AU=46, AV=47, AW=48
        target_columns_idx = [
            6, 7, 8, 9, 10, 18, 19, 20, 22, 23, 24, 25, 
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 
            41, 44, 45, 46, 47, 48
        ]
        
        # Mengumpulkan semua URL foto yang valid dari kolom-kolom di atas
        valid_photos = []
        for idx in target_columns_idx:
            if idx < len(df_asset.columns):
                col_name = df_asset.columns[idx]
                cell_value = str(data_asset_select[col_name]).strip()
                # Cek apakah cell berisi link gambar (Google Drive/Web Link)
                if cell_value.startswith("http"):
                    valid_photos.append((col_name, cell_value))
        
        if valid_photos:
            # Tampilkan foto menggunakan grid kolom Streamlit (misal maksimal 4 kolom per baris)
            photo_cols = st.columns(4)
            for i, (col_label, img_url) in enumerate(valid_photos):
                with photo_cols[i % 4]:
                    # Catatan: Jika gambar dari Google Drive, pastikan format URL-nya sudah berupa direct-download link
                    st.image(img_url, caption=f"Kolom {col_label}", use_container_width=True)
                    st.button("Download", key=f"dl_{i}")
        else:
            st.info("Tidak ada link foto yang tersedia pada kolom-kolom asset karyawan ini.")
    else:
        st.warning("Foto tidak dapat dimuat karena data pada sheet Asset untuk karyawan ini kosong.")

else:
    st.warning("Pastikan nama sheet 'SDM' dan 'ALL ASSET MBP CME TE REG KALIMANTAN' di isi dengan benar.")
