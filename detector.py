import cv2
import time
import json
import numpy as np
import mediapipe as mp
import pygame
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from ultralytics import YOLO
from confluent_kafka import Producer

# --- Konfigurasi Kafka ---
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'drowsiness_topic'

def delivery_report(err, msg):
    """ Callback untuk mengetahui apakah pesan sukses dikirim ke Kafka """
    if err is not None:
        print(f"[ERROR] Gagal mengirim pesan ke Kafka: {err}")

# --- Konfigurasi Threshold ---
EAR_THRESHOLD = 0.25      # Eye Aspect Ratio untuk mata tertutup
MAR_THRESHOLD = 0.5       # Mouth Aspect Ratio untuk menguap
HEAD_DOWN_THRESHOLD = -15 # Sudut pitch kepala menunduk (derajat)
TIME_THRESHOLD = 3.0      # Batas waktu (detik) untuk memicu "Mengantuk"

def calculate_ear(eye_landmarks):
    """Menghitung Eye Aspect Ratio (EAR)"""
    v1 = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
    v2 = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
    h = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
    ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
    return ear

def get_student_info():
    """Meminta input data mahasiswa sebelum sesi dimulai"""
    print("\n" + "="*50)
    print("    FOCUSGUARD - SISTEM DETEKSI KANTUK")
    print("="*50)
    student_id = input("Masukkan ID Mahasiswa (contoh: STD-001): ").strip()
    student_name = input("Masukkan Nama Lengkap: ").strip()
    if not student_id:
        student_id = "STD-001"
    if not student_name:
        student_name = "Mahasiswa Uji Coba"
    return student_id, student_name

def main():
    # Input data mahasiswa sebelum sesi dimulai
    student_id, student_name = get_student_info()

    print("\n[INFO] Inisialisasi Audio Alarm (Pygame)...")
    try:
        pygame.mixer.init()
        # Path di-update untuk mengarah ke folder sound_alarm/
        pygame.mixer.music.load("sound_alarm/Hidup jokowi  sound meme.mp3")
        alarm_ready = True
        print("[INFO] Audio Alarm berhasil dimuat.")
    except Exception as e:
        print(f"[WARNING] Gagal memuat file MP3 alarm: {e}")
        alarm_ready = False
    
    alarm_playing = False

    print("\n[INFO] Memuat model YOLOv8...")
    yolo_model = YOLO("yolov8n.pt")

    print("[INFO] Memuat model MediaPipe Face Landmarker...")
    base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1)
    face_landmarker = vision.FaceLandmarker.create_from_options(options)

    print("[INFO] Menghubungkan ke Kafka...")
    kafka_producer = None
    try:
        kafka_producer = Producer({'bootstrap.servers': KAFKA_BROKER,
                                   'socket.timeout.ms': 3000})
        print("[INFO] Berhasil inisialisasi Kafka Producer.")
    except Exception as e:
        print(f"[WARNING] Gagal inisialisasi Kafka: {e}. Data hanya dicetak di layar.")

    print("[INFO] Membuka webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Webcam tidak dapat diakses. Periksa koneksi kamera Anda.")
        return

    # Variabel state timer
    eyes_closed_start = None
    head_down_start = None
    
    # Untuk membatasi frekuensi pengiriman data (setiap 1 detik, bukan setiap frame)
    last_send_time = 0
    SEND_INTERVAL = 1.0

    print("\n" + "="*50)
    print(f"SESI DIMULAI: {student_name} ({student_id})")
    print("SISTEM DETEKSI KANTUK AKTIF. Tekan 'q' untuk keluar.")
    print("="*50 + "\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Gagal membaca frame dari webcam.")
            break

        frame_h, frame_w, _ = frame.shape  # DIPERBAIKI: Tidak ada konflik nama variabel

        # --- 1. YOLOv8: Deteksi Person ---
        results = yolo_model(frame, classes=[0], verbose=False)
        person_detected = False
        # DIPERBAIKI: Inisialisasi box koordinat agar tidak ada NameError
        bbox = (10, 10, frame_w - 10, frame_h - 10)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bbox = (x1, y1, x2, y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 120, 0), 2)
                cv2.putText(frame, "Person Detected", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 120, 0), 1)
                person_detected = True
                break

        # --- 2. MediaPipe: Ekstraksi Landmark Wajah ---
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = face_landmarker.detect(mp_image)

        status_text = "Fokus"
        eyes_closed_flag = False
        head_down_flag = False
        yawn_flag = False
        confidence = 0.0

        if detection_result.face_landmarks and person_detected:
            landmarks = detection_result.face_landmarks[0]
            confidence = 0.95

            # Konversi koordinat normalisasi ke piksel (menggunakan frame_w, frame_h)
            pts = [(int(pt.x * frame_w), int(pt.y * frame_h)) for pt in landmarks]

            # Landmark mata
            left_eye  = [pts[33], pts[160], pts[158], pts[133], pts[153], pts[144]]
            right_eye = [pts[362], pts[385], pts[387], pts[263], pts[373], pts[380]]

            # --- EAR (Mata) ---
            avg_ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

            # --- MAR (Mulut) ---
            mar_v = np.linalg.norm(np.array(pts[13]) - np.array(pts[14]))
            mar_h_dist = np.linalg.norm(np.array(pts[61]) - np.array(pts[291]))
            mar = mar_v / mar_h_dist if mar_h_dist > 0 else 0

            # --- Head Pose (Pitch) ---
            face_3d, face_2d = [], []
            for idx in [33, 263, 1, 61, 291, 152]:
                lm = landmarks[idx]
                px, py = int(lm.x * frame_w), int(lm.y * frame_h)
                face_2d.append([px, py])
                face_3d.append([px, py, lm.z])

            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            focal_length = frame_w
            cam_matrix = np.array([[focal_length, 0, frame_w / 2],
                                   [0, focal_length, frame_h / 2],
                                   [0, 0, 1]], dtype=np.float64)
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            success, rot_vec, _ = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
            if success:
                rmat, _ = cv2.Rodrigues(rot_vec)
                angles, *_ = cv2.RQDecomp3x3(rmat)
                pitch = angles[0] * 360
            else:
                pitch = 0

            # --- Timer Logic ---
            if avg_ear < EAR_THRESHOLD:
                eyes_closed_flag = True
                if eyes_closed_start is None:
                    eyes_closed_start = time.time()
            else:
                eyes_closed_flag = False
                eyes_closed_start = None

            if pitch < HEAD_DOWN_THRESHOLD:
                head_down_flag = True
                if head_down_start is None:
                    head_down_start = time.time()
            else:
                head_down_flag = False
                head_down_start = None

            if mar > MAR_THRESHOLD:
                yawn_flag = True

            eyes_closed_duration = time.time() - eyes_closed_start if eyes_closed_start else 0
            head_down_duration   = time.time() - head_down_start   if head_down_start   else 0

            if eyes_closed_duration >= TIME_THRESHOLD or head_down_duration >= TIME_THRESHOLD or yawn_flag:
                status_text = "Mengantuk"
                
                # --- Mainkan Alarm ---
                if alarm_ready and not alarm_playing:
                    pygame.mixer.music.play(-1) # -1 berarti loop terus menerus
                    alarm_playing = True
            else:
                # --- Hentikan Alarm jika Sadar ---
                if alarm_ready and alarm_playing:
                    pygame.mixer.music.stop()
                    alarm_playing = False

            # Tampilkan metrik debug di layar
            bx1, by1, bx2, by2 = bbox
            cv2.putText(frame, f"EAR: {avg_ear:.2f}", (bx1, by2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            cv2.putText(frame, f"MAR: {mar:.2f}",     (bx1, by2 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            cv2.putText(frame, f"Pitch: {pitch:.1f}", (bx1, by2 + 56), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # --- 3. Kirim Data (throttled, 1x/detik) ---
        current_time = time.time()
        if current_time - last_send_time >= SEND_INTERVAL:
            last_send_time = current_time
            data_payload = {
                "id_mahasiswa": student_id,
                "nama": student_name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status_text,
                "confidence": round(confidence, 2),
                "mata_tertutup": eyes_closed_flag,
                "kepala_menunduk": head_down_flag,
                "menguap": yawn_flag
            }
            json_string = json.dumps(data_payload)
            print(json_string)

            if kafka_producer:
                kafka_producer.produce(KAFKA_TOPIC, json_string.encode('utf-8'), callback=delivery_report)
                kafka_producer.poll(0)

        # --- 4. Render UI di Webcam Window ---
        color = (0, 0, 255) if status_text == "Mengantuk" else (0, 220, 50)
        cv2.rectangle(frame, (0, 0), (frame_w, 55), (30, 30, 30), -1)
        cv2.putText(frame, f"FocusGuard | {student_name}", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(frame, f"Status: {status_text}", (10, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("FocusGuard - Deteksi Kantuk", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Hentikan alarm saat keluar
    if alarm_ready and alarm_playing:
        pygame.mixer.music.stop()

    cap.release()
    cv2.destroyAllWindows()

    if kafka_producer:
        print("\n[INFO] Menyelesaikan antrean pesan Kafka sebelum keluar...")
        kafka_producer.flush()
        print("[INFO] Selesai. Data sesi tersimpan.")

if __name__ == "__main__":
    main()
