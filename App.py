import streamlit as st
import pandas as pd
import gspread
import base64
import cloudinary
import cloudinary.uploader
import requests
import math
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import re

# ==========================================
# 0. KONFIGURASI HALAMAN & SUPER PREMIUM UI
# ==========================================
st.set_page_config(page_title="SiRAPI Enterprise", page_icon="💎", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800;900&display=swap');
        
        .main { background: #f4f7f6; font-family: 'Plus Jakarta Sans', sans-serif; }
        
        /* Premium Header Card */
        .header-card {
            background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
            padding: 45px 30px; border-radius: 24px; color: white; text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.25); margin-bottom: 40px;
            animation: fadeInDown 0.8s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative; overflow: hidden;
            border-bottom: 6px solid #00F2FE;
        }
        .header-card h1, .header-card h2 { font-weight: 900; letter-spacing: 1px; margin-bottom: 5px; }
        .header-card p { font-size: 1.1rem; color: #cbd5e1; }
        
        /* Glassmorphism 3D Metrics */
        .metric-3d {
            background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px);
            padding: 30px; border-radius: 24px; text-align: center;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05); border: 1px solid rgba(255,255,255,0.7);
            border-top: 6px solid #4FACFE; margin-bottom: 25px;
            transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        .metric-3d:hover {
            transform: translateY(-12px) scale(1.03);
            box-shadow: 0 25px 45px rgba(79, 172, 254, 0.2);
            border-top: 6px solid #00F2FE;
        }
        .metric-title { font-size: 0.85rem; color: #64748b; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;}
        .metric-value { font-size: 2rem; font-weight: 900; margin-top: 10px; background: -webkit-linear-gradient(45deg, #0F2027, #4FACFE); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
        
        /* Dashboard Main Buttons */
        div[data-testid="stButton"] > button {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid #e2e8f0 !important; border-radius: 24px !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.03) !important;
            height: 180px !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        div[data-testid="stButton"] > button:hover {
            background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%) !important;
            border: none !important;
            transform: translateY(-10px) !important;
            box-shadow: 0 20px 40px rgba(0, 242, 254, 0.35) !important;
        }
        div[data-testid="stButton"] > button p { color: #1e293b !important; font-size: 1.25rem !important; font-weight: 800 !important; transition: color 0.3s ease; }
        div[data-testid="stButton"] > button:hover p { color: white !important; }
        
        /* Section Titles */
        .section-title { color: #0F2027; font-size: 1.35rem; font-weight: 900; border-bottom: 3px solid #e2e8f0; padding-bottom: 10px; margin-top: 35px; margin-bottom: 25px;}
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .stApp { animation: fadeInDown 0.6s ease-out; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MASTER DATA & KONFIGURASI
# ==========================================
AUTHORIZED_PASSWORDS = [
    "B09241925", "B09252588", "B09252589", "B09262648", "B09262667",
    "B09262771", "B09262669", "B09262799", "B09252583", "B0924649",
    "B09252500", "B09252501", "B0922270", "B0924599", "B09241097",
    "B09241113", "B09241115", "B09252576", "B09241146", "B09252184",
    "B09262613", "B09252531", "B09262666", "B09252577", "Yui2025",
]
CUTOFF_DATE = datetime(2026, 8, 1).date()

cloudinary.config(cloud_name="fxm61tjv", api_key="624877324969231", api_secret="LIFO6pfEg9fOM3nbsY8FBbVTpSI", secure=True)

SHEET_REQUEST = "Form Request dana"        
SHEET_PJB = "Form PJB"
SHEET_UM = "Data UM"
SHEET_APP = "Approval BBM"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MASTER_DATA = {
    "Palangkaraya": {"spreadsheet_id": "1HvgVicTWwO4RMQI6ZR3Mu3IgGicwjcLZl9mDN1auvJU", "clusters": ["Palangkaraya", "Barito Raya"], "names": ["ADI BOWO SANTOSO", "AHMAD", "AHMAD MUZAKIR", "AHMAD SETIAWAN", "ALFI SYAHRI", "ARMADI", "AULIA RAHMAN", "DARLI SUTANTO", "DIDI RIYADI", "FAHMI", "FRANS EJHA ADITYA", "GYLLBRHED ALFARY LOLOMSAIT", "HARUN NURASYID", "HORY YUSMANTO", "INDRA", "JAMES JIMBRIS TAMAILANG", "JUMADI", "KHILAL DAWAI KATIRI", "LEONARD HARA", "M. RIFANI", "MUHAMMAD MUKHLIS", "MUHAMMAD MUKTI", "MUNAWIR AHMAD", "MURJANI", "NURHAYAT", "OKY BANGKIT PAMUNGKAS", "PRADILA KANDI", "PUJIANTO", "PUTRA WARDANA", "REYNALDI RICARDO PUTRA", "RIKI HIDAYAT", "RIKO SETIADI", "SAILILLAH", "SARUL SAPUTRA", "SARWONO", "TAKLIM", "TIVIANSYAH", "TRISNO SUSANTO", "YAHYA MUHAMAD", "OKTA PRDIKA", "M KIKI FIRMANSYAH", "MAWARDAH", "HD"]},
    "Pangkalanbun": {"spreadsheet_id": "1bc0lDhR5iMtXZsKiKIdEwPY8JTaASeHFtaJSeXkywE4", "clusters": ["Ketapang", "Sampit", "Pangkalanbun"], "names": ["RIRIH HARIANTO", "MUKHAMAD ABDUL KHOLIP", "YAMA DEWANTA", "BAGUS SANTOSO", "IMRON SETIAWAN", "JOENDRIS HERDIAN KARA", "STEVEN HERDIAN KARA", "YUDIONO", "DADANG WAHYU SYAHPUTRA", "CAVIN ANDREAN EKA PUTRA", "RAHMAT RIYAN WAHYUDIN", "SUWITO", "DIDIK PRIYONO", "GUNTUR WAHYU PRADANA", "UTI MUHAMMAD KHAIRUL HUDA", "IDRUS MAULANA", "M. RIZKY", "TRIYONO", "ERIK SETIAWAN", "AGUS SUGANDA", "AJI SAPUTRA", "DIAN WAHYUDI", "HAFID BUDIANTO", "IWAN ZAINAL ABIDIN", "DANDI PUTRA", "PONIRAN", "PARYADI KUSUMA", "HERWANI", "DIAN WILDANI", "IPAN HARIONO", "FIRDAUS", "RONI YUDI ISYANTO", "AYU NUR ISLAMIAH", "ARDIANSYAH.", "DAYU SHANDY", "WAHYUDI", "TAJAM SAPUTRA", "MUJHAHID ALWI", "NANDA FIRMANSYAH", "WAHYU RAHMADANI", "TEGUH WICAKSONO", "FERI HARIADI", "NASUKI", "ANDARIANTO PUJI SURO", "BONDAN PRAMUDYA ANANTATUR", "SOLEKHAN", "RIZAL IHZAMAHENDRA", "MUHAMMAD ROIS FERDIANSYAH", "WIDI ARYANTO", "FHANNY AGUSTIAWAN"]},
    "Tarakan": {"spreadsheet_id": "1lRj1YdZGQwY5vHg8P4wudK9V1O_lJuEYjdyHkXoB-Wg", "clusters": ["Tarakan Inner", "Tarakan Outer"], "names": ["HENDRA WIRTASI SIMANULLANG", "ARIZONA ROSADI", "KUKUH BHASKARA", "NATAL SIMBOLON", "HERMAWAN", "IRVAN DINATA VANDITYAWAN", "ENDRAS SAPTA", "AHMADI", "EDI PANJI ERMAYANA", "HANS RISKY RONI TUAH GIRSANG", "IRMANSYAH B. SANGAJI", "REMO REMOLDUS MANALU", "MOHAMMAD RAFAI", "FIRMAN SYAHRUL", "AZMIR", "PETRUS RESI KELORE", "ANIR REZKY", "AHDAN", "PARJON SIMANULLANG", "RUSDI", "HASRIADI", "PURO SUGONDO", "ALIMUDIN M. SAER", "KORNELIUS USI KELORE", "RUSDIANSYAH", "JONTES YUSDA SIMANULLANG", "NANI SETIANINGSIH", "UNGGUL NUGRAHA", "YOGABITA INDOTENO", "JHON KENNEDI SIMANULLANG", "RAFI MUHAMAD SYARIF", "AGRIVA", "SEPTIAN ALVITO", "M. DEDI RIZALDI", "SAHARUDDIN.", "MUHAMMAD RASYID", "SUPRIADI", "JULIMAT SIHITE", "EFNI NURYADIN", "ERWIN SAPUTRA ARIANSYAH", "ALVEUS", "SUPRIADI BANDANGAN"]},
    "Pontianak": {"spreadsheet_id": "1VmoWPImNFMjnaIQpBXEVYdMiTEzsz3P4tpmzfA0EMDE", "clusters": ["Sintang", "Singkawang", "Pontianak"], "names": ["ALOYSIUS", "RUDI", "RONIYANTO", "SUKADI", "HAIRIL", "AZMI ASHADIQI", "SUYADI", "ARIEF DARUL IKHWAN", "MUHAMMAD AL FATAH", "YUDIANSYAH", "RAHMAD INDRA IRAWAN", "MATIUS MARTIN", "RYVAEEL DEWANGGA", "AMIRDA ANGGA SAPUTRA", "IZHARUDDIN", "VINSENSIUS YOGI", "GUSTI ARIZAL", "MUHAMMAD MIFTAHUDIN, A.MD", "BAYU ANGGARA PUTRA", "YONI IRAWAN", "SUGANDI", "IRVAN ANDRIYANA", "ALDIANSYAH", "ABANG HAMDANI", "ABANG KUSDIANSYAH", "SUMAN", "SANGGARA ISMARAWARI", "IBIN", "VALENTINUS PETRO", "DWI KURNIAWAN ISMANTO", "ARISAFRIADI", "DONATUS DONI", "NUR AHMAD KARDIYANTO", "AGRI PERDANA", "AKHSANUL FIKI", "ALI ALAMSYAH", "MUHAMMAD FIRZHA GIANNI HARSYA", "RICKY ARDILAY", "FAISAL", "WIJI SANTOSO", "HISYAM MUTHOYIB", "ARIF RAHMAN NUGROHO", "TOTOK SUGIARTO", "PURWANDI SETIAWAN", "JULIANTO BHAKTI PUTRO, SH", "ILHAMMUDIN", "AGUNG", "ROSIDI", "ABRAR ELZAH FATHALIF", "HENDRI YULIANSYAH", "JAMIL", "GORO SUKARTONO", "OKTAPIANUS JUMIN", "ONNIE SYAEFUDDIN", "BUDI", "ULUL AMRY", "RUHIAT, A.MD", "SUPIANDI", "WAHYUDI", "SUHENDRIK", "M. ARKAM", "SYAFRI APRIJAL", "ARIANTO SUMANTRI", "TUTU AGE ANDIKA", "VIRANDA SAPTA, A.MD", "TOTO HERMANSYAH", "KURNIAWAN", "ROBI ISKANDAR MASDIANSYAH", "MUTIIN CHANDRA", "MISJANI", "KHAIRUL FARISD", "ANDRA", "DODI RATMAYANTO", "WAWAN DARYANA", "MISWARDI", "JUPRILIAUS PICO", "DEDY PURNOMO", "EDI KURNIAWAN", "DEDE GUNAWAN", "WANDALA JAGOARDI PANDALO", "KARIYADI", "REZQI AL BARQAH", "FIRMANSYAH, SP"]}
}
LIST_KEPERLUAN = ["", "Tshoot", "Backup", "Support", "PM", "Program BCP", "Program Quikwin", "Program G348T", "Pengiriman Material SPMS", "Pembelian Material","Transportasi Air"]

# ==========================================
# 2. FUNGSI INTI & CACHING 
# ==========================================
def parse_date(date_str):
    try: return datetime.strptime(str(date_str).strip(), "%d/%m/%Y").date()
    except: return datetime(1970, 1, 1).date()

def clean_nominal(val):
    if pd.isna(val) or val == "": return 0
    v = str(val).replace('Rp', '').replace(' ', '').strip()
    if v.endswith(',00'): v = v[:-3]
    if v.endswith('.00'): v = v[:-3]
    v = v.replace('.', '').replace(',', '')
    try: return int(v)
    except: return 0

def clean_coord(val):
    try:
        if pd.isna(val) or val == "": return 0.0
        return float(str(val).replace(',', '.').strip())
    except: return 0.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def decode_polyline(polyline_str):
    index, lat, lng, coordinates = 0, 0, 0, []
    while index < len(polyline_str):
        changes = {'lat': 0, 'lng': 0}
        for unit in ['lat', 'lng']:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20: break
            changes[unit] = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += changes['lat']; lng += changes['lng']
        coordinates.append([lng / 100000.0, lat / 100000.0])
    return coordinates

def get_route_and_distance(lon1, lat1, lon2, lat2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=simplified"
        res = requests.get(url, timeout=5).json()
        if res.get("code") == "Ok":
            dist_km = res["routes"][0]["distance"] / 1000
            poly = decode_polyline(res["routes"][0]["geometry"])
            return dist_km, poly
    except: pass
    dist_km = haversine(lat1, lon1, lat2, lon2) * 1.3 
    return dist_km, [[lon1, lat1], [lon2, lat2]]

@st.cache_resource
def get_credentials():
    with open("credentials.json", "w") as f: f.write(st.secrets["gcp_json"])
    return Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

@st.cache_data(ttl=300)
def fetch_spreadsheet_data(spreadsheet_id):
    client = gspread.authorize(get_credentials()).open_by_key(spreadsheet_id)
    ws_names = [SHEET_REQUEST, SHEET_PJB, SHEET_UM, SHEET_APP, "Rekap PJB"]
    data = {}
    for name in ws_names:
        try: data[name] = client.worksheet(name).get_all_values()
        except: data[name] = []
    return data

@st.cache_data(ttl=600)
def fetch_jabatan_sdm():
    """ Mengambil List Role/Jabatan secara live dari Sheet SDM """
    try:
        SPREADSHEET_ID_SDM = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
        client = gspread.authorize(get_credentials())
        sheet = client.open_by_key(SPREADSHEET_ID_SDM).worksheet("SDM")
        data = sheet.get_all_values()
        roles = set()
        for row in data[1:]: # Mulai dari baris 2 (mengabaikan header)
            if len(row) > 2 and str(row[2]).strip() != "":
                roles.add(str(row[2]).strip().upper())
        return sorted(list(roles))
    except Exception as e:
        st.error(f"⚠️ Gagal menarik data Jabatan dari SDM: {e}")
        return []

def get_nop_by_name(nama_target):
    """ Fungsi pembersih untuk mencari NOP berdasarkan Nama (Anti Case-Sensitive & Anti Spasi) """
    nama_clean = str(nama_target).strip().upper()
    for nop, data in MASTER_DATA.items():
        list_nama_master = [n.strip().upper() for n in data["names"]]
        if nama_clean in list_nama_master:
            return nop
    return "NONE"

def parse_status_tool(status_raw):
    """ Standarisasi klasifikasi status kondisi tools agar tidak miskalkulasi menjadi 0 """
    val = str(status_raw).strip().upper()
    if val in ["OKE", "BAGUS", "V", "TRUE", "ADA", "OK"]: return "OKE"
    elif val in ["NOK", "RUSAK", "X", "FALSE"]: return "NOK"
    elif val in ["NY", "TDK ADA", "TIDAK ADA", "-", "PENDING KUT", "KOSONG", ""]: return "NY"
    elif val in ["NA", "TDK WAJIB"]: return "NA"
    elif val in ["MP", "MILIK PRIBADI"]: return "MP"
    elif val in ["ABM"]: return "ABM"
    return "NY" # Default pengaman

@st.cache_data(ttl=60)
def load_excel_data():
    try:
        df_site = pd.read_excel("Hasil_910_Site.xlsx").fillna(0)
        site_dict = df_site.set_index('Site ID')[['Latitude Tujuan', 'Longtitude Tujuan']].to_dict('index')
        site_list = df_site['Site ID'].astype(str).tolist()
    except: site_dict, site_list = {}, []
    
    tim_dict = {}
    try:
        df_tim = pd.read_excel("lonlat tim.xlsx").fillna(0)
        for _, row in df_tim.iterrows():
            nama_key = str(row['Nama']).strip().upper()
            tim_dict[nama_key] = {
                'Latitude': row.get('Latitude', 0), 
                'Longtitude': row.get('Longtitude', 0)
            }
    except: pass
        
    list_nopol = []
    try:
        df_nopol = pd.read_csv("DATA NOPOL MOBIL DAN GENSET NOP PLK.csv", sep=None, engine='python')
        if 'NOPOL' not in df_nopol.columns and 'PIC' not in df_nopol.columns:
            df_nopol.columns = df_nopol.iloc[0].astype(str).str.strip()
            df_nopol = df_nopol[1:].reset_index(drop=True)
            
        df_nopol = df_nopol.fillna("")
        if 'NOPOL' in df_nopol.columns:
            list_nopol_raw = df_nopol['NOPOL'].astype(str).unique().tolist()
            list_nopol = sorted([n for n in list_nopol_raw if n.strip() not in ["", "0", "nan", "None", "NOPOL"]])
            for _, row in df_nopol.iterrows():
                if 'PIC' in df_nopol.columns:
                    pic_name = str(row['PIC']).strip().upper()
                    nopol_val = str(row['NOPOL']).strip()
                    if pic_name:
                        if pic_name not in tim_dict:
                            tim_dict[pic_name] = {'Latitude': 0, 'Longtitude': 0}
                        tim_dict[pic_name]['NOPOL'] = nopol_val
    except Exception: pass
    return site_dict, site_list, tim_dict, list_nopol

def get_user_tickets_status(nama, req_rows, pjb_rows, app_rows):
    if nama == "-- Pilih Nama --" or nama == "": return [], [], [], []
    req_tickets = {}
    for r in req_rows[1:]:
        if len(r) > 5 and r[5].strip().upper() == nama.strip().upper():
            tk_raw = r[3].strip().upper()
            if tk_raw != "":
                req_tickets[tk_raw] = r[1]
                
    pjb_tickets = {r[21].strip().upper() for r in pjb_rows[1:] if len(r) > 21 and r[4].strip().upper() == nama.strip().upper() and r[21].strip() != ""}
    pjb_app_status = {}
    for r in app_rows[1:]:
        if len(r) > 5 and r[3] == "Verifikasi PJB":
            tiket_app = r[2].strip().upper()
            if tiket_app != "":
                pjb_app_status[tiket_app] = {"status": r[5].strip(), "catatan": r[6] if len(r)>6 else ""}

    outstanding_all, outstanding_lock, aging_august, history = [], [], [], []
    today = datetime.now().date()
    
    for tkt, tgl in req_tickets.items():
        if tkt not in pjb_tickets:
            outstanding_all.append(tkt)
            req_date = parse_date(tgl)
            if req_date >= CUTOFF_DATE: outstanding_lock.append(tkt)
            
            aging_days = (today - req_date).days
            if req_date.month == 8 and aging_days > 3:
                aging_august.append(tkt)
                history.append({"Tiket": tkt, "Tanggal": tgl, "Status": f"🚨 Telat {aging_days} Hari"})
            else:
                history.append({"Tiket": tkt, "Tanggal": tgl, "Status": "🔴 Menunggu PJB (Belum Input)"})
        else:
            app_data = pjb_app_status.get(tkt, {"status": "APPROVED", "catatan": ""})
            if app_data["status"] == "PENDING":
                outstanding_all.append(tkt)
                outstanding_lock.append(tkt)
                history.append({"Tiket": tkt, "Tanggal": tgl, "Status": "⏳ PJB Menunggu Verifikasi Admin"})
            elif app_data["status"] == "REJECTED":
                outstanding_all.append(tkt)
                outstanding_lock.append(tkt)
                history.append({"Tiket": tkt, "Tanggal": tgl, "Status": f"❌ PJB DITOLAK: {app_data['catatan']}"})
            else:
                history.append({"Tiket": tkt, "Tanggal": tgl, "Status": "🟢 PJB Selesai & Approved"})
            
    return outstanding_all, outstanding_lock, aging_august, sorted(history, key=lambda x: x["Status"], reverse=True)

def upload_foto(file):
    if file is None: return ""
    try:
        encoded = base64.b64encode(file.getvalue()).decode('utf-8')
        return cloudinary.uploader.upload(f"data:{file.type};base64,{encoded}", resource_type="auto").get("secure_url") 
    except Exception: return ""

def append_data(sheet_name, data, spreadsheet_id):
    gspread.authorize(get_credentials()).open_by_key(spreadsheet_id).worksheet(sheet_name).append_row(data)
    fetch_spreadsheet_data.clear()

def update_approval_status(spreadsheet_id, row_index, new_status, remark="-"):
    try:
        client = gspread.authorize(get_credentials()).open_by_key(spreadsheet_id)
        ws = client.worksheet(SHEET_APP)
        ws.update_cell(row_index + 1, 6, new_status)
        ws.update_cell(row_index + 1, 7, remark)
        fetch_spreadsheet_data.clear()
    except Exception as e:
        st.error(f"Terjadi kendala saat update ke Google Sheets. (Code: {e})")

# ==========================================
# 3. SIDEBAR & NAVIGASI 
# ==========================================
if 'page' not in st.session_state: st.session_state.page = "🏠 Hub Menu Utama"

try: st.sidebar.image("koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp", use_container_width=True)
except: st.sidebar.markdown("<h2 style='text-align:center; font-weight:900;'>KUT SYSTEM</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr>", unsafe_allow_html=True)

if st.sidebar.button("🏠 Home Dashboard", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()

st.sidebar.markdown("### 📊 MENU ADMIN")
st.sidebar.text_input("🔑 Password Akses Analitik:", type="password", key="admin_password")
if st.session_state.get("admin_password") in AUTHORIZED_PASSWORDS:
    st.sidebar.success("✅ Akses Admin Terbuka")
    if st.sidebar.button("🛡️ Approval Center", use_container_width=True): st.session_state.page = "🛡️ Approval Center"; st.rerun()
    if st.sidebar.button("📊 Neraca / Buku Kas", use_container_width=True): st.session_state.page = "📊 Neraca / Buku Kas"; st.rerun()
    if st.sidebar.button("📈 Live Monitoring", use_container_width=True): st.session_state.page = "📈 Live Monitoring"; st.rerun()
    if st.sidebar.button("🛠️ Tracker & SDM", use_container_width=True): st.session_state.page = "🛠️ Tracker Tools & SDM"; st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 CEK STATUS TIKET")
cek_nop = st.sidebar.selectbox("📂 Area", ["-- Pilih Area --"] + list(MASTER_DATA.keys()))
if cek_nop != "-- Pilih Area --":
    cek_nama = st.sidebar.selectbox("👤 Petugas", ["-- Pilih Nama --"] + MASTER_DATA[cek_nop]["names"])
    if st.sidebar.button("Cari Histori"):
        if cek_nama != "-- Pilih Nama --" and cek_nama != "":
            data_cek = fetch_spreadsheet_data(MASTER_DATA[cek_nop]["spreadsheet_id"])
            out_all, out_lock, aging_august, hist_tkt = get_user_tickets_status(cek_nama, data_cek[SHEET_REQUEST], data_cek[SHEET_PJB], data_cek[SHEET_APP])
            if hist_tkt:
                st.sidebar.dataframe(pd.DataFrame(hist_tkt), hide_index=True)
                if aging_august:
                    st.sidebar.warning(f"🔔 PENGINGAT AGING: Ada {len(aging_august)} tiket tertunda >3 Hari. Mohon segera lakukan PJB!")
                if out_all: 
                    st.sidebar.error(f"⚠️ {len(out_all)} Tiket memblokir status Anda (Belum PJB / Ditolak / Pending Verifikasi).")
                else: st.sidebar.success("✅ Seluruh tiket aman dan Approved!")
            else: st.sidebar.info("Tidak ada data.")

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; color: #64748B; font-size: 0.85rem; font-weight: bold; margin-top:20px;'>Created by Okta Pradika<br>v4.0 Enterprise Edition</div>", unsafe_allow_html=True)


# ==========================================
# PAGE 0: HUB MENU UTAMA
# ==========================================
if st.session_state.page == "🏠 Hub Menu Utama":
    st.markdown("""
        <style>
            section.main div[data-testid="column"] div[data-testid="stButton"] > button {
                height: 180px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="padding: 10px 0 40px 0; text-align:center;">
            <h1 style="font-size: 2.8rem; font-weight: 900; color: #0F2027; margin-bottom: 5px;">Si<span style="color: #4FACFE;">RAPI</span> Enterprise</h1>
            <p style="color: #64748B; font-size: 1.1rem; font-weight:600;">Sistem Rekapitulasi Anggaran Pertanggungjawaban Informasi.</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💸\nREQUEST DANA\nPengajuan & Estimasi", use_container_width=True): st.session_state.page = "📝 Form Request Dana"; st.rerun()
    with c2:
        if st.button("✅\nPJB OPERASIONAL\nRealisasi & Kalkulasi", use_container_width=True): st.session_state.page = "✅ Form PJB Operasional"; st.rerun()
    with c3:
        if st.button("🛡️\nAPPROVAL CENTER\nVerifikasi Admin", use_container_width=True): 
            if st.session_state.get("admin_password") in AUTHORIZED_PASSWORDS: st.session_state.page = "🛡️ Approval Center"; st.rerun()
            else: st.error("Silakan login Admin di Sidebar terlebih dahulu.")
            
    st.markdown("<br>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("📊\nBUKU BESAR / NERACA\nHistori Kas (Admin)", use_container_width=True): 
            if st.session_state.get("admin_password") in AUTHORIZED_PASSWORDS: st.session_state.page = "📊 Neraca / Buku Kas"; st.rerun()
            else: st.error("Silakan login Admin di Sidebar.")
    with c5:
        if st.button("📈\nLIVE MONITORING\nBurn Rate & Tracker", use_container_width=True): 
            if st.session_state.get("admin_password") in AUTHORIZED_PASSWORDS: st.session_state.page = "📈 Live Monitoring"; st.rerun()
            else: st.error("Silakan login Admin di Sidebar.")
    with c6:
        if st.button("🛠️\nTRACKER TOOLS & SDM\nKondisi & Kelengkapan", use_container_width=True): 
            if st.session_state.get("admin_password") in AUTHORIZED_PASSWORDS: st.session_state.page = "🛠️ Tracker Tools & SDM"; st.rerun()
            else: st.error("Silakan login Admin di Sidebar.")

# ==========================================
# PAGE 1: FORM REQUEST DANA
# ==========================================
elif st.session_state.page == "📝 Form Request Dana":
    st.markdown("<div class='header-card'><h2>📝 PORTAL PENGAJUAN DANA</h2><p>Operational System - Input Pengajuan Baru</p></div>", unsafe_allow_html=True)
    
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    with col_nav2:
        if st.button("👉 Lanjut ke Form PJB", type="primary", use_container_width=True): st.session_state.page = "✅ Form PJB Operasional"; st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    nop = st.selectbox("📌 1. Pilih Database Regional (NOP)", [""] + list(MASTER_DATA.keys()))
    
    if nop != "":
        st.markdown("<div class='section-title'>📋 2. Informasi Petugas & Tiket</div>", unsafe_allow_html=True)
        target_ss = MASTER_DATA[nop]["spreadsheet_id"]
        data_all = fetch_spreadsheet_data(target_ss)
        req_r, pjb_r, app_r = data_all[SHEET_REQUEST], data_all[SHEET_PJB], data_all[SHEET_APP]
        
        all_requested_tickets = [r[3].strip().upper() for r in req_r[1:] if len(r) > 3]
        site_dict, site_list, tim_dict, list_nopol = load_excel_data()
        auto_lat_tujuan, auto_long_tujuan, auto_lat_brgkt, auto_long_brgkt = "0", "0", "0", "0"

        status_app_motor = "NONE"
        motor_limit_lock = False

        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.date_input("Tanggal Pengajuan")
            cluster = st.selectbox("Cluster Regional", [""] + MASTER_DATA[nop]["clusters"])
            nama = st.selectbox("Nama Petugas / Pemohon (PIC Utama)", [""] + MASTER_DATA[nop]["names"])
            
            nama_lookup = nama.strip().upper()
            
            out_all, out_lock, aging_august, hist_cek = get_user_tickets_status(nama, req_r, pjb_r, app_r)
            if aging_august:
                st.warning(f"🔔 PENGINGAT: Sdr/i {nama}, Anda memiliki **{len(aging_august)}** tiket bulan Agustus yang sudah lewat >3 Hari belum di-PJB. Jadikan ini prioritas!")
            
            for hc in hist_cek:
                if "DITOLAK" in hc["Status"]:
                    st.error(f"⚠️ {hc['Tiket']} {hc['Status']} -> HARAP REVISI PJB!")
                elif "Review Admin" in hc["Status"]:
                    st.warning(f"⏳ {hc['Tiket']} Sedang Dalam Verifikasi Admin.")

            default_bank, default_no_rek = "BNI", ""
            if nama_lookup != "" and nama_lookup in tim_dict:
                auto_lat_brgkt, auto_long_brgkt = str(tim_dict[nama_lookup].get("Latitude", "0")), str(tim_dict[nama_lookup].get("Longtitude", "0"))
                for r in reversed(req_r[1:]): 
                    if len(r) > 18 and str(r[5]).strip().upper() == nama_lookup:
                        if str(r[17]).strip() in ["BNI", "BCA", "MANDIRI", "BRI"]:
                            default_bank, default_no_rek = str(r[17]).strip(), str(r[18]).strip(); break
                            
            is_locked_user = len(out_lock) > 0
            tiket = st.text_input("Nomor Tiket SWFM (WAJIB)")
            is_duplicate = (tiket.strip().upper() in all_requested_tickets) and tiket.strip() != ""
            role = st.selectbox("Role Jabatan", ["-- Pilih Role --", "PM", "TE", "MBP", "CME"])
            
            if nop == "Palangkaraya" and len(site_list) > 0:
                site_id = st.selectbox("ID Site / Lokasi", [""] + site_list)
                if site_id != "-- Pilih Site ID --" and site_id in site_dict:
                    auto_lat_tujuan, auto_long_tujuan = str(site_dict[site_id].get("Latitude Tujuan", "0")), str(site_dict[site_id].get("Longtitude Tujuan", "0"))
            else: site_id = st.text_input("ID Site / Lokasi")
            
        with col2:
            keperluan = st.selectbox("Klasifikasi Keperluan Dana", LIST_KEPERLUAN)
            jns_kendaraan = st.selectbox("Jenis Kendaraan / Peralatan", ["", "Mobil", "Motor", "Genset", "Lainnya"])
            
            tim_bareng = []
            tim_terkunci = []
            if jns_kendaraan.lower() == "mobil":
                st.markdown("<div style='background-color:#F8FAFC; padding:15px; border-radius:10px; border-left: 5px solid #3B82F6; margin-bottom: 15px;'><b>🚙 Info Perjalanan Mobil</b></div>", unsafe_allow_html=True)
                list_nama_tim = [n for n in MASTER_DATA[nop]["names"] if n.strip().upper() != nama_lookup and n != ""]
                tim_bareng = st.multiselect("👥 Pilih Rekan Tim yang Berangkat Bersama (Opsional)", list_nama_tim)
                
                if role in ["TE", "MBP", "CME"] and tim_bareng:
                    for member in tim_bareng:
                        _, m_out_lock, _, _ = get_user_tickets_status(member, req_r, pjb_r, app_r)
                        if len(m_out_lock) > 0: 
                            tim_terkunci.append(member)
            
            kebutuhan = 0
            jenis_bahan_bakar = ""
            motor_anomali = False
            total_motor_this_month = 0
            
            if jns_kendaraan.lower() == "motor":
                st.markdown("<div style='background-color:#E0F2FE; padding:15px; border-radius:10px; border-left: 5px solid #0284C7; margin-bottom: 15px;'><b>🏍️ Kalkulasi BBM Motor Spesifik</b></div>", unsafe_allow_html=True)
                k_tangki = st.number_input("Kapasitas Tangki (Liter)", min_value=0.0, step=0.1)
                h_satuan = st.number_input("Harga Satuan BBM (Rp/Liter)", min_value=0, step=500)
                l_butuh = st.number_input("Berapa Liter Kebutuhan?", min_value=0.0, step=0.1)
                
                kebutuhan = int(l_butuh * h_satuan)
                st.info(f"💰 Estimasi Kebutuhan Dana (Otomatis): **Rp {kebutuhan:,.0f}**")
                jenis_bahan_bakar = st.selectbox("Pilih Jenis BBM (Wajib)", ["", "Pertalite", "Pertamax"])
                final_bbm = f"{jns_kendaraan} - {jenis_bahan_bakar}" if jenis_bahan_bakar else jns_kendaraan
                
                if l_butuh > k_tangki and k_tangki > 0:
                    motor_anomali = True
                    st.error("🚨 ANOMALI DANA REQUEST: Pengisian liter melebihi kapasitas tangki! TOLONG SESUAIKAN KEBUTUHAN DAN KEAKTUALAN.")
                
                current_month_str = datetime.now().strftime("%m/%Y")
                for r in req_r[1:]:
                    if len(r) > 10:
                        try:
                            tgl_req = parse_date(r[1])
                            if tgl_req.strftime("%m/%Y") == current_month_str and str(r[5]).strip().upper() == nama_lookup:
                                if "motor" in str(r[10]).lower():
                                    total_motor_this_month += clean_nominal(r[9])
                        except: pass
                
                if (total_motor_this_month + kebutuhan) > 500000:
                    st.error(f"⚠️ LIMIT MOTOR TERCAPAI: Total request BBM Motor Anda bulan ini telah mencapai limit. Limit digunakan memblokir tombol simpan di bawah.")
                    
                    for r in reversed(app_r):
                        if len(r) > 5 and str(r[2]).strip().upper() == tiket.strip().upper() and r[3] == "Limit Motor":
                            status_app_motor = str(r[5]).strip().upper()
                            break
                    
                    if status_app_motor == "APPROVED":
                        st.success("✅ Request kelebihan limit telah disetujui Admin. Anda dapat melanjutkan Form ke bawah.")
                    else:
                        motor_limit_lock = True
                        
            elif jns_kendaraan.lower() in ["mobil", "genset"]:
                jenis_bahan_bakar = st.selectbox("Pilih Jenis BBM (Wajib)", ["", "Pertalite", "Pertamax", "Dexlite", "Bio Solar", "Pertamina Dex"])
                final_bbm = f"{jns_kendaraan} - {jenis_bahan_bakar}" if jenis_bahan_bakar else jns_kendaraan
                kebutuhan = st.number_input("Estimasi Kebutuhan Dana (Rp)", min_value=0, step=1000)
            else:
                final_bbm = jns_kendaraan
                kebutuhan = st.number_input("Estimasi Kebutuhan Dana (Rp)", min_value=0, step=1000)
            
            auto_nopol = ""
            if nama_lookup != "" and nama_lookup in tim_dict:
                auto_nopol = str(tim_dict[nama_lookup].get("NOPOL", "")).strip()
                if auto_nopol in ["nan", "0", "None"]: auto_nopol = ""
                
            if role in ["PM", "MBP", "CME"]:
                if auto_nopol != "": plat = st.text_input("Plat Nomor Kendaraan (Otomatis)", value=auto_nopol, disabled=True)
                else: plat = st.text_input("Plat Nomor Kendaraan / ID Genset (Ketik Manual)")
            elif role != "-- Pilih Role --":
                plat_options = ["-- Pilih NOPOL --"] + list_nopol + ["Lainnya (Ketik Manual)"]
                plat_choice = st.selectbox("Pilih Plat Nomor Kendaraan", plat_options)
                if plat_choice == "Lainnya (Ketik Manual)": plat = st.text_input("Ketik Plat Nomor Manual")
                else: plat = "" if plat_choice == "-- Pilih NOPOL --" else plat_choice
            else:
                plat = st.text_input("Plat Nomor Kendaraan / ID Genset")
                
            plat_clean = plat.strip().replace(" ", "").upper()
            
            last_indikator = 0
            if plat_clean != "" and jns_kendaraan.lower() in ["mobil", "motor", "genset"]:
                for r in reversed(pjb_r[1:]): 
                    if len(r) > 12:
                        history_plat = str(r[12]).strip().replace(" ", "").upper()
                        if history_plat == plat_clean:
                            try: 
                                last_indikator = int(clean_nominal(r[10]))
                                break
                            except: pass

            if jns_kendaraan.lower() == "genset":
                st.info(f"⏱️ Histori PJB: RH Genset terakhir untuk plat/ID **{plat}** adalah **{last_indikator}**")
                label_indikator = "Input RH Genset Awal (Hour)"
            elif jns_kendaraan.lower() in ["mobil", "motor"]:
                st.info(f"🛣️ Histori PJB: KM Kendaraan terakhir untuk plat **{plat}** adalah **{last_indikator}**")
                label_indikator = "Input KM Awal Kendaraan"
            else: label_indikator = "Indikator Awal (Ketik 0 jika tidak relevan)"
                
            km_awal = st.number_input(label_indikator, min_value=0, value=last_indikator)
            deskripsi = st.text_area("Deskripsi Pekerjaan / Justifikasi")
            
            if tim_bareng:
                deskripsi_final = deskripsi + f"\n\n[Berangkat bersama tim: {', '.join(tim_bareng)}]"
            else:
                deskripsi_final = deskripsi

        is_vehicle = jns_kendaraan.lower() in ['mobil', 'motor']
        st.markdown("<div class='section-title'>📍 3. Rute Peta (Satelit) & Keuangan</div>", unsafe_allow_html=True)
        if not is_vehicle: st.info("ℹ️ Pengisian Koordinat Maps dikunci (0) karena kategori bukan Mobil/Motor.")
        
        col3, col4 = st.columns(2)
        with col3:
            lat_berangkat = st.text_input("Latitude Berangkat (Auto)", value=auto_lat_brgkt if is_vehicle else "0", disabled=not is_vehicle)
            long_berangkat = st.text_input("Longitude Berangkat (Auto)", value=auto_long_brgkt if is_vehicle else "0", disabled=not is_vehicle)
            bank_idx = ["BNI", "BCA", "MANDIRI", "BRI"].index(default_bank) if default_bank in ["BNI", "BCA", "MANDIRI", "BRI"] else 0
            rek_penerima = st.selectbox("Bank Penerima / E-Wallet", ["BNI", "BCA", "MANDIRI", "BRI"], index=bank_idx)
        with col4:
            lat_tujuan = st.text_input("Latitude Tujuan (Auto)", value=auto_lat_tujuan if is_vehicle else "0", disabled=not is_vehicle)
            long_tujuan = st.text_input("Longitude Tujuan (Auto)", value=auto_long_tujuan if is_vehicle else "0", disabled=not is_vehicle)
            no_rek = st.text_input("Nomor Rekening Tujuan", value=default_no_rek)
            nominal_tf = st.number_input("Total Nominal Transfer (Rp)", min_value=0, step=1000)

        jarak_final_text, invalid_coords = "", False
        if is_vehicle:
            c_lat1, c_lon1 = clean_coord(lat_berangkat), clean_coord(long_berangkat)
            c_lat2, c_lon2 = clean_coord(lat_tujuan), clean_coord(long_tujuan)
            if c_lat1 != 0 and c_lon1 != 0 and c_lat2 != 0 and c_lon2 != 0:
                with st.spinner("Satelit sedang menarik data jalan raya..."):
                    jarak_km_oneway, poly_coords = get_route_and_distance(c_lon1, c_lat1, c_lon2, c_lat2)
                jarak_km_pp = jarak_km_oneway * 2
                bbm_req = (jarak_km_pp / 7) if jns_kendaraan.lower() == 'mobil' else (jarak_km_pp / 15)
                jarak_final_text = f"{jarak_km_pp:.1f} Km (PP)"
                
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"<div class='metric-3d'><div class='metric-title'>Jarak Tempuh (PP)</div><div class='metric-value'>{jarak_final_text}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-3d'><div class='metric-title'>BBM Estimasi (PP)</div><div class='metric-value'>{bbm_req:.1f} Liter</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-3d'><div class='metric-title'>Tipe BBM</div><div class='metric-value'>{(jenis_bahan_bakar or '-').upper()}</div></div>", unsafe_allow_html=True)
            else: invalid_coords = True

        st.markdown("<div class='section-title'>📸 4. Bukti Lampiran Fisik</div>", unsafe_allow_html=True)
        c_up1, c_up2 = st.columns(2)
        with c_up1: foto_km = st.file_uploader("Upload Foto KM / RH Genset Awal", type=["jpg", "png", "jpeg"])
        with c_up2: foto_evidance = st.file_uploader("Upload Foto Kendaraan/Pekerjaan", type=["jpg", "png", "jpeg"])
        
        form_invalid = (nama == "" or cluster == "" or role == "-- Pilih Role --" or keperluan == "" or jns_kendaraan == "")
        izin_lanjut = True
        
        if is_duplicate:
            st.warning("⚠️ DATA DUPLIKAT: Sistem mendeteksi Tiket ini sudah diinput.")
            if not st.checkbox("✅ Ya, saya yakin data ini aman (Revisi/Baru)."): izin_lanjut = False

        if is_locked_user or motor_anomali or motor_limit_lock or len(tim_terkunci) > 0 or (is_duplicate and not izin_lanjut):
            if is_locked_user: st.error(f"⛔ AKSES DITOLAK: Sdr. {nama} dilarang Request Dana karena masih memiliki tiket PENDING Verifikasi, DITOLAK Admin, atau Belum di-PJB!")
            if motor_anomali: st.error("⛔ AKSES DITOLAK: Liter Kebutuhan melebih Kapasitas Tangki Motor.")
            if len(tim_terkunci) > 0: st.error(f"⛔ AKSES DITOLAK: Rekan setim yang Anda bawa ({', '.join(tim_terkunci)}) memiliki PJB yang bermasalah/pending! Minta mereka verifikasi terlebih dahulu (Kecuali Role PM).")
            
            if motor_limit_lock:
                st.markdown("<div style='background-color:#FFE4E6; padding:20px; border-radius:10px; border-left: 5px solid #E11D48; margin-top:15px; margin-bottom: 25px;'>", unsafe_allow_html=True)
                if status_app_motor == "PENDING":
                    st.warning("⏳ **STATUS APPROVAL:** Request kelebihan Limit Motor Anda sedang MENUNGGU VERIFIKASI Admin. Tolong hubungi Admin untuk cek Approval Center.")
                elif status_app_motor == "REJECTED":
                    st.error("❌ **STATUS APPROVAL:** DITOLAK Admin. Silakan kurangi nominal pengajuan atau hubungi Atasan.")
                    if st.button("🔄 Ajukan Ulang Approval Limit Motor", type="primary", use_container_width=True):
                        append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nama, tiket.strip().upper(), "Limit Motor", kebutuhan, "PENDING", f"Bulan ini: Rp {total_motor_this_month:,.0f}"], target_ss)
                        st.success("Terkirim ulang ke Admin!")
                        time.sleep(2); st.rerun()
                else:
                    st.error("🚨 **AKSES DITOLAK (LIMIT MOTOR):** Anda mencapai batas limit BBM Motor bulanan (>500k). Anda HARUS meminta persetujuan khusus dari Admin untuk melanjutkan tiket ini.")
                    if not tiket.strip():
                        st.warning("⚠️ **WAJIB:** Ketik [Nomor Tiket] pada form di atas terlebih dahulu agar tombol 'Minta Approval' muncul di sini.")
                    else:
                        if st.button("🚨 Minta Approval Kelebihan Limit ke Admin Sekarang", type="primary", use_container_width=True):
                            append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nama, tiket.strip().upper(), "Limit Motor", kebutuhan, "PENDING", f"Bulan ini: Rp {total_motor_this_month:,.0f}"], target_ss)
                            st.success("Berhasil diajukan ke Admin! Silakan tunggu Admin melakukan Approve di Approval Center.")
                            time.sleep(2.5); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            if st.text_input("🔑 Password Khusus (Bypass Admin):", type="password") in AUTHORIZED_PASSWORDS:
                if st.button("💡 Paksakan Kirim Request Dana (Bypass)", type="primary"):
                    if form_invalid or not tiket.strip() or invalid_coords: st.error("Lengkapi form!")
                    else:
                        with st.spinner("Processing..."):
                            data_req = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tanggal.strftime("%d/%m/%Y"), nop, tiket, cluster, nama, role, site_id, keperluan, kebutuhan, final_bbm, deskripsi_final, str(km_awal), jarak_final_text, lat_berangkat, long_berangkat, plat, rek_penerima, no_rek, nominal_tf, upload_foto(foto_km), upload_foto(foto_evidance), lat_tujuan, long_tujuan]
                            append_data(SHEET_REQUEST, data_req, target_ss)
                            st.balloons(); st.success("🎉 Berhasil Bypass!"); time.sleep(2); st.rerun()
        else:
            if st.button("📤 Kirim Form Request Dana", type="primary"):
                if form_invalid or not tiket.strip() or invalid_coords: st.error("Lengkapi form!")
                else:
                    with st.spinner("Memproses ke Database..."):
                        data_req = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tanggal.strftime("%d/%m/%Y"), nop, tiket, cluster, nama, role, site_id, keperluan, kebutuhan, final_bbm, deskripsi_final, str(km_awal), jarak_final_text, lat_berangkat, long_berangkat, plat, rek_penerima, no_rek, nominal_tf, upload_foto(foto_km), upload_foto(foto_evidance), lat_tujuan, long_tujuan]
                        append_data(SHEET_REQUEST, data_req, target_ss)
                        st.balloons(); st.success("🎉 Data Anda Berhasil Dikirim!"); time.sleep(2.5); st.rerun()

# ==========================================
# PAGE 2: FORM PJB OPERASIONAL 
# ==========================================
elif st.session_state.page == "✅ Form PJB Operasional":
    st.markdown("<div class='header-card'><h2>✅ PORTAL PJB (PENYELESAIAN)</h2><p>Lengkapi nota realisasi untuk diverifikasi oleh Admin.</p></div>", unsafe_allow_html=True)
    
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    
    nop_cari = st.selectbox("📂 1. Pilih Database (NOP):", ["-- Pilih NOP --"] + list(MASTER_DATA.keys()))
    
    if nop_cari != "-- Pilih NOP --":
        target_ss = MASTER_DATA[nop_cari]["spreadsheet_id"]
        data_all = fetch_spreadsheet_data(target_ss)
        req_r, pjb_r, app_r = data_all[SHEET_REQUEST], data_all[SHEET_PJB], data_all[SHEET_APP]
        
        pjb_tickets_all = {str(r[21]).strip().upper() for r in pjb_r[1:] if len(r) > 21}
        
        status_verif_dict = {}
        catatan_verif_dict = {}
        for r in app_r[1:]:
            if len(r) > 5 and r[3] == "Verifikasi PJB":
                tk = str(r[2]).strip().upper()
                if tk != "":
                    status_verif_dict[tk] = str(r[5]).strip()
                    if len(r) > 6: catatan_verif_dict[tk] = r[6]
        
        st.markdown("<div class='section-title'>🔍 2. Identifikasi Tim & Tarik Data</div>", unsafe_allow_html=True)
        col_id1, col_id2 = st.columns([2, 2])
        with col_id1: nama_pjb = st.selectbox("👤 Pilih Nama Anda:", ["-- Pilih Nama --"] + MASTER_DATA[nop_cari]["names"])
        
        if nama_pjb != "-- Pilih Nama --":
            out_all, out_lock, aging_august, hist_cek = get_user_tickets_status(nama_pjb, req_r, pjb_r, app_r)
            if aging_august:
                st.warning(f"🔔 NOTIFIKASI: Anda memiliki **{len(aging_august)}** tiket bulan Agustus yang tertunda lebih dari 3 hari. Segera diselesaikan!")
            for hc in hist_cek:
                if "DITOLAK" in hc["Status"]: st.error(f"⚠️ HARAP REVISI PJB: {hc['Tiket']} {hc['Status']}")
                elif "Review Admin" in hc["Status"]: st.warning(f"⏳ PENDING VERIFIKASI: {hc['Tiket']}")

        with col_id2: pass_nominal = st.text_input("🔑 Akses Nominal (Admin):", type="password")
            
        pending_list, pending_options = [], []
        for r in req_r[1:]:
            if len(r)>5 and str(r[3]).strip() != "":
                tk = str(r[3]).strip().upper()
                nm = str(r[5]).strip().upper()
                
                is_ready_to_pjb = False
                if tk not in pjb_tickets_all:
                    is_ready_to_pjb = True
                elif status_verif_dict.get(tk) == "REJECTED":
                    is_ready_to_pjb = True 
                    
                if is_ready_to_pjb:
                    item = {"Tanggal": r[1], "Nama": r[5], "No Tiket": tk, "Kategori": r[10] if len(r)>10 else "", "Keperluan": r[8] if len(r)>8 else ""}
                    if pass_nominal == "B0924649": item["Nominal Request"] = f"Rp {clean_nominal(r[9]):,.0f}" if len(r)>9 else "Rp 0"
                    if nama_pjb != "-- Pilih Nama --":
                        if nm == nama_pjb.strip().upper(): pending_list.append(item); pending_options.append(tk)
                    else: pending_list.append(item)
        
        if pending_list: st.dataframe(pd.DataFrame(pending_list), hide_index=True, use_container_width=True)
        else: st.success("💎 Seluruh tiket clear atau sedang dalam review Admin!")
        
        col_s2, col_s3 = st.columns([3, 1])
        with col_s2: 
            pilihan_tiket = st.selectbox("🎫 Pilih Nomor Tiket Pending:", ["-- Pilih Tiket --"] + pending_options + ["-- Ketik Manual --"]) if pending_options else "-- Ketik Manual --"
            cari_tiket = st.text_input("Ketik Manual:") if pilihan_tiket == "-- Ketik Manual --" else ("" if pilihan_tiket == "-- Pilih Tiket --" else pilihan_tiket)
        
        valid_cari_tiket = str(cari_tiket).strip().upper()

        with col_s3: 
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Tarik Data", type="primary", use_container_width=True) and valid_cari_tiket:
                ditemukan = None
                for r in req_r[1:]:
                    if len(r) > 3 and str(r[3]).strip().upper() == valid_cari_tiket:
                        ditemukan = {"NOP": r[2], "Cluster": r[4], "Nama": r[5], "Role": r[6], "Site": r[7], "Keperluan": r[8], "BBM": r[10], "Desc": r[11], "KMAwal": clean_nominal(r[12]) if len(r)>12 else 0, "NominalReq": clean_nominal(r[9]) if len(r)>9 else 0, "Jarak": r[13] if len(r)>13 else "", "Plat": r[16] if len(r)>16 else ""}
                if ditemukan: st.session_state.pjb_data = ditemukan; st.success("🎉 Data Ditarik!")
                else: st.session_state.pjb_data = None; st.error("❌ Tidak ditemukan.")

        if st.session_state.get("pjb_data"):
            d = st.session_state.pjb_data
            st.markdown("<div class='section-title'>💸 Validasi Budget & Bukti Transfer</div>", unsafe_allow_html=True)
            f_transfer = st.file_uploader("Upload Foto Bukti Transfer Dana (WAJIB untuk mengakses Form PJB)", type=["jpg", "png", "jpeg"])
            
            if f_transfer is None:
                st.warning("⚠️ **AKSES TERKUNCI:** Silakan upload Bukti Transfer dari Admin terlebih dahulu agar form pengisian PJB terbuka.")
            else:
                st.success("✅ Bukti Transfer terlampir. Akses form PJB terbuka.")
                st.markdown("<div class='section-title'>🔒 Rincian Terkunci (Sistem)</div>", unsafe_allow_html=True)
                c_a, c_b = st.columns(2)
                with c_a:
                    tgl_pjb = st.date_input("Tanggal PJB")
                    st.text_input("Nama Petugas", d["Nama"], disabled=True)
                    st.text_input("Kategori & Plat", f'{d["BBM"]} - {d["Plat"]}', disabled=True)
                with c_b:
                    st.text_input("Site ID Tujuan", d["Site"], disabled=True)
                    st.text_input("Keperluan", d["Keperluan"], disabled=True)
                    nominal_pjb = st.number_input("Nominal PJB Terpakai (Otomatis Dikunci)", value=int(d["NominalReq"]), disabled=True)

                st.markdown("<div class='section-title'>📝 Realisasi Lapangan & KM/RH</div>", unsafe_allow_html=True)
                c_c, c_d = st.columns(2)
                is_genset = "genset" in str(d["BBM"]).lower()
                label_akhir = "RH Genset Akhir" if is_genset else "KM Akhir Kendaraan"
                info_text = "Total Jam Backup (RH)" if is_genset else "Total Perjalanan (KM)"
                icon_text = "⏱️" if is_genset else "🛣️"
                
                with c_c:
                    km_akhir = st.number_input(f"{label_akhir} (Wajib Update)", min_value=int(d["KMAwal"]), value=int(d["KMAwal"]))
                    total_km_tempuh = km_akhir - int(d["KMAwal"])
                    st.info(f"{icon_text} Kalkulasi {info_text}: **{total_km_tempuh}**")
                with c_d:
                    tot_liter = st.text_input("Total Liter BBM/Material", value="0")
                    harga_satuan = st.number_input("Harga Satuan (BBM/Material)", min_value=0, step=500)
                    tot_nilai_nota = st.number_input("Total Fisik Sesuai Nota (Rp)", min_value=0, step=1000)
                
                st.markdown("<div class='section-title'>📸 Lampiran Bukti (Foto)</div>", unsafe_allow_html=True)
                p1, p2, p3 = st.columns(3)
                with p1: f_isi = st.file_uploader("Evidance Pengisian", type=["jpg","png"]); f_nota_bbm = st.file_uploader("Nota BBM", type=["jpg","png"])
                with p2: f_mat = st.file_uploader("Foto Material", type=["jpg","png"]); f_notamat = st.file_uploader("Nota Material", type=["jpg","png"])
                with p3: f_inap = st.file_uploader("Nota Penginapan", type=["jpg","png"]); f_kerja = st.file_uploader("Evidance Pekerjaan", type=["jpg","png"]); f_km = st.file_uploader("Foto KM/RH Akhir (Disanding)", type=["jpg","png"])
                
                is_bbm_anomali = is_genset and ("dexlite" in str(d["BBM"]).lower() or "bio solar" in str(d["BBM"]).lower()) and (harga_satuan > 28000)
                if is_bbm_anomali:
                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.error("🚨 DETEKSI ANOMALI GENSET: Harga Dexlite/Bio Solar melebihi batas wajar.")
                    status_approval = "NONE"
                    for r in reversed(app_r):
                        if len(r) > 5 and str(r[2]).strip().upper() == valid_cari_tiket and "Genset" in str(r[3]): 
                            status_approval = str(r[5]).strip()
                            break
                    
                    if status_approval == "PENDING":
                        st.warning("⏳ Status: **MENUNGGU APPROVAL Harga**. Silakan hubungi atasan.")
                        st.stop()
                    elif status_approval == "REJECTED":
                        st.error("❌ Status: **DITOLAK!** Harga satuan tidak disetujui. Ajukan ulang.")
                        if st.button("Ajukan Ulang Approval Harga"):
                            append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), d["Nama"], valid_cari_tiket, f"Genset Anomali ({d['BBM']})", harga_satuan, "PENDING", "-"], target_ss)
                            st.success("Terkirim ulang!"); time.sleep(1.5); st.rerun()
                        st.stop()
                    elif status_approval == "APPROVED": st.success("✅ Harga Anomali telah di-APPROVE.")
                    else:
                        if st.button("🚨 Ajukan Approval Harga ke Admin", type="primary"):
                            append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), d["Nama"], valid_cari_tiket, f"Genset Anomali ({d['BBM']})", harga_satuan, "PENDING", "-"], target_ss)
                            st.success("Sistem berhasil mencatat!"); time.sleep(2); st.rerun()
                        st.stop()

                st.markdown("<br>", unsafe_allow_html=True)
                is_double_input = any(len(r)>21 and str(r[21]).strip().upper() == valid_cari_tiket for r in pjb_r[1:])
                status_v = status_verif_dict.get(valid_cari_tiket, "NONE")
                catatan_v = catatan_verif_dict.get(valid_cari_tiket, "")
                
                if status_v == "PENDING":
                    st.warning("⏳ PJB tiket ini sedang dalam proses review Admin. Anda belum bisa mensubmit/mengubah data saat ini.")
                    st.stop()
                elif is_double_input:
                    if status_v == "REJECTED":
                        st.error(f"❌ PJB Anda sebelumnya DITOLAK! Alasan: **{catatan_v}**")
                        st.info("Silakan perbaiki data/foto yang direquest oleh Admin dan Submit Ulang (Revisi) di bawah ini.")
                        if st.button("🚀 Submit Ulang (Revisi PJB)", type="primary", use_container_width=True):
                            with st.spinner("Mengupload foto revisi..."):
                                data_pjb = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tgl_pjb.strftime("%d/%m/%Y"), d["NOP"], d["Cluster"], d["Nama"], d["Role"], d["Site"], d["Keperluan"], d["BBM"], d["Desc"], str(km_akhir), nominal_pjb, d["Plat"], upload_foto(f_isi), upload_foto(f_nota_bbm), upload_foto(f_km), upload_foto(f_mat), upload_foto(f_notamat), upload_foto(f_inap), upload_foto(f_kerja), tot_nilai_nota, valid_cari_tiket, tot_liter, harga_satuan, str(total_km_tempuh), "", "", upload_foto(f_transfer)]
                                append_data(SHEET_PJB, [(r+[""]*28)[:28] for r in [data_pjb]][0], target_ss)
                                append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), d["Nama"], valid_cari_tiket, "Verifikasi PJB", nominal_pjb, "PENDING", "-"], target_ss)
                                st.balloons(); st.success("🎉 PJB Revisi Berhasil Dikirim ke Admin!"); st.session_state.pjb_data = None; time.sleep(2.5); st.rerun()
                    else:
                        st.warning("⚠️ **PERINGATAN DOUBLE INPUT:** Tiket ini sudah pernah di-PJB dan diverifikasi.")
                        bypass_pwd = st.text_input("🔑 Masukkan Password Bypass (Koordokt):", type="password")
                        if bypass_pwd == "Koordokt":
                            st.success("✅ Password benar! Anda diizinkan melakukan PJB duplikat.")
                            if st.button("🚀 Sahkan Pelaporan PJB (Bypass)", type="primary", use_container_width=True):
                                with st.spinner("Mengupload foto..."):
                                    data_pjb = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tgl_pjb.strftime("%d/%m/%Y"), d["NOP"], d["Cluster"], d["Nama"], d["Role"], d["Site"], d["Keperluan"], d["BBM"], d["Desc"], str(km_akhir), nominal_pjb, d["Plat"], upload_foto(f_isi), upload_foto(f_nota_bbm), upload_foto(f_km), upload_foto(f_mat), upload_foto(f_notamat), upload_foto(f_inap), upload_foto(f_kerja), tot_nilai_nota, valid_cari_tiket, tot_liter, harga_satuan, str(total_km_tempuh), "", "", upload_foto(f_transfer)]
                                    append_data(SHEET_PJB, [(r+[""]*28)[:28] for r in [data_pjb]][0], target_ss)
                                    append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), d["Nama"], valid_cari_tiket, "Verifikasi PJB", nominal_pjb, "PENDING", "-"], target_ss)
                                    st.balloons(); st.success("🎉 Laporan Berhasil Ditutup!"); st.session_state.pjb_data = None; time.sleep(2.5); st.rerun()
                        else: st.error("Password salah.")
                else:
                    if st.button("🚀 Sahkan Pelaporan PJB (Kirim ke Admin)", type="primary", use_container_width=True):
                        with st.spinner("Mengupload foto dan memproses PJB..."):
                            data_pjb = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tgl_pjb.strftime("%d/%m/%Y"), d["NOP"], d["Cluster"], d["Nama"], d["Role"], d["Site"], d["Keperluan"], d["BBM"], d["Desc"], str(km_akhir), nominal_pjb, d["Plat"], upload_foto(f_isi), upload_foto(f_nota_bbm), upload_foto(f_km), upload_foto(f_mat), upload_foto(f_notamat), upload_foto(f_inap), upload_foto(f_kerja), tot_nilai_nota, valid_cari_tiket, tot_liter, harga_satuan, str(total_km_tempuh), "", "", upload_foto(f_transfer)]
                            append_data(SHEET_PJB, [(r+[""]*28)[:28] for r in [data_pjb]][0], target_ss)
                            append_data(SHEET_APP, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), d["Nama"], valid_cari_tiket, "Verifikasi PJB", nominal_pjb, "PENDING", "-"], target_ss)
                            st.balloons(); st.success("🎉 PJB Berhasil Dikirim untuk Verifikasi Admin!"); st.session_state.pjb_data = None; time.sleep(2.5); st.rerun()

# ==========================================
# PAGE 3: APPROVAL CENTER (KHUSUS ADMIN)
# ==========================================
elif st.session_state.page == "🛡️ Approval Center":
    st.markdown("<div class='header-card'><h2>🛡️ APPROVAL CENTER</h2><p>Pusat Verifikasi PJB & Harga BBM Anomali</p></div>", unsafe_allow_html=True)
    if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    
    if st.session_state.get("admin_password") not in AUTHORIZED_PASSWORDS:
        st.error("⛔ AKSES TERKUNCI: Halaman khusus Admin.")
    else:
        nop_admin = st.selectbox("📂 Wilayah (NOP):", ["-- Pilih NOP --"] + list(MASTER_DATA.keys()))
        if nop_admin != "-- Pilih NOP --":
            target_ss = MASTER_DATA[nop_admin]["spreadsheet_id"]
            data_all = fetch_spreadsheet_data(target_ss)
            app_r, pjb_r = data_all[SHEET_APP], data_all[SHEET_PJB]
            
            pending_anomali, pending_pjb = [], []
            if len(app_r) > 0:
                for idx, r in enumerate(app_r):
                    if len(r) > 5 and str(r[5]).strip() == "PENDING":
                        item = {
                            "Row Index": idx, "Waktu": str(r[0]), "Nama": str(r[1]), "No Tiket": str(r[2]), 
                            "Jenis Pengajuan": str(r[3]), "Nominal": f"Rp {clean_nominal(r[4]):,.0f}", 
                            "Status": str(r[5]).strip(), "Keterangan": str(r[6]) if len(r) > 6 else "-"
                        }
                        if r[3] == "Verifikasi PJB": pending_pjb.append(item)
                        else: pending_anomali.append(item)
            
            tab_app1, tab_app2 = st.tabs(["📸 Verifikasi Foto PJB", "⛽ Approval Limit Motor & Anomali BBM"])
            with tab_app1:
                st.markdown("### 🔍 Daftar Tunggu Verifikasi PJB")
                if pending_pjb:
                    st.dataframe(pd.DataFrame(pending_pjb).drop(columns=["Row Index"]), hide_index=True, use_container_width=True)
                    target_tiket_pjb = st.selectbox("Pilih Tiket PJB untuk divalidasi:", [p["No Tiket"] for p in pending_pjb], key="sel_pjb")
                    
                    pjb_target = None
                    for r in reversed(pjb_r[1:]):
                        if len(r) > 21 and str(r[21]).strip().upper() == target_tiket_pjb.strip().upper(): pjb_target = r; break
                            
                    if pjb_target:
                        st.markdown("<div style='background:#F8FAFC; padding:15px; border-radius:10px; margin-bottom:15px;'><b>Bukti Terlampir:</b></div>", unsafe_allow_html=True)
                        cf1, cf2 = st.columns(2)
                        with cf1:
                            if len(pjb_target) > 14 and pjb_target[14]: st.image(pjb_target[14], caption="Kolom O: Foto Nota BBM / Material", use_container_width=True)
                            else: st.info("Tidak ada Foto Nota.")
                        with cf2:
                            if len(pjb_target) > 19 and pjb_target[19]: st.image(pjb_target[19], caption="Kolom T: Foto Evidance Pekerjaan", use_container_width=True)
                            else: st.info("Tidak ada Foto Pekerjaan.")
                    
                    st.markdown("### ⚡ Eksekusi Keputusan")
                    ca1, ca2 = st.columns(2)
                    with ca1: action_pjb = st.radio("Keputusan Admin:", ["Setujui PJB (APPROVE)", "Tolak PJB (REJECT)"], key="rad_pjb")
                    with ca2: remark_pjb = st.text_input("Catatan / Remark (Wajib diisi jika ditolak):", key="rem_pjb")
                    
                    if st.button("Proses Verifikasi PJB", type="primary"):
                        if "REJECT" in action_pjb and not remark_pjb.strip():
                            st.error("⚠️ Mohon berikan Alasan / Catatan Penolakan agar tim tahu bagian yang harus direvisi.")
                        else:
                            target_indices = [p["Row Index"] for p in pending_pjb if p["No Tiket"] == target_tiket_pjb]
                            new_status = "APPROVED" if "APPROVE" in action_pjb else "REJECTED"
                            with st.spinner("Memperbarui database..."):
                                for idx in target_indices:
                                    update_approval_status(target_ss, idx, new_status, remark_pjb if remark_pjb else "-")
                                st.success(f"✅ Tiket {target_tiket_pjb} berhasil di-{new_status}!")
                                time.sleep(2); st.rerun()
                else: st.success("✅ Tidak ada PJB yang menunggu verifikasi (Inbox Kosong).")
                    
            with tab_app2:
                st.markdown("### 🚨 Daftar Tunggu Approval Harga / Limit Motor")
                if pending_anomali:
                    st.dataframe(pd.DataFrame(pending_anomali).drop(columns=["Row Index"]), hide_index=True, use_container_width=True)
                    ce1, ce2 = st.columns(2)
                    with ce1: target_tiket_anm = st.selectbox("Pilih Tiket / Pengajuan:", [p["No Tiket"] for p in pending_anomali], key="sel_anm")
                    with ce2: action_anm = st.radio("Keputusan Admin:", ["Setujui (APPROVE)", "Tolak (REJECT)"], key="rad_anm")
                    
                    if st.button("Proses Keputusan Harga/Limit", type="primary"):
                        target_indices = [p["Row Index"] for p in pending_anomali if p["No Tiket"] == target_tiket_anm]
                        new_status = "APPROVED" if "APPROVE" in action_anm else "REJECTED"
                        with st.spinner("Memperbarui database..."):
                            for idx in target_indices:
                                update_approval_status(target_ss, idx, new_status, "-")
                            st.success(f"✅ Pengajuan untuk {target_tiket_anm} berhasil di-{new_status}!")
                            time.sleep(2); st.rerun()
                else: st.success("✅ Tidak ada anomali harga atau limit yang menggantung.")

# ==========================================
# PAGE 4: NERACA & BUKU KAS
# ==========================================
elif st.session_state.page == "📊 Neraca / Buku Kas":
    st.markdown("<div class='header-card'><h2>📊 BUKU BESAR & LAPORAN KEUANGAN</h2><p>Rekapitulasi Kas Regional</p></div>", unsafe_allow_html=True)
    if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    if st.session_state.get("admin_password") not in AUTHORIZED_PASSWORDS: st.error("⛔ AKSES TERKUNCI")
    else:
        nop_admin = st.selectbox("📂 Wilayah (NOP):", ["-- Pilih NOP --"] + list(MASTER_DATA.keys()))
        if nop_admin != "-- Pilih NOP --":
            target_ss = MASTER_DATA[nop_admin]["spreadsheet_id"]
            data_all = fetch_spreadsheet_data(target_ss)
            req_r, pjb_r, um_r, rekap_r = data_all[SHEET_REQUEST], data_all[SHEET_PJB], data_all[SHEET_UM], data_all["Rekap PJB"]
            
            st.markdown("<div class='section-title'>📥 1. Input Kas Masuk (Uang Muka)</div>", unsafe_allow_html=True)
            with st.form("form_tambah_um"):
                c_u1, c_u2, c_u3 = st.columns([1, 2, 1])
                with c_u1: tgl_um = st.date_input("Tanggal UM Masuk")
                with c_u2: um_nobis = st.text_input("Ref Dokumen UM")
                with c_u3: um_nominal = st.number_input("Nominal (Rp)", min_value=0, step=1000)
                if st.form_submit_button("💾 Rekam Kas Masuk"):
                    if um_nominal > 0 and um_nobis:
                        append_data(SHEET_UM, [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), tgl_um.strftime("%d/%m/%Y"), um_nobis, um_nominal], target_ss); st.success("✅ Terekam!"); time.sleep(1); st.rerun()
            
            unique_periode = list(set([r[16].strip() for r in rekap_r[1:] if len(r) > 16 and r[16].strip() != ""]))
            st.markdown("<div class='section-title'>📅 2. Laporan & Ekstraksi Data</div>", unsafe_allow_html=True)
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1: start_date = st.date_input("Dari Tanggal")
            with c_d2: end_date = st.date_input("Sampai")
            with c_d3: filter_q_neraca = st.selectbox("📌 Filter Sinkronisasi Kolom Q", ["-- Semua Periode --"] + sorted(unique_periode))
            
            if st.button("🔄 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Mengkompilasi Data & Visualisasi..."):
                    tot_um = 0
                    if len(um_r) > 1:
                        padded_um = [(r + [""] * 4)[:4] for r in um_r[1:]]
                        df_um = pd.DataFrame(padded_um, columns=["Waktu", "Tanggal", "Deskripsi", "Nominal"])
                        df_um['Tanggal_Real'] = pd.to_datetime(df_um['Tanggal'], format='%d/%m/%Y', errors='coerce')
                        start_ts, end_ts = pd.to_datetime(start_date), pd.to_datetime(end_date)
                        mask = (df_um['Tanggal_Real'] >= start_ts) & (df_um['Tanggal_Real'] <= end_ts)
                        tot_um = df_um[mask]['Nominal'].apply(clean_nominal).sum()
                    
                    tot_pjb = sum([clean_nominal(r[15]) for r in rekap_r[1:] if len(r) > 16 and (r[16].strip() == filter_q_neraca or filter_q_neraca == "-- Semua Periode --")]) if len(rekap_r)>1 else 0
                    
                    t1, t2, t3 = st.tabs(["📊 Executive Summary", "📓 Buku Besar (Ledger)", "📈 Visualisasi Pengeluaran"])
                    with t1:
                        m1, m2, m3 = st.columns(3)
                        m1.markdown(f"<div class='metric-3d'><div class='metric-title'>Total Kas Masuk</div><div class='metric-value'>Rp {tot_um:,.0f}</div></div>", unsafe_allow_html=True)
                        m2.markdown(f"<div class='metric-3d'><div class='metric-title'>Total Penyerapan</div><div class='metric-value'>Rp {tot_pjb:,.0f}</div></div>", unsafe_allow_html=True)
                        m3.markdown(f"<div class='metric-3d'><div class='metric-title'>Sisa Kas (Equity)</div><div class='metric-value'>Rp {tot_um - tot_pjb:,.0f}</div></div>", unsafe_allow_html=True)
                    with t2:
                        if len(pjb_r) > 1:
                            df_p = pd.DataFrame([(r + [""] * 28)[:28] for r in pjb_r[1:]], columns=["Waktu","Tanggal","N","C","Nama","R","S","Keperluan","B","D","K","Nominal","Pl","u1","u2","u3","u4","u5","u6","u7","NN","NoTiket","Lt","Hs","TKM_RH","u8","u9","BuktiTF"])
                            df_p['Nominal'] = df_p['Nominal'].apply(clean_nominal)
                            st.dataframe(df_p[['Tanggal', 'NoTiket', 'Nama', 'Keperluan', 'TKM_RH', 'Nominal']], use_container_width=True)
                            csv = df_p.to_csv(index=False).encode('utf-8')
                            st.download_button(label="📥 Export Ledger ke CSV/Excel", data=csv, file_name=f"BukuBesar_{nop_admin}.csv", mime='text/csv', use_container_width=True)
                    with t3:
                        if len(pjb_r) > 1:
                            df_grafik = df_p.groupby("Keperluan")["Nominal"].sum().reset_index()
                            st.bar_chart(df_grafik.set_index("Keperluan"))

# ==========================================
# PAGE 5: LIVE MONITORING
# ==========================================
elif st.session_state.page == "📈 Live Monitoring":
    st.markdown("<div class='header-card'><h2>📈 LIVE MONITORING DASHBOARD</h2><p>Sistem Analisa Kas, Daily Pengeluaran, Tracker Satelit, & Anomali BBM</p></div>", unsafe_allow_html=True)
    if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    
    if st.session_state.get("admin_password") not in AUTHORIZED_PASSWORDS: st.error("⛔ AKSES TERKUNCI")
    else:
        nop_live = st.selectbox("🌐 Pilih Market (NOP):", ["-- Pilih NOP --"] + list(MASTER_DATA.keys()))
        if nop_live != "-- Pilih NOP --":
            data_all = fetch_spreadsheet_data(MASTER_DATA[nop_live]["spreadsheet_id"])
            um_r, rekap_r, pjb_r, req_r, app_r = data_all[SHEET_UM], data_all["Rekap PJB"], data_all[SHEET_PJB], data_all[SHEET_REQUEST], data_all[SHEET_APP]
            
            t1, t2, t3 = st.tabs(["💰 1. Sisa Kas, Daily Graph & Kategori BBM", "🚨 2. Record Anomali & Warning Tim", "🕵️ 3. Evaluasi Kinerja (Track KM/RH)"])
            with t1:
                total_um = sum([clean_nominal(r[3]) for r in um_r[1:] if len(r)>3]) if len(um_r)>1 else 0
                tot_serap = sum([clean_nominal(r[15]) for r in rekap_r[1:] if len(r)>15]) if len(rekap_r)>1 else 0
                sisa_kas = total_um - tot_serap
                burn_rate = (tot_serap / total_um * 100) if total_um > 0 else 0
                
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"<div class='metric-3d'><div class='metric-title'>Total Kas Masuk</div><div class='metric-value'>Rp {total_um:,.0f}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-3d'><div class='metric-title'>Total Penyerapan PJB</div><div class='metric-value'>Rp {tot_serap:,.0f}</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-3d'><div class='metric-title'>Sisa Kas (Burn Rate: {burn_rate:.1f}%)</div><div class='metric-value'>Rp {sisa_kas:,.0f}</div></div>", unsafe_allow_html=True)
                
                if len(pjb_r) > 1:
                    df_pjb_all = pd.DataFrame([(r + [""] * 28)[:28] for r in pjb_r[1:]], columns=["Waktu","Tanggal","N","C","Nama","R","S","Keperluan","BBM","D","KMAkhir","Nominal","Pl","u1","u2","u3","u4","u5","u6","u7","NN","NoTiket","Lt","Hs","TKM_RH","u8","u9","BuktiTF"])
                    df_pjb_all['Nominal_Clean'] = df_pjb_all['Nominal'].apply(clean_nominal)
                    df_pjb_all['Tanggal_PJB'] = pd.to_datetime(df_pjb_all['Tanggal'], format='%d/%m/%Y', errors='coerce')
                    df_daily = df_pjb_all.dropna(subset=['Tanggal_PJB']).groupby('Tanggal_PJB')['Nominal_Clean'].sum().reset_index().sort_values('Tanggal_PJB')
                    
                    if not df_daily.empty:
                        df_daily.columns = ['Tanggal PJB', 'Total Pengeluaran (Rp)_num']
                        st.markdown("#### 📈 Grafik Tren Pengeluaran Harian")
                        st.area_chart(df_daily.set_index('Tanggal PJB')['Total Pengeluaran (Rp)_num'], use_container_width=True)
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            df_daily_tabel = df_daily.copy().sort_values('Tanggal PJB', ascending=False)
                            df_daily_tabel['Tanggal PJB'] = df_daily_tabel['Tanggal PJB'].dt.strftime('%d/%m/%Y')
                            df_daily_tabel['Total Pengeluaran (Rp)'] = df_daily_tabel['Total Pengeluaran (Rp)_num'].apply(lambda x: f"Rp {x:,.0f}")
                            st.dataframe(df_daily_tabel[['Tanggal PJB', 'Total Pengeluaran (Rp)']], hide_index=True, use_container_width=True)
                        with col_d2:
                            df_cat = df_pjb_all.groupby('BBM')['Nominal_Clean'].sum().reset_index().sort_values('Nominal_Clean', ascending=False)
                            if not df_cat.empty:
                                df_cat.columns = ['Jenis BBM / Kategori', 'Total Nominal (Rp)']
                                df_cat['Total Nominal (Rp)'] = df_cat['Total Nominal (Rp)'].apply(lambda x: f"Rp {x:,.0f}")
                                st.dataframe(df_cat, hide_index=True, use_container_width=True)
                else: st.info("Belum ada data PJB untuk direkap.")
            
            with t2:
                warning_list = []
                for pjb in pjb_r[1:]:
                    if len(pjb) > 24:
                        no_tiket = pjb[21]
                        req_match = next((x for x in req_r[1:] if len(x) > 13 and x[3] == no_tiket), None)
                        if req_match:
                            nama_petugas, kategori_bbm = req_match[5], req_match[10]
                            km_awal, km_akhir = int(clean_nominal(req_match[12])), int(clean_nominal(pjb[10]))
                            total_km = km_akhir - km_awal
                            nominal_pjb_val = clean_nominal(pjb[11]) if len(pjb)>11 else clean_nominal(req_match[9])
                            
                            try: liter_val = float(str(pjb[22]).replace(',', '.'))
                            except: liter_val = 0.0
                            
                            is_mobil, is_motor, is_genset = "mobil" in str(kategori_bbm).lower(), "motor" in str(kategori_bbm).lower(), "genset" in str(kategori_bbm).lower()
                            is_boros, ket_status = False, "Normal"
                            if liter_val > 0:
                                ratio = total_km / liter_val
                                if is_mobil and ratio < 7: is_boros, ket_status = True, f"🔴 Mobil Boros ({ratio:.1f} KM/L < 7)"
                                elif is_motor and ratio < 15: is_boros, ket_status = True, f"🔴 Motor Boros ({ratio:.1f} KM/L < 15)"
                            
                            harga_satuan_val = clean_nominal(pjb[23]) if len(pjb)>23 else 0
                            if is_genset and ("dexlite" in str(kategori_bbm).lower() or "bio solar" in str(kategori_bbm).lower()) and harga_satuan_val > 28000:
                                is_boros, ket_status = True, f"🚨 Anomali Harga Genset (Rp {harga_satuan_val:,})"
                                
                            if is_boros: warning_list.append({"Nama Tim": nama_petugas, "Tiket": no_tiket, "Nominal PJB": f"Rp {nominal_pjb_val:,.0f}", "Kategori": kategori_bbm, "Total Jarak/RH": total_km, "Liter": liter_val, "Status Warning": ket_status})
                            
                if warning_list: st.dataframe(pd.DataFrame(warning_list), hide_index=True, use_container_width=True)
                else: st.success("✨ Sempurna! Tidak ada anomali atau pemborosan pada tim wilayah ini.")

            with t3:
                eval_list = []
                for pjb in pjb_r[1:]:
                    if len(pjb) > 24:
                        no_tiket = str(pjb[21]).strip().upper()
                        req_match = next((x for x in req_r[1:] if len(x) > 13 and str(x[3]).strip().upper() == no_tiket), None)
                        if req_match:
                            kategori, jarak_satelit = req_match[10], req_match[13]
                            angka_satelit = 0
                            try:
                                match = re.search(r"([\d\.]+)", str(jarak_satelit))
                                if match: angka_satelit = float(match.group(1))
                            except: pass

                            km_awal, km_akhir = int(clean_nominal(req_match[12])), int(clean_nominal(pjb[10]))
                            total_input_tim = km_akhir - km_awal
                            nominal_pjb_val = clean_nominal(pjb[11]) if len(pjb)>11 else clean_nominal(req_match[9])
                            
                            is_genset, is_mobil, is_motor = "genset" in str(kategori).lower(), "mobil" in str(kategori).lower(), "motor" in str(kategori).lower()
                            liter_val = 0.0
                            if len(pjb) > 22:
                                try: liter_val = float(str(pjb[22]).replace(',', '.'))
                                except: pass
                                
                            status_bbm, analisa_bbm, status_jarak = "-", "-", "🟢 Aman"
                            if liter_val > 0:
                                val_per_liter = total_input_tim / liter_val
                                analisa_bbm = f"{val_per_liter:.1f} {'KM/L' if not is_genset else 'RH/L'}"
                                if is_mobil: status_bbm = "🔴 Boros (< 7 KM/L)" if val_per_liter < 7 else "🟢 Normal"
                                elif is_motor: status_bbm = "🔴 Boros (< 15 KM/L)" if val_per_liter < 15 else "🟢 Normal"
                                else: status_bbm = "⚪ N/A"

                            if not is_genset:
                                if angka_satelit > 0: status_jarak = "🟢 Aman & Wajar" if total_input_tim > angka_satelit else "🟢 Aman"
                                else: status_jarak = "⚪ Data Satelit Kosong"
                            else: status_jarak = "⏱️ (RH Genset)"

                            eval_list.append({"Nama Tim": req_match[5], "Tiket": no_tiket, "Nominal PJB": f"Rp {nominal_pjb_val:,.0f}", "Kategori": kategori, "KM/RH Awal": km_awal, "KM/RH Akhir": km_akhir, "Total Jarak": f"{total_input_tim}", "Jarak Satelit": f"{angka_satelit}" if not is_genset and angka_satelit > 0 else "-", "Status Jarak": status_jarak, "Rasio Aktual": analisa_bbm, "Status Konsumsi": status_bbm})
                
                if eval_list:
                    def highlight_markup(s): return ['background-color: #FEE2E2; color: #DC2626; font-weight: bold' if '🔴' in str(v) else '' for v in s]
                    st.dataframe(pd.DataFrame(eval_list).style.apply(highlight_markup, subset=['Status Jarak', 'Status Konsumsi']), hide_index=True, use_container_width=True)
                else: st.info("Belum ada data realisasi PJB yang dapat disandingkan dengan Satelit.")


# ==========================================
# PAGE 6: TRACKER & SDM (NEW FIX)
# ==========================================
elif st.session_state.page == "🛠️ Tracker Tools & SDM":
    st.markdown("<div class='header-card'><h2>🛠️ TRACKER & SDM MONITORING</h2><p>Filter Makro, Tracking Registrasi & Kondisi Tools Tim</p></div>", unsafe_allow_html=True)
    if st.button("🏠 Kembali ke Home Menu", use_container_width=True): st.session_state.page = "🏠 Hub Menu Utama"; st.rerun()
    
    if st.session_state.get("admin_password") not in AUTHORIZED_PASSWORDS: 
        st.error("⛔ AKSES TERKUNCI: Halaman ini khusus Admin.")
    else:
        st.markdown("### 🔍 Filter Makro & Analisa Kebutuhan")
        
        # 1. Menarik Jabatan dari Sheet SDM (Anti Hardcode)
        with st.spinner("Memuat Filter SDM..."):
            list_jabatan_dinamis = fetch_jabatan_sdm()
        pilihan_jabatan = ["SEMUA JABATAN"] + list_jabatan_dinamis

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1: filter_nop = st.selectbox("🏢 NOP (CABANG):", ["SEMUA NOP"] + list(MASTER_DATA.keys()))
        with col_f2: filter_jabatan = st.selectbox("💼 JABATAN (ROLE):", pilihan_jabatan)
        with col_f3: filter_lokasi = st.selectbox("📍 LOKASI KERJA:", ["SEMUA LOKER"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background: linear-gradient(90deg, #0f172a, #1e293b); padding: 20px; border-radius: 15px; border-left: 5px solid #3b82f6; margin-bottom: 20px;">
                <h3 style="color: white; margin:0;">🎯 TRACKER REGISTRASI TIM (PER NOP)</h3>
                <p style="color: #94a3b8; font-size:0.9rem; margin:0;">Memantau progres input data untuk keseluruhan cabang secara global.</p>
            </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------------
        # ⚠️ CATATAN UNTUK ANDA (OKTA): 
        # Karena saya tidak tahu persis cara Anda mengambil data "tools_tim" dari Spreadsheet sebelumnya, 
        # saya membuatkan MOCKUP TAHAN BANTING. Anda HANYA PERLU memasukkan array/list 'missing_names' 
        # (daftar nama yang belum input) ke bagian di bawah ini dari variabel Spreadsheet Anda.
        # -----------------------------------------------------

        tab_tr1, tab_tr2, tab_tr3 = st.tabs(["🚗 Spesifikasi R2/R4", "⚡ Parameter Genset", "🔧 Inventaris Tools"])
        
        with tab_tr3: # Khusus Tab Inventaris Tools
            # Variabel Penampung Tabel Rincian Tools
            rincian_tools_list = []
            grand_ny, grand_nok, grand_oke = 0, 0, 0
            
            for nop_name, nop_data in MASTER_DATA.items():
                list_semua_tim = nop_data["names"]
                total_tim = len(list_semua_tim)
                
                # --- [GANTI BAGIAN INI DENGAN DATA SPREADSHEET TOOLS ANDA] ---
                # Simulasi: Tim yang sudah input dan yang belum (missing)
                # Misal: Anda cek if nama in daftar_sudah_input_di_sheet
                missing_names = [] 
                tim_sudah_input = []
                
                # [Ini hanya simulasi, hapus blok for ini jika sudah connect spreadsheet]
                for idx, nm in enumerate(list_semua_tim):
                    if idx % 5 == 0: missing_names.append(nm) # Simulasi bbrp nama blm input
                    else: tim_sudah_input.append(nm)
                # --------------------------------------------------------------

                inputted_count = total_tim - len(missing_names)
                pct = int((inputted_count / total_tim) * 100) if total_tim > 0 else 0
                
                # 2. Render Progress Bar & Warning Kurang
                col_pt1, col_pt2 = st.columns([1, 1])
                with col_pt1: st.markdown(f"**NOP {nop_name}**")
                with col_pt2:
                    if len(missing_names) > 0:
                        st.markdown(f"<div style='color: #F87171; font-size: 0.85rem; font-weight: 600; text-align: right;'>⚠️ Kurang {len(missing_names)} Tim (Unik)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='color: #10B981; font-size: 0.85rem; font-weight: 600; text-align: right;'>✅ Selesai Semua</div>", unsafe_allow_html=True)
                
                st.progress(pct)
                
                # 3. Render Desain UI Berjejer Rapi (Pills)
                if len(missing_names) > 0:
                    html_pills = "".join([f"<span style='background-color: #1E293B; color: #94A3B8; padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; border: 1px solid #334155; margin: 4px; display: inline-block;'>{n}</span>" for n in sorted(missing_names)])
                    with st.expander(f"🔍 Rincian {len(missing_names)} Tim Belum Input"):
                        st.markdown(f"<div style='padding: 10px 0;'>{html_pills}</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0; border-color:#cbd5e1'>", unsafe_allow_html=True)

                # --- SIMULASI PEMBACAAN ALGORITMA TABEL RINCIAN ---
                # Anda bisa mengaplikasikan parser pembersih saya (parse_status_tool) ke loop Google Sheets Anda
                for nm in tim_sudah_input:
                    # [Ganti dictionary ini dengan row data dari sheet Tools Anda]
                    # Misal: status_val = row_tools[index_kolom]
                    simulasi_data_tools = {
                        "WORK POSITIONING LANYARD": "NY", "SAFETY CIVIL GLOVE": "OKE", 
                        "SAFETY ELEKTRIK GLOVE": "OKE", "RAIN COAT": "NOK", 
                        "WIRE STRIPPER": " NY", "HELM": "OKE "
                    }
                    
                    jml_ny, jml_nok, jml_oke = 0, 0, 0
                    list_ny, list_nok, list_oke = [], [], []
                    
                    for tool_name, status_val in simulasi_data_tools.items():
                        status_bersih = parse_status_tool(status_val) # PENGAMAN ANTI-0
                        
                        if status_bersih == "OKE":
                            jml_oke += 1; list_oke.append(tool_name); grand_oke += 1
                        elif status_bersih == "NOK":
                            jml_nok += 1; list_nok.append(tool_name); grand_nok += 1
                        elif status_bersih == "NY":
                            jml_ny += 1; list_ny.append(tool_name); grand_ny += 1
                            
                    # Gabungkan menjadi String dengan koma agar cantik
                    str_ny = ", ".join(list_ny) if list_ny else "-"
                    str_nok = ", ".join(list_nok) if list_nok else "-"
                    str_oke = ", ".join(list_oke) if list_oke else "-"
                    
                    rincian_tools_list.append({
                        "Nama Personel": nm, "Cabang NOP": get_nop_by_name(nm), # AUTO FIND NOP YANG BENAR
                        "🔥 Jml NY": jml_ny, "List Tools NY (Pending KUT)": str_ny,
                        "❌ Jml NOK": jml_nok, "List Tools NOK (Rusak)": str_nok,
                        "✅ Jml OKE": jml_oke, "List Tools OKE (Bagus)": str_oke,
                        "NA": 0, "MP": 0, "ABM": 0
                    })

            # TAMPILAN GRAND TOTAL (GAMBAR 3 ATAS)
            st.markdown("<br>", unsafe_allow_html=True)
            col_gt1, col_gt2, col_gt3 = st.columns(3)
            col_gt1.markdown(f"<div style='border:1px solid #F87171; border-radius:10px; padding:15px; text-align:center;'><h5 style='color:#F87171; margin:0;'>🔥 GRAND TOTAL NY (PENDING KUT)</h5><h2 style='color:white; margin:0;'>{grand_ny} Item</h2></div>", unsafe_allow_html=True)
            col_gt2.markdown(f"<div style='border:1px solid #FBBF24; border-radius:10px; padding:15px; text-align:center;'><h5 style='color:#FBBF24; margin:0;'>❌ GRAND TOTAL NOK (RUSAK)</h5><h2 style='color:white; margin:0;'>{grand_nok} Item</h2></div>", unsafe_allow_html=True)
            col_gt3.markdown(f"<div style='border:1px solid #34D399; border-radius:10px; padding:15px; text-align:center;'><h5 style='color:#34D399; margin:0;'>✅ GRAND TOTAL OKE (BAGUS)</h5><h2 style='color:white; margin:0;'>{grand_oke} Item</h2></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # TAMPILAN TABEL PANJANG (WRAP TEXT ANTI TERPOTONG)
            with st.expander("📄 LIHAT TABEL RINCIAN KONDISI TOOLS TIM & NAMA ITEM-NYA", expanded=True):
                if rincian_tools_list:
                    df_rincian = pd.DataFrame(rincian_tools_list)
                    
                    # Filter jika NOP dropdown aktif (opsional)
                    if filter_nop != "SEMUA NOP": df_rincian = df_rincian[df_rincian["Cabang NOP"] == filter_nop]
                    
                    st.dataframe(
                        df_rincian, hide_index=True, use_container_width=True,
                        column_config={
                            "Nama Personel": st.column_config.TextColumn("Nama Personel", width="medium"),
                            "Cabang NOP": st.column_config.TextColumn("Cabang NOP", width="medium"),
                            "List Tools NY (Pending KUT)": st.column_config.TextColumn("List Tools NY (Pending KUT)", width="large"),
                            "List Tools NOK (Rusak)": st.column_config.TextColumn("List Tools NOK (Rusak)", width="large"),
                            "List Tools OKE (Bagus)": st.column_config.TextColumn("List Tools OKE (Bagus)", width="large")
                        }
                    )
                else: st.info("Tidak ada data tools yang ditemukan.")
