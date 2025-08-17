from flask import Blueprint, jsonify, current_app, request as flask_request

from picamguard.state import State

bp = Blueprint("api", __name__)

def _fmt_bytes(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


@bp.get("/status")
def status():
    s: State = current_app.extensions["state"]
    used = s.memory_usage
    return jsonify({
        "motion_score": s.last_motion_score,
        "threshold": s.cfg["MOTION_THRESHOLD"],
        "last_alert_epoch": s.last_notify_time,
        "num_snapshots": s.num_snapshots,
        "memory_usage": _fmt_bytes(used),
        "memory_usage_bytes": used
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

