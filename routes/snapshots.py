from flask import Blueprint, render_template, send_from_directory, abort, jsonify, current_app, request
from pathlib import Path
import os, time, numpy as np, cv2

bp = Blueprint("snapshots", __name__)
# helpers
def _snap_dir(state): return state.snap_dir
def _safe(path, base):
    try:
        return base in path.resolve().parents or path.resolve() == base
    except Exception:
        return False

@bp.route("/")
def page():
    state = current_app.extensions["state"]
    files = state.snapshot_manager.get_snapshots()
    names = [Path(p).name for p in files if Path(p).exists()]
    return render_template("snapshots.html", names=names)

@bp.route("/<path:filename>")
def file(filename):
    state = current_app.extensions["state"]
    base = _snap_dir(state)
    target = base / filename
    if not _safe(target, base) or not target.exists():
        return abort(404)
    return send_from_directory(base, filename, as_attachment=False)

@bp.route("/<path:filename>/download")
def download(filename):
    state = current_app.extensions["state"]
    base = _snap_dir(state)
    target = base / filename
    if not _safe(target, base) or not target.exists():
        return abort(404)
    return send_from_directory(base, filename, as_attachment=True)

@bp.route("/<path:filename>/delete", methods=["POST"])
def delete(filename):
    state = current_app.extensions["state"]
    base = _snap_dir(state)
    target = base / filename
    if not _safe(target, base) or not target.exists():
        return jsonify({"ok": False, "error": "Not found"}), 404
    try:
        os.remove(target)
        abs_path = str(target.resolve())
        if abs_path in state.snapshot_manager.snapshots:
            state.snapshot_manager.snapshots.remove(abs_path)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/save_latest", methods=["POST"])
def save_latest():
    state = current_app.extensions["state"]
    with state.latest_lock:
        if not state.latest_jpeg:
            return {"ok": False, "msg": "No frame yet"}, 503
        arr = np.frombuffer(state.latest_jpeg, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    filename = f"manual_{int(time.time())}.jpg"
    path = state.snapshot_manager.save_snapshot(frame, filename)
    return {"ok": True, "filename": filename, "path": path}
