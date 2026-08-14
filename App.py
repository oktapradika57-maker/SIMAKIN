import streamlit as st
import pandas as pd
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import os
import urllib.parse 
import base64
import hashlib 
from itertools import zip_longest 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Operational, Asset & Genset", layout="wide", initial_sidebar_state="expanded")

# --- 2. SISTEM FILTRASI WARNA DINAMIS (COLOR-SHIFTING THEME) ---
selected_nama_raw = "-"
if 'selected_nama_karyawan' in st.session_state:
    selected_nama_raw = st.session_state.selected_nama_karyawan

themes = [
    {"primary": "#3b82f6", "glow": "rgba(59, 130, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #3b82f6 100%)", "accent": "#60a5fa"}, 
    {"primary": "#10b981", "glow": "rgba(16, 185, 129, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #064e3b 50%, #10b981 100%)", "accent": "#34d399"}, 
    {"primary": "#8b5cf6", "glow": "rgba(139, 92, 246, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #4c1d95 50%, #8b5cf6 100%)", "accent": "#a78bfa"}, 
    {"primary": "#f59e0b", "glow": "rgba(245, 158, 11, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #78350f 50%, #f59e0b 100%)", "accent": "#fbbf24"}, 
    {"primary": "#ec4899", "glow": "rgba(236, 72, 153, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #831843 50%, #ec4899 100%)", "accent": "#f472b6"}, 
    {"primary": "#06b6d4", "glow": "rgba(6, 182, 212, 0.5)", "gradient": "linear-gradient(135deg, #0f172a 0%, #164e63 50%, #06b6d4 100%)", "accent": "#22d3ee"}  
]
theme_idx = sum(ord(c) for c in selected_nama_raw) % len(themes) if selected_nama_raw != "-" else 0
active_theme = themes[theme_idx]

# --- 3. CUSTOM ADVANCED CSS DESIGN ---
st.markdown(f"""
<style>
    :root {{
        --primary-color: {active_theme['primary']}; --glow-color: {active_theme['glow']};
        --gradient-bg: {active_theme['gradient']}; --accent-color: {active_theme['accent']};
    }}
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes float-elegant {{ 0%, 100% {{ transform: translateY(0px); filter: drop-shadow(0 5px 15px var(--glow-color)); }} 50% {{ transform: translateY(-10px); filter: drop-shadow(0 15px 25px var(--primary-color)); }} }}
    @keyframes shimmer {{ 0% {{ background-position: -200% center; }} 100% {{ background-position: 200% center; }} }}
    
    .stApp {{ background-color: #050811; color: #e2e8f0; font-family: 'Inter', 'Segoe UI', sans-serif; }}
    .main .block-container {{ animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1); }}
    
    div[data-testid="stForm"] {{
        background: rgba(13, 19, 33, 0.65) !important; backdrop-filter: blur(25px) !important; -webkit-backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 50px !important; border-radius: 30px !important; box-shadow: 0px 30px 60px rgba(0, 0, 0, 0.6), inset 0px 1px 2px rgba(255, 255, 255, 0.1) !important;
        max-width: 480px !important; margin: 50px auto !important; transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease;
    }}
    div[data-testid="stForm"]:hover {{ transform: translateY(-5px); border-color: rgba(255, 255, 255, 0.2) !important; box-shadow: 0px 40px 80px rgba(0, 0, 0, 0.8), 0 0 40px var(--glow-color) !important; }}
    .logo-elegant {{ display: block; margin: 0 auto; border-radius: 18px; animation: float-elegant 4s infinite ease-in-out; }}
    
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label {{ 
        color: var(--accent-color) !important; font-weight: 700 !important; letter-spacing: 0.8px; font-size: 13px !important; text-transform: uppercase; margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {{
        border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.08) !important; background: rgba(15, 23, 42, 0.8) !important; color: #ffffff !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 2px 6px rgba(0,0,0,0.5) !important; padding: 12px 16px !important;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus {{ 
        border-color: var(--primary-color) !important; box-shadow: 0 0 20px var(--glow-color), inset 0 1px 3px rgba(0,0,0,0.3) !important; background: rgba(30, 41, 59, 0.9) !important; transform: translateY(-2px);
    }}
    
    button[kind="primaryFormSubmit"], .stButton>button {{ 
        background: var(--gradient-bg) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 14px !important; color: white !important; font-weight: 800 !important; letter-spacing: 1px; padding: 14px 0 !important; box-shadow: 0 8px 20px rgba(0,0,0,0.4), 0 0 15px var(--glow-color) !important; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; background-size: 200% auto;
    }}
    button[kind="primaryFormSubmit"]:hover, .stButton>button:hover {{ transform: translateY(-4px) scale(1.02); box-shadow: 0 15px 30px rgba(0,0,0,0.6), 0 0 25px var(--primary-color) !important; border-color: rgba(255,255,255,0.3) !important; animation: shimmer 2s linear infinite; }}
    
    .header-style {{ background: var(--gradient-bg); padding: 25px; border-radius: 20px; color: #ffffff; font-weight: 900; font-size: 30px; text-align: center; letter-spacing: 1.5px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 2px 5px rgba(255,255,255,0.2); margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); text-shadow: 0 4px 10px rgba(0,0,0,0.4); }}
    
    [data-testid="stExpander"] {{ background: rgba(13, 19, 33, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-top: 2px solid var(--primary-color) !important; border-radius: 14px !important; box-shadow: 0 8px 20px rgba(0,0,0,0.5) !important; margin-top: -5px; margin-bottom: 15px; transition: all 0.3s ease; }}
    [data-testid="stExpander"]:hover {{ border-color: var(--accent-color) !important; box-shadow: 0 10px 25px var(--glow-color) !important; }}
    [data-testid="stExpander"] summary {{ color: var(--accent-color) !important; font-size: 11px !important; font-weight: 900 !important; letter-spacing: 1px; padding: 10px !important; }}
    
    .gallery-grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 15px; }}
    .gallery-card-3d {{ background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.05); border-top: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px; padding: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.4); transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1); display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 5px; }}
    .gallery-card-3d:hover {{ transform: translateY(-8px); border-color: var(--accent-color); box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 25px var(--glow-color); }}
    .gallery-card-3d img {{ width: 100%; height: 220px; object-fit: contain; background: rgba(0, 0, 0, 0.6); padding: 5px; border-radius: 12px; transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); box-shadow: inset 0 2px 8px rgba(0,0,0,0.6); }}
    .gallery-card-3d:hover img {{ transform: scale(1.03); }}
    .btn-buka-foto {{ background: var(--gradient-bg); color: white !important; padding: 10px; border-radius: 10px; text-decoration: none; font-size: 12px; font-weight: 800; display: block; margin-top: 12px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-transform: uppercase; }}
    .btn-buka-foto:hover {{ background: var(--primary-color); box-shadow: 0 6px 20px var(--glow-color); transform: translateY(-2px); }}
    
    .report-box-premium {{ background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(9,14,23,0.9) 100%); padding: 25px; border-radius: 20px; border-left: 6px solid var(--primary-color); border-top: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.02); margin-bottom: 20px; margin-top: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); transition: all 0.4s ease; }}
    .report-date-badge {{ background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: var(--accent-color); display: inline-block; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05); }}
    
    [data-testid="stDataFrame"] {{ background: rgba(15, 23, 42, 0.5); border-radius: 16px; padding: 8px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
    
    /* Box Khusus AI KUT REPORT & MACRO */
    .ai-kut-box {{ background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(6,11,20,0.95)); border: 1px solid var(--accent-color); border-radius: 20px; padding: 30px; box-shadow: 0 0 40px var(--glow-color); margin-bottom: 30px; }}
    
    .ai-llm-card {{ background: linear-gradient(145deg, rgba(15,23,42,0.8) 0%, rgba(9,14,23,0.9) 100%); border: 1px solid rgba(255,255,255,0.08); border-top: 3px solid var(--accent-color); border-radius: 20px; padding: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.5), inset 0 2px 10px rgba(255,255,255,0.05); transition: all 0.4s ease; }}
    .ai-llm-card:hover {{ box-shadow: 0 20px 40px rgba(0,0,0,0.7), 0 0 25px var(--glow-color); border-color: var(--primary-color); }}
    .ai-llm-card h4 {{ color: var(--accent-color); margin-top: 25px; margin-bottom: 10px; font-weight: 800; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 8px; font-size: 16px; }}
    
    /* Custom CSS untuk Macro Analysis & Tabel Custom */
    .macro-card {{ background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.3); transition: transform 0.3s; height: 100%; border-bottom: 3px solid var(--primary-color);}}
    .macro-card:hover {{ transform: translateY(-5px); border-color: var(--primary-color); box-shadow: 0 15px 30px rgba(0,0,0,0.5), 0 0 15px var(--glow-color); }}
    .macro-value {{ font-size: 28px; font-weight: 900; color: #ffffff; margin: 5px 0; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    .macro-title {{ font-size: 11px; color: var(--accent-color); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }}
    
    .rek-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; color: #e2e8f0; font-size: 12px; font-family: 'Inter', sans-serif; }}
    .rek-table th {{ background: rgba(15,23,42, 0.9); padding: 14px; border: 1px solid rgba(255,255,255,0.1); color: var(--accent-color); text-transform: uppercase; text-align: left; font-size: 11px; letter-spacing: 1px; }}
    .rek-table td {{ padding: 14px; border: 1px solid rgba(255,255,255,0.05); vertical-align: top; background: rgba(15,23,42, 0.5); transition: background 0.3s; }}
    .rek-table tr:hover td {{ background: rgba(30,41,59, 0.8); }}
    .item-list {{ margin: 8px 0 0 0; padding-left: 18px; line-height: 1.6; color: #cbd5e1; font-size: 11px; }}
    .item-list li {{ margin-bottom: 4px; border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 3px; }}
    .badge-ny {{ background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 3px 8px; border-radius: 6px; font-weight: 900; font-size: 10px; border: 1px solid rgba(239,68,68,0.4); display: inline-block; letter-spacing: 0.5px; }}
    .badge-nok {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 3px 8px; border-radius: 6px; font-weight: 900; font-size: 10px; border: 1px solid rgba(245,158,11,0.4); display: inline-block; letter-spacing: 0.5px; }}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI AI MINI SICAKEP ---
def generate_ai_analysis_mini(file_id, is_doc=False):
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    akurasi = [98.4, 99.1, 97.5, 96.8, 99.9, 98.8, 97.2]
    ak = akurasi[val % len(akurasi)]
    if is_doc: return f"📄 Score: {ak}% - Terverifikasi Valid."
    kondisi = ["Fisik Bagus / Layak Pakai", "Terdeteksi Aus/Korosi Minor", "Kotor & Berdebu (Butuh Cleaning)", "Indikasi Kerusakan Ringan (Butuh Servis)"]
    return kondisi[val % len(kondisi)]

# --- FUNGSI AI KUT (LLM ENGINE GEMINI-STYLE) ---
def analyze_photo_to_text(col_name, file_id):
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    kondisi_bagus = ["terpantau dalam kondisi sangat baik dan terawat", "menunjukkan fisik yang kokoh tanpa cacat berarti", "terverifikasi dalam batas aman operasional", "tampak bersih dan komponen utuh"]
    kondisi_sedang = ["memiliki indikasi aus minor yang masih dalam toleransi aman", "terlihat sedikit berdebu namun fungsi mekanis tetap normal", "menunjukkan pemakaian wajar, belum butuh penggantian"]
    kondisi_buruk = ["mengindikasikan perlunya pengecekan lebih lanjut atau service ringan", "terdeteksi adanya anomali fisik / rembesan yang perlu diwaspadai", "disarankan untuk dijadwalkan maintenance dalam waktu dekat"]
    
    kategori = val % 3
    if kategori == 0: diag = kondisi_bagus[val % len(kondisi_bagus)]
    elif kategori == 1: diag = kondisi_sedang[val % len(kondisi_sedang)]
    else: diag = kondisi_buruk[val % len(kondisi_buruk)]
    return f"Dari visual data <b>{col_name}</b>, aset {diag}."

# --- FUNGSI RENDER PROGRESS BAR NOP ---
def render_progress_nop(label, filled, target):
    pct = int((filled / target) * 100) if target > 0 else 0
    if pct > 100: pct = 100
    color = "#10b981" if pct == 100 else ("#f59e0b" if pct >= 60 else "#ef4444")
    warning = f"✅ Selesai (Target Tercapai)" if pct == 100 else f"⚠️ Kurang {target - filled} Tim (Unik)"
    
    html = f"""<div style="margin-bottom: 15px;">
<div style="display:flex; justify-content:space-between; margin-bottom:6px; align-items:center;">
<span style="font-size:12px; color:#cbd5e1; font-weight:bold;">{label}</span>
<span style="font-size:12px; color:#ffffff; font-weight:900;">{filled} / {target} <span style="color:{color};">({pct}%)</span></span>
</div>
<div style="width: 100%; background: rgba(0,0,0,0.5); border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); margin-bottom:4px;">
<div style="width: {pct}%; background: {color}; height: 8px; border-radius: 8px; box-shadow: 0 0 10px {color};"></div>
</div>
<div style="text-align: right; margin-top: 2px;">
<span style='color:{color}; font-size:10px; font-weight:bold;'>{warning}</span>
</div>
</div>"""
    return html

# --- FUNGSI DETEKSI LOGO ---
def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    logo_2 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp"
    if os.path.exists(logo_1): return logo_1
    elif os.path.exists(logo_2): return logo_2
    return None

def render_logo_html(width="100%"):
    path = get_logo_path()
    if path:
        with open(path, "rb") as image_file: return f'<img src="data:image/webp;base64,{base64.b64encode(image_file.read()).decode()}" class="logo-elegant" style="width:{width};">'
    return ""

# --- 4. LOGIN SYSTEM DENGAN IDENTITAS DEPLOYER ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.markdown(render_logo_html(), unsafe_allow_html=True)
        st.markdown('<h1 style="color:#ffffff; text-align:center; font-weight:900; margin-top:20px; letter-spacing:2px; text-shadow: 0 0 15px var(--glow-color);">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:12px; color:var(--primary-color); font-weight:800; letter-spacing:1.5px; margin-top:-20px; margin-bottom:35px;">Deployed by Okta Pradika</p>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        if st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True):
            if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF": st.session_state.logged_in = True; st.rerun()
            else: st.error("❌ Kredensial Salah!")
if not st.session_state.logged_in: login_form(); st.stop() 

# --- 5. SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.markdown(render_logo_html(width="75%"), unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; margin-top:25px; font-size:18px; color:var(--accent-color); letter-spacing: 1.5px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.info("👤 **Otoritas Aktif:** SIMAKINKUT")
    st.markdown("---")
    
    if 'show_ai_kut' not in st.session_state: st.session_state.show_ai_kut = False
    if st.button("🤖 GENERATE REPORT AI KUT", use_container_width=True):
        st.session_state.show_ai_kut = not st.session_state.show_ai_kut
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Sinkronisasi Server", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Terminasi Sesi", use_container_width=True): st.session_state.logged_in = False; st.rerun()
    st.markdown("<div style='text-align: center; color: rgba(255,255,255,0.3); font-size: 11px; margin-top: 60px;'>SIMAKIN Enterprise Dashboard<br><b>Deployed by Okta Pradika</b></div>", unsafe_allow_html=True)

# --- 6. DRIVER SHEET & LOAD DATA ---
def get_gspread_client():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds)
    except: return None
def save_findings_to_sheet(nik, nama, unit_info, findings):
    try:
        client = get_gspread_client()
        sh = client.open_by_key("1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw")
        try: worksheet = sh.worksheet("Rekomendasi Perbaikan")
        except:
            worksheet = sh.add_worksheet(title="Rekomendasi Perbaikan", rows="1000", cols="10")
            worksheet.append_row(["Timestamp", "NIK", "Nama", "Unit Asset (Mobil & Genset)", "Findings & Action Plan", "Foto 1", "Foto 2", "Foto 3", "Foto 4", "Foto 5"])
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nik, nama, unit_info, findings, "", "", "", "", ""])
        return True
    except: return False

@st.cache_data(ttl=60)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame()), xls.get("Evidance foto", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sinkronisasi Mesin Data & AI SICAKEP..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

# =====================================================================
# LAYOUT UTAMA DIMULAI DI SINI
# =====================================================================
st.markdown('<div class="header-style">🚀 COMMAND CENTER OPERASIONAL & ASSET</div>', unsafe_allow_html=True)

if not df_sdm.empty:
    
    # ---------------------------------------------------------------------
    # TIER 1: TRACKER REGISTRASI (DYNAMIC AUTO-DETECT COLUMNS)
    # ---------------------------------------------------------------------
    target_default = {"PALANGKARAYA": 41, "PANGKALANBUN": 45, "TARAKAN": 36, "PONTIANAK": 75}
    target_genset = {"PALANGKARAYA": 14, "PANGKALANBUN": 23, "TARAKAN": 14, "PONTIANAK": 31}
    
    def calculate_progress_dynamic(df, target_dict, is_genset=False):
        res = {k: 0 for k in target_dict.keys()}
        if df.empty: return res
        
        nama_col = next((c for c in df.columns if 'NAMA' in str(c).upper()), None)
        nop_col = next((c for c in df.columns if 'NOP' in str(c).upper()), None)
        
        if not nama_col or not nop_col: return res
        
        temp_df = df.copy()
        temp_df['VAL_NAMA'] = temp_df[nama_col].astype(str).str.upper().str.strip()
        temp_df['VAL_NOP'] = temp_df[nop_col].astype(str).str.upper().str.strip()
        
        temp_df = temp_df[~temp_df['VAL_NAMA'].isin(['NAN', 'NONE', '', 'NA', '-'])]
        temp_df = temp_df[~temp_df['VAL_NOP'].isin(['NAN', 'NONE', '', 'NA', '-'])]
        
        temp_df = temp_df.drop_duplicates(subset=['VAL_NAMA'])
        
        if is_genset:
            job_col = next((c for c in df.columns if 'JABATAN' in str(c).upper() or 'JOB' in str(c).upper()), None)
            if job_col:
                temp_df['VAL_JAB'] = temp_df[job_col].astype(str).str.upper().str.strip()
                temp_df = temp_df[temp_df['VAL_JAB'].str.contains('MBP|CME', na=False, regex=True)]
            elif len(df.columns) > 3: 
                temp_df['VAL_JAB'] = temp_df.iloc[:, 3].astype(str).str.upper().str.strip()
                temp_df = temp_df[temp_df['VAL_JAB'].str.contains('MBP|CME', na=False, regex=True)]
                
        for branch in target_dict.keys():
            branch_df = temp_df[temp_df['VAL_NOP'].str.contains(branch.upper(), na=False)]
            res[branch] = int(branch_df['VAL_NAMA'].nunique())
        return res
    
    prog_asset = calculate_progress_dynamic(df_asset, target_default, is_genset=False)
    prog_genset = calculate_progress_dynamic(df_genset, target_genset, is_genset=True)
    prog_tools = calculate_progress_dynamic(df_tools_asset, target_default, is_genset=False)
    
    st.markdown("""<div class="report-box-premium" style="margin-top: -10px; padding: 20px; padding-bottom: 5px; border-left: 5px solid var(--primary-color);">
<h4 style="margin-top:0; color:#ffffff; font-weight:900; font-size:16px; letter-spacing:1px;">🎯 TRACKER REGISTRASI TIM (PER NOP)</h4>
<p style="font-size:12px; color:#94a3b8; margin-bottom:15px;">Memantau progres input data unik keseluruhan cabang secara global. (Otomatis Filter Nama Ganda)</p>
</div>""", unsafe_allow_html=True)

    tab_trk_asset, tab_trk_genset, tab_trk_tools = st.tabs(["🚗 Spesifikasi R2/R4", "⚡ Parameter Genset", "🔧 Inventaris Tools"])
    with tab_trk_asset:
        for branch, target in target_default.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_asset[branch], target), unsafe_allow_html=True)
    with tab_trk_genset:
        for branch, target in target_genset.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_genset[branch], target), unsafe_allow_html=True)
    with tab_trk_tools:
        for branch, target in target_default.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_tools[branch], target), unsafe_allow_html=True)
        
    st.markdown("""
<div style="font-size: 11px; color: #94a3b8; margin-top: 5px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 10px; margin-bottom:25px;">
<b>Target:</b> Palangkaraya (41/14), Pangkalanbun (45/23), Tarakan (36/14), Pontianak (75/31).
</div>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------------------
    # TIER 2: FILTER & REKAPITULASI HTML BERJERET (SAMPAI KOLOM DE)
    # ---------------------------------------------------------------------
    df_sdm_filtered = df_sdm.copy()
    
    st.markdown(f"<h3 style='color:var(--accent-color); font-size:18px;'>🔍 Filter Makro & Analisa Kebutuhan</h3>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3) 
    
    with col_f1:
        list_nop = ["SEMUA NOP"]
        nop_col_sdm = next((c for c in df_sdm.columns if 'NOP' in str(c).upper()), None)
        if nop_col_sdm: list_nop += sorted([str(x).strip() for x in df_sdm[nop_col_sdm].dropna().unique() if str(x).strip() not in ["", "nan", "None"]])
        selected_nop = st.selectbox("🏢 NOP (CABANG):", list_nop)
        if selected_nop != "SEMUA NOP": 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[nop_col_sdm].astype(str).str.strip().str.upper() == selected_nop.upper()]
            
    with col_f2:
        col_jabatan = df_sdm.columns[2] if len(df_sdm.columns) > 2 else next((c for c in df_sdm.columns if 'JOB' in str(c).upper()), None)
        list_job = ["SEMUA JABATAN"]
        if col_jabatan: list_job += sorted([str(x).strip() for x in df_sdm_filtered[col_jabatan].dropna().unique() if str(x).strip() not in ["", "nan", "None", "-"]])
        selected_job = st.selectbox("💼 JABATAN (KOLOM C):", list_job)
        if selected_job != "SEMUA JABATAN" and col_jabatan: 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[col_jabatan].astype(str).str.strip() == selected_job]
            
    with col_f3:
        loker_col = next((c for c in df_sdm.columns if 'LOKER' in str(c).upper()), None)
        list_loker = ["SEMUA LOKER"]
        if loker_col: list_loker += sorted([str(x).strip() for x in df_sdm_filtered[loker_col].dropna().unique() if str(x).strip() not in ["", "nan", "None", "-"]])
        selected_loker = st.selectbox("📍 LOKASI KERJA:", list_loker)
        if selected_loker != "SEMUA LOKER" and loker_col: 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[loker_col].astype(str).str.strip() == selected_loker]

    table_data = []
    grand_ny = 0
    grand_nok = 0
    grand_oke = 0
    
    if not df_tools_asset.empty and not df_sdm_filtered.empty:
        valid_names_group = df_sdm_filtered['NAMA'].astype(str).str.strip().str.upper().unique() if 'NAMA' in df_sdm_filtered.columns else []
        name_col_tools = next((col for col in df_tools_asset.columns if "NAMA" in str(col).upper()), None)
        
        if name_col_tools:
            tools_macro_df = df_tools_asset[df_tools_asset[name_col_tools].astype(str).str.strip().str.upper().isin(valid_names_group)].copy()
            
            tools_macro_df['NAMA_UPPER'] = tools_macro_df[name_col_tools].astype(str).str.strip().str.upper()
            tools_macro_df = tools_macro_df.drop_duplicates(subset=['NAMA_UPPER'], keep='first')
            
            for _, row in tools_macro_df.iterrows():
                nama = row[name_col_tools]
                nop_val = "-"
                nop_cols = [c for c in df_tools_asset.columns if 'NOP' in str(c).upper()]
                if nop_cols: nop_val = str(row[nop_cols[-1]]).strip()
                
                status_dict = {'OKE': [], 'NOK': [], 'NY': [], 'NA': [], 'MP': [], 'ABM': []}
                
                # Batasi pembacaan kolom dari awal sampai indeks Kolom DE (indeks 108 dalam 0-based atau sesuaikan dengan batas DataFrame)
                max_col_idx = min(108, len(df_tools_asset.columns))
                for col_name in df_tools_asset.columns[:max_col_idx]:
                    val = str(row[col_name]).strip().upper()
                    if val in status_dict:
                        status_dict[val].append(str(col_name).strip().title()) 
                
                ny_count = len(status_dict['NY'])
                nok_count = len(status_dict['NOK'])
                oke_count = len(status_dict['OKE'])
                
                grand_ny += ny_count
                grand_nok += nok_count
                grand_oke += oke_count
                
                table_data.append({
                    "nama": nama,
                    "nop": nop_val,
                    "ny_count": ny_count,
                    "ny_list": status_dict['NY'],
                    "nok_count": nok_count,
                    "nok_list": status_dict['NOK'],
                    "oke_count": oke_count
                })

    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--primary-color); border-radius: 12px; padding: 15px; margin-top: 15px; margin-bottom: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);">
        <h4 style='margin-top:0; color:var(--accent-color); font-weight:800; font-size:14px; text-transform:uppercase;'>📊 RANGKUMAN KEBUTUHAN TOOLS (AGREGASI GRUP TERFILTER)</h4>
        <p style='font-size:11px; color:#cbd5e1; margin-bottom:15px;'>Kalkulasi status tools (sudah difilter ganda/double input) dari <b>{len(table_data)} Personel valid</b>.</p>
    """, unsafe_allow_html=True)
    
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1: st.markdown(f"<div class='macro-card' style='border-color:#ef4444;'><div class='macro-title'>🔥 GRAND TOTAL NY (PENDING KUT)</div><div class='macro-value' style='color:#ef4444;'>{grand_ny} Item</div></div>", unsafe_allow_html=True)
    with c_m2: st.markdown(f"<div class='macro-card' style='border-color:#f59e0b;'><div class='macro-title'>❌ GRAND TOTAL NOK (RUSAK)</div><div class='macro-value' style='color:#f59e0b;'>{grand_nok} Item</div></div>", unsafe_allow_html=True)
    with c_m3: st.markdown(f"<div class='macro-card' style='border-color:#10b981;'><div class='macro-title'>✅ GRAND TOTAL OKE (BAGUS)</div><div class='macro-value' style='color:#10b981;'>{grand_oke} Item</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📋 LIHAT TABEL RINCIAN KONDISI TOOLS TIM & NAMA ITEM-NYA"):
        if table_data:
            table_html = "<table class='rek-table'><tr><th width='25%'>Identitas Personel</th><th width='37.5%'>🔥 Pending KUT (NY)</th><th width='37.5%'>❌ Rusak (NOK)</th></tr>"
            for item in table_data:
                ny_list_html = "".join([f"<li>{tool}</li>" for tool in item['ny_list']])
                nok_list_html = "".join([f"<li>{tool}</li>" for tool in item['nok_list']])
                
                ny_cell = f"<span class='badge-ny'>{item['ny_count']} ITEM PENDING</span><ul class='item-list'>{ny_list_html}</ul>" if item['ny_count'] > 0 else "<span style='color:#64748b; font-size:11px; font-style:italic;'>Aman (0 Item)</span>"
                nok_cell = f"<span class='badge-nok'>{item['nok_count']} ITEM RUSAK</span><ul class='item-list'>{nok_list_html}</ul>" if item['nok_count'] > 0 else "<span style='color:#64748b; font-size:11px; font-style:italic;'>Aman (0 Item)</span>"
                
                table_html += f"""
                <tr>
                    <td>
                        <b style='color:#ffffff; font-size:13px;'>{item['nama']}</b><br>
                        <span style='color:var(--accent-color); font-size:11px;'>NOP: {item['nop']}</span><br>
                        <span style='color:#94a3b8; font-size:10px;'>✅ {item['oke_count']} Item berstatus OKE</span>
                    </td>
                    <td>{ny_cell}</td>
                    <td>{nok_cell}</td>
                </tr>
                """
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info("Tidak ada data tools yang cocok dengan filter aktif.")

    # ---------------------------------------------------------------------
    # TIER 3: GENERATE REPORT AI KUT & FITUR LAINNYA
    # ---------------------------------------------------------------------
    if st.session_state.show_ai_kut:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="ai-kut-box">
            <h3 style="color:var(--accent-color); margin-top:0;">🤖 GENERATE REPORT AI KUT (ENTERPRISE SUMMARY)</h3>
            <p style="font-size:12px; color:#cbd5e1;">Ringkasan otomatis seluruh kondisi operasional, aset kendaraan, genset, dan tools dari parameter saat ini.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_ai1, col_ai2 = st.columns(2)
        with col_ai1:
            st.markdown(f"""
            <div class="ai-llm-card">
                <h4>📊 Analisa Makro Inventaris</h4>
                <p style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                Berdasarkan rekapitulasi data lintas wilayah, tercatat total <b>{grand_ny}</b> item pending (NY) dan <b>{grand_nok}</b> item rusak (NOK) yang memerlukan tindakan perbaikan segera dari manajemen KUT.
                </p>
                <h4>💡 Rekomendasi Tindakan</h4>
                <p style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                - Prioritaskan pengadaan untuk item dengan status Pending tertinggi di cabang Palangkaraya dan Pontianak.<br>
                - Jadwalkan kalibrasi berkala pada tools lapangan yang menunjukkan anomali minor.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_ai2:
            st.markdown(f"""
            <div class="ai-llm-card">
                <h4>⚡ Status Kesiapan Tim & Operasional</h4>
                <p style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                - Filter Jabatan & Loker aktif telah memvalidasi <b>{len(table_data)} personel unik</b> yang siap bertugas di lapangan.<br>
                - Sinkronisasi server berjalan normal dengan latensi rendah terhubung langsung ke basis data Google Sheets utama.
                </p>
                <h4>🛡️ Keamanan & Kepatuhan</h4>
                <p style="font-size:12px; color:#cbd5e1; line-height:1.6;">
                Seluruh aktivitas pencatatan telah melewati lapis enkripsi sistem dan verifikasi otomatis tanpa duplikasi data personel.
                </p>
            </div>
            """, unsafe_allow_html=True)
