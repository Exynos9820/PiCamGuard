import time
import cv2
import numpy as np
from threading import Thread

def _encode_jpeg(frame):
    ok, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes() if ok else None

def loop(state):
    cam = state.picam2
    while True:
        frame = cam.capture_array()

        # update stream buffer
        jpg = _encode_jpeg(frame)
        if jpg:
            with state.latest_lock:
                state.latest_jpeg = jpg

        # motion + throttle
        triggered = state.motion_detector.detect_motion(frame)
        state.last_motion_score = state.motion_detector.last_motion_score

        if triggered and (time.time() - state.last_notify_time > state.cfg["NOTIFY_INTERVAL"]):
            print(f"\nMotion detected (score={state.last_motion_score}) — handling...")
            if state.save_to_telegram:
                state.telegram_worker.send_telegram_notification(frame)
            state.snapshot_manager.add_snapshot(frame, f"motion_{int(time.time())}.jpg")
            state.last_notify_time = time.time()

        # small sleep to avoid maxing CPU
        fi = state.cfg["FRAME_INTERVAL"]
        if fi > 0:
            time.sleep(fi)

def start_camera_worker(state):
    t = Thread(target=loop, args=(state,), daemon=True)
    t.start()
