
from flask import Blueprint, Response, render_template, current_app, send_file
import time, io

bp = Blueprint("main", __name__)

def mjpeg_stream(state):
    while True:
        with state.latest_lock:
            frame_bytes = state.latest_jpeg
        if frame_bytes:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.05)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/video_feed")
def video_feed():
    state = current_app.extensions["state"]
    return Response(mjpeg_stream(state), mimetype="multipart/x-mixed-replace; boundary=frame")

@bp.route("/snapshot")
def snapshot():
    state = current_app.extensions["state"]
    with state.latest_lock:
        if not state.latest_jpeg:
            return "No frame yet", 503
        return send_file(io.BytesIO(state.latest_jpeg),
                         mimetype="image/jpeg",
                         as_attachment=False,
                         download_name="snapshot.jpg")
