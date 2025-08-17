from collections import deque
import threading
import time
import cv2
import numpy as np

class MotionDetector:
    def __init__(self, motion_threshold, bucket_seconds=5, window_hours=24):
        self.prev_frame = None
        self.last_motion_score = 0
        self.motion_threshold = motion_threshold

        self.bucket_seconds = int(bucket_seconds)
        self.max_points = int((window_hours * 3600) // self.bucket_seconds)
        self.series = deque(maxlen=self.max_points)   # each item = (bucket_ts, score)
        self._last_bucket_ts = None
        self._lock = threading.Lock()

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            self.last_motion_score = 0
            # also create an initial bucket (score 0)
            self._record(0, time.time())
            return False

        delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        score = int(np.sum(thresh))  # each white pixel adds 255

        self.prev_frame = gray
        self.last_motion_score = score
        self._record(score, time.time())
        return score > self.motion_threshold

    def _record(self, score, now):
        bucket_ts = int(now // self.bucket_seconds) * self.bucket_seconds
        with self._lock:
            if self.series and self._last_bucket_ts == bucket_ts:
                last_ts, last_score = self.series[-1]
                if score > last_score:
                    self.series[-1] = (last_ts, score)
            else:
                self.series.append((bucket_ts, score))
                self._last_bucket_ts = bucket_ts

    def get_series(self, hours=24):
        """Return (ts_list, score_list) for the last `hours` hours."""
        cutoff = time.time() - hours * 3600
        with self._lock:
            ts = [t for (t, s) in self.series if t >= cutoff]
            vs = [s for (t, s) in self.series if t >= cutoff]
        return ts, vs
