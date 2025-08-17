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
            self.snapshots.append(str(p))  # keep strings
        self.memory_usage = sum(
            os.path.getsize(fp) for fp in self.snapshots if os.path.exists(fp)
        )

    def add_snapshot(self, image, filename: str):
        path = self.save_snapshot(image, filename)
        if path:
            self.snapshots.append(path)
        self.remove_old_snapshots()

        if self.snapshots and len(self.snapshots) > self.max_snapshots:
            self.remove_snapshot(self.snapshots[0])

    def remove_snapshot(self, snapshot_path: str):
        try:
            size = os.path.getsize(snapshot_path) if os.path.exists(snapshot_path) else 0
            os.remove(snapshot_path)
            if snapshot_path in self.snapshots:
                self.snapshots.remove(snapshot_path)
            self.memory_usage = max(0, self.memory_usage - size)
            print(f"Removed snapshot {snapshot_path}")
        except Exception as e:
            print(f"Error removing snapshot {snapshot_path}: {e}")

    def remove_old_snapshots(self):
        cutoff = 20 * 24 * 60 * 60  # 20 days in seconds
        for snapshot in list(self.snapshots):  # iterate over a copy
            if os.path.exists(snapshot):
                age = time.time() - os.path.getmtime(snapshot)
                if age > cutoff:
                    size = os.path.getsize(snapshot)
                    self.remove_snapshot(snapshot)           # updates list
                    self.memory_usage = max(0, self.memory_usage - size)

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

        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        out_path = self.base_dir / filename
        ok = cv2.imwrite(str(out_path), bgr)
        if not ok:
            print(f"save_snapshot: imwrite failed to {out_path}")
            print(f"cwd={os.getcwd()}  exists(SNAP_DIR)={self.base_dir.exists()}")
            return None

        print(f"Saved snapshot -> {out_path}")
        self.memory_usage += os.path.getsize(str(out_path))
        self.remove_old_snapshots()
        return str(out_path)

    @property
    def num_snapshots(self):
        return len(self.snapshots)

