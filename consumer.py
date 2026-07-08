import json
import traceback
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaError, KafkaException
# pyrefly: ignore [missing-import]
from confluent_kafka.admin import AdminClient, NewTopic
from pymongo import MongoClient

# --- Konfigurasi ---
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'drowsiness_topic'
GROUP_ID = 'focusguard-consumer-group'

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME = 'focusguard'
COLLECTION_NAME = 'history'

def main():
    print(f"[INFO] Menghubungkan ke MongoDB di {MONGO_URI}...")
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info() # Pastikan koneksi sukses
        db = mongo_client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("[INFO] Berhasil terhubung ke MongoDB.")
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke MongoDB. Pastikan container MongoDB menyala. Detail: {e}")
        return

    print(f"[INFO] Menghubungkan ke Kafka broker di {KAFKA_BROKER}...")
    
    # 1. Pastikan topik ada (buat jika belum ada)
    admin_client = AdminClient({'bootstrap.servers': KAFKA_BROKER})
    try:
        topic_metadata = admin_client.list_topics(timeout=5)
        if KAFKA_TOPIC not in topic_metadata.topics:
            print(f"[INFO] Topik '{KAFKA_TOPIC}' tidak ditemukan. Membuat topik baru...")
            new_topic = NewTopic(KAFKA_TOPIC, num_partitions=1, replication_factor=1)
            fs = admin_client.create_topics([new_topic])
            for topic, f in fs.items():
                try:
                    f.result()  # Menunggu hasil pembuatan
                    print(f"[SUCCESS] Topik '{topic}' berhasil dibuat.")
                except Exception as e:
                    print(f"[ERROR] Gagal membuat topik '{topic}': {e}")
        else:
            print(f"[INFO] Topik '{KAFKA_TOPIC}' sudah tersedia.")
    except Exception as e:
        print(f"[WARNING] Gagal mengecek/membuat topik via AdminClient: {e}")

    # 2. Inisialisasi Consumer
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'latest'
    }
    
    consumer = Consumer(conf)
    
    try:
        consumer.subscribe([KAFKA_TOPIC])
        print(f"[INFO] Berhasil subscribe ke topik '{KAFKA_TOPIC}'. Menunggu aliran data...")
        
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"[ERROR] Kafka error: {msg.error()}")
                    continue
                    
            try:
                raw_value = msg.value().decode('utf-8')
                data = json.loads(raw_value)
                
                # Simpan payload JSON ke MongoDB
                result = collection.insert_one(data)
                
                print(f"[{data.get('timestamp')}] Tersimpan ke DB -> Mahasiswa: {data.get('nama')} | Status: {data.get('status')} | DB_ID: {result.inserted_id}")
                
            except json.JSONDecodeError:
                print(f"[ERROR] Pesan Kafka bukan format JSON yang valid.")
            except Exception as e:
                print(f"[ERROR] Terjadi kesalahan: {e}")
                
    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan oleh pengguna.")
    finally:
        consumer.close()
        mongo_client.close()
        print("[INFO] Koneksi ditutup dengan aman.")

if __name__ == '__main__':
    main()
