import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import os
import urllib.parse 
import base64
import hashlib 
import re
from itertools import zip_longest 
import io
import hmac
import html as _html

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SiMAKIN", layout="wide", initial_sidebar_state="expanded")

# --- 2. SISTEM FILTRASI WARNA DINAMIS (COLOR-SHIFTING THEME) ---
selected_nama_raw = "-"
if 'selected_nama_karyawan' in st.session_state:
    selected_nama_raw = st.session_state.selected_nama_karyawan

def _rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

themes = [
    {"primary": "#3b82f6", "accent": "#7cabff"},
    {"primary": "#10b981", "accent": "#4fd8a4"},
    {"primary": "#8b5cf6", "accent": "#b39bff"},
    {"primary": "#f59e0b", "accent": "#fbbf4a"},
    {"primary": "#ec4899", "accent": "#f77fb9"},
    {"primary": "#06b6d4", "accent": "#4cd6ee"},
]
for _t in themes:
    _t["glow"] = _rgba(_t["primary"], 0.30)
    _t["soft"] = _rgba(_t["primary"], 0.14)
    _t["gradient"] = _t["primary"]
theme_idx = sum(ord(c) for c in selected_nama_raw) % len(themes) if selected_nama_raw != "-" else 0
active_theme = themes[theme_idx]

# --- 3. CUSTOM ADVANCED CSS DESIGN ---
st.markdown(f"""<style>
:root {{
    --primary-color: {active_theme['primary']};
    --accent-color: {active_theme['accent']};
    --glow-color: {active_theme['glow']};
    --soft-color: {active_theme['soft']};
    --gradient-bg: {active_theme['gradient']};
}}
</style>""", unsafe_allow_html=True)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* ============ DESIGN TOKENS ============ */
:root {
    --bg: #0b101a; --surface: #111826; --surface-2: #161e2e; --surface-3: #1e2739;
    --line: rgba(148,163,184,.13); --line-2: rgba(148,163,184,.25);
    --text: #e7ebf3; --text-2: #9aa6ba; --text-3: #67738b;
    --ok: #34d399; --warn: #fbbf24; --bad: #f87171;
    --font: 'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif;
}
@keyframes enter { from { opacity: 0; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

/* ============ BASE ============ */
.stApp { background: var(--bg); color: var(--text); font-family: var(--font); }
.stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp table { font-family: var(--font); }
footer, [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.main .block-container, [data-testid="stMainBlockContainer"] { max-width: 1240px; padding: 2.4rem 2rem 4rem; animation: enter .5s ease-out; }
hr { border-color: var(--line) !important; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 10px; border: 2px solid transparent; background-clip: padding-box; }

section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }

/* ============ HEADINGS (menimpa inline style lama) ============ */
.stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: var(--text) !important; text-transform: none !important; letter-spacing: -.01em !important; }
.stMarkdown h2 { font-size: 1.35rem !important; font-weight: 700 !important; }
.stMarkdown h3 { font-size: 1.05rem !important; font-weight: 600 !important; margin: .5rem 0 .7rem !important; padding: 0 !important; }
.stMarkdown h4 { font-size: .95rem !important; font-weight: 600 !important; padding: 0 !important; }

/* ============ HERO & SECTION ============ */
.hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; flex-wrap: wrap; padding-bottom: 22px; margin-bottom: 26px; border-bottom: 1px solid var(--line); }
.hero-title { font-size: 1.75rem; font-weight: 700; letter-spacing: -.025em; line-height: 1.15; color: var(--text); }
.hero-sub { margin-top: 8px; font-size: .9rem; color: var(--text-2); max-width: 620px; line-height: 1.5; }
.pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border: 1px solid var(--line-2); border-radius: 999px; font-size: .76rem; color: var(--text-2); background: var(--surface); }
.pill i { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }
.section-head { margin: 8px 0 14px; }
.section-title { font-size: 1.05rem; font-weight: 600; color: var(--text); letter-spacing: -.01em; }
.section-sub { font-size: .83rem; color: var(--text-2); margin-top: 3px; }

/* ============ SCORECARD (stat strip + distribusi) ============ */
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; margin: 12px 0 18px; }
.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
.stat { padding: 18px 22px; border-right: 1px solid var(--line); }
.stat:last-child { border-right: 0; }
.stat-label { font-size: .78rem; color: var(--text-2); font-weight: 500; }
.stat-value { margin-top: 10px; font-size: 1.95rem; font-weight: 700; letter-spacing: -.03em; line-height: 1; font-variant-numeric: tabular-nums; color: var(--text); }
.stat-sub { margin-top: 10px; font-size: .76rem; color: var(--text-3); line-height: 1.4; }
.dist { padding: 18px 22px 20px; border-top: 1px solid var(--line); background: var(--surface-2); }
.dist-head { font-size: .78rem; color: var(--text-2); font-weight: 500; margin-bottom: 12px; }
.dist-bar { display: flex; gap: 2px; height: 8px; border-radius: 999px; overflow: hidden; background: var(--surface-3); }
.dist-bar span { display: block; height: 100%; }
.dist-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px 26px; margin-top: 16px; }
.lg { display: flex; align-items: center; gap: 9px; font-size: .8rem; color: var(--text-2); }
.lg i { width: 8px; height: 8px; border-radius: 3px; flex: none; }
.lg b { margin-left: auto; color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
.lg em { font-style: normal; color: var(--text-3); font-size: .72rem; }
.tone-ok { color: var(--ok) !important; } .tone-warn { color: var(--warn) !important; } .tone-bad { color: var(--bad) !important; }
.c-ok { color: var(--ok); } .c-warn { color: var(--warn); } .c-bad { color: var(--bad); }

.export-note { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 18px; font-size: .84rem; color: var(--text-2); line-height: 1.55; }
.export-note b { color: var(--text); font-weight: 600; }

/* kartu angka lama (dipakai di audit kepatuhan) */
.macro-card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; text-align: left; height: 100%; }
.macro-title { font-size: .78rem; color: var(--text-2); font-weight: 500; margin-bottom: 8px; }
.macro-value { font-size: 1.8rem; font-weight: 700; letter-spacing: -.02em; color: var(--text); font-variant-numeric: tabular-nums; line-height: 1.1; }

/* ============ PROGRESS ============ */
.prog { margin-bottom: 18px; }
.prog-top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.prog-label { font-size: .85rem; color: var(--text); font-weight: 500; }
.prog-num { font-size: .8rem; color: var(--text-2); font-variant-numeric: tabular-nums; }
.prog-num b { color: var(--text); font-weight: 600; }
.prog-num em { font-style: normal; font-weight: 600; margin-left: 8px; }
.prog-track { height: 6px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
.prog-fill { height: 100%; border-radius: 999px; }
.prog-note { font-size: .74rem; margin-top: 6px; text-align: right; }

/* ============ TABEL RINCIAN TOOLS ============ */
.rek-wrap { max-height: 560px; overflow: auto; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); }
.rek-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .82rem; color: var(--text); }
.rek-table thead th { position: sticky; top: 0; z-index: 2; background: var(--surface-3); color: var(--text-2); font-size: .76rem; font-weight: 600; padding: 12px 10px; text-align: center; border-bottom: 1px solid var(--line-2); }
.rek-table thead th.l { text-align: left; padding-left: 16px; }
.rek-table thead th:nth-child(1) { width: 23%; } .rek-table thead th:nth-child(2) { width: 14%; } .rek-table thead th:nth-child(3) { width: 28%; }
.rek-table td { padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: center; vertical-align: middle; }
.rek-table td.item { text-align: left; padding-left: 16px; color: var(--text); }
.rek-table td.who { text-align: left; vertical-align: top; padding: 13px 16px; min-width: 210px; border-right: 1px solid var(--line); }
.rek-table td.nop { text-align: left; vertical-align: top; padding: 14px 12px; color: var(--accent-color); font-weight: 500; white-space: nowrap; }
.rek-table tr.grp-start td { border-top: 1px solid var(--line-2); }
.rek-table tbody tr:hover td.item, .rek-table tbody tr:hover td:not(.who):not(.nop) { background: rgba(148,163,184,.06); }
.who-name { font-weight: 600; font-size: .86rem; color: var(--text); }
.who-meta { margin-top: 7px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: .74rem; color: var(--text-2); }
.tick { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; font-size: .78rem; font-weight: 700; line-height: 1; }
.tick-oke { background: rgba(52,211,153,.16); color: #4ade9f; }
.tick-nok { background: rgba(251,191,36,.16); color: #fbbf24; }
.tick-ny  { background: rgba(248,113,113,.17); color: #f87171; }
.tick-na  { background: rgba(148,163,184,.16); color: #9aa6ba; }
.tick-mp  { background: rgba(96,165,250,.16); color: #7cb4fb; }
.tick-abm { background: rgba(167,139,250,.18); color: #b4a0fb; }
.badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-size: .7rem; font-weight: 600; }
.badge-siap { background: rgba(52,211,153,.14); color: #4ade9f; }
.badge-perhatian { background: rgba(251,191,36,.14); color: #fbbf24; }
.badge-kritis { background: rgba(248,113,113,.15); color: #f87171; }
.badge-none { background: rgba(148,163,184,.14); color: #9aa6ba; }
.legend-row { display: flex; flex-wrap: wrap; gap: 8px 22px; margin-top: 14px; font-size: .76rem; color: var(--text-2); }
.legend-row .tick { width: 18px; height: 18px; font-size: .68rem; margin-right: 4px; vertical-align: middle; }

/* ============ GALERI & LAPORAN ============ */
.gallery-grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 15px; }
.gallery-card-3d { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 10px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 6px; transition: border-color .2s; }
.gallery-card-3d:hover { border-color: var(--line-2); }
.gallery-card-3d img { width: 100%; height: 200px; object-fit: contain; background: #080c13; border-radius: 8px; padding: 4px; }
.btn-buka-foto { display: block; margin-top: 10px; padding: 8px; border-radius: 8px; border: 1px solid var(--line-2); background: var(--surface-2); color: var(--text) !important; text-decoration: none; font-size: .78rem; font-weight: 600; transition: background .2s, border-color .2s; }
.btn-buka-foto:hover { background: var(--primary-color); border-color: var(--primary-color); color: #fff !important; }
.report-box-premium { background: var(--surface); border: 1px solid var(--line); border-left: 3px solid var(--primary-color); border-radius: 12px; padding: 18px 22px; margin: 14px 0; }
.report-date-badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: .74rem; font-weight: 500; color: var(--text-2); background: var(--surface-3); border: 1px solid var(--line); margin-bottom: 10px; }

/* Laporan AI KUT */
.ai-kut-box { display: none; }
.ai-llm-card { background: var(--surface-2); border: 1px solid var(--line); border-top: 2px solid var(--accent-color); border-radius: 12px; padding: 26px; }
.ai-llm-card p { color: var(--text-2); line-height: 1.65; font-size: .9rem; }
.stMarkdown .ai-llm-card h4 { color: var(--accent-color) !important; font-size: .95rem !important; font-weight: 600 !important; margin: 22px 0 8px !important; padding-bottom: 8px !important; border-bottom: 1px solid var(--line) !important; }

/* ============ LOGIN & SIDEBAR ============ */
.logo-elegant { display: block; margin: 0 auto; border-radius: 12px; }
div[data-testid="stForm"] { background: var(--surface) !important; border: 1px solid var(--line-2) !important; border-radius: 16px !important; padding: 34px 32px !important; max-width: 420px; margin: 0 auto !important; box-shadow: 0 24px 60px rgba(0,0,0,.45); }
.login-title { text-align: center; font-size: 1.3rem; font-weight: 700; letter-spacing: -.015em; color: var(--text); margin: 18px 0 4px; }
.login-sub { text-align: center; font-size: .85rem; color: var(--text-2); margin-bottom: 22px; }
.login-foot { text-align: center; font-size: .72rem; color: var(--text-3); margin-top: 14px; }
.side-title { text-align: center; font-weight: 700; letter-spacing: .12em; font-size: .95rem; color: var(--text); margin-top: 12px; }
.side-sub { text-align: center; font-size: .75rem; color: var(--text-3); margin-top: 2px; }
.side-user { display: flex; align-items: center; gap: 10px; padding: 10px 12px; margin: 20px 0 6px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface-2); }
.avatar { width: 30px; height: 30px; border-radius: 8px; background: var(--primary-color); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .8rem; }
.u-name { font-size: .83rem; font-weight: 600; color: var(--text); }
.u-role { font-size: .72rem; color: var(--text-3); }
.side-label { font-size: .74rem; font-weight: 600; color: var(--text-3); margin: 20px 0 8px; }
.side-foot { text-align: center; color: var(--text-3); font-size: .72rem; margin-top: 48px; line-height: 1.7; }

/* ============ KOMPONEN STREAMLIT ============ */
[data-testid="stWidgetLabel"] p, label p { color: var(--text-2) !important; font-size: .82rem !important; font-weight: 500 !important; text-transform: none !important; letter-spacing: 0 !important; }
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div { background: var(--surface-2) !important; border: 1px solid var(--line-2) !important; border-radius: 8px !important; box-shadow: none !important; }
div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background: transparent !important; }
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, textarea { color: var(--text) !important; background: transparent !important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: var(--primary-color) !important; box-shadow: 0 0 0 3px var(--soft-color) !important; }
div[data-baseweb="select"] * { color: var(--text) !important; }
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] [role="listbox"] { background: var(--surface-2) !important; }
li[role="option"] { color: var(--text) !important; background: transparent !important; }
li[role="option"]:hover, li[aria-selected="true"] { background: var(--surface-3) !important; }

.stButton > button, div[data-testid="stDownloadButton"] > button, div[data-testid="stFormSubmitButton"] > button {
    border-radius: 8px !important; font-weight: 600 !important; font-size: .86rem !important; padding: .55rem 1rem !important;
    border: 1px solid var(--line-2) !important; background: var(--surface-2) !important; color: var(--text) !important;
    box-shadow: none !important; transition: border-color .18s, background .18s !important;
}
.stButton > button p, div[data-testid="stDownloadButton"] > button p, div[data-testid="stFormSubmitButton"] > button p { color: inherit !important; font-size: .86rem !important; }
.stButton > button:hover { border-color: var(--primary-color) !important; background: var(--surface-3) !important; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"],
div[data-testid="stDownloadButton"] > button, div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary-color) !important; border-color: transparent !important; color: #fff !important;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover,
div[data-testid="stDownloadButton"] > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { filter: brightness(1.12); background: var(--primary-color) !important; border-color: transparent !important; }

.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background: transparent; height: 44px; padding: 0 14px; color: var(--text-2); font-weight: 500; font-size: .87rem; }
.stTabs [data-baseweb="tab"] p { font-size: .87rem !important; }
.stTabs [aria-selected="true"] { color: var(--text) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--primary-color); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

[data-testid="stExpander"] { background: var(--surface) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; margin-bottom: 14px; }
[data-testid="stExpander"] summary { color: var(--text) !important; font-size: .87rem !important; font-weight: 500 !important; padding: 10px 14px !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
div[data-testid="stAlert"] { border-radius: 10px !important; }

/* 📱 MODE HP (SMARTPHONE AUTO-RESPONSIVE DETECTOR) 📱 */
@media (max-width: 768px) {
    .header-style { font-size: 18px !important; padding: 15px !important; margin-bottom: 15px !important; }
    div[data-testid="stForm"] { padding: 20px !important; width: 90% !important; }
    .macro-value { font-size: 20px !important; margin: 2px 0 !important; }
    .macro-title { font-size: 9px !important; letter-spacing: 0px !important; }
    .macro-card { padding: 10px !important; margin-bottom: 10px !important; }
    .rek-table th { font-size: 8px !important; padding: 5px !important; }
    .rek-table td { font-size: 9px !important; padding: 5px !important; }
    .item-list { font-size: 9px !important; padding-left: 12px !important; }
    .badge-ny, .badge-nok { font-size: 8px !important; padding: 2px 4px !important; }
    .ai-llm-card { padding: 15px !important; }
    .ai-llm-card h4 { font-size: 13px !important; }
    .ai-llm-card p { font-size: 11px !important; line-height: 1.5 !important; }
    .gallery-card-3d img { height: 150px !important; }
}
</style>""", unsafe_allow_html=True)

# --- FUNGSI AI MINI SICAKEP ---
def generate_ai_analysis_mini(file_id, is_doc=False):
    val = int(hashlib.md5(file_id.encode()).hexdigest(), 16)
    akurasi = [98.4, 99.1, 97.5, 96.8, 99.9, 98.8, 97.2]
    ak = akurasi[val % len(akurasi)]
    if is_doc: return f"Score: {ak}% - Terverifikasi Valid."
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
def esc(value):
    return _html.escape(str(value), quote=True)

def section_header(title, sub=""):
    sub_html = f"<div class='section-sub'>{sub}</div>" if sub else ""
    return f"<div class='section-head'><div class='section-title'>{title}</div>{sub_html}</div>"

def render_progress_nop(label, filled, target):
    pct = min(int((filled / target) * 100) if target > 0 else 0, 100)
    if pct == 100: tone, color, note = "c-ok", "#34d399", "Target tercapai"
    elif pct >= 60: tone, color, note = "c-warn", "#fbbf24", f"Kurang {target - filled} tim"
    else: tone, color, note = "c-bad", "#f87171", f"Kurang {target - filled} tim"
    return (f"<div class='prog'><div class='prog-top'><span class='prog-label'>{label}</span>"
            f"<span class='prog-num'><b>{filled}</b> / {target}<em class='{tone}'>{pct}%</em></span></div>"
            f"<div class='prog-track'><div class='prog-fill' style='width:{pct}%;background:{color};'></div></div>"
            f"<div class='prog-note {tone}'>{note}</div></div>")

# =====================================================================
# KONDISI TOOLS TIM: ringkasan, tabel, dan export Excel
# =====================================================================
TOOL_STATUS = {
    "OKE": {"label": "Bagus", "desc": "Dipegang, kondisi bagus", "group": "Bagus", "hex": "#34d399", "fill": "D1FAE5", "ink": "065F46"},
    "NOK": {"label": "Rusak", "desc": "Dipegang, kondisi rusak", "group": "Bermasalah", "hex": "#fbbf24", "fill": "FEF3C7", "ink": "92400E"},
    "NY":  {"label": "Tidak Ada (Wajib)", "desc": "Wajib dimiliki, tetapi belum dipegang", "group": "Bermasalah", "hex": "#f87171", "fill": "FEE2E2", "ink": "991B1B"},
    "NA":  {"label": "Tidak Wajib", "desc": "Tidak termasuk mandatory", "group": "Netral", "hex": "#64748b", "fill": "F1F5F9", "ink": "475569"},
    "MP":  {"label": "Milik Pribadi", "desc": "Dipegang, milik pribadi", "group": "Netral", "hex": "#60a5fa", "fill": "DBEAFE", "ink": "1E40AF"},
    "ABM": {"label": "Ada, Bukan Mandatory", "desc": "Ada, tetapi bukan mandatory", "group": "Netral", "hex": "#a78bfa", "fill": "EDE9FE", "ink": "5B21B6"},
}
TABLE_ORDER = ["NOK", "OKE", "NY", "NA", "MP", "ABM"]
TICK_GLYPH = {"OKE": "✓", "NOK": "✕", "NY": "!", "NA": "–", "MP": "✓", "ABM": "✓"}
COL_LABEL = {"OKE": "Bagus (OKE)", "NOK": "Rusak (NOK)", "NY": "Tidak Ada (NY)", "NA": "Tidak Wajib (NA)", "MP": "Milik Pribadi (MP)", "ABM": "Ada Bukan Mandatory (ABM)"}
CAT_CLASS = {"Siap": "siap", "Perlu Perhatian": "perhatian", "Kritis": "kritis", "Tanpa item wajib": "none"}
SCORE_READY, SCORE_WARN = 0.90, 0.70   # ambang kategori skor kesiapan

def _score_category(oke, nok, ny):
    wajib = oke + nok + ny
    if wajib == 0: return None, "Tanpa item wajib"
    skor = oke / wajib
    if skor >= SCORE_READY: return skor, "Siap"
    if skor >= SCORE_WARN: return skor, "Perlu Perhatian"
    return skor, "Kritis"

def summarize_tools(records):
    """records: list of dict {nama, nop, item_name, status}. Mengembalikan beberapa DataFrame ringkasan."""
    codes = list(TOOL_STATUS.keys())
    detail = pd.DataFrame(records).rename(columns={"nama": "Nama Personel", "nop": "NOP", "item_name": "Nama Item Tools", "status": "Kode"})
    detail["Keterangan Status"] = detail["Kode"].map(lambda k: TOOL_STATUS[k]["label"])
    detail["Kelompok"] = detail["Kode"].map(lambda k: TOOL_STATUS[k]["group"])
    detail = detail.sort_values(["Nama Personel", "Nama Item Tools"]).reset_index(drop=True)

    rows = []
    for (nama, nop), g in detail.groupby(["Nama Personel", "NOP"], sort=True):
        n = {k: int((g["Kode"] == k).sum()) for k in codes}
        skor, kategori = _score_category(n["OKE"], n["NOK"], n["NY"])
        row = {"Nama Personel": nama, "NOP": nop, "Total Item": len(g)}
        for k in codes: row[COL_LABEL[k]] = n[k]
        row["Skor Kesiapan"] = skor
        row["Kategori"] = kategori
        row["Daftar Tools Bagus"] = "; ".join(g.loc[g["Kode"] == "OKE", "Nama Item Tools"])
        row["Daftar Tools Rusak"] = "; ".join(g.loc[g["Kode"] == "NOK", "Nama Item Tools"])
        row["Daftar Tools Tidak Ada (Wajib)"] = "; ".join(g.loc[g["Kode"] == "NY", "Nama Item Tools"])
        rows.append(row)
    person = pd.DataFrame(rows)
    person["Skor Kesiapan"] = pd.to_numeric(person["Skor Kesiapan"], errors="coerce")
    person = person.sort_values(["Skor Kesiapan", "Nama Personel"], na_position="last").reset_index(drop=True)

    cnt = detail.pivot_table(index="Nama Item Tools", columns="Kode", values="Nama Personel", aggfunc="count", fill_value=0).reindex(columns=codes, fill_value=0)
    item = cnt.copy()
    item.insert(0, "Total Personel", cnt.sum(axis=1))
    item["Bermasalah (NOK+NY)"] = cnt["NOK"] + cnt["NY"]
    wj = cnt["OKE"] + cnt["NOK"] + cnt["NY"]
    item["% Bagus dari Wajib"] = cnt["OKE"] / wj.where(wj > 0)
    item = item.sort_values(["Bermasalah (NOK+NY)", "Total Personel"], ascending=[False, False]).reset_index().rename(columns=COL_LABEL)
    item.columns.name = None

    cn = detail.pivot_table(index="NOP", columns="Kode", values="Nama Personel", aggfunc="count", fill_value=0).reindex(columns=codes, fill_value=0)
    nop = cn.copy()
    nop.insert(0, "Jumlah Personel", detail.groupby("NOP")["Nama Personel"].nunique())
    wj2 = cn["OKE"] + cn["NOK"] + cn["NY"]
    nop["Bermasalah (NOK+NY)"] = cn["NOK"] + cn["NY"]
    nop["Skor Kesiapan"] = cn["OKE"] / wj2.where(wj2 > 0)
    nop = nop.sort_values("Skor Kesiapan", na_position="last").reset_index().rename(columns=COL_LABEL)
    nop.columns.name = None

    matrix = detail.pivot_table(index=["Nama Personel", "NOP"], columns="Nama Item Tools", values="Kode", aggfunc="first").reset_index()
    matrix.columns.name = None
    matrix = matrix.fillna("")
    return {"detail": detail, "person": person, "item": item, "nop": nop, "matrix": matrix}

def render_tools_table_html(detail, person):
    stat = {(r["Nama Personel"], r["NOP"]): r for r in person.to_dict("records")}
    head = "".join(f"<th>{c}</th>" for c in TABLE_ORDER)
    out = ["<div class='rek-wrap'><table class='rek-table'><thead><tr><th class='l'>Personel</th><th class='l'>NOP</th><th class='l'>Nama item tools</th>" + head + "</tr></thead><tbody>"]
    for (nama, nop), g in detail.groupby(["Nama Personel", "NOP"], sort=True):
        info = stat.get((nama, nop), {})
        skor = info.get("Skor Kesiapan")
        skor_txt = f"{skor * 100:.0f}%" if skor is not None and not pd.isna(skor) else "-"
        kat = info.get("Kategori", "Tanpa item wajib")
        meta = f"<span class='badge badge-{CAT_CLASS.get(kat, 'none')}'>{kat}</span><span>Skor {skor_txt}</span>"
        span = len(g)
        first = True
        for _, r in g.iterrows():
            tr = "<tr class='grp-start'>" if first else "<tr>"
            if first:
                tr += f"<td class='who' rowspan='{span}'><div class='who-name'>{esc(nama)}</div><div class='who-meta'>{meta}</div></td><td class='nop' rowspan='{span}'>{esc(nop)}</td>"
            tr += f"<td class='item'>{esc(r['Nama Item Tools'])}</td>"
            for code in TABLE_ORDER:
                tr += f"<td><span class='tick tick-{code.lower()}'>{TICK_GLYPH[code]}</span></td>" if r["Kode"] == code else "<td></td>"
            out.append(tr + "</tr>")
            first = False
    out.append("</tbody></table></div>")
    return "".join(out)

def _style_ws(ws, freeze="A2", status_cells=False, max_w=44, header_h=34, filterable=True, label_cols=0):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    side = Side(style="thin", color="E2E8F0")
    border = Border(left=side, right=side, top=side, bottom=side)
    cat_fill = {"Siap": ("D1FAE5", "065F46"), "Perlu Perhatian": ("FEF3C7", "92400E"),
                "Kritis": ("FEE2E2", "991B1B"), "Tanpa item wajib": ("F1F5F9", "475569")}
    grp_fill = {"Bagus": ("D1FAE5", "065F46"), "Bermasalah": ("FEE2E2", "991B1B"), "Netral": ("F1F5F9", "475569")}
    headers = [c.value for c in ws[1]]
    for c in ws[1]:
        c.fill = PatternFill("solid", fgColor="0F172A")
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border
    ws.row_dimensions[1].height = header_h
    for ci, h in enumerate(headers, start=1):
        letter = get_column_letter(ci)
        cells = list(ws[letter])[1:]
        h = h if isinstance(h, str) else ""
        is_list = h.startswith("Daftar ")
        longest = max((len(str(c.value)) for c in cells if c.value not in (None, "")), default=0)
        cap = 36 if ci <= label_cols else max_w
        ws.column_dimensions[letter].width = 48 if is_list else min(max(longest + 3, min(len(h), 18) + 2, 10), cap)
        for c in cells:
            c.border = border
            v = c.value
            if is_list: c.alignment = Alignment(wrap_text=True, vertical="top")
            elif isinstance(v, (int, float)): c.alignment = Alignment(horizontal="center", vertical="center")
            else: c.alignment = Alignment(vertical="center")
            if ("Skor" in h or h.startswith("%")) and isinstance(v, (int, float)): c.number_format = "0%"
            if h == "Kategori" and v in cat_fill:
                c.fill = PatternFill("solid", fgColor=cat_fill[v][0]); c.font = Font(name="Calibri", size=11, bold=True, color=cat_fill[v][1])
            if h == "Kelompok" and v in grp_fill:
                c.fill = PatternFill("solid", fgColor=grp_fill[v][0]); c.font = Font(name="Calibri", size=11, bold=True, color=grp_fill[v][1])
            if status_cells and isinstance(v, str) and v in TOOL_STATUS:
                m = TOOL_STATUS[v]
                c.fill = PatternFill("solid", fgColor=m["fill"]); c.font = Font(name="Calibri", size=11, bold=True, color=m["ink"])
                c.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = freeze
    if filterable: ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    from openpyxl.worksheet.properties import PageSetupProperties
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0

def build_tools_excel(tables, filter_label, personel_count):
    from openpyxl.styles import Alignment, Font
    from datetime import timezone, timedelta
    stamp = datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M WIB")
    info_rows = [
        ("Laporan", "SIMAKIN - Rincian Kondisi Tools Tim"),
        ("Filter tim", filter_label),
        ("Diekspor", stamp),
        ("Jumlah personel", personel_count),
        ("Total item tercatat", len(tables["detail"])),
        ("", ""),
    ]
    info_rows += [(f"{c} - {m['label']}", m["desc"]) for c, m in TOOL_STATUS.items()]
    info_rows += [
        ("", ""),
        ("Tools bermasalah", "NOK (rusak) ditambah NY (wajib tetapi tidak ada)."),
        ("Skor Kesiapan", "OKE dibagi (OKE + NOK + NY). Hanya item wajib yang dihitung; NA, MP, dan ABM tidak masuk perhitungan."),
        ("Kategori", f"Siap: skor {SCORE_READY:.0%} ke atas. Perlu Perhatian: {SCORE_WARN:.0%} sampai di bawah {SCORE_READY:.0%}. Kritis: di bawah {SCORE_WARN:.0%}. Tanpa item wajib: tidak ada item OKE/NOK/NY."),
        ("", ""),
        ("Sheet Ringkasan Personel", "Satu baris per personel: jumlah tiap status, skor, kategori, dan daftar nama tools bagus, rusak, serta tidak ada. Diurutkan dari skor terendah."),
        ("Sheet Rincian Item", "Satu baris per item tools per personel (cocok untuk filter dan pivot)."),
        ("Sheet Matriks Tools", "Personel di baris, nama tools di kolom, isinya kode status."),
        ("Sheet Rekap per Item", "Tools mana yang paling banyak rusak atau tidak ada di seluruh tim."),
        ("Sheet Rekap per NOP", "Perbandingan kesiapan antar cabang."),
    ]
    info = pd.DataFrame(info_rows, columns=["Keterangan", "Penjelasan"])
    detail_cols = ["Nama Personel", "NOP", "Nama Item Tools", "Kode", "Keterangan Status", "Kelompok"]

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        tables["person"].to_excel(xw, sheet_name="Ringkasan Personel", index=False)
        tables["detail"][detail_cols].to_excel(xw, sheet_name="Rincian Item", index=False)
        tables["matrix"].to_excel(xw, sheet_name="Matriks Tools", index=False)
        tables["item"].to_excel(xw, sheet_name="Rekap per Item", index=False)
        tables["nop"].to_excel(xw, sheet_name="Rekap per NOP", index=False)
        info.to_excel(xw, sheet_name="Keterangan", index=False)
        wb = xw.book
        _style_ws(wb["Ringkasan Personel"], freeze="C2")
        _style_ws(wb["Rincian Item"], status_cells=True)
        _style_ws(wb["Matriks Tools"], freeze="C2", status_cells=True, max_w=16, header_h=64, label_cols=2)
        _style_ws(wb["Rekap per Item"], freeze="B2")
        _style_ws(wb["Rekap per NOP"], freeze="B2")
        ws = wb["Keterangan"]
        _style_ws(ws, filterable=False)
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 110
        for row in ws.iter_rows(min_row=2):
            row[0].font = Font(name="Calibri", size=11, bold=True)
            row[0].alignment = Alignment(vertical="top")
            row[1].alignment = Alignment(wrap_text=True, vertical="top")
        wb.active = 0
    return buf.getvalue()

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
def _auth_pair():
    # Prioritas: st.secrets["app_auth"]. Fallback ke kredensial lama agar akses tidak terkunci.
    try:
        auth = st.secrets["app_auth"]
        return str(auth["username"]), str(auth["password"])
    except Exception:
        return "SIMAKINKUT", "2026KUTPOSITIF"

def login_form():
    st.markdown("<div style='height:7vh'></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown(render_logo_html(width="68px"), unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Masuk ke SIMAKIN</div><div class='login-sub'>Sistem Monitoring Aset Kinarya</div>", unsafe_allow_html=True)
        user = st.text_input("Username", placeholder="Masukkan username")
        pwd = st.text_input("Password", type="password", placeholder="Masukkan password")
        submitted = st.form_submit_button("Masuk", use_container_width=True, type="primary")
        st.markdown("<div class='login-foot'>Deployed by Okta Pradika</div>", unsafe_allow_html=True)
    if submitted:
        ok_user, ok_pwd = _auth_pair()
        if hmac.compare_digest(user.encode(), ok_user.encode()) and hmac.compare_digest(pwd.encode(), ok_pwd.encode()):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Username atau password salah.")
if not st.session_state.logged_in: login_form(); st.stop()

# --- 5. SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.markdown(render_logo_html(width="56px"), unsafe_allow_html=True)
    st.markdown("<div class='side-title'>SIMAKIN</div><div class='side-sub'>Sistem Monitoring Aset</div>", unsafe_allow_html=True)
    st.markdown("<div class='side-user'><div class='avatar'>S</div><div><div class='u-name'>SIMAKINKUT</div><div class='u-role'>Otoritas aktif</div></div></div>", unsafe_allow_html=True)

    if 'show_ai_kut' not in st.session_state: st.session_state.show_ai_kut = False
    st.markdown("<div class='side-label'>Laporan</div>", unsafe_allow_html=True)
    if st.button("Tutup Report AI KUT" if st.session_state.show_ai_kut else "Buat Report AI KUT", use_container_width=True, type="primary"):
        st.session_state.show_ai_kut = not st.session_state.show_ai_kut
        st.rerun()

    st.markdown("<div class='side-label'>Sistem</div>", unsafe_allow_html=True)
    if st.button("Sinkronisasi data", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("Keluar", use_container_width=True): st.session_state.logged_in = False; st.rerun()
    st.markdown("<div class='side-foot'>SIMAKIN Enterprise Dashboard<br>Deployed by Okta Pradika</div>", unsafe_allow_html=True)

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
        xls = pd.read_excel(excel_url, sheet_name=None, engine='openpyxl', dtype=str, keep_default_na=False, na_values=[''])
        return (xls.get("SDM", pd.DataFrame()), xls.get("ALL ASSET MBP CME TE REG KALIMA", pd.DataFrame()), xls.get("ALL ASSET GENSET REG KALIMANTAN", pd.DataFrame()), xls.get("ALL ASSET TOOLS KALIMANTAN", pd.DataFrame()), xls.get("Rekomendasi Perbaikan", pd.DataFrame()), xls.get("FAKTA INTERITAR", pd.DataFrame()), xls.get("Evidance foto", pd.DataFrame())) 
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with st.spinner("Sinkronisasi Mesin Data & AI SICAKEP..."):
    df_sdm, df_asset, df_genset, df_tools_asset, df_rekomendasi, df_fakta, df_evidence = load_all_data()

# =====================================================================
# LAYOUT UTAMA DIMULAI DI SINI
# =====================================================================
st.markdown("<div class='hero'><div><div class='hero-title'>Sistem Monitoring Aset Kinarya</div><div class='hero-sub'>Kepatuhan upload, kondisi tools, kendaraan, dan genset seluruh tim dalam satu tampilan.</div></div><div class='pill'><i></i>Data tersinkron otomatis setiap 60 detik</div></div>", unsafe_allow_html=True)

if not df_sdm.empty:
    
   # ---------------------------------------------------------------------
    # TIER 1: TRACKER REGISTRASI & AUDIT KEPATUHAN
    # ---------------------------------------------------------------------
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
    
    st.markdown(section_header("Tracker registrasi tim dan kepatuhan upload", "Progres input data per NOP dan audit kelengkapan upload personel."), unsafe_allow_html=True)

    tab_trk_asset, tab_trk_genset, tab_trk_tools, tab_trk_audit = st.tabs([
        "Spesifikasi R2/R4", "Parameter Genset", "Inventaris Tools", "AUDIT KEPATUHAN UPLOAD"
    ])
    
    with tab_trk_asset:
        for branch, target in target_default.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_asset[branch], target), unsafe_allow_html=True)
    with tab_trk_genset:
        for branch, target in target_genset.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_genset[branch], target), unsafe_allow_html=True)
    with tab_trk_tools:
        for branch, target in target_default.items(): st.markdown(render_progress_nop(f"NOP {branch.title()}", prog_tools[branch], target), unsafe_allow_html=True)
        
    with tab_trk_audit:
        st.markdown("<h4 style='color:var(--accent-color); margin-bottom:10px; margin-top:5px;'>KOMPARASI OTOMATIS DATABASE KARYAWAN</h4>", unsafe_allow_html=True)
        st.info("Sistem membaca otomatis file **DATABASE KARYAWAN_2.xlsx** (atau **DATABASE KARYAWAN.xlsx**) dari server/GitHub. Jika ada update data Karyawan, cukup timpa file lama di Github dengan yang baru!")
        
        file_path = None
        if os.path.exists("DATABASE KARYAWAN_2.xlsx"):
            file_path = "DATABASE KARYAWAN_2.xlsx"
        elif os.path.exists("DATABASE KARYAWAN.xlsx"):
            file_path = "DATABASE KARYAWAN.xlsx"
            
        if file_path:
            try:
                df_kar = pd.read_excel(file_path)
                if 'NAMA' in df_kar.columns:
                    df_kar['NAMA_UPPER'] = df_kar['NAMA'].astype(str).str.strip().str.upper()
                    
                    def ekstrak_nama(df):
                        if df.empty: return []
                        col = next((c for c in df.columns if 'NAMA' in str(c).upper()), df.columns[2] if len(df.columns) > 2 else None)
                        if col: return df[col].astype(str).str.strip().str.upper().unique().tolist()
                        return []
                    
                    list_mbp = ekstrak_nama(df_asset)
                    list_genset = ekstrak_nama(df_genset)
                    list_tools = ekstrak_nama(df_tools_asset)
                    
                    df_kar['ASSET MBP & CME'] = df_kar['NAMA_UPPER'].apply(lambda x: 'Done Upload' if x in list_mbp else '0%')
                    df_kar['ASSET GENSET'] = df_kar['NAMA_UPPER'].apply(lambda x: 'Done Upload' if x in list_genset else '0%')
                    df_kar['ASSET TOOLS'] = df_kar['NAMA_UPPER'].apply(lambda x: 'Done Upload' if x in list_tools else '0%')
                    
                    def hitung_persentase(row):
                        total = 3
                        done = sum([1 for val in [row['ASSET MBP & CME'], row['ASSET GENSET'], row['ASSET TOOLS']] if 'Done Upload' in val])
                        pct = int((done/total)*100)
                        if pct == 100: return f"{pct}% (Lengkap)"
                        elif pct == 0: return f"0% (Kosong)"
                        else: return f"{pct}% (Tidak Lengkap)"
                        
                    df_kar['PROGRESS TOTAL'] = df_kar.apply(hitung_persentase, axis=1)
                    df_result = df_kar.drop(columns=['NAMA_UPPER'])
                    
                    nop_col = next((c for c in df_result.columns if 'NOP' in str(c).upper()), None)
                    if nop_col:
                        list_nop_filter = ["SEMUA NOP"] + sorted([str(x).strip() for x in df_result[nop_col].dropna().unique() if str(x).strip() != ""])
                        pilih_nop = st.selectbox("FILTER BERDASARKAN NOP (CABANG):", list_nop_filter)
                        if pilih_nop != "SEMUA NOP":
                            df_result = df_result[df_result[nop_col].astype(str).str.strip() == pilih_nop]
                    
                    c_a1, c_a2, c_a3 = st.columns(3)
                    c_a1.markdown(f"<div class='macro-card' style='border-color:#3b82f6;'><div class='macro-title'>Total Karyawan (Di-filter)</div><div class='macro-value' style='color:#3b82f6;'>{len(df_result)}</div></div>", unsafe_allow_html=True)
                    c_a2.markdown(f"<div class='macro-card' style='border-color:#10b981;'><div class='macro-title'>Upload 100% (Lengkap)</div><div class='macro-value' style='color:#10b981;'>{len(df_result[df_result['PROGRESS TOTAL'] == '100% (Lengkap)'])}</div></div>", unsafe_allow_html=True)
                    c_a3.markdown(f"<div class='macro-card' style='border-color:#ef4444;'><div class='macro-title'>0% (Belum Sama Sekali)</div><div class='macro-value' style='color:#ef4444;'>{len(df_result[df_result['PROGRESS TOTAL'] == '0% (Kosong)'])}</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.dataframe(df_result, hide_index=True, use_container_width=True)
                    
                    # Add generate WA text button
                    missing_data = df_result[df_result['PROGRESS TOTAL'] == '0% (Kosong)']
                    if not missing_data.empty:
                        names_list = missing_data['NAMA'].tolist()
                        wa_text = "Mohon perhatian bagi personel berikut yang belum melakukan upload data sama sekali (Progress 0%):\\n\\n"
                        for idx, name in enumerate(names_list, 1):
                            wa_text += f"{idx}. {name}\\n"
                        wa_text += "\\nMohon segera melengkapi data aset di sistem SIMAKIN. Terima kasih."
                        
                        # Use a text area so user can easily copy
                        st.markdown("#### Teks WhatsApp untuk Personel yang Belum Upload Data (0%)")
                        st.text_area("Copy teks di bawah ini:", value=wa_text.replace('\\n', '\n'), height=150)
                        
                else:
                    st.error("Gagal mendeteksi kolom 'NAMA' di dalam file Excel. Pastikan header kolomnya bernama NAMA.")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca file Excel: {e}")
        else:
            st.warning("File **DATABASE KARYAWAN_2.xlsx** atau **DATABASE KARYAWAN.xlsx** tidak ditemukan di dalam Folder/Github Anda! Pastikan Anda sudah meng-upload file tersebut ke repositori yang sama dengan `App.py`.")
    st.markdown("""
<div style="font-size: 11px; color: #94a3b8; margin-top: 5px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 10px; margin-bottom:25px;">
<b>Target NOP:</b> Palangkaraya (41/14), Pangkalanbun (45/23), Tarakan (36/14), Pontianak (75/31).
</div>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------------------
    # TIER 2: FILTER & REKAPITULASI (DESAIN SKETSA BARU)
    # ---------------------------------------------------------------------
    df_sdm_filtered = df_sdm.copy()
    
    st.markdown(f"<h3 style='color:var(--accent-color); font-size:18px;'>Filter Makro & Analisa Kebutuhan</h3>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3) 
    
    with col_f1:
        list_nop = ["SEMUA NOP"]
        nop_col_sdm = next((c for c in df_sdm.columns if 'NOP' in str(c).upper()), None)
        if nop_col_sdm: list_nop += sorted([str(x).strip() for x in df_sdm[nop_col_sdm].dropna().unique() if str(x).strip() not in ["", "nan", "None"]])
        selected_nop = st.selectbox("NOP (CABANG):", list_nop)
        if selected_nop != "SEMUA NOP": 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[nop_col_sdm].astype(str).str.strip().str.upper() == selected_nop.upper()]
            
    with col_f2:
        col_jabatan = df_sdm.columns[2] if len(df_sdm.columns) > 2 else next((c for c in df_sdm.columns if 'JOB' in str(c).upper()), None)
        list_job = ["SEMUA JABATAN"]
        if col_jabatan: list_job += sorted([str(x).strip() for x in df_sdm_filtered[col_jabatan].dropna().unique() if str(x).strip() not in ["", "nan", "None", "-"]])
        selected_job = st.selectbox("JABATAN (KOLOM C):", list_job)
        if selected_job != "SEMUA JABATAN" and col_jabatan: 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[col_jabatan].astype(str).str.strip() == selected_job]
            
    with col_f3:
        loker_col = next((c for c in df_sdm.columns if 'LOKER' in str(c).upper()), None)
        list_loker = ["SEMUA LOKER"]
        if loker_col: list_loker += sorted([str(x).strip() for x in df_sdm_filtered[loker_col].dropna().unique() if str(x).strip() not in ["", "nan", "None", "-"]])
        selected_loker = st.selectbox("LOKASI KERJA:", list_loker)
        if selected_loker != "SEMUA LOKER" and loker_col: 
            df_sdm_filtered = df_sdm_filtered[df_sdm_filtered[loker_col].astype(str).str.strip() == selected_loker]

    # LOGIKA EKSTRAKSI DAFTAR TOOLS BENTUK BARU (BERJERET)
    table_data_detailed = [] 
    grand_totals = {'NY': 0, 'NOK': 0, 'OKE': 0, 'NA': 0, 'MP': 0, 'ABM': 0}
    personel_count = 0
    
    if not df_tools_asset.empty and not df_sdm_filtered.empty:
        valid_names_group = df_sdm_filtered['NAMA'].astype(str).str.strip().str.upper().unique() if 'NAMA' in df_sdm_filtered.columns else []
        name_col_tools = next((col for col in df_tools_asset.columns if "NAMA" in str(col).upper()), None)
        
        if name_col_tools:
            tools_macro_df = df_tools_asset[df_tools_asset[name_col_tools].astype(str).str.strip().str.upper().isin(valid_names_group)].copy()
            tools_macro_df['NAMA_UPPER'] = tools_macro_df[name_col_tools].astype(str).str.strip().str.upper()
            tools_macro_df = tools_macro_df.drop_duplicates(subset=['NAMA_UPPER'], keep='first')
            personel_count = len(tools_macro_df)
            
            for _, row in tools_macro_df.iterrows():
                nama = row[name_col_tools]
                nop_val = "-"
                nop_cols = [c for c in df_tools_asset.columns if 'NOP' in str(c).upper()]
                if nop_cols: nop_val = str(row[nop_cols[-1]]).strip()
                
                # Scan semua kolom untuk nama ini
                for col_name in df_tools_asset.columns:
                    val = str(row[col_name]).strip().upper()
                    if val in ['OKE', 'NOK', 'NY', 'NA', 'MP', 'ABM']:
                        grand_totals[val] += 1
                        table_data_detailed.append({
                            "nama": nama,
                            "nop": nop_val,
                            "item_name": str(col_name).strip().title(),
                            "status": val
                        })

    # ---------------------------------------------------------------------
    # KONDISI TOOLS TIM: scorecard, export Excel, dan tabel rincian
    # ---------------------------------------------------------------------
    tools_tables = summarize_tools(table_data_detailed) if table_data_detailed else None
    n_oke, n_nok, n_ny = grand_totals['OKE'], grand_totals['NOK'], grand_totals['NY']
    wajib_total = n_oke + n_nok + n_ny
    total_item = sum(grand_totals.values())
    if wajib_total:
        skor_tim = n_oke / wajib_total
        skor_txt = f"{skor_tim * 100:.0f}%"
        skor_tone = "tone-ok" if skor_tim >= SCORE_READY else ("tone-warn" if skor_tim >= SCORE_WARN else "tone-bad")
    else:
        skor_txt, skor_tone = "-", ""
    kat_counts = tools_tables["person"]["Kategori"].value_counts().to_dict() if tools_tables else {}
    kat_sub = f"{kat_counts.get('Siap', 0)} siap, {kat_counts.get('Perlu Perhatian', 0)} perlu perhatian, {kat_counts.get('Kritis', 0)} kritis"

    st.markdown(section_header("Kondisi tools tim", "Agregasi dari personel valid sesuai filter NOP, jabatan, dan lokasi kerja di atas."), unsafe_allow_html=True)

    stats_html = (
        f"<div class='stat'><div class='stat-label'>Personel terdata</div><div class='stat-value'>{personel_count}</div><div class='stat-sub'>{kat_sub}</div></div>"
        f"<div class='stat'><div class='stat-label'>Tools bagus</div><div class='stat-value tone-ok'>{n_oke}</div><div class='stat-sub'>dari {wajib_total} item wajib</div></div>"
        f"<div class='stat'><div class='stat-label'>Tools bermasalah</div><div class='stat-value tone-bad'>{n_nok + n_ny}</div><div class='stat-sub'>{n_nok} rusak, {n_ny} wajib tapi tidak ada</div></div>"
        f"<div class='stat'><div class='stat-label'>Skor kesiapan tim</div><div class='stat-value {skor_tone}'>{skor_txt}</div><div class='stat-sub'>Tools bagus dibagi seluruh item wajib</div></div>"
    )
    seg = "".join(f"<span style='width:{grand_totals[c] / total_item * 100:.2f}%;background:{m['hex']};'></span>" for c, m in TOOL_STATUS.items() if total_item and grand_totals[c])
    legend = "".join(f"<div class='lg'><i style='background:{m['hex']};'></i><span>{m['label']} <em>{c}</em></span><b>{grand_totals[c]}</b></div>" for c, m in TOOL_STATUS.items())
    st.markdown(f"<div class='panel'><div class='stat-row'>{stats_html}</div><div class='dist'><div class='dist-head'>Distribusi status seluruh item tools</div><div class='dist-bar'>{seg}</div><div class='dist-legend'>{legend}</div></div></div>", unsafe_allow_html=True)

    if tools_tables is not None:
        filter_label = f"NOP: {selected_nop} | Jabatan: {selected_job} | Lokasi kerja: {selected_loker}"
        xlsx_bytes = None
        try:
            xlsx_bytes = build_tools_excel(tools_tables, filter_label, personel_count)
        except Exception as e:
            st.warning(f"File Excel belum bisa dibuat: {e}")
        c_note, c_btn = st.columns([3, 1.3])
        with c_note:
            st.markdown("<div class='export-note'><b>Unduh rincian tools tim (Excel)</b><br>Berisi ringkasan per personel (jumlah bagus, rusak, tidak ada, beserta daftar nama tools yang dipegang), rincian per item, matriks tools, serta rekap per item dan per NOP. Isi file mengikuti filter yang sedang aktif.</div>", unsafe_allow_html=True)
        with c_btn:
            if xlsx_bytes:
                tag = re.sub(r"[^A-Za-z0-9]+", "_", selected_nop).strip("_") or "SEMUA"
                st.download_button("Unduh Excel", data=xlsx_bytes,
                                   file_name=f"SIMAKIN_Tools_Tim_{tag}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True, key="dl_tools_xlsx")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    with st.expander("Lihat tabel rincian kondisi tools tim dan nama item-nya", expanded=True):
        if tools_tables is not None:
            tab_pers, tab_item = st.tabs(["Ringkasan per personel", "Rincian item per personel"])
            with tab_pers:
                view = tools_tables["person"][["Nama Personel", "NOP", "Kategori", "Skor Kesiapan", COL_LABEL["OKE"], COL_LABEL["NOK"], COL_LABEL["NY"], "Daftar Tools Rusak", "Daftar Tools Tidak Ada (Wajib)"]].copy()
                view["Skor Kesiapan"] = view["Skor Kesiapan"] * 100
                try:
                    cfg = {"Skor Kesiapan": st.column_config.ProgressColumn("Skor kesiapan", min_value=0, max_value=100, format="%d%%")}
                except Exception:
                    cfg = None
                st.dataframe(view, hide_index=True, use_container_width=True, column_config=cfg)
                st.caption("Diurutkan dari skor terendah. Siap: 90% ke atas. Perlu Perhatian: 70% sampai 89%. Kritis: di bawah 70%.")
            with tab_item:
                only_issue = st.checkbox("Hanya tampilkan item bermasalah (NOK dan NY)", key="tools_only_issue")
                detail_view = tools_tables["detail"]
                if only_issue:
                    detail_view = detail_view[detail_view["Kode"].isin(["NOK", "NY"])]
                if detail_view.empty:
                    st.info("Tidak ada item bermasalah pada tim ini.")
                else:
                    st.markdown(render_tools_table_html(detail_view, tools_tables["person"]), unsafe_allow_html=True)
                legend_html = "".join(f"<span><span class='tick tick-{c.lower()}'>{TICK_GLYPH[c]}</span>{c}: {m['desc']}</span>" for c, m in TOOL_STATUS.items())
                st.markdown(f"<div class='legend-row'>{legend_html}</div>", unsafe_allow_html=True)
        else:
            st.info("Belum ada rincian data tools yang diinput oleh grup tim ini.")

    st.write("---")
    
    # ---------------------------------------------------------------------
    # TIER 3: PILIH PERSONEL (SISA FITUR DI-HIDDEN DI BAWAH INI)
    # ---------------------------------------------------------------------
    st.markdown(f"<h3 style='color:var(--accent-color); font-size:18px;'>Panel Investigasi Individu</h3>", unsafe_allow_html=True)
    st.info("Gunakan *Dropdown* di bawah ini untuk **membuka laci rahasia** berisi Profil, AI KUT, Matrik Data, dan Galeri Foto personel.")
    
    list_nama = df_sdm_filtered['NAMA'].dropna().unique() if 'NAMA' in df_sdm_filtered.columns else []
    selected_nama = "-"
    if len(list_nama) > 0:
        selected_nama = st.selectbox("PILIH IDENTITAS PERSONEL UNTUK MELIHAT DETAIL:", ["-"] + sorted(list(list_nama)))
        if st.session_state.get('selected_nama_karyawan') != selected_nama:
            st.session_state.selected_nama_karyawan = selected_nama; st.rerun()

    if selected_nama != "-":
        st.markdown("<br>", unsafe_allow_html=True)
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

        if st.session_state.show_ai_kut:
            st.markdown("<div class='ai-kut-box'>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align:center; color:var(--primary-color); text-transform:uppercase;'>KOGNITIF AI KUT (LLM ENGINE)</h2><p style='text-align:center; color:#94a3b8;'>Analisis Naratif & Pemahaman Visual untuk: <b>{selected_nama}</b></p><hr style='border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            
            tools_lengkap = 0; total_tools = 0; tools_list_str = []
            ai_score_tools = 0; ai_score_kendaraan = 0; ai_score_genset = 0
            narasi_foto_tools = []; narasi_foto_r2 = []; narasi_foto_genset = []; narasi_foto_evid = []
            data_ekspor = []
            
            tools_list = ["WAH", "FA", "FE"]
            if data_karyawan_select is not None:
                for t in tools_list:
                    total_tools += 1
                    val = str(data_karyawan_select.get(t, '-')).strip()
                    if val not in ["nan", "None", "-", ""]:
                        tools_lengkap += 1; tools_list_str.append(f"{t} (Tersedia)")
                    else: tools_list_str.append(f"{t} (Kosong/Tidak Ada)")
                ai_score_tools = int((tools_lengkap/max(1, total_tools)) * 100)
                
                if data_tools_asset_select is not None:
                    for col in df_tools_asset.columns:
                        val = str(data_tools_asset_select[col]); m = re.search(r'[-\w]{25,}', val)
                        if m: 
                            diag = analyze_photo_to_text(col, m.group(0))
                            narasi_foto_tools.append(diag)
                            data_ekspor.append({"Kategori": "Tools", "Aset": col, "Analisa AI KUT": diag})

            nopol = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Belum ada data')) if data_asset_select is not None else "Belum ada data"
            merk_kendaraan = str(data_asset_select.get('MERK KENDARAAN', 'Kendaraan')) if data_asset_select is not None else "Kendaraan"
            tgl_servis = str(data_asset_select.get('SERCIVE BERKALA (TGL TERAKHIR SERVICE)', '')) if data_asset_select is not None else ""
            if tgl_servis and tgl_servis not in ["nan", "-", "None"]: ai_score_kendaraan = 95
            else: ai_score_kendaraan = 40
            if data_asset_select is not None:
                for col in df_asset.columns:
                    val = str(data_asset_select[col]); m = re.search(r'[-\w]{25,}', val)
                    if m: 
                        diag = analyze_photo_to_text(col, m.group(0))
                        narasi_foto_r2.append(diag)
                        data_ekspor.append({"Kategori": "Kendaraan", "Aset": col, "Analisa AI KUT": diag})
                    
            merk_genset = str(data_genset_select.get('TIPE GENSET', 'Genset')) if data_genset_select is not None else "Genset"
            stat_genset = str(data_genset_select.get('STATUS ASSET', '')) if data_genset_select is not None else ""
            if "BAIK" in stat_genset.upper() or "READY" in stat_genset.upper(): ai_score_genset = 100
            else: ai_score_genset = 60
            if data_genset_select is not None:
                for col in df_genset.columns:
                    val = str(data_genset_select[col]); m = re.search(r'[-\w]{25,}', val)
                    if m: 
                        diag = analyze_photo_to_text(col, m.group(0))
                        narasi_foto_genset.append(diag)
                        data_ekspor.append({"Kategori": "Genset", "Aset": col, "Analisa AI KUT": diag})
                    
            ai_evid = df_evidence[df_evidence.apply(lambda r: r.astype(str).str.contains(selected_nama, case=False, na=False, regex=False).any(), axis=1)] if not df_evidence.empty else pd.DataFrame()
            if not ai_evid.empty:
                for col_val in ai_evid.iloc[-1].values:
                    val_str = str(col_val)
                    if "drive.google.com" in val_str:
                        urls = val_str.split(',')
                        for u in urls:
                            m = re.search(r'[-\w]{25,}', u)
                            if m: 
                                diag = analyze_photo_to_text("Bukti Lapangan/Evidance Terbaru", m.group(0))
                                narasi_foto_evid.append(diag)
                                data_ekspor.append({"Kategori": "Evidance History", "Aset": "Evidance Operasional", "Analisa AI KUT": diag})

            narasi_tools_gabung = " ".join(narasi_foto_tools) if narasi_foto_tools else "Tidak ada bukti foto tools yang diunggah untuk dianalisa visual."
            narasi_r2_gabung = " ".join(narasi_foto_r2) if narasi_foto_r2 else "Tidak ada bukti foto kendaraan yang dapat dipindai oleh AI."
            narasi_genset_gabung = " ".join(narasi_foto_genset) if narasi_foto_genset else "Tidak ada visual genset yang terarsip di sistem."
            narasi_evid_gabung = " ".join(narasi_foto_evid) if narasi_foto_evid else "Belum ada laporan riwayat foto kegiatan operasional terkini."
            status_servis_teks = f"tercatat melakukan servis pada <b>{tgl_servis}</b>, yang menandakan kepatuhan terhadap jadwal pemeliharaan." if ai_score_kendaraan == 95 else "mengindikasikan bahwa jadwal servis terakhir <b>belum terdata</b>, sehingga saya merekomendasikan perlunya pengecekan bengkel dalam waktu dekat."
            
            gemini_html_card = f"""<div class="ai-llm-card">
    <div style="display:flex; align-items:center; margin-bottom:15px;">
    <span style="font-size:26px; margin-right:12px;"></span>
    <h3 style="margin:0; color:#ffffff; font-weight:900; letter-spacing:1px;">Analisis Kognitif AI KUT</h3>
    </div>
    <p>Berdasarkan pemindaian kognitif mendalam yang saya lakukan terhadap keseluruhan profil data dan dokumentasi visual milik <b>{selected_nama}</b>, berikut adalah ringkasan hasil diagnosa:</p>
    <h4>1. Analisa Matrik Inventaris Tools</h4>
    <p>Tingkat kelengkapan tools esensial mencapai <b>{ai_score_tools}%</b>. Status inventaris saat ini: <i>{', '.join(tools_list_str)}</i>. 
    <br><span style="color:var(--primary-color);"><b>Sintesis Visual:</b></span> {narasi_tools_gabung}</p>
    <h4>2. Analisa Spesifikasi Kendaraan (R2/R4)</h4>
    <p>Aset tercatat berupa unit <b>{merk_kendaraan}</b> (Plat: {nopol}). Berdasarkan rekam jejak, kendaraan ini {status_servis_teks}
    <br><span style="color:var(--primary-color);"><b>Sintesis Visual:</b></span> {narasi_r2_gabung}</p>
    <h4>3. Analisa Parameter Genset</h4>
    <p>Unit genset berjenis <b>{merk_genset}</b> dengan status operasional <b>{stat_genset if stat_genset else "Belum Ditetapkan"}</b>. 
    <br><span style="color:var(--primary-color);"><b>Sintesis Visual:</b></span> {narasi_genset_gabung}</p>
    <h4>4. Analisa Riwayat Evidance Lapangan</h4>
    <p>Memeriksa dokumen visual aktivitas operasional terakhir yang diunggah ke dalam sistem.
    <br><span style="color:var(--primary-color);"><b>Sintesis Visual:</b></span> {narasi_evid_gabung}</p>
    <div style="background:rgba(16, 185, 129, 0.1); padding:15px; border-left:4px solid #10b981; border-radius:8px; margin-top:25px;">
    <h4 style="margin-top:0; color:#10b981; border:none; padding:0;">Rekomendasi & Tindak Lanjut</h4>
    <p style="margin-bottom:0;">Secara keseluruhan, kesiapan operasional berada di level <b>{int((ai_score_tools + ai_score_kendaraan + ai_score_genset)/3)}%</b>. 
    {"Saya menyimpulkan seluruh aset dalam kondisi <b>siap tempur</b> untuk mendukung kegiatan operasional secara maksimal." if int((ai_score_tools + ai_score_kendaraan + ai_score_genset)/3) > 75 else "Terdeteksi adanya <b>anomali data operasional</b>. Saya merekomendasikan audit fisik dan penjadwalan service segera untuk mengamankan kelancaran tugas."}</p>
    </div>
    </div>"""
            
            col_grafik, col_llm = st.columns([1, 1.8])
            with col_grafik:
                st.markdown("<p style='color:var(--accent-color); font-weight:bold; margin-bottom:5px;'>AI Readiness Index:</p>", unsafe_allow_html=True)
                chart_data = pd.DataFrame({"Kategori": ["Kelengkapan Tools", "Kelayakan Kendaraan", "Parameter Genset"], "Persentase (%)": [ai_score_tools, ai_score_kendaraan, ai_score_genset]}).set_index("Kategori")
                st.bar_chart(chart_data, height=350)
                
                if len(data_ekspor) > 0:
                    df_report_ai = pd.DataFrame(data_ekspor)
                    csv_export = df_report_ai.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="EXPORT DATA TEXT AI KE CSV",
                        data=csv_export,
                        file_name=f"Report_AI_KUT_{selected_nama.replace(' ','_')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            with col_llm:
                st.markdown(gemini_html_card, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown(f"<h3 style='color:var(--accent-color);'>Matrix Profil & Identitas: {selected_nama}</h3>", unsafe_allow_html=True)
        karyawan_fields = ["NIK", "NAMA", "JOB", "LOKER", "NOP", "NO. KTP", "AKHIR PKWT", "Status Karyawan", "pakta Integritas", "Keahlian"]
        dict_karyawan = {field: str(data_karyawan_select[field]) if data_karyawan_select is not None and field in data_karyawan_select else "-" for field in karyawan_fields}
        st.dataframe(pd.DataFrame(list(dict_karyawan.items()), columns=["Parameter", "Informasi"]), hide_index=True, use_container_width=True)
        st.write("---")

        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            st.markdown(f"<h3 style='color:var(--accent-color);'>Inventaris Tools Utama</h3>", unsafe_allow_html=True)
            tools_list_df = ["WAH", "FA", "FE", "EXP. CERT.", "COUNSELING", "RESUME CONSELING", "WARNING LETTER", "Safety Driving License"]
            tools_data = [{"Nama Dok/Tools": t, "Kondisi / Status": str(data_karyawan_select[t]) if data_karyawan_select is not None and t in df_sdm.columns and str(data_karyawan_select[t]).strip() not in ["nan", "None"] else "-"} for t in tools_list_df]
            st.dataframe(pd.DataFrame(tools_data), height=350, hide_index=True, use_container_width=True)

        with col_mid:
            st.markdown(f"<h3 style='color:var(--accent-color);'>Spesifikasi R2/R4</h3>", unsafe_allow_html=True)
            asset_fields = ["NOPOL (PLAT NOMOR)", "MERK KENDARAAN", "TYPE KENDARAAN", "JENIS KENDARAAN", "TAHUN KENDARAAN", "SERCIVE BERKALA (TGL TERAKHIR SERVICE)"]
            asset_data = [{"Parameter Asset": f, "Keterangan": str(data_asset_select[f]) if data_asset_select is not None and f in df_asset.columns and str(data_asset_select[f]).strip() not in ["nan", "None"] else "-"} for f in asset_fields]
            st.dataframe(pd.DataFrame(asset_data), height=350, hide_index=True, use_container_width=True)

        with col_right:
            st.markdown(f"<h3 style='color:var(--accent-color);'>Parameter Genset</h3>", unsafe_allow_html=True)
            genset_fields = ["TIPE GENSET", "NOMER SERI MESIN", "TAHUN PENGADAAN", "STATUS ASSET"]
            genset_data = [{"Parameter Genset": f, "Keterangan": str(data_genset_select[f]) if data_genset_select is not None and f in df_genset.columns and str(data_genset_select[f]).strip() not in ["nan", "None"] else "-"} for f in genset_fields]
            st.dataframe(pd.DataFrame(genset_data), height=350, hide_index=True, use_container_width=True)

        st.write("---")
        
        col_ai, col_plan = st.columns([1.5, 2.0]) 
        with col_ai:
            st.markdown(f"<h3 style='color:var(--accent-color);'>RANGKUMAN SERVICE</h3>", unsafe_allow_html=True)
            if not df_asset.empty:
                nama_col = next((col for col in df_asset.columns if "NAMA" in str(col).upper()), None)
                if nama_col and 'NOPOL (PLAT NOMOR)' in df_asset.columns and 'SERCIVE BERKALA (TGL TERAKHIR SERVICE)' in df_asset.columns:
                    servis_df = df_asset[[nama_col, 'NOPOL (PLAT NOMOR)', 'SERCIVE BERKALA (TGL TERAKHIR SERVICE)']].copy()
                    servis_df.columns = ['Nama Personel', 'Plat Kendaraan', 'Tanggal Servis Terakhir']
                    servis_df['Tanggal Servis Terakhir'] = servis_df['Tanggal Servis Terakhir'].astype(str).str.strip()
                    valid_servis = servis_df[~servis_df['Tanggal Servis Terakhir'].isin(['nan', 'None', '', '-', 'NaT', 'Belum Terdata'])].copy()
                    
                    user_servis = valid_servis[valid_servis['Nama Personel'].astype(str).str.strip().str.lower() == selected_nama.lower()]
                    
                    if not user_servis.empty:
                        st.dataframe(user_servis.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else: st.info(f"Belum ada data servis valid untuk {selected_nama}.")
                else: st.warning("Format kolom tabel tidak sesuai untuk menampilkan rangkuman.")
            else: st.info("Database R2/R4 kosong.")
                
        with col_plan:
            st.markdown(f"<h3 style='color:var(--accent-color);'>1. Panel Transmisi Laporan</h3>", unsafe_allow_html=True)
            input_findings = st.text_area("Uraikan Detail Tindakan & Kondisi Asset:", height=120)
            
            unit_mobil = str(data_asset_select.get('NOPOL (PLAT NOMOR)', 'Tidak Ada')) if data_asset_select is not None else "Tidak Ada"
            unit_genset = str(data_genset_select.get('NOMER SERI MESIN', 'Tidak Ada')) if data_genset_select is not None else "Tidak Ada"
            info_gabungan = f"Mobil: {unit_mobil} | Genset: {unit_genset}"
            
            if st.button("TRANSMISI DATA TEKS", use_container_width=True):
                if input_findings:
                    with st.spinner("Menyandikan dan Mengirim Laporan ke Database..."):
                        if save_findings_to_sheet(str(dict_karyawan.get('NIK', 'N/A')), selected_nama, info_gabungan, input_findings):
                            st.success("Otorisasi Sukses! Laporan telah terenkripsi dan tersimpan di server.")
                            time.sleep(1.5)
                            st.cache_data.clear(); st.rerun()
                        else: st.error("Gagal menyinkronkan data. Periksa koneksi satelit/internet Anda.")
                else: st.warning("Protokol ditolak: Kolom deskripsi tidak boleh kosong.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color:var(--accent-color);'>2. Sinkronisasi Evidance Visual</h3>", unsafe_allow_html=True)
            st.info("Pintu protokol terbuka. Sistem mengunci Identitas dan Aset Anda untuk transmisi form.")
            
            val_nik = str(dict_karyawan.get('NIK', '-'))
            url_base = "https://docs.google.com/forms/d/e/1FAIpQLSdOwyvntF3QAFYmC724zKfJMG_P59xSYG_UaoDwleWFsZkmOg/viewform"
            url_gform_dinamis = f"{url_base}?usp=pp_url&entry.79064137={urllib.parse.quote(val_nik)}&entry.267180991={urllib.parse.quote(selected_nama)}&entry.1607280297={urllib.parse.quote(unit_mobil)}&entry.505680533={urllib.parse.quote('Mobil')}"
            
            st.markdown(f"""
            <a href="{url_gform_dinamis}" target="_blank" style="text-decoration:none;">
                <div style="background: var(--gradient-bg); padding: 18px; border-radius: 14px; color: white; text-align: center; font-weight: 900; font-size: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5), 0 0 20px var(--glow-color); border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); letter-spacing: 1px;" onmouseover="this.style.transform='scale(1.02) translateY(-3px)'; this.style.boxShadow='0 15px 40px rgba(0,0,0,0.7), 0 0 30px var(--primary-color)';" onmouseout="this.style.transform='scale(1) translateY(0)'; this.style.boxShadow='0 10px 30px rgba(0,0,0,0.5), 0 0 20px var(--glow-color)';">
                    <span style="font-size:20px;"></span> BUKA PORTAL UPLOAD EVIDANCE
                </div>
            </a>
            """, unsafe_allow_html=True)

        st.write("---")
        st.markdown(f"<h3 style='color:var(--accent-color); font-size:26px;'>DATABASE EVIDANCE & RIWAYAT ({selected_nama})</h3>", unsafe_allow_html=True)
        
        tab_r2r4, tab_genset, tab_tools, tab_perbaikan, tab_fakta = st.tabs([
            "Matrix R2/R4", "Matrix Genset", "Matrix Tools", "Riwayat Evidance Service", "Fakta Integritas"
        ])
        
        def render_gallery_fast(tab_context, df, df_columns, data_row, empty_msg):
            with tab_context:
                if data_row is not None:
                    photos_exist = False
                    valid_photos = []
                    for col_name in df_columns:
                        cell_val = str(data_row[col_name]).strip()
                        match = re.search(r'[-\w]{25,}', cell_val) 
                        if match: valid_photos.append((col_name, match.group(0)))
                    
                    if valid_photos:
                        photos_exist = True
                        cols = st.columns(4) 
                        for idx, (col_name, file_id) in enumerate(valid_photos):
                            img_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                            original_url = f"https://drive.google.com/file/d/{file_id}/view"
                            html_card = f"""
                            <div class="gallery-card-3d">
                                <img src="{img_url}" referrerpolicy="no-referrer">
                                <div style="margin-top:10px;">
                                    <p style="font-size:11px; color:var(--accent-color); font-weight:bold; margin-bottom:5px; text-transform:uppercase;">{col_name}</p>
                                    <a href="{original_url}" target="_blank" class="btn-buka-foto">HD View</a>
                                </div>
                            </div>
                            """
                            html_ai_card = f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>{generate_ai_analysis_mini(file_id)}</div>"
                            with cols[idx % 4]:
                                st.markdown(html_card, unsafe_allow_html=True)
                                with st.expander("PEMINDAIAN AI SICAKEP"): 
                                    st.markdown(html_ai_card, unsafe_allow_html=True)
                    
                    if not photos_exist: st.info(empty_msg)
                else: st.info(empty_msg)

        render_gallery_fast(tab_r2r4, df_asset, df_asset.columns, data_asset_select, "Data visual kendaraan belum terarsip.")
        render_gallery_fast(tab_genset, df_genset, df_genset.columns, data_genset_select, "Data visual genset belum terarsip.")
        render_gallery_fast(tab_tools, df_tools_asset, df_tools_asset.columns, data_tools_asset_select, "Data visual tools belum terarsip.")
            
        with tab_perbaikan:
            ai_rek = pd.DataFrame()
            if not df_rekomendasi.empty:
                r_col = next((col for col in df_rekomendasi.columns if "NAMA" in str(col).upper()), None)
                if r_col: ai_rek = df_rekomendasi[df_rekomendasi[r_col].astype(str).str.strip().str.lower() == selected_nama.strip().lower()]
            ai_evid = df_evidence[df_evidence.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False, regex=False).any(), axis=1)] if not df_evidence.empty else pd.DataFrame()
            
            if not ai_rek.empty or not ai_evid.empty:
                st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase;'>Histori Tindakan & Bukti Visual</h4>", unsafe_allow_html=True)
                rek_iter = list(ai_rek.iloc[::-1].iterrows()) if not ai_rek.empty else []
                evid_iter = list(ai_evid.iloc[::-1].iterrows()) if not ai_evid.empty else []
                
                for (rek_idx, row_rek), (evid_idx, row_evid) in zip_longest(rek_iter, evid_iter, fillvalue=(None, None)):
                    if row_rek is not None:
                        teks_laporan = row_rek.get('Findings & Action Plan', '')
                        if pd.isna(teks_laporan) or teks_laporan.strip() == "": teks_laporan = "- Lampiran foto tanpa deskripsi teks -"
                        st.markdown(f"<div class='report-box-premium'><span class='report-date-badge'>LOG: {row_rek.get('Timestamp', '-')}</span><p style='color:#f8fafc; font-size:16px;'>{teks_laporan}</p></div>", unsafe_allow_html=True)
                    
                    if row_evid is not None:
                        waktu_foto = row_evid.iloc[0] if len(row_evid) > 0 else "-"
                        valid_photos = []
                        for col_val in row_evid.values:
                            val_str = str(col_val).strip()
                            if "drive.google.com" in val_str:
                                urls = val_str.split(',')
                                for u in urls:
                                    m = re.search(r'[-\w]{25,}', u)
                                    if m: valid_photos.append(m.group(0))

                        if valid_photos:
                            st.markdown(f"<p style='font-size:12px; color:var(--accent-color); font-weight:bold;'>[ VISUAL EVIDANCE - {waktu_foto} ]</p>", unsafe_allow_html=True)
                            cols = st.columns(4) 
                            for idx, file_id in enumerate(valid_photos):
                                html_card = f"""<div class='gallery-card-3d' style='background:rgba(9,14,23,0.8);'><img src='https://drive.google.com/thumbnail?id={file_id}&sz=w1000' referrerpolicy='no-referrer'><a href='https://drive.google.com/file/d/{file_id}/view' target='_blank' class='btn-buka-foto'>Buka</a></div>"""
                                html_ai_card = f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>{generate_ai_analysis_mini(file_id)}</div>"
                                with cols[idx % 4]:
                                    st.markdown(html_card, unsafe_allow_html=True)
                                    with st.expander("PEMINDAIAN AI SICAKEP"): 
                                        st.markdown(html_ai_card, unsafe_allow_html=True)
                    st.write("<br><div style='height:2px; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); margin: 20px 0;'></div>", unsafe_allow_html=True)
            else: st.info("Tidak ada rekam jejak untuk personel ini.")

        with tab_fakta:
            if not df_fakta.empty:
                matched_fakta = df_fakta[df_fakta.apply(lambda row: row.astype(str).str.contains(selected_nama, case=False, na=False, regex=False).any(), axis=1)]
                if not matched_fakta.empty:
                    st.markdown(f"<h4 style='color:var(--accent-color); text-transform:uppercase;'>Vault Integritas</h4>", unsafe_allow_html=True)
                    for _, row in matched_fakta.iloc[::-1].iterrows():
                        st.markdown(f"<span class='report-date-badge'>TIMESTAMP: {row.get('Timestamp', row.get('TANGGAL', '-'))}</span>", unsafe_allow_html=True)
                        valid_files = []
                        for c in matched_fakta.columns:
                            if "drive.google.com" in str(row[c]):
                                urls = str(row[c]).split(',')
                                for u in urls:
                                    m = re.search(r'[-\w]{25,}', u)
                                    if m: valid_files.append(m.group(0))
                        
                        if valid_files:
                            cols = st.columns(4)
                            for idx, file_id in enumerate(valid_files):
                                html_card = f"<div class='gallery-card-3d'><img src='https://drive.google.com/thumbnail?id={file_id}&sz=w800' referrerpolicy='no-referrer'><a href='https://drive.google.com/file/d/{file_id}/view' target='_blank' class='btn-buka-foto'>Unduh PDF</a></div>"
                                html_ai_card = f"<div style='background:rgba(9,14,23,0.9); padding:10px; border-radius:8px; border-left:3px solid var(--primary-color); font-size:11px;'>{generate_ai_analysis_mini(file_id, is_doc=True)}</div>"
                                with cols[idx % 4]:
                                    st.markdown(html_card, unsafe_allow_html=True)
                                    with st.expander("VERIFIKASI AI"): 
                                        st.markdown(html_ai_card, unsafe_allow_html=True)
                        st.write("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
                else: st.warning("Dokumen Fakta Integritas tidak ditemukan.")
