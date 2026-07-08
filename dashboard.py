import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi MongoDB
MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'focusguard'
COLLECTION_NAME = 'history'

# Set konfigurasi halaman Streamlit
st.set_page_config(
    page_title="FocusGuard Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card { background: #1e1e2e; border-radius: 12px; padding: 20px; text-align: center; }
    .status-focus { color: #34eb64; font-weight: bold; font-size: 1.2em; }
    .status-drowsy { color: #ff4b4b; font-weight: bold; font-size: 1.2em; }
    .stMetric label { font-size: 0.85rem !important; color: #aaa !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
def get_data():
    """Ambil seluruh data dari MongoDB"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        data = list(collection.find({}, {"_id": 0}))
        client.close()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke MongoDB: {e}")
        return pd.DataFrame()


# ============================================================
# Header
# ============================================================
st.title("🎓 FocusGuard Analytics")
st.markdown("**Sistem Monitoring dan Analisis Kantuk Siswa** — Berbasis YOLOv8 & Big Data")
st.divider()

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=80)
st.sidebar.title("FocusGuard")
role = st.sidebar.selectbox("👤 Role Dashboard", ["Mahasiswa", "Dosen"])

# Auto-refresh
auto_refresh = st.sidebar.toggle("🔄 Auto Refresh (5 detik)", value=False)
if auto_refresh:
    import time
    time.sleep(5)
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("🔄 Refresh Manual"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.info("💡 Pastikan Docker Compose, Consumer, dan Detector sedang aktif.")

# ============================================================
# Load Data
# ============================================================
df = get_data()

if df.empty:
    st.warning("⚠️ Belum ada data. Pastikan sistem deteksi (detector.py) dan consumer.py aktif dan terhubung ke MongoDB.")
    st.code("# Urutan menjalankan sistem:\n1. docker-compose up -d\n2. python consumer.py\n3. python detector.py\n4. streamlit run dashboard.py", language="bash")
    st.stop()

# ============================================================
# Dashboard Mahasiswa
# ============================================================
if role == "Mahasiswa":
    st.header("👤 Dashboard Mahasiswa")

    mahasiswa_list = sorted(df['nama'].unique())
    selected_mhs = st.sidebar.selectbox("Pilih Mahasiswa", mahasiswa_list)

    df_mhs = df[df['nama'] == selected_mhs].copy()

    if df_mhs.empty:
        st.warning("Tidak ada data untuk mahasiswa ini.")
        st.stop()

    # Hitung metrik
    total_data   = len(df_mhs)
    fokus_count  = len(df_mhs[df_mhs['status'] == "Fokus"])
    drowsy_count = total_data - fokus_count
    pct_fokus    = (fokus_count / total_data * 100) if total_data > 0 else 0
    yawn_total   = int(df_mhs['menguap'].sum())
    latest_status = df_mhs.iloc[-1]['status']

    # --- Metrik Utama ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Status Terkini", latest_status)
    col2.metric("✅ Persentase Fokus", f"{pct_fokus:.1f}%")
    col3.metric("😴 Frekuensi Mengantuk", f"{drowsy_count} kali")
    col4.metric("🥱 Total Menguap", f"{yawn_total} kali")

    st.divider()

    # --- Grafik Konsentrasi ---
    st.subheader("📈 Grafik Konsentrasi Waktu Nyata")
    df_mhs['score'] = df_mhs['status'].apply(lambda x: 1 if x == "Fokus" else 0)

    fig = px.area(
        df_mhs, x='timestamp', y='score',
        color_discrete_sequence=["#34eb64"],
        labels={'score': 'Status (1=Fokus, 0=Mengantuk)', 'timestamp': 'Waktu'},
        range_y=[-0.1, 1.1]
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.05)')
    st.plotly_chart(fig, use_container_width=True)

    # --- Grafik Donut Fokus ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🎯 Distribusi Status")
        fig_pie = px.pie(
            values=[fokus_count, drowsy_count],
            names=['Fokus', 'Mengantuk'],
            color_discrete_sequence=["#34eb64", "#ff4b4b"],
            hole=0.45
        )
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        # --- Rekomendasi Belajar ---
        st.subheader("💡 Rekomendasi Belajar")
        if pct_fokus > 80:
            st.success("🌟 Tingkat fokus Anda sangat baik! Pertahankan ritme belajar Anda saat ini.")
        elif 50 <= pct_fokus <= 80:
            st.info("🧃 Fokus Anda mulai menurun. Disarankan untuk istirahat 5 menit, minum air putih, dan lakukan peregangan ringan.")
        else:
            st.error("🚨 Anda sangat sering mengantuk! Hentikan belajar sejenak selama 15 menit. Cuci muka, berjalan-jalan ringan, atau tidur siang singkat (20 menit).")

        if yawn_total > 3:
            st.warning("🥱 Anda sering menguap. Pastikan ruangan memiliki ventilasi yang cukup, atau buka jendela untuk sirkulasi udara segar.")

        # Info tambahan
        sesi_mulai = df_mhs['timestamp'].min().strftime("%H:%M:%S")
        sesi_akhir = df_mhs['timestamp'].max().strftime("%H:%M:%S")
        durasi = df_mhs['timestamp'].max() - df_mhs['timestamp'].min()
        st.info(f"📅 Sesi belajar: **{sesi_mulai}** — **{sesi_akhir}** ({int(durasi.total_seconds() // 60)} menit)")

    # --- Riwayat Detail ---
    st.subheader("📋 Riwayat Belajar Lengkap")
    display_cols = ['timestamp', 'status', 'confidence', 'mata_tertutup', 'kepala_menunduk', 'menguap']
    cols_available = [c for c in display_cols if c in df_mhs.columns]
    st.dataframe(df_mhs[cols_available].sort_values('timestamp', ascending=False), use_container_width=True)

# ============================================================
# Dashboard Dosen
# ============================================================
else:
    st.header("👨‍🏫 Dashboard Dosen")
    st.markdown("Pantauan kondisi kelas secara *real-time*")

    # Status terkini tiap mahasiswa
    latest_status = df.sort_values('timestamp').groupby('nama').last().reset_index()

    total_mhs    = df['nama'].nunique()
    mhs_fokus    = len(latest_status[latest_status['status'] == 'Fokus'])
    mhs_mengantuk = len(latest_status[latest_status['status'] == 'Mengantuk'])
    pct_kelas    = (mhs_fokus / total_mhs * 100) if total_mhs > 0 else 0

    # Metrik kelas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Mahasiswa Aktif", total_mhs)
    c2.metric("✅ Sedang Fokus", mhs_fokus)
    c3.metric("😴 Sedang Mengantuk", mhs_mengantuk)
    c4.metric("📊 Fokus Kelas", f"{pct_kelas:.0f}%")

    st.divider()

    # --- Alert Dosen ---
    if mhs_mengantuk > (total_mhs / 2) and total_mhs > 0:
        st.error("🚨 **Peringatan Kelas!** Lebih dari separuh mahasiswa sedang mengantuk. Disarankan untuk melakukan *ice breaking* atau sesi tanya jawab singkat.")
    elif mhs_mengantuk > 0:
        st.warning(f"⚠️ Ada **{mhs_mengantuk} mahasiswa** yang terdeteksi mengantuk saat ini.")
    else:
        st.success("✅ Kondisi kelas sangat kondusif! Semua mahasiswa sedang fokus.")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📋 Status Terkini Tiap Mahasiswa")
        # Beri warna berdasarkan status
        def highlight_status(val):
            color = '#2a5c3a' if val == 'Fokus' else '#5c2a2a'
            return f'background-color: {color}'
        
        display_latest = latest_status[['nama', 'id_mahasiswa', 'timestamp', 'status']].copy()
        st.dataframe(display_latest, use_container_width=True)

    with col_right:
        st.subheader("📊 Distribusi Status Kelas")
        fig_bar = px.bar(
            x=['Fokus', 'Mengantuk'],
            y=[mhs_fokus, mhs_mengantuk],
            color=['Fokus', 'Mengantuk'],
            color_discrete_map={'Fokus': '#34eb64', 'Mengantuk': '#ff4b4b'},
            labels={'x': 'Status', 'y': 'Jumlah Mahasiswa'}
        )
        fig_bar.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.05)')
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tren kantuk per waktu (semua mahasiswa)
    st.subheader("📈 Tren Kantuk Kelas (Timeline)")
    df_drowsy_trend = df[df['status'] == 'Mengantuk'].copy()
    if not df_drowsy_trend.empty:
        df_drowsy_trend['menit'] = df_drowsy_trend['timestamp'].dt.floor('min')
        tren = df_drowsy_trend.groupby('menit').size().reset_index(name='jumlah_mengantuk')
        fig_trend = px.line(tren, x='menit', y='jumlah_mengantuk',
                            color_discrete_sequence=['#ff4b4b'],
                            labels={'menit': 'Waktu', 'jumlah_mengantuk': 'Jumlah Deteksi Mengantuk'})
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.05)')
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Belum ada data kantuk yang tercatat di sesi ini.")

    st.subheader("🗂️ Semua Riwayat Sesi")
    st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True)
