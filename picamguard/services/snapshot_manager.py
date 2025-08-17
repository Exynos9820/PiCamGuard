import os
from pathlib import Path
import cv2
import time
import numpy as np

# Create a stable absolute directory next to this script
class SnapshotsManager:
    def __init__(self, max_snapshots, base_dir: Path):
        self.max_snapshots = max_snapshots
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots = []
        self.load_snapshots()

    def load_snapshots(self):
        """Load snapshots from the filesystem."""
        for p in sorted(self.base_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True):
            self.snapshots.append(str(p))  # trust existing files

    def add_snapshot(self, image, filename: str):
        path = self.save_snapshot(image, filename)
        if path:
            self.snapshots.append(path)
        self.remove_old_snapshots()

        if self.snapshots and len(self.snapshots) > self.max_snapshots:
            self.remove_snapshot(self.snapshots[0])

    def remove_snapshot(self, snapshot_path: str):
        try:
            os.remove(snapshot_path)
            self.snapshots.remove(snapshot_path)
            print(f"Removed snapshot {snapshot_path}")
        except Exception as e:
            print(f"Error removing snapshot {snapshot_path}: {e}")

    def remove_old_snapshots(self):
        # if snapshot is older than 20 days, then remove it
        for snapshot in self.snapshots:
            if os.path.exists(snapshot):
                age = time.time() - os.path.getmtime(snapshot)
                if age > 20 * 24 * 60 * 60:  # 20 days in seconds
                    self.remove_snapshot(snapshot)

    def get_snapshots(self):
        return self.snapshots

    def clear_snapshots(self):
        self.snapshots.clear()

    def shutdown(self):
        self.clear_snapshots()
        # remove old snapshots
        for snapshot in self.snapshots:
            try:
                os.remove(snapshot)
            except Exception as e:
                print(f"Error removing snapshot {snapshot}: {e}")

    def save_snapshot(self, image, filename: str):
        """
        Save a frame to snapshots/ and log the result.
        Returns the absolute path or None on failure.
        """
        if image is None:
            print("save_snapshot: image is None")
            return None

        # Ensure correct dtype
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        # If your frames are RGB (Picamera2 RGB888), convert to BGR for correct colors
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        out_path = self.base_dir / filename
        ok = cv2.imwrite(str(out_path), bgr)
        if not ok:
            print(f"save_snapshot: imwrite failed to {out_path}")
            print(f"cwd={os.getcwd()}  exists(SNAP_DIR)={self.base_dir.exists()}")
            return None

        print(f"Saved snapshot -> {out_path}")
        self.remove_old_snapshots()
        return str(out_path)
