import os
import sys
import time
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

class MantleBridge:
    """
    Gen Pen Pardus 23 MantleDB v2 Entegrasyon Köprüsü.
    - Otomatik oda (namespace) claim eder ve 256-bit X-Mantle-Key alır.
    - Arka planda mobilden gelen görselleri dinler (polling).
    - Yeni bir görsel geldiğinde yerel önbellek klasörüne (günlük) kaydeder.
    - Eski günlere ait verileri otomatik olarak temizler (24 saat kuralı).
    """

    MANTLE_BASE_URL = "https://mantledb.sh/v2"
    USER_AGENT = "GenPen-Pardus23-Desktop/2.0 (Debian; Linux x86_64)"

    def __init__(self, room_id=None, cache_base_dir="~/.cache/genpen"):
        self.room_id = room_id or f"genpen-{int(time.time()) % 1000000}"
        self.api_key = None
        self.cache_dir = os.path.expanduser(cache_base_dir)
        self.today_dir = os.path.join(self.cache_dir, "incoming", datetime.now().strftime("%Y-%m-%d"))
        self.last_received_id = None
        self.is_running = False

        self._ensure_cache_dir()
        self.purge_old_cache()

    def _ensure_cache_dir(self):
        os.makedirs(self.today_dir, exist_ok=True)

    def purge_old_cache(self, max_age_seconds=86400):
        """24 saatten eski tüm geçici klasörleri temizler."""
        incoming_root = os.path.join(self.cache_dir, "incoming")
        if not os.path.exists(incoming_root):
            return

        now = time.time()
        for folder_name in os.listdir(incoming_root):
            folder_path = os.path.join(incoming_root, folder_name)
            if os.path.isdir(folder_path):
                # Klasörün son değiştirilme zamanı 24 saati aştıysa ve bugünün klasörü değilse sil
                if (now - os.path.getmtime(folder_path)) > max_age_seconds and folder_path != self.today_dir:
                    try:
                        import shutil
                        shutil.rmtree(folder_path)
                        print(f"[GenPen Temizleyici] Dünden kalan geçici önbellek silindi: {folder_name}")
                    except Exception as e:
                        print(f"[GenPen Temizleyici] Hata: {e}")

    def claim_room(self):
        """MantleDB v2 üzerinde odayı rezerve eder ve API anahtarını alır."""
        url = f"{self.MANTLE_BASE_URL}/claim/{self.room_id}"
        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    self.api_key = data.get("key")
                    print(f"\n[MantleDB] Başarıyla Bağlandı!")
                    print(f" -> Oda (Namespace): {self.room_id}")
                    print(f" -> Güvenlik Anahtarı (X-Mantle-Key): {self.api_key}")
                    return True
                else:
                    print(f"[MantleDB] Claim hatası: {data}")
                    return False
        except urllib.error.HTTPError as e:
            print(f"[MantleDB] HTTP Hatası: {e.code} {e.reason}")
            return False
        except Exception as e:
            print(f"[MantleDB] Bağlantı Hatası: {e}")
            return False

    def generate_connection_url(self, companion_base_url="https://genpen.app"):
        """Mobil cihazın tarayacağı tam bağlantı URL'ini ve JSON yükünü döndürür."""
        web_url = f"{companion_base_url}/?ns={self.room_id}&key={self.api_key}"
        json_payload = json.dumps({
            "app": "genpen",
            "v": "2.0",
            "ns": self.room_id,
            "key": self.api_key,
            "url": web_url
        })
        return web_url, json_payload

    def poll_incoming(self):
        """MantleDB'den yeni gelen görsel verisini sorgular."""
        if not self.api_key:
            return None

        url = f"{self.MANTLE_BASE_URL}/{self.room_id}/incoming"
        headers = {
            "User-Agent": self.USER_AGENT,
            "X-Mantle-Key": self.api_key
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, dict) and "data" in data:
                    item_id = data.get("id") or str(data.get("timestamp"))
                    if item_id != self.last_received_id:
                        self.last_received_id = item_id
                        return self._save_incoming_media(data)
        except urllib.error.HTTPError as e:
            if e.code != 404:  # Henüz veri gönderilmemişse 404 dönmesi normaldir
                print(f"[MantleDB Poller] HTTP {e.code}")
        except Exception as e:
            pass
        return None

    def _save_incoming_media(self, payload):
        """Gelen base64 görselini yerel günlük dizine JPEG olarak kaydeder."""
        try:
            b64_data = payload.get("data", "")
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]

            binary_data = base64.b64decode(b64_data)
            timestamp_str = datetime.now().strftime("%H%M%S")
            filename = f"img_{timestamp_str}_{payload.get('id', 'photo')}.jpg"
            file_path = os.path.join(self.today_dir, filename)

            with open(file_path, "wb") as f:
                f.write(binary_data)

            print(f"\n[GenPen Medya] Yeni Görsel Alındı!")
            print(f" -> Gönderen: {payload.get('sender', 'Bilinmeyen')}")
            print(f" -> Kaydedildiği Dosya: {file_path}")
            print(f" -> Boyut: {len(binary_data) // 1024} KB")

            payload["local_file_path"] = file_path
            return payload
        except Exception as e:
            print(f"[GenPen Medya] Kaydetme hatası: {e}")
            return None

    def start_listener_loop(self, on_image_received=None, interval=1.5):
        """Konsol test döngüsü."""
        self.is_running = True
        print(f"[MantleDB Dinleyici] Aktif. Tahtaya görsel bekleniyor (Aralık: {interval}s)...")
        while self.is_running:
            media = self.poll_incoming()
            if media:
                if on_image_received:
                    on_image_received(media)
            time.sleep(interval)


if __name__ == "__main__":
    bridge = MantleBridge()
    if bridge.claim_room():
        web_url, qr_json = bridge.generate_connection_url("https://genpen.app")
        print("\n" + "=" * 60)
        print("GEN PEN MOBİL BAĞLANTI BİLGİLERİ:")
        print(f"Mobil Web URL: {web_url}")
        print(f"QR Veri Yükü : {qr_json}")
        print("=" * 60 + "\n")
        
        # Test dinleyici (CTRL+C ile durdurulabilir)
        try:
            bridge.start_listener_loop()
        except KeyboardInterrupt:
            print("\nDinleyici durduruldu.")
