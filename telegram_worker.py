import cv2
import requests

class TelegramWorker:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id

    def send_telegram_notification(self, image):
        if not self.token or not self.chat_id:
            print(f"Telegram not configured (token? {bool(self.token)} chat? {bool(self.chat_id)})")
            return
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        ok, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            print("Failed to encode JPEG")
            return
        files = {'photo': ('motion.jpg', buffer.tobytes())}
        data = {'chat_id': self.chat_id, 'caption': 'Motion detected!'}
        try:
            r = requests.post(url, files=files, data=data, timeout=10)
            if r.status_code != 200:
                print(f"Telegram error {r.status_code}: {r.text}")
            else:
                print("Telegram photo sent OK")
        except Exception as e:
            print(f"Telegram exception: {e}")
