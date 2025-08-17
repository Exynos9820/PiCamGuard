import threading
from pathlib import Path
from picamera2 import Picamera2
from libcamera import Transform

from .services.snapshot_manager import SnapshotsManager
from .services.telegram_worker import TelegramWorker
from .services.motion_detector import MotionDetector

class State:
    def __init__(self, cfg):
        self.cfg = cfg

        # Camera
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.preview_configuration.transform = Transform(hflip=True, vflip=True)
        self.picam2.configure("preview")
        self.picam2.start()

        # Shared data for stream
        self.latest_jpeg: bytes | None = None
        self.latest_lock = threading.Lock()

        # Motion + alerts
        self.last_notify_time = 0
        self.motion_detector = MotionDetector(cfg["MOTION_THRESHOLD"])
        self.telegram_worker = TelegramWorker(cfg["TELEGRAM_BOT_TOKEN"], cfg["TELEGRAM_CHAT_ID"])
        self.save_to_telegram = cfg["SAVE_TO_TELEGRAM"]

        # Snapshots
        self.snap_dir = Path(__file__).resolve().parents[1] / "snapshots"
        self.snap_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_manager = SnapshotsManager(cfg["MAX_NUM_SNAPSHOTS"], base_dir=self.snap_dir)

        # Telemetry (optional)
        self.last_motion_score = 0
