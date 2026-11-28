"""Timestamped PNG snapshots; no video, no network, no automatic deletion."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid

INTERVAL_SECONDS = 3
MIN_FREE_BYTES = 5 * 1024**3

class ScreenshotStore:
    def __init__(self, parent, min_free=MIN_FREE_BYTES):
        self.parent = Path(parent)
        self.parent.mkdir(parents=True, exist_ok=True)
        self.folder = self.parent / (datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC") + "_" + uuid.uuid4().hex[:8])
        self.folder.mkdir()
        self.min_free = min_free
        self.sequence = 0

    def has_space(self):
        return shutil.disk_usage(self.folder).free >= self.min_free

    def save(self, png, when=None):
        if not isinstance(png, bytes) or not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Expected encoded PNG bytes")
        if not self.has_space():
            return None
        when = when or datetime.now(timezone.utc)
        self.sequence += 1
        name = f"{when.strftime('%Y%m%dT%H%M%S_%fZ')}_{self.sequence:08d}.png"
        path = self.folder / name
        tmp = path.with_suffix(".part")
        try:
            with tmp.open("xb") as f:
                f.write(png)
                f.flush()
            tmp.replace(path)
        finally:
            if tmp.exists():
                tmp.unlink()
        return path
