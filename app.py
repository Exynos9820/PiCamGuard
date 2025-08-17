# app.py
from flask import Flask, Response, render_template, send_file, jsonify
from picamera2 import Picamera2
from libcamera import Transform
import cv2, os, requests, numpy as np, time, threading, io
from dotenv import load_dotenv
from flask import send_from_directory, abort
from pathlib import Path
from motion_detector import detect_motion
from snapshot_manager import SnapshotsManager
from telegram_worker import TelegramWorker

# --- CONFIG ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
SAVE_TO_TELEGRAM   = os.getenv("SAVE_TO_TELEGRAM", "false").lower() == "true"
MAX_NUM_SNAPSHOTS  = int(os.getenv("MAX_NUM_SNAPSHOTS", 200))

NOTIFY_INTERVAL   = 60
MOTION_THRESHOLD  = 500_000
FRAME_INTERVAL    = 0.05  # ~20 fps

# --- Camera setup ---
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.transform = Transform(hflip=True, vflip=True)
picam2.configure("preview")
picam2.start()

# --- Globals ---
prev_frame = None
last_notify_time = 0
latest_jpeg = None
latest_lock = threading.Lock()
last_motion_score = 0
snapshot_manager = SnapshotsManager(MAX_NUM_SNAPSHOTS)
telegram_worker = TelegramWorker(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)


def camera_worker():
    global last_notify_time, latest_jpeg
    while True:
        frame = picam2.capture_array()

        ok, buf = cv2.imencode('.jpg', frame)
        if ok:
            with latest_lock:
                latest_jpeg = buf.tobytes()

        if detect_motion(frame) and (time.time() - last_notify_time > NOTIFY_INTERVAL):
            print(f"\nMotion detected (score={last_motion_score}) — sending alert...")
            if SAVE_TO_TELEGRAM:
                telegram_worker.send_telegram_notification(frame)
            snapshot_manager.add_snapshot(frame, f"motion_{int(time.time())}.jpg")

            last_notify_time = time.time()

        if FRAME_INTERVAL > 0:
            time.sleep(FRAME_INTERVAL)

t = threading.Thread(target=camera_worker, daemon=True)
t.start()

app = Flask(__name__)

def mjpeg_generator():
    while True:
        with latest_lock:
            frame_bytes = latest_jpeg
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)

# ---- Web routes ----
@app.route("/")
def index():
    # Renders templates/index.html
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")



@app.route("/snapshot")
def snapshot():
    # Returns the most recent frame as a single JPEG file
    with latest_lock:
        if latest_jpeg is None:
            return "No frame yet", 503
        return send_file(io.BytesIO(latest_jpeg),
                         mimetype="image/jpeg",
                         as_attachment=False,
                         download_name="snapshot.jpg")

@app.route("/status")
def status():
    # Small JSON API you can hit from JS
    return jsonify({
        "motion_score": last_motion_score,
        "threshold": MOTION_THRESHOLD,
        "last_alert_epoch": last_notify_time
    })



SNAP_DIR = Path(__file__).resolve().parent / "snapshots"  # same as in snapshot_manager.py

def _is_safe_snap(path: Path) -> bool:
    # prevent path traversal
    try:
        return SNAP_DIR in path.resolve().parents or path.resolve() == SNAP_DIR
    except Exception:
        return False

@app.route("/snapshots")
def snapshots_page():
    """
    HTML gallery of snapshots.
    """
    files = snapshot_manager.get_snapshots()  # absolute paths (strings)
    # Convert to filenames relative to SNAP_DIR for URLs
    names = [Path(p).name for p in files if Path(p).exists()]
    return render_template("snapshots.html", names=names)

@app.route("/snapshots/<path:filename>")
def snapshots_file(filename):
    """
    Serve a single snapshot image by filename.
    """
    # only allow files inside SNAP_DIR
    target = SNAP_DIR / filename
    if not _is_safe_snap(target) or not target.exists():
        return abort(404)
    # serve with correct headers
    return send_from_directory(SNAP_DIR, filename, as_attachment=False)

@app.route("/api/snapshots")
def snapshots_api():
    """
    JSON list of snapshot filenames (newest first).
    """
    files = snapshot_manager.get_snapshots()
    names = [Path(p).name for p in files if Path(p).exists()]
    return jsonify({"snapshots": names})

@app.route("/snapshots/latest")
def snapshots_latest():
    """
    Redirect (or serve) the most recent snapshot.
    """
    files = snapshot_manager.get_snapshots()
    for p in files:
        pp = Path(p)
        if pp.exists():
            return send_from_directory(SNAP_DIR, pp.name, as_attachment=False)
    return "No snapshots yet", 404

from werkzeug.utils import safe_join

@app.route("/snapshots/<path:filename>/download")
def snapshots_download(filename):
    target = SNAP_DIR / filename
    if not _is_safe_snap(target) or not target.exists():
        return abort(404)
    return send_from_directory(SNAP_DIR, filename, as_attachment=True)

@app.route("/snapshots/<path:filename>/delete", methods=["POST"])
def snapshots_delete(filename):
    target = SNAP_DIR / filename
    if not _is_safe_snap(target) or not target.exists():
        return abort(404)
    try:
        os.remove(target)
        # Update manager list
        abs_path = str(target.resolve())
        if abs_path in snapshot_manager.snapshots:
            snapshot_manager.snapshots.remove(abs_path)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
