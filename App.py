import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard SDM & Tools", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Tema Gelap ala Dashboard di Gambar) ---
st.markdown("""
<style>
    .reportview-container {
        background: #1e1e24;
        color: white;
    }
    .stDataFrame {
        border-radius: 5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 16px;
    }
    .header-style {
        background-color: #d32f2f;
        padding: 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI LOAD DATA DARI GOOGLE SHEETS ---
@st.cache_data(ttl=600) # Cache data selama 10 menit
def load_data():
    # URL Asli: https://docs.google.com/spreadsheets/d/1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw/edit?gid=1104205638#gid=1104205638
    # Diubah ke format export CSV
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    gid = "1104205638"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Spreadsheet. Pastikan link diset ke 'Public'. Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- HEADER DASHBOARD ---
st.markdown('<div class="header-style">🚀 DASHBOARD SDM & INVENTARIS TOOLS | NOP PALANGKARAYA</div>', unsafe_allow_html=True)
st.write("---")

if not df.empty:
    # --- FILTER DATA ---
    # Asumsi ada kolom 'NAMA' di spreadsheet Anda untuk memilih karyawan
    if 'NAMA' in df.columns:
        selected_nama = st.selectbox("Pilih Karyawan / Nama Tim:", df['NAMA'].unique())
        user_data = df[df['NAMA'] == selected_nama].iloc[0]
    else:
        st.warning("Kolom 'NAMA' tidak ditemukan di Spreadsheet.")
        user_data = df.iloc[0] # Ambil baris pertama sebagai default

    # --- LAYOUT KOLOM ---
    col1, col2, col3 = st.columns([1, 1.5, 1.5])

    # ==========================================
    # KOLOM 1: DATA KARYAWAN (Pengganti Site Master)
    # ==========================================
    with col1:
        st.markdown("### 👤 Data Karyawan")
        # List kolom sesuai permintaan
        karyawan_fields = [
            "NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", 
            "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"
        ]
        
        # Menampilkan data karyawan dalam bentuk tabel rapi
        dict_karyawan = {}
        for field in karyawan_fields:
            # Pengecekan apakah kolom ada di gsheet
            dict_karyawan[field] = user_data[field] if field in df.columns else "-"
            
        df_karyawan = pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Value"])
        st.dataframe(df_karyawan, hide_index=True, use_container_width=True)


    # ==========================================
    # KOLOM 2: DATA TOOLS (Pengganti Tech Specs - Scrollable)
    # ==========================================
    with col2:
        st.markdown("### 🔧 Data Tools (Kondisi & Jumlah)")
        
        # List tools sesuai permintaan
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

        # Membuat dataframe khusus untuk tools. 
        # Asumsi di Spreadsheet formatnya: Nama Kolom Tool (berisi kondisi/jumlah, misal "1 - Bagus" atau kolom terpisah)
        tools_data = []
        status_bagus = 0
        status_rusak = 0

        for tool in tools_list:
            if tool in df.columns:
                val = str(user_data[tool])
                tools_data.append({"Nama Tools": tool, "Informasi / Kondisi": val})
                
                # Logika sederhana untuk grafik: hitung kata 'Bagus' atau 'Rusak' (Sesuaikan dengan data asli Anda)
                if 'bagus' in val.lower() or 'ok' in val.lower() or 'ada' in val.lower():
                    status_bagus += 1
                elif 'rusak' in val.lower() or 'hilang' in val.lower() or 'tidak' in val.lower():
                    status_rusak += 1
            else:
                tools_data.append({"Nama Tools": tool, "Informasi / Kondisi": "Data tidak tersedia"})

        df_tools = pd.DataFrame(tools_data)
        
        # Fitur SCROLLABLE: menggunakan height pada st.dataframe
        st.dataframe(df_tools, height=450, hide_index=True, use_container_width=True)


    # ==========================================
    # KOLOM 3: GRAFIK KONDISI (Pengganti Daily Trend)
    # ==========================================
    with col3:
        st.markdown("### 📊 Total Bagus / Rusak Tools")
        
        # Membuat Dataframe untuk Chart
        chart_data = pd.DataFrame({
            "Kondisi": ["Bagus / Tersedia", "Rusak / Tidak Ada"],
            "Jumlah": [status_bagus, status_rusak]
        })

        if status_bagus == 0 and status_rusak == 0:
            st.info("Tidak ada data status (Bagus/Rusak) yang terdeteksi untuk user ini.")
        else:
            # Membuat Bar Chart menggunakan Plotly
            fig = px.pie(chart_data, values='Jumlah', names='Kondisi', 
                         color='Kondisi',
                         color_discrete_map={'Bagus / Tersedia':'#00b4d8', 'Rusak / Tidak Ada':'#d62828'},
                         hole=0.4)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color="white",
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("### 📝 Findings & Action Plan")
        st.text_area("Input Rekomendasi / Analisa:", height=150)
        st.button("Push Update Data")

    # ==========================================
    # BAGIAN BAWAH: EVIDENCE / FOTO DARI GOOGLE DRIVE
    # ==========================================
    st.write("---")
    st.markdown("### 📸 Evidence & Documented Slide")
    
    # Placeholder untuk gambar. 
    # Jika di Gsheet ada link gambar GDrive, Anda bisa melooping url tersebut.
    # Karena Google Drive URL perlu format khusus untuk ditampilkan, ini contoh strukturnya:
    image_cols = st.columns(8)
    for i in range(8):
        with image_cols[i]:
            # Ganti URL ini dengan URL gambar asli dari spreadsheet Anda
            st.image("https://via.placeholder.com/150", caption=f"Foto {i+1}", use_column_width=True)
            st.button("Download", key=f"btn_{i}")

else:
    st.warning("Data kosong atau belum terhubung.")
