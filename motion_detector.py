import cv2
import numpy as np

MOTION_THRESHOLD = 500_000
last_motion_score = 0
prev_frame = None


def detect_motion(frame):
    global prev_frame, last_motion_score
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if prev_frame is None:
        prev_frame = gray
        last_motion_score = 0
        return False

    delta = cv2.absdiff(prev_frame, gray)
    thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    score = int(np.sum(thresh))  # each white pixel adds 255
    prev_frame = gray
    last_motion_score = score
    return score > MOTION_THRESHOLD
