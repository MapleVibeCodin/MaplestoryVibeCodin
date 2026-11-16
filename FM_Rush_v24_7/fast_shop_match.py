"""Pure matching and persistence logic for the Discord-IGN-driven shop highlighter.

No manual-name input. Partial matches are treated as candidates, not proof of identity.
Only screen pixels are used; never game memory or the network.
"""
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
import re


def norm(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(value).casefold())


@dataclass(frozen=True)
class Hit:
    text: str
    box: tuple[int, int, int, int]
    score: float
    mode: str  # EXACT, FUZZY, PARTIAL4, PARTIAL3


def overlap(a: str, b: str, n: int = 4) -> bool:
    """Require a contiguous n-letter run shared with the alerted IGN."""
    if len(a) < n or len(b) < n:
        return False
    return any(a[i:i+n] in b for i in range(len(a)-n+1))


def candidates(lines, boxes, scores, target: str, min_ocr_score: float = .30) -> list[Hit]:
    """Parse RapidOCR lines; coords are window-local pixels.

    Four matching contiguous characters can recover clipped/partially legible IGN.
    Three-character candidates only when the IGN itself has three characters,
    to avoid claiming a generic three-letter fragment as exact identification.
    """
    wanted = norm(target)
    if len(wanted) < 3 or not lines or boxes is None:
        return []
    found: list[Hit] = []
    for i, raw in enumerate(lines):
        if i >= len(boxes) or not raw:
            continue
        confidence = float(scores[i]) if scores is not None and i < len(scores) else .8
        if confidence < min_ocr_score:
            continue
        name = norm(raw)
        if len(name) < 3 or len(name) > max(40,len(wanted)*3):
            continue
        mode = ''
        if name == wanted or wanted in name:
            score=1.0;mode='EXACT'
        elif len(wanted)>=5 and abs(len(name)-len(wanted))<=max(2,len(wanted)//3) and (s:=SequenceMatcher(None,wanted,name).ratio())>=.83:
            score=float(s);mode='FUZZY'
        elif overlap(wanted,name,4):
            # 4+ contiguous letters, more credible than arbitrary 3-char fragments
            score=.78+min(.15,(min(len(name),len(wanted))-4)*.025);mode='PARTIAL4'
        elif len(wanted)==3 and name==wanted:
            score=1.;mode='PARTIAL3'
        else:
            continue
        pts=boxes[i]
        try:
            x0=int(min(float(p[0]) for p in pts));y0=int(min(float(p[1]) for p in pts))
            x1=int(max(float(p[0]) for p in pts));y1=int(max(float(p[1]) for p in pts))
        except (ValueError,IndexError,TypeError):
            continue
        if x1<=x0 or y1<=y0:
            continue
        found.append(Hit(str(raw),(x0,y0,x1,y1),round(score,3),mode))
    return sorted(found,key=lambda h:-h.score)


def pick_unique(hits: list[Hit]) -> Hit | None:
    """Don't confidently select from multiple plausible text locations."""
    if not hits:
        return None
    if len(hits)==1:
        return hits[0]
    # Confidence separation: full exact match beats weak partial candidates.
    if hits[0].mode=='EXACT' and hits[1].score<.96:
        return hits[0]
    return None


@dataclass
class StickyResult:
    """Keep a last-known highlighted location until next accepted Discord alert."""
    target: str=''
    box: tuple[int,int,int,int]|None=None
    mode: str='SEARCHING'
    seen_text: str=''

    def set_target(self, target: str) -> None:
        if norm(self.target)!=norm(target):
            self.target=target
            self.box=None
            self.mode='SEARCHING'
            self.seen_text=''

    def found(self, hit: Hit) -> None:
        self.box=hit.box
        self.mode='FOUND' if hit.mode in ('EXACT','FUZZY') else 'PARTIAL'
        self.seen_text=hit.text

    def missed(self) -> None:
        # Keep box highlighted; label as last known until a new recognition.
        if self.box is not None:
            self.mode='LAST SEEN'
        else:
            self.mode='SEARCHING'
