import os
from flask import Flask
from dotenv import load_dotenv

from .state import State
from .camera_worker import start_camera_worker
from routes.main import bp as main_bp
from routes.snapshots import bp as snaps_bp
from routes.api import bp as api_bp

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # ---- Config (env → python types) ----
    app.config.update(
        TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", ""),
        SAVE_TO_TELEGRAM=os.getenv("SAVE_TO_TELEGRAM", "false").lower() == "true",
        MAX_NUM_SNAPSHOTS=int(os.getenv("MAX_NUM_SNAPSHOTS", 200)),
        NOTIFY_INTERVAL=int(os.getenv("NOTIFY_INTERVAL", 60)),
        MOTION_THRESHOLD=int(os.getenv("MOTION_THRESHOLD", 500_000)),
        FRAME_INTERVAL=float(os.getenv("FRAME_INTERVAL", 0.05)),
    )

    # ---- Shared state (camera, locks, managers) ----
    state = State(app.config)
    app.extensions["state"] = state  # accessible via current_app.extensions["state"]

    # ---- Start background camera worker ----
    start_camera_worker(state)

    # ---- Register blueprints ----
    app.register_blueprint(main_bp)                # /
    app.register_blueprint(snaps_bp, url_prefix="/snapshots")
    app.register_blueprint(api_bp,   url_prefix="/api")

    return app
