from flask import Blueprint, jsonify, current_app

from picamguard.state import State

bp = Blueprint("api", __name__)

@bp.get("/status")
def status():
    s: State = current_app.extensions["state"]
    return jsonify({
        "motion_score": s.motion_detector.last_motion_score,
        "threshold": s.cfg["MOTION_THRESHOLD"],
        "last_alert_epoch": s.last_notify_time,
        "num_snapshots": s.num_snapshots,
    })

@bp.get("/snapshots")
def list_snaps():
    s = current_app.extensions["state"]
    names = [p.name for p in s.snap_dir.glob("*.jpg")]
    names.sort(reverse=True)
    return jsonify({"snapshots": names})
