import cv2
import numpy as np

class MotionDetector:
    def __init__(self, motion_threshold):
        self.prev_frame = None
        self.last_motion_score = 0
        self.motion_threshold = motion_threshold

    def detect_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            self.last_motion_score = 0
            return False

        delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        score = int(np.sum(thresh))  # each white pixel adds 255
        self.prev_frame = gray
        self.last_motion_score = score
        return score > self.motion_threshold
