import os
import time
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import json
import csv
from datetime import datetime, time as dtime
import threading

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="JASAKULA Presensi",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Sistem Presensi PT JASAKULA PURWALUHUR v1.0"}
)

st.markdown("""
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    :root {
        --primary: #1d4ed8;
        --primary-dark: #1e40af;
        --primary-light: #93c5fd;
        --accent: #f59e0b;
        --accent-dark: #d97706;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --bg-input: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border-color: #334155;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --late: #f97316;
    }

    body, .main, .stApp {
        background: linear-gradient(160deg, #0f172a 0%, #1e1b3a 100%);
        color: var(--text-primary);
    }

    /* ── Header ── */
    .header-wrap {
        background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 60%, #7c3aed 100%);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        box-shadow: 0 8px 32px rgba(29,78,216,0.35);
    }
    .header-logo {
        font-size: 3.2rem;
        filter: drop-shadow(0 2px 8px rgba(0,0,0,0.4));
    }
    .header-text h1 {
        font-size: 1.8rem;
        font-weight: 800;
        color: #fff;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }
    .header-text .sub {
        font-size: 0.85rem;
        color: #bfdbfe;
        font-weight: 400;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 0.25rem;
    }
    .header-badge {
        margin-left: auto;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 20px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        color: #fff;
        backdrop-filter: blur(8px);
    }

    /* ── Cards ── */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .card-header {
        font-size: 1rem;
        font-weight: 700;
        color: var(--primary-light);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ── Status Chips ── */
    .chip {
        display: inline-block;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .chip-on-time { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid #10b981; }
    .chip-late    { background: rgba(249,115,22,0.15);  color: #f97316; border: 1px solid #f97316; }
    .chip-absent  { background: rgba(239,68,68,0.15);   color: #ef4444; border: 1px solid #ef4444; }

    /* ── Attendance Cards ── */
    .att-row {
        background: var(--bg-input);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        border-left: 4px solid var(--primary);
    }
    .att-row.late { border-left-color: var(--late); }
    .att-name { font-weight: 700; font-size: 0.95rem; flex: 1; }
    .att-time { font-size: 0.85rem; color: var(--text-secondary); }
    .att-type { font-size: 0.75rem; font-weight: 600; }

    /* ── Metric boxes ── */
    .metric-box {
        background: var(--bg-input);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-val { font-size: 2rem; font-weight: 800; color: var(--primary-light); line-height: 1.1; margin-top: 0.25rem; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        font-size: 0.95rem;
        cursor: pointer;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(29,78,216,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(29,78,216,0.4);
    }

    /* ── Jam realtime ── */
    .clock-display {
        text-align: center;
        background: var(--bg-input);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .clock-time {
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--accent);
        font-variant-numeric: tabular-nums;
        letter-spacing: 2px;
    }
    .clock-date { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem; }

    /* ── Schedule box ── */
    .schedule-box {
        background: linear-gradient(135deg, rgba(29,78,216,0.15), rgba(124,58,237,0.1));
        border: 1px solid rgba(29,78,216,0.4);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .sched-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
    .sched-val { font-size: 1.3rem; font-weight: 700; color: #fff; margin-top: 0.1rem; }
    .sched-late { font-size: 0.75rem; color: var(--late); margin-top: 0.1rem; }

    /* ── Confidence bar ── */
    .conf-wrap { margin: 0.5rem 0; }
    .conf-row { display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 3px; }
    .conf-bar { background: var(--border-color); border-radius: 4px; height: 5px; overflow: hidden; }
    .conf-fill-hi { height: 100%; background: linear-gradient(90deg,#10b981,#6ee7b7); border-radius: 4px; }
    .conf-fill-md { height: 100%; background: linear-gradient(90deg,#f59e0b,#fcd34d); border-radius: 4px; }
    .conf-fill-lo { height: 100%; background: linear-gradient(90deg,#ef4444,#fca5a5); border-radius: 4px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f35 0%, #0f172a 100%);
        border-right: 1px solid var(--border-color);
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS & HELPERS
# ============================================================================

PRESENSI_FILE = "data_presensi.json"
CSV_FILE      = "rekap_presensi.csv"
LOCK          = threading.Lock()

# ── Persistence helpers ──────────────────────────────────────────────────────

def load_presensi() -> dict:
    if os.path.exists(PRESENSI_FILE):
        with open(PRESENSI_FILE, "r") as f:
            return json.load(f)
    return {}

def save_presensi(data: dict):
    with LOCK:
        with open(PRESENSI_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def export_csv(data: dict):
    rows = []
    for date_key, day_data in data.items():
        for emp, recs in day_data.items():
            for r in recs:
                rows.append({
                    "Tanggal": date_key,
                    "Nama": emp,
                    "Tipe": r.get("tipe", ""),
                    "Jam": r.get("jam", ""),
                    "Status": r.get("status", ""),
                    "Confidence": r.get("confidence", ""),
                })
    if not rows:
        return
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Tanggal","Nama","Tipe","Jam","Status","Confidence"])
        writer.writeheader()
        writer.writerows(rows)

# ── Time helpers ─────────────────────────────────────────────────────────────

def get_now():
    return datetime.now()

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def compute_status(now_time: dtime, masuk_time: dtime, toleransi_menit: int, tipe: str) -> str:
    """Return 'Tepat Waktu', 'Terlambat X menit', atau 'Tidak Ada Jadwal'"""
    if tipe == "Masuk":
        delta = (datetime.combine(datetime.today(), now_time)
                 - datetime.combine(datetime.today(), masuk_time))
        mins = int(delta.total_seconds() / 60)
        if mins <= 0:
            return "Tepat Waktu"
        elif mins <= toleransi_menit:
            return f"Terlambat {mins} menit (dalam toleransi)"
        else:
            return f"Terlambat {mins} menit"
    else:
        return "Selesai Bekerja"

# ── Draw boxes ───────────────────────────────────────────────────────────────

def parse_results(result):
    dets = []
    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            dets.append((cls_id, conf, x1, y1, x2, y2))
    return dets

def draw_boxes(image_bgr: np.ndarray, detections: list, names: dict, status_map: dict = None) -> np.ndarray:
    img = image_bgr.copy()
    for idx, (cls_id, conf, x1, y1, x2, y2) in enumerate(detections):
        name  = names.get(cls_id, str(cls_id))
        label = f"{name}  {conf*100:.1f}%"

        if conf >= 0.75:
            color = (16, 185, 129)
        elif conf >= 0.50:
            color = (245, 158, 11)
        else:
            color = (239, 68, 68)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        lsz = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
        ly  = max(y1 - 10, 22)
        cv2.rectangle(img, (x1-4, ly-lsz[1]-8), (x1+lsz[0]+6, ly+5), color, -1)
        cv2.putText(img, label, (x1, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2, cv2.LINE_AA)

        # status bawah
        if status_map and name in status_map:
            status_txt = status_map[name]
            s_color = (16,185,129) if "Tepat" in status_txt else (249,115,22)
            cv2.rectangle(img, (x1, y2+2), (x1+300, y2+26), s_color, -1)
            cv2.putText(img, status_txt, (x1+4, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
    return img

# ── Model loader ─────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_model(path: str):
    if not os.path.exists(path):
        return None
    return YOLO(path)

# ============================================================================
# SESSION STATE
# ============================================================================

if "cam_active"      not in st.session_state: st.session_state.cam_active      = False
if "absen_log"       not in st.session_state: st.session_state.absen_log       = {}   # {nama: {jam, tipe, status}}
if "absen_done"      not in st.session_state: st.session_state.absen_done      = set()
if "tipe_presensi"   not in st.session_state: st.session_state.tipe_presensi   = "Masuk"
if "jam_masuk"       not in st.session_state: st.session_state.jam_masuk       = dtime(8, 0)
if "jam_keluar"      not in st.session_state: st.session_state.jam_keluar      = dtime(17, 0)
if "toleransi"       not in st.session_state: st.session_state.toleransi       = 15
if "conf_thresh"     not in st.session_state: st.session_state.conf_thresh     = 0.45
if "iou_thresh"      not in st.session_state: st.session_state.iou_thresh      = 0.45

# ============================================================================
# LOAD MODEL
# ============================================================================

model_path = "best.pt"
model      = load_model(model_path)

# ============================================================================
# HEADER
# ============================================================================

now_dt = get_now()
st.markdown(f"""
<div class="header-wrap">
    <div class="header-logo">🏢</div>
    <div class="header-text">
        <h1>Sistem Presensi Digital</h1>
        <div class="sub">PT JASAKULA PURWALUHUR</div>
    </div>
    <div class="header-badge">📅 {now_dt.strftime("%A, %d %B %Y")}</div>
</div>
""", unsafe_allow_html=True)

if model is None:
    st.error("❌ Model `best.pt` tidak ditemukan. Letakkan file model di folder yang sama.")
    st.stop()

names = model.names

# ============================================================================
# SIDEBAR — PENGATURAN
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Pengaturan Presensi")
    st.markdown("---")

    st.markdown("### 🕐 Jadwal Kerja")

    h_masuk = st.number_input("Jam Masuk (Jam)", 0, 23, st.session_state.jam_masuk.hour, key="h_masuk")
    m_masuk = st.number_input("Jam Masuk (Menit)", 0, 59, st.session_state.jam_masuk.minute, key="m_masuk")
    st.session_state.jam_masuk = dtime(h_masuk, m_masuk)

    h_keluar = st.number_input("Jam Keluar (Jam)", 0, 23, st.session_state.jam_keluar.hour, key="h_keluar")
    m_keluar = st.number_input("Jam Keluar (Menit)", 0, 59, st.session_state.jam_keluar.minute, key="m_keluar")
    st.session_state.jam_keluar = dtime(h_keluar, m_keluar)

    st.session_state.toleransi = st.slider(
        "⏱ Toleransi Keterlambatan (menit)", 0, 60, st.session_state.toleransi,
        help="Berapa menit terlambat masih dianggap dalam toleransi"
    )

    st.markdown("---")
    st.markdown("### 🎯 Parameter Deteksi")
    st.session_state.conf_thresh = st.slider("Confidence Threshold", 0.05, 1.0, st.session_state.conf_thresh, 0.01)
    st.session_state.iou_thresh  = st.slider("IoU (NMS)", 0.05, 1.0, st.session_state.iou_thresh, 0.01)

    st.markdown("---")
    st.markdown("### 📂 Reset Sesi")
    if st.button("🗑️ Hapus Log Sesi Ini"):
        st.session_state.absen_log  = {}
        st.session_state.absen_done = set()
        st.success("Log sesi dihapus.")

# ============================================================================
# JADWAL & JAM SEKARANG (INFO PANEL)
# ============================================================================

col_a, col_b, col_c = st.columns(3)

jam_masuk_str  = st.session_state.jam_masuk.strftime("%H:%M")
jam_keluar_str = st.session_state.jam_keluar.strftime("%H:%M")
tol            = st.session_state.toleransi
batas_terlambat = (datetime.combine(datetime.today(), st.session_state.jam_masuk)
                   + __import__("datetime").timedelta(minutes=tol)).strftime("%H:%M")

with col_a:
    st.markdown(f"""
    <div class="schedule-box">
        <div class="sched-label">⏰ Jam Masuk</div>
        <div class="sched-val">{jam_masuk_str}</div>
        <div class="sched-late">Batas toleransi: {batas_terlambat} (+{tol} mnt)</div>
    </div>""", unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class="schedule-box">
        <div class="sched-label">🏁 Jam Keluar</div>
        <div class="sched-val">{jam_keluar_str}</div>
        <div class="sched-late">Setelah jam pulang</div>
    </div>""", unsafe_allow_html=True)

with col_c:
    st.markdown(f"""
    <div class="clock-display">
        <div class="clock-time">{now_dt.strftime("%H:%M:%S")}</div>
        <div class="clock-date">{now_dt.strftime("%d %b %Y")}</div>
    </div>""", unsafe_allow_html=True)

# ============================================================================
# MODE SELECTOR
# ============================================================================

st.markdown("---")
mode = st.radio(
    "Mode Presensi",
    ["📸 Presensi via Foto", "🎥 Presensi via Kamera Realtime"],
    horizontal=True,
    label_visibility="collapsed"
)

tipe_presensi = st.radio(
    "Jenis Presensi",
    ["Masuk", "Keluar"],
    horizontal=True,
    help="Pilih apakah ini absen masuk atau absen keluar"
)
st.session_state.tipe_presensi = tipe_presensi

# ============================================================================
# FUNGSI SIMPAN PRESENSI
# ============================================================================

def record_attendance(name: str, conf: float, tipe: str):
    """Catat kehadiran ke session state dan file JSON."""
    if name in st.session_state.absen_done and tipe == "Masuk":
        return None   # sudah absen hari ini (masuk)

    now = get_now()
    jam_str    = now.strftime("%H:%M:%S")
    tanggal    = today_str()

    status = compute_status(
        now.time(),
        st.session_state.jam_masuk,
        st.session_state.toleransi,
        tipe
    )

    record = {
        "jam"        : jam_str,
        "tipe"       : tipe,
        "status"     : status,
        "confidence" : round(conf, 4),
        "timestamp"  : now.isoformat(),
    }

    # Session log
    if name not in st.session_state.absen_log:
        st.session_state.absen_log[name] = []
    st.session_state.absen_log[name].append(record)

    if tipe == "Masuk":
        st.session_state.absen_done.add(name)

    # Persistent JSON
    data = load_presensi()
    if tanggal not in data:
        data[tanggal] = {}
    if name not in data[tanggal]:
        data[tanggal][name] = []
    data[tanggal][name].append(record)
    save_presensi(data)
    export_csv(data)

    return record


# ============================================================================
# MODE: FOTO
# ============================================================================

if mode == "📸 Presensi via Foto":
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📤 Upload Foto</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Pilih foto pegawai",
            type=["jpg","jpeg","png","bmp","webp"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_files:
            if st.button(f"✅ Mulai Absen {tipe_presensi}", use_container_width=True, type="primary"):
                st.session_state["run_foto"] = True

    with col2:
        if not uploaded_files:
            st.markdown("""
            <div class="card" style="text-align:center; padding:2.5rem 1rem;">
                <div style="font-size:3rem; margin-bottom:0.75rem;">📁</div>
                <div style="color:var(--text-secondary);">Upload foto pegawai untuk melakukan presensi</div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.75rem;">Format: JPG · PNG · BMP · WEBP</div>
            </div>""", unsafe_allow_html=True)
        elif st.session_state.get("run_foto"):
            st.session_state["run_foto"] = False
            new_records = []

            with st.spinner(f"⏳ Memproses {len(uploaded_files)} foto..."):
                for uf in uploaded_files:
                    image    = Image.open(uf).convert("RGB")
                    img_rgb  = np.array(image)
                    img_bgr  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

                    t0 = time.perf_counter()
                    results = model.predict(
                        img_bgr,
                        conf=st.session_state.conf_thresh,
                        iou=st.session_state.iou_thresh,
                        verbose=False
                    )
                    elapsed = (time.perf_counter() - t0) * 1000
                    dets    = parse_results(results[0])

                    status_map = {}
                    for cls_id, conf_val, *_ in dets:
                        emp_name = names.get(cls_id, f"ID-{cls_id}")
                        rec      = record_attendance(emp_name, conf_val, tipe_presensi)
                        if rec:
                            new_records.append((emp_name, rec))
                            status_map[emp_name] = rec["status"]

                    annotated_bgr = draw_boxes(img_bgr, dets, names, status_map)
                    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

                    st.markdown(f'<div class="card-header">📷 {uf.name} &nbsp;·&nbsp; {elapsed:.0f}ms</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown('<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:4px;">FOTO ASLI</div>', unsafe_allow_html=True)
                        st.image(img_rgb)
                    with c2:
                        st.markdown('<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:4px;">HASIL DETEKSI</div>', unsafe_allow_html=True)
                        st.image(annotated_rgb)

                    if not dets:
                        st.warning("⚠️ Tidak ada wajah terdeteksi pada foto ini.")

            if new_records:
                st.success(f"✅ {len(new_records)} pegawai berhasil diabsen!")
                for emp, rec in new_records:
                    chip_class = "chip-on-time" if "Tepat" in rec["status"] else "chip-late"
                    st.markdown(f"""
                    <div class="att-row {'late' if 'Terlambat' in rec['status'] else ''}">
                        <div style="font-size:1.5rem;">👤</div>
                        <div class="att-name">{emp}</div>
                        <div class="att-time">{rec['jam']}</div>
                        <span class="chip {chip_class}">{rec['status']}</span>
                    </div>""", unsafe_allow_html=True)


# ============================================================================
# MODE: KAMERA REALTIME
# ============================================================================

elif mode == "🎥 Presensi via Kamera Realtime":

    st.markdown("""
    <div class="card" style="text-align:center; padding:1rem;">
        <div style="font-size:1.1rem; font-weight:700; color:var(--primary-light); margin-bottom:0.5rem;">
            🎥 Presensi Realtime via Kamera
        </div>
        <div style="font-size:0.85rem; color:var(--text-secondary);">
            Arahkan wajah ke kamera · Tekan <b>START</b> untuk memulai · Presensi tersimpan otomatis
        </div>
    </div>""", unsafe_allow_html=True)

    col_cam, col_info = st.columns([3, 2])

    with col_cam:
        # Shared state untuk komunikasi antara thread WebRTC & main thread
        if "rt_detections" not in st.session_state:
            st.session_state.rt_detections = []

        class LivePresensiProcessor(VideoProcessorBase):
            def recv(self, frame):
                img  = frame.to_ndarray(format="bgr24")
                res  = model.predict(
                    img,
                    conf=st.session_state.conf_thresh,
                    iou=st.session_state.iou_thresh,
                    verbose=False
                )
                dets = parse_results(res[0])

                # Auto-absen setiap frame jika wajah terdeteksi
                status_map = {}
                for cls_id, conf_val, *_ in dets:
                    emp_name = names.get(cls_id, f"ID-{cls_id}")
                    rec      = record_attendance(emp_name, conf_val, st.session_state.tipe_presensi)
                    if rec:
                        st.session_state.rt_detections.append((emp_name, rec))
                        status_map[emp_name] = rec["status"]

                annotated = draw_boxes(img, dets, names, status_map)
                return av.VideoFrame.from_ndarray(annotated, format="bgr24")

        webrtc_streamer(
            key="presensi-live",
            video_processor_factory=LivePresensiProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    with col_info:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📋 Absen Masuk Hari Ini</div>', unsafe_allow_html=True)

        log = st.session_state.absen_log
        if log:
            for emp, recs in log.items():
                for r in recs:
                    chip_class = "chip-on-time" if "Tepat" in r["status"] else "chip-late"
                    st.markdown(f"""
                    <div class="att-row {'late' if 'Terlambat' in r['status'] else ''}">
                        <div style="font-size:1.2rem;">👤</div>
                        <div>
                            <div class="att-name">{emp}</div>
                            <div class="att-time">{r['jam']} · {r['tipe']}</div>
                        </div>
                        <span class="chip {chip_class}" style="font-size:0.7rem;">{r['status']}</span>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:var(--text-secondary); font-size:0.85rem;">Belum ada presensi dalam sesi ini.</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# REKAP HARI INI
# ============================================================================

st.markdown("---")
st.markdown("## 📊 Rekap Presensi Hari Ini")

data_all  = load_presensi()
today_key = today_str()
today_dat = data_all.get(today_key, {})

total_emp   = len(today_dat)
tepat_count = sum(
    1 for recs in today_dat.values()
    for r in recs if "Tepat" in r.get("status","")
)
late_count  = total_emp - tepat_count

mc1, mc2, mc3 = st.columns(3)
with mc1:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Total Pegawai Hadir</div><div class="metric-val">{total_emp}</div></div>', unsafe_allow_html=True)
with mc2:
    st.markdown(f'<div class="metric-box"><div class="metric-label">✅ Tepat Waktu</div><div class="metric-val" style="color:#10b981">{tepat_count}</div></div>', unsafe_allow_html=True)
with mc3:
    st.markdown(f'<div class="metric-box"><div class="metric-label">⚠️ Terlambat</div><div class="metric-val" style="color:#f97316">{late_count}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if today_dat:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📋 Daftar Hadir</div>', unsafe_allow_html=True)
    for emp, recs in today_dat.items():
        for r in recs:
            chip_class = "chip-on-time" if "Tepat" in r["status"] else "chip-late"
            st.markdown(f"""
            <div class="att-row {'late' if 'Terlambat' in r['status'] else ''}">
                <div style="font-size:1.4rem;">👤</div>
                <div style="flex:1">
                    <div class="att-name">{emp}</div>
                    <div class="att-time">{r['tipe']} · {r['jam']} · Conf: {float(r['confidence'])*100:.1f}%</div>
                </div>
                <span class="chip {chip_class}">{r['status']}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("📄 Lihat Data JSON Lengkap"):
        st.json(today_dat)

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            st.download_button(
                "⬇️ Download Rekap CSV",
                data=f,
                file_name=f"presensi_{today_key}.csv",
                mime="text/csv"
            )
else:
    st.info("Belum ada data presensi untuk hari ini.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div class="footer">
    Sistem Presensi Digital · PT JASAKULA PURWALUHUR · Powered by YOLOv11 Face Recognition
</div>
""", unsafe_allow_html=True)
