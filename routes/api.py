from flask import Blueprint, jsonify, current_app, request as flask_request

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


@bp.get("/motion_series")
def motion_series():
    s = current_app.extensions["state"]
    try:
        hours = float(flask_request.args.get("hours", 24))
    except (TypeError, ValueError):
        hours = 24.0
    ts, vs = s.motion_detector.get_series(hours=hours)
    return jsonify({"t": ts, "v": vs, "bucket_seconds": s.motion_detector.bucket_seconds})

