"""Cheap FM-room minimap detection without OCR or game memory access.

The v15 gate looked exclusively for a transition *after* it was armed. That
failed when the user opened the scanner while already in FM <3>. v16 tests a
small reference of the numbered FM-room minimap first, then retains the old
transition fallback for previously unseen minimap themes and sizes.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import numpy as np


def minimap_signature(bgr: np.ndarray) -> np.ndarray | None:
    if bgr is None or getattr(bgr, 'ndim', None) != 3:
        return None
    h, w = bgr.shape[:2]
    if w < 300 or h < 260:
        return None
    x0, x1 = 20, min(135, w)
    y0, y1 = 94, min(156, h)
    if x1-x0 < 30 or y1-y0 < 25:
        return None
    import cv2
    thumb=cv2.resize(bgr[y0:y1,x0:x1], (48,24), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(thumb,cv2.COLOR_BGR2GRAY)


def difference(a: np.ndarray | None, b: np.ndarray | None) -> float:
    if a is None or b is None or a.shape != b.shape:
        return 0.
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))) / 255.)


@lru_cache(maxsize=1)
def references():
    path=Path(__file__).with_name('assets')/'fm_minimap_references.npz'
    if not path.exists():
        return {}, {}
    with np.load(path) as files:
        room={k:files[k] for k in ('room1','room3','room7') if k in files.files}
        entrance={k:files[k] for k in ('entrance_a','entrance_b') if k in files.files}
    return room,entrance


def current_room(signature: np.ndarray | None) -> bool:
    """Conservative visual match for a numbered FM interior, even at startup.

    Refuse ambiguous patterns: a false room match would waste CPU outside FM.
    The references are user-provided sample minimaps, not a game-memory query.
    """
    if signature is None:
        return False
    room, entrance = references()
    if not room or not entrance:
        return False
    room_distance=min(difference(signature,ref) for ref in room.values())
    entrance_distance=min(difference(signature,ref) for ref in entrance.values())
    return room_distance <= .105 and entrance_distance - room_distance >= .04


@dataclass
class EntryGate:
    threshold: float = .11
    hold_frames: int = 2
    armed: bool = False
    entered: bool = False
    baseline: np.ndarray | None = None
    streak: int = 0
    room_streak: int = 0
    reason: str = ''

    def reset(self) -> None:
        self.armed=True
        self.entered=False
        self.baseline=None
        self.streak=0
        self.room_streak=0
        self.reason=''

    def observe(self,bgr:np.ndarray)->bool:
        if not self.armed or self.entered:
            return False
        signature=minimap_signature(bgr)
        if signature is None or float(signature.mean()) < 16:
            self.streak=0
            self.room_streak=0
            return False
        # First-class state detection: scanning launched after entering FM <N>.
        if current_room(signature):
            self.room_streak+=1
            if self.room_streak>=self.hold_frames:
                self.entered=True
                self.reason='ALREADY INSIDE FM ROOM' if self.baseline is not None else 'FM ROOM DETECTED'
                return True
        else:
            self.room_streak=0
        # Backwards-compatible transition trigger for other windows/themes.
        if self.baseline is None:
            self.baseline=signature.copy()
            return False
        delta=difference(self.baseline,signature)
        if delta>=self.threshold:
            self.streak+=1
            if self.streak>=self.hold_frames:
                self.entered=True
                self.reason='FM MAP TRANSITION'
                return True
        else:
            self.streak=0
        return False


class SnapshotGate:
    """Explicitly armed loading-screen detector; independent of minimap layout.

    The user arms this in FM. Any subsequent black loading transition can
    trigger, including a same-room channel change. Tiny samples only; no OCR.
    """
    def __init__(self, settle_seconds=.25, first_visible=False,visible_level=55):
        self.settle_seconds=settle_seconds
        self.first_visible=first_visible
        self.visible_level=visible_level
        self.reset()

    def reset(self):
        self.loading=False
        self.invalidated=False
        self.done=False
        self.stable_since=None
        self.previous_levels=None

    def consume(self,bgr):
        self.loading=False
        self.done=True

    def observe(self,bgr,now=None):
        import time
        now=time.monotonic() if now is None else now
        self.invalidated=False
        if bgr is None or bgr.ndim!=3 or min(bgr.shape[:2])<100:
            return False
        h,w=bgr.shape[:2]
        # Five interior tiles avoid borders, minimap, chat and the bottom HUD.
        levels=[]
        for x,y in ((.25,.25),(.75,.25),(.5,.5),(.25,.7),(.75,.7)):
            tile=bgr[int((y-.07)*h):int((y+.07)*h):8,
                     int((x-.07)*w):int((x+.07)*w):8]
            levels.append(float(tile.mean()))
        dark=sum(v<24 for v in levels)>=4
        visible=sum(v>self.visible_level for v in levels)>=4
        if dark:
            if not self.loading:self.invalidated=True
            self.loading=True
            self.stable_since=None
            self.previous_levels=None
            self.done=False
            return False
        if self.loading and visible:
            if self.first_visible:
                self.consume(bgr)
                return True
            # A first nonblack frame is often halfway through the fade. Require
            # a brightness plateau for the configured interval; animation in one tile is tolerated.
            stable=(self.previous_levels is not None and
                    float(np.median(np.abs(np.array(levels)-self.previous_levels))) <= 2.)
            self.previous_levels=np.array(levels)
            if not stable:
                self.stable_since=now
            elif self.stable_since is not None and now-self.stable_since>=self.settle_seconds:
                self.consume(bgr)
                return True
        elif self.loading:
            self.stable_since=None
            self.previous_levels=None
        return False
