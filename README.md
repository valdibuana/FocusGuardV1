# 🎓 FocusGuard V1

![FocusGuard Banner](https://img.shields.io/badge/FocusGuard-AI%20Drowsiness%20Detection-34eb64?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Python-3.12-blue?style=flat-square) ![OpenCV](https://img.shields.io/badge/OpenCV-YOLOv8-red?style=flat-square) ![Kafka](https://img.shields.io/badge/Apache_Kafka-Data_Pipeline-black?style=flat-square) ![MongoDB](https://img.shields.io/badge/MongoDB-Big_Data-green?style=flat-square) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=flat-square)

**FocusGuard** adalah purwarupa sistem cerdas berbasis *Computer Vision* dan *Big Data* yang dirancang untuk memantau, mendeteksi, dan menganalisis tingkat kantuk atau fokus mahasiswa secara *real-time*.

---

## 💼 Latar Belakang Bisnis & Nilai Tambah (Business Value)

Dalam ekosistem pendidikan modern maupun lingkungan kerja, **fokus dan konsentrasi** adalah kunci utama produktivitas. Seringkali, dosen atau instruktur kesulitan memantau kondisi seluruh siswa di dalam kelas, terutama di kelas berkapasitas besar. Di sisi lain, siswa mungkin tidak menyadari kapan konsentrasi mereka mulai menurun.

**Fokus Bisnis FocusGuard:**
1. **Pendidikan (EdTech):** Memberikan *feedback* instan kepada dosen terkait kondisi kelas (kondusif atau mengantuk). Jika separuh kelas terdeteksi mengantuk, dosen bisa melakukan *ice breaking* atau evaluasi materi.
2. **Kesehatan & Keamanan Otomatis:** Fitur peringatan (alarm audio otomatis) membantu mengembalikan fokus pengguna secara langsung.
3. **Analitik Jangka Panjang:** Dengan ekosistem Big Data (Kafka & MongoDB), institusi pendidikan dapat melakukan profiling kebiasaan belajar siswa untuk meningkatkan kurikulum dan manajemen waktu perkuliahan.

---

## 🏗️ Arsitektur Sistem (Big Data Pipeline)

FocusGuard mengimplementasikan *End-to-End Data Pipeline* yang terdiri dari 4 komponen utama:

1. **AI Edge Node (`detector.py`)**: 
   - Menggunakan **YOLOv8** untuk mendeteksi keberadaan orang di depan kamera.
   - Menggunakan **MediaPipe Face Landmarker** untuk memetakan 468 titik wajah.
   - Menghitung *Eye Aspect Ratio* (EAR) untuk deteksi mata tertutup, *Mouth Aspect Ratio* (MAR) untuk deteksi menguap, dan *Head Pose Pitch* untuk deteksi kepala menunduk.
   - Bertindak sebagai **Kafka Producer** yang mengirim data per detik ke infrastruktur backend.

2. **Message Broker (Apache Kafka)**: 
   - Menangani aliran data dengan *throughput* tinggi melalui topik `drowsiness_topic`. Memastikan tidak ada data yang hilang meskipun sistem sedang padat.

3. **Data Storage (`consumer.py` & MongoDB)**: 
   - Bertindak sebagai **Kafka Consumer** yang mendengarkan data dan menyimpannya secara permanen ke dalam **MongoDB** (NoSQL Database). Format data JSON sangat cocok disimpan di MongoDB untuk mempermudah analitik data berskala besar (Big Data).

4. **Analytics Dashboard (`dashboard.py`)**: 
   - Dibangun dengan **Streamlit** dan **Plotly**, menyediakan dua antarmuka:
     - **Dashboard Mahasiswa:** Menampilkan persentase fokus, riwayat belajar, dan rekomendasi istirahat secara personal.
     - **Dashboard Dosen:** Memantau seluruh aktivitas kelas secara *real-time*, melihat agregasi jumlah siswa yang fokus vs mengantuk.

---

## 🚀 Panduan Instalasi & Menjalankan Sistem

### 1. Prasyarat
- Python 3.10 atau yang lebih baru.
- **Docker Desktop** (wajib aktif untuk menjalankan Kafka & MongoDB).
- Kamera/Webcam aktif.

### 2. Instalasi Dependensi
Jalankan perintah berikut di terminal Anda untuk meng-install seluruh pustaka Python yang dibutuhkan:
```bash
pip install -r requirements.txt
```

### 3. Menjalankan Infrastruktur Big Data
Buka terminal baru dan nyalakan kontainer Docker (Zookeeper, Kafka, MongoDB):
```bash
docker-compose up -d
```
*(Tunggu sekitar 10-15 detik hingga Kafka benar-benar siap)*

### 4. Menjalankan Komponen Sistem (Buka 3 Terminal Berbeda)

**Terminal 1 (Consumer - Penyimpan Data):**
```bash
python consumer.py
```

**Terminal 2 (AI Camera - Deteksi & Alarm):**
```bash
python detector.py
```
*(Sistem akan meminta Anda memasukkan ID dan Nama Mahasiswa terlebih dahulu. Jika terdeteksi mengantuk, audio peringatan dari folder `sound_alarm/` akan otomatis berbunyi!)*

**Terminal 3 (Dashboard Analytics):**
```bash
streamlit run dashboard.py
```

---

## 🛠️ Fitur Tambahan
- **Auto-Alarm System:** Terintegrasi dengan `pygame-ce` yang akan otomatis memutar MP3 teguran ketika pengguna terdeteksi mengantuk selama lebih dari 3 detik. Alarm berhenti otomatis jika pengguna sadar kembali.
- **Throttling Data:** Pengiriman data ke Kafka dibatasi 1x per detik (tidak per *frame* kamera) untuk menjaga efisiensi *bandwidth* dan penyimpanan *database*.

---
*Dibuat untuk keperluan Proyek Akhir Mata Kuliah Big Data - 2026.*
