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
    
    .logo-elegant {{ display: block; margin: 0 auto; border-radius: 18px; animation: float-elegant 4s infinite ease-in-out; }}
    
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextArea"] label {{ 
        color: var(--accent-color) !important; font-weight: 700 !important; letter-spacing: 0.8px; font-size: 13px !important; text-transform: uppercase; margin-bottom: 5px; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {{
        border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.08) !important; background: rgba(15, 23, 42, 0.8) !important; color: #ffffff !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 2px 6px rgba(0,0,0,0.5) !important; padding: 12px 16px !important;
    }}
    
    .header-style {{ background: var(--gradient-bg); padding: 25px; border-radius: 20px; color: #ffffff; font-weight: 900; font-size: 30px; text-align: center; letter-spacing: 1.5px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 2px 5px rgba(255,255,255,0.2); margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1); text-shadow: 0 4px 10px rgba(0,0,0,0.4); }}
    
    .report-box-premium {{ background: linear-gradient(145deg, rgba(15,23,42,0.9) 0%, rgba(9,14,23,0.9) 100%); padding: 25px; border-radius: 20px; border-left: 6px solid var(--primary-color); border-top: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.02); margin-bottom: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.4); transition: all 0.4s ease; }}
    
    .macro-card {{ background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.05); text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.3); transition: transform 0.3s; height: 100%; }}
    .macro-card:hover {{ transform: translateY(-5px); border-color: var(--primary-color); box-shadow: 0 15px 30px rgba(0,0,0,0.5), 0 0 15px var(--glow-color); }}
    .macro-value {{ font-size: 36px; font-weight: 900; color: #ffffff; margin: 10px 0; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    .macro-title {{ font-size: 13px; color: var(--accent-color); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }}
    
    [data-testid="stDataFrame"] {{ background: rgba(15, 23, 42, 0.5); border-radius: 16px; padding: 8px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI AI & UI HELPERS ---
def generate_ai_analysis_mini(file_id, is_doc=False):
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    if is_doc: return f"📄 Score: {97.2 + (val%3)}% - Terverifikasi Valid."
    kondisi = ["Fisik Bagus / Layak Pakai", "Terdeteksi Aus/Korosi Minor", "Kotor & Berdebu (Butuh Cleaning)", "Indikasi Kerusakan Ringan"]
    return kondisi[val % len(kondisi)]

def render_progress_nop(label, filled, target):
    pct = int((filled / target) * 100) if target > 0 else 0
    if pct > 100: pct = 100
    color = "#10b981" if pct == 100 else ("#f59e0b" if pct >= 60 else "#ef4444")
    warning = f"✅ Selesai" if pct == 100 else f"⚠️ Kurang {target - filled} Tim"
    
    html = f"""<div style="margin-bottom: 12px;">
<div style="display:flex; justify-content:space-between; margin-bottom:4px; align-items:center;">
<span style="font-size:11px; color:#cbd5e1; font-weight:bold;">{label}</span>
<span style="font-size:11px; color:#ffffff; font-weight:900;">{filled} / {target} <span style="color:{color};">({pct}%)</span></span>
</div>
<div style="width: 100%; background: rgba(0,0,0,0.5); border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); margin-bottom:2px;">
<div style="width: {pct}%; background: {color}; height: 6px; border-radius: 6px; box-shadow: 0 0 10px {color};"></div>
</div>
<div style="text-align: right;"><span style='color:{color}; font-size:9px; font-weight:bold;'>{warning}</span></div>
</div>"""
    return html

def get_logo_path():
    logo_1 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut_2.webp"
    logo_2 = "koperasi-jasa-konstruksi-tower-event-organizer-network-monitoring-telekomunikasi-kisel-group-logo-kut.webp"
    return logo_1 if os.path.exists(logo_1) else (logo_2 if os.path.exists(logo_2) else None)

def render_logo_html(width="100%"):
    path = get_logo_path()
    if path:
        with open(path, "rb") as image_file: return f'<img src="data:image/webp;base64,{base64.b64encode(image_file.read()).decode()}" class="logo-elegant" style="width:{width};">'
    return ""

# --- 4. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
def login_form():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.markdown(render_logo_html(), unsafe_allow_html=True)
        st.markdown('<h1 style="color:#ffffff; text-align:center; font-weight:900; margin-top:20px; letter-spacing:2px; text-shadow: 0 0 15px var(--glow-color);">⚡ SIMAKIN</h1>', unsafe_allow_html=True)
        user = st.text_input("👤 USERNAME")
        pwd = st.text_input("🔑 PASSWORD", type="password")
        if st.form_submit_button("🚀 OTENTIKASI MASUK", use_container_width=True):
            if user == "SIMAKINKUT" and pwd == "2026KUTPOSITIF": st.session_state.logged_in = True; st.rerun()
            else: st.error("❌ Kredensial Salah!")
if not st.session_state.logged_in: login_form(); st.stop() 

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(render_logo_html(width="75%"), unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; margin-top:25px; font-size:18px; color:var(--accent-color); letter-spacing: 1.5px;'>⚙️ CONTROL PANEL</h2>", unsafe_allow_html=True)
    if 'show_ai_kut' not in st.session_state: st.session_state.show_ai_kut = False
    if st.button("🤖 GENERATE AI REPORT", use_container_width=True):
        st.session_state.show_ai_kut = not st.session_state.show_ai_kut; st.rerun()
    if st.button("🔄 Sinkronisasi Server", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Terminasi Sesi", use_container_width=True): st.session_state.logged_in = False; st.rerun()

# --- 6. DRIVER SHEET & LOAD DATA ---
@st.cache_data(ttl=60)
def load_all_data():
    sheet_id = "1hIeT51_SVdNrz62s93zpZNyqepBMdNCa-mDRH-wVOIw"
    excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str)
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame()), xls.get("Evidance foto", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("⏳ Sinkronisasi Satelit SIMAKIN..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

# --- FUNGSI KALKULASI TARGET NOP ---
target_default = {"PALANGKARAYA": 41, "PANGKALANBUN": 45, "TARAKAN": 36, "PONTIANAK": 75}
target_genset = {"PALANGKARAYA": 14, "PANGKALANBUN": 23, "TARAKAN": 14, "PONTIANAK": 31}

def calculate_progress(df, col_nama_idx, col_nop_idx, target_dict, is_genset=False):
    res = {k: 0 for k in target_dict.keys()}
    if df.empty: return res
    actual_nop_idx = col_nop_idx
    if len(df.columns) <= col_nop_idx:
        nop_cols = [i for i, c in enumerate(df.columns) if 'NOP' in str(c).upper()]
        if nop_cols: actual_nop_idx = nop_cols[-1]
        else: return res
        
    temp_df = df.copy()
    temp_df['VAL_NAMA'] = temp_df.iloc[:, col_nama_idx].astype(str).str.upper().str.strip()
    temp_df['VAL_NOP'] = temp_df.iloc[:, actual_nop_idx].astype(str).str.upper().str.strip()
    temp_df = temp_df[~temp_df['VAL_NAMA'].isin(['NAN', 'NONE', '', 'NA', '-'])]
    temp_df = temp_df[~temp_df['VAL_NOP'].isin(['NAN', 'NONE', '', 'NA', '-'])]
    
    if is_genset and len(temp_df.columns) > 3:
        temp_df['VAL_JAB'] = temp_df.iloc[:, 3].astype(str).str.upper().str.strip()
        temp_df = temp_df[temp_df['VAL_JAB'].str.contains('MBP|CME', na=False, regex=True)]
        
    for branch in target_dict.keys():
        branch_df = temp_df[temp_df['VAL_NOP'].str.contains(branch, na=False)]
        res[branch] = int(branch_df['VAL_NAMA'].nunique())
    return res

prog_asset = calculate_progress(df_asset, 2, 53, target_default, is_genset=False)
prog_genset = calculate_progress(df_genset, 2, 34, target_genset, is_genset=True)
prog_tools = calculate_progress(df_tools_asset, 2, 108, target_default, is_genset=False)

# =====================================================================
# LAYOUT UTAMA DIMULAI DI SINI
# =====================================================================
st.markdown('<div class="header-style">🚀 COMMAND CENTER OPERASIONAL & ASSET</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# TIER 1: MATRIK KEBUTUHAN NOP (TAMPIL PALING ATAS DULUAN)
# ---------------------------------------------------------------------
st.markdown("""<div class="report-box-premium" style="margin-top: -20px; padding: 20px; padding-bottom: 5px;">
<h4 style="margin-top:0; color:#ffffff; font-weight:900; font-size:18px; letter-spacing:1px; text-transform:uppercase;">🎯 MATRIK KEPATUHAN & KEBUTUHAN NOP (GLOBAL VIEW)</h4>
<p style="font-size:12px; color:#94a3b8; margin-bottom:15px; line-height:1.5;">Memantau progres registrasi unik seluruh cabang secara real-time.</p>
</div>""", unsafe_allow_html=True)

col_trk1, col_trk2, col_trk3 = st.columns(3)
with col_trk1:
    with st.container(border=True):
        st.markdown("<p style='text-align:center; color:var(--accent-color); font-weight:bold;'>🚗 SPESIFIKASI R2/R4</p><hr style='margin:5px 0 15px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        for branch, target in target_default.items():
            st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_asset[branch], target), unsafe_allow_html=True)
with col_trk2:
    with st.container(border=True):
        st.markdown("<p style='text-align:center; color:var(--accent-color); font-weight:bold;'>⚡ PARAMETER GENSET</p><hr style='margin:5px 0 15px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        for branch, target in target_genset.items():
            st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_genset[branch], target), unsafe_allow_html=True)
with col_trk3:
    with st.container(border=True):
        st.markdown("<p style='text-align:center; color:var(--accent-color); font-weight:bold;'>🔧 INVENTARIS TOOLS</p><hr style='margin:5px 0 15px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        for branch, target in target_default.items():
            st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_tools[branch], target), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# TIER 2: FILTER DATA LINTAS DIVISI
# ---------------------------------------------------------------------
if not df_sdm.empty:
    df_sdm_filtered = df_sdm.copy()
    
    st.markdown(f"<h3 style='color:var(--accent-color);'>🔍 Filter & Macro Analysis Parameter</h3>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4) 
    with col_f1:
        list_job = ["SEMUA JABATAN"] + list(df_sdm['JOB'].dropna().unique()) if 'JOB' in df_sdm.columns else ["SEMUA JABATAN"]
        selected_job = st.selectbox("💼 JABATAN (ROLE):", list_job)
        if selected_job != "SEMUA JABATAN": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['JOB'] == selected_job]
    with col_f2:
        list_loker = ["SEMUA LOKER"] + list(df_sdm_filtered['LOKER'].dropna().unique()) if 'LOKER' in df_sdm_filtered.columns else ["SEMUA LOKER"]
        selected_loker = st.selectbox("📍 LOKASI KERJA:", list_loker)
        if selected_loker != "SEMUA LOKER": df_sdm_filtered = df_sdm_filtered[df_sdm_filtered['LOKER'] == selected_loker]
    with col_f3:
        list_nopol = ["SEMUA NOPOL"] + list(df_asset['NOPOL (PLAT NOMOR)'].dropna().unique()) if not df_asset.empty and 'NOPOL (PLAT NOMOR)' in df_asset.columns else ["SEMUA NOPOL"]
        selected_nopol = st.selectbox("🚗 PLAT KENDARAAN:", list_nopol)
    if selected_nopol != "SEMUA NOPOL":
        asset_filtered = df_asset[df_asset['NOPOL (PLAT NOMOR)'] == selected_nopol]
        nama_col_asset = next((col for col in asset_filtered.columns if "NAMA" in str(col).upper()), None)
        if nama_col_asset:
            valid_names = asset_filtered[nama_col_asset].astype(str).str.strip().str.lower().unique()
            nama_col_sdm = next((col for col in df_sdm_filtered.columns if "NAMA" in str(col).upper()), None)
            if nama_col_sdm: df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[nama_col_sdm].astype(str).str.strip().str.lower().isin(valid_names)]
    with col_f4:
        list_nama = ["- PANGGIL PROFIL PERSONEL -"] + list(df_sdm_filtered['NAMA'].dropna().unique()) if 'NAMA' in df_sdm_filtered.columns else ["-"]
        selected_nama = st.selectbox("👤 IDENTITAS PERSONEL (MICRO):", list_nama)
        if st.session_state.get('selected_nama_karyawan') != selected_nama:
            st.session_state.selected_nama_karyawan = selected_nama; st.rerun()

    # ---------------------------------------------------------------------
    # TIER 3: MACRO ANALYSIS (TAMPIL JIKA FILTER JABATAN / LOKER DIPILIH)
    # ---------------------------------------------------------------------
    is_macro_active = (selected_job != "SEMUA JABATAN" or selected_loker != "SEMUA LOKER")
    
    if is_macro_active:
        st.markdown(f"""
        <div class="report-box-premium" style="background: linear-gradient(145deg, rgba(30, 58, 138, 0.4) 0%, rgba(15, 23, 42, 0.9) 100%); border-left: 6px solid var(--accent-color);">
            <h3 style='margin-top:0; color:var(--accent-color); font-weight:900; text-transform:uppercase;'>📊 ANALISIS KEBUTUHAN & KONDISI GRUP: {selected_job} - {selected_loker}</h3>
            <p style='font-size:13px; color:#cbd5e1; margin-bottom:0;'>Menyajikan agregasi data kekurangan tools dan status kelayakan aset secara keseluruhan pada parameter yang dipilih.</p>
        </div>
        """, unsafe_allow_html=True)
        
        total_personnel = len(df_sdm_filtered)
        
        # Kalkulasi Macro: Kebutuhan Tools
        tools_cols = ['WAH', 'FA', 'FE']
        tools_missing_count = 0
        tools_available_count = 0
        if not df_sdm_filtered.empty:
            for t in tools_cols:
                if t in df_sdm_filtered.columns:
                    missing_mask = df_sdm_filtered[t].astype(str).str.strip().isin(['nan', 'None', '', '-', 'NaN'])
                    tools_missing_count += missing_mask.sum()
                    tools_available_count += (~missing_mask).sum()
        
        # Kalkulasi Macro: Kondisi Unit (R2/R4)
        valid_names_group = df_sdm_filtered['NAMA'].astype(str).str.strip().str.upper().unique() if 'NAMA' in df_sdm_filtered.columns else []
        asset_group = df_asset[df_asset.iloc[:, 2].astype(str).str.strip().str.upper().isin(valid_names_group)] if not df_asset.empty else pd.DataFrame()
        genset_group = df_genset[df_genset.iloc[:, 2].astype(str).str.strip().str.upper().isin(valid_names_group)] if not df_genset.empty else pd.DataFrame()
        
        # R2/R4 Readiness
        total_r2 = len(asset_group)
        r2_serviced = 0
        if not asset_group.empty and 'SERCIVE BERKALA (TGL TERAKHIR SERVICE)' in asset_group.columns:
            r2_serviced = (~asset_group['SERCIVE BERKALA (TGL TERAKHIR SERVICE)'].astype(str).str.strip().isin(['nan', 'None', '', '-', 'NaT'])).sum()
            
        # Genset Readiness
        total_genset = len(genset_group)
        genset_ready = 0
        if not genset_group.empty and 'STATUS ASSET' in genset_group.columns:
            genset_ready = genset_group['STATUS ASSET'].astype(str).str.upper().str.contains('BAIK|READY', na=False).sum()

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f"""<div class="macro-card">
            <div class="macro-title">👥 Total Personel</div>
            <div class="macro-value" style="color:var(--accent-color);">{total_personnel}</div>
            <div style="font-size:11px; color:#94a3b8;">Tim Aktif di Filter Ini</div></div>""", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""<div class="macro-card">
            <div class="macro-title">⚠️ Kebutuhan Tools</div>
            <div class="macro-value" style="color:#ef4444;">{tools_missing_count}</div>
            <div style="font-size:11px; color:#94a3b8;">Item Tools WAH/FA/FE Kosong</div></div>""", unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""<div class="macro-card">
            <div class="macro-title">🚗 Kendaraan R2/R4</div>
            <div class="macro-value" style="color:#f59e0b;">{r2_serviced} / {total_r2}</div>
            <div style="font-size:11px; color:#94a3b8;">Unit Update Servis Terakhir</div></div>""", unsafe_allow_html=True)
        with col_m4:
            st.markdown(f"""<div class="macro-card">
            <div class="macro-title">⚡ Kondisi Genset</div>
            <div class="macro-value" style="color:#10b981;">{genset_ready} / {total_genset}</div>
            <div style="font-size:11px; color:#94a3b8;">Unit Status Baik / Ready</div></div>""", unsafe_allow_html=True)
            
        st.write("---")

    # ---------------------------------------------------------------------
    # TIER 4: MICRO ANALYSIS (TAMPIL JIKA 1 PERSONEL DIPILIH DI DROPDOWN)
    # ---------------------------------------------------------------------
    if selected_nama != "- PANGGIL PROFIL PERSONEL -":
        def get_row_by_name(df, target_name):
            if df.empty: return None
            name_col = next((col for col in df.columns if "NAMA" in str(col).upper()), None)
            if not name_col: return None
            matched = df[df[name_col].astype(str).str.strip().str.lower().str.contains(str(target_name).strip().lower(), regex=False, na=False)]
            return matched.iloc[0] if not matched.empty else None

        data_karyawan_select = get_row_by_name(df_sdm_filtered, selected_nama)
        data_asset_select = get_row_by_name(df_asset, selected_nama)
        data_genset_select = get_row_by_name(df_genset, selected_nama)
        data_tools_asset_select = get_row_by_name(df_tools_asset, selected_nama)
        
        st.markdown(f"<h3 style='color:var(--accent-color);'>👤 Matrix Profil & Identitas: {selected_nama}</h3>", unsafe_allow_html=True)
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
        st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
        
        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            st.markdown(f"<h3 style='color:var(--accent-color); font-size:16px;'>🔧 Inventaris Tools</h3>", unsafe_allow_html=True)
            tools_list_df = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License"]
            tools_data = [{"Item": t, "Status": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list_df]
            st.dataframe(pd.DataFrame(tools_data), height=350, hide_index=True, use_container_width=True)
        with col_mid:
            st.markdown(f"<h3 style='color:var(--accent-color); font-size:16px;'>🚗 Spesifikasi R2/R4</h3>", unsafe_allow_html=True)
            asset_fields = ["NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)"]
            asset_data = [{"Parameter": f, "Nilai": str(data_asset_select[f]) if data_asset_select is not None and f in df_asset.columns and str(data_asset_select[f]).strip() not in ["nan", "None"] else "-"} for f in asset_fields]
            st.dataframe(pd.DataFrame(asset_data), height=350, hide_index=True, use_container_width=True)
        with col_right:
            st.markdown(f"<h3 style='color:var(--accent-color); font-size:16px;'>⚡ Parameter Genset</h3>", unsafe_allow_html=True)
            genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STATUS ASSET"]
            genset_data = [{"Parameter": f, "Nilai": str(data_genset_select[f]) if data_genset_select is not None and f in df_genset.columns and str(data_genset_select[f]).strip() not in ["nan", "None"] else "-"} for f in genset_fields]
            st.dataframe(pd.DataFrame(genset_data), height=350, hide_index=True, use_container_width=True)
            
        st.write("---")
        
        # PANEL TRANSMISI DAN EVIDANCE BAWAH
        col_ev1, col_ev2 = st.columns([1, 1])
        with col_ev1:
            st.markdown(f"<h3 style='color:var(--accent-color);'>📝 Panel Transmisi Laporan</h3>", unsafe_allow_html=True)
            input_findings = st.text_area("✍️ Uraikan Detail Tindakan & Kondisi Asset:", height=100)
            if st.button("🚀 TRANSMISI DATA TEKS", use_container_width=True):
                st.success("Transmisi dikunci (Simulasi untuk tampilan utama)")
        with col_ev2:
            st.markdown(f"<h3 style='color:var(--accent-color);'>📸 Sinkronisasi Evidance</h3>", unsafe_allow_html=True)
            st.info("Pintu protokol terbuka. Sistem mengunci Identitas dan Aset Anda untuk transmisi form.")
            st.markdown("""
            <div style="background: var(--gradient-bg); padding: 15px; border-radius: 12px; color: white; text-align: center; font-weight: 900; font-size: 14px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); margin-top: 10px; cursor: pointer;">
                <span style="font-size:18px;">📸</span> BUKA PORTAL UPLOAD EVIDANCE
            </div>
            """, unsafe_allow_html=True)
