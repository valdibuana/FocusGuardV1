Berikut PRD singkat yang tetap mencakup kebutuhan utama proyek Anda.

Product Requirement Document (PRD)

Nama Produk

FocusGuard

Judul

Sistem Monitoring dan Analisis Kantuk Siswa Saat Belajar Menggunakan Kamera Laptop Berbasis YOLOv8 dan Big Data Analytics

## 1. Latar Belakang

Mahasiswa sering mengalami penurunan konsentrasi saat belajar di depan laptop tanpa disadari. Sistem ini dirancang untuk mendeteksi kantuk secara real-time menggunakan kamera laptop, menyimpan histori aktivitas, serta menganalisis data untuk membantu meningkatkan kualitas belajar.

## 2. Tujuan

- Mendeteksi kantuk secara real-time menggunakan YOLOv8.

- Menyimpan histori aktivitas belajar.

- Menganalisis pola kantuk siswa.

- Menampilkan dashboard analitik.

- Memberikan rekomendasi belajar.

## 3. Ruang Lingkup

## In Scope

- Deteksi mata tertutup

- Deteksi kepala menunduk

- Deteksi menguap

- Webcam laptop


- Penyimpanan data ke MongoDB

- Dashboard analitik

- Rekomendasi belajar

## Out of Scope

- Face Recognition

- Aplikasi mobile

- Integrasi LMS

- Multi kamera

## 4. Pengguna

## Pengguna Fungsi

Mahasiswa Menggunakan sistem dan melihat hasil analisis

Dosen Memantau tingkat konsentrasi mahasiswa

Admin Mengelola sistem

## 5. Kebutuhan Fungsional

## ID Kebutuhan

FR-01 Login pengguna

FR-02 Mengaktifkan webcam

FR-03 Deteksi kantuk menggunakan YOLOv8

FR-04 Menampilkan hasil deteksi secara real-time

FR-05 Menyimpan histori deteksi ke MongoDB

FR-06 Menampilkan dashboard analitik

FR-07 Memberikan rekomendasi belajar


- 6. Kebutuhan Non-Fungsional

- Akurasi deteksi e 95%

- Waktu deteksi < 1 detik

- Sistem berjalan pada Windows

- Menggunakan webcam bawaan laptop

- Data tersimpan secara otomatis

## 7. Arsitektur Sistem

Webcam Laptop

│

YOLOv8 Detection

│

Generate JSON

│

Apache Kafka

│

MongoDB

│

Dashboard

│


Rekomendasi Belajar

## 8. Teknologi

## Komponen Teknologi

AI

Bahasa

Streaming Apache Kafka

Database MongoDB

Dashboard Streamlit

API

YOLOv8

Python

FastAPI

## 9. Data yang Disimpan

- ID Mahasiswa

- Nama

- Tanggal & Waktu

- Status (Normal/Mengantuk)

- Confidence

- Mata tertutup

- Kepala menunduk

- Menguap

- Durasi deteksi

## 10. Dashboard

## Dashboard Mahasiswa


- Persentase fokus

- Grafik konsentrasi

- Riwayat belajar

- Rekomendasi belajar

## Dashboard Dosen

- Jumlah mahasiswa aktif

- Jumlah mahasiswa mengantuk

- Statistik kelas

- Laporan harian

## 11. Indikator Kantuk

Sistem akan memberikan status Mengantuk jika memenuhi salah satu kondisi berikut:

- Mata tertutup selama e 3 detik.

- Kepala menunduk selama e 3 detik.

- Menguap terdeteksi secara berulang dalam satu sesi belajar.

## 12. Output Sistem

- Deteksi kantuk secara real-time.

- Histori aktivitas belajar tersimpan di MongoDB.

- Dashboard analitik untuk dosen dan mahasiswa.

- Rekomendasi belajar berdasarkan pola kantuk.

PRD ini sudah cukup ringkas (sekitar 3–5 halaman) dan dapat dijadikan acuan implementasi maupun lampiran proposal tugas akhir mata kuliah Big Data.
