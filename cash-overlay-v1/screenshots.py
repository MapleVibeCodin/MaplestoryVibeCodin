"""Timestamped lossless WebP/PNG snapshots; no video, network or automatic deletion."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import json
import uuid

INTERVAL_SECONDS = 1
MIN_FREE_BYTES = 5 * 1024**3

def lossless_webp(data):
    # OpenCV produces simple VP8L WebP for 3-channel BGR images. Reject lossy VP8.
    return (isinstance(data, bytes) and len(data) >= 20 and data[:4] == b'RIFF'
            and data[8:16] == b'WEBPVP8L')

def encode_lossless(img):
    """Encode and compare every decoded pixel; fall back to PNG if WebP is unavailable."""
    import cv2
    import numpy as np
    try:
        ok, packed = cv2.imencode('.webp', img, [cv2.IMWRITE_WEBP_QUALITY, 101])
        if ok:
            data = packed.tobytes()
            if lossless_webp(data):
                decoded = cv2.imdecode(packed, cv2.IMREAD_UNCHANGED)
                if decoded is not None and decoded.dtype == img.dtype and np.array_equal(decoded, img):
                    return data
    except (cv2.error, AttributeError):
        pass
    ok, packed = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 1])
    if not ok:
        raise OSError('Lossless screenshot encoding failed')
    return packed.tobytes()

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

    def metadata(self, path, data):
        dest = path.with_suffix('.json')
        tmp = dest.with_suffix('.json.part')
        try:
            with tmp.open('x', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, allow_nan=False)
            tmp.replace(dest)
        finally:
            if tmp.exists():
                tmp.unlink()

    def reserve_metadata_frame(self,when=None):
        # Unique virtual image name; no image bytes are written or claimed.
        if not self.has_space(): return None
        when=when or datetime.now(timezone.utc)
        self.sequence+=1
        return self.folder / f"{when.strftime('%Y%m%dT%H%M%S_%fZ')}_{self.sequence:08d}.jpg"

    def save_scene(self, data, when=None):
        # JPEG is allowed only through the explicit hybrid capture interface.
        return self.save(data, when, allow_scene=True)

    def save(self, png, when=None, allow_scene=False):
        if lossless_webp(png):
            ext = '.webp'
        elif isinstance(png, bytes) and png.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = '.png'
        elif allow_scene and isinstance(png, bytes) and png[:2]==b'\xff\xd8' and png[-2:]==b'\xff\xd9':
            ext = '.jpg'
        else:
            raise ValueError('Expected lossless WebP or PNG bytes')
        if not self.has_space():
            return None
        when = when or datetime.now(timezone.utc)
        self.sequence += 1
        name = f"{when.strftime('%Y%m%dT%H%M%S_%fZ')}_{self.sequence:08d}{ext}"
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
