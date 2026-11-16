"""Optional fast Windows 11 built-in OCR backend via WinOCR.

WinOCR uses Windows.Media.Ocr. It accepts BGR NumPy frames and returns the
same Hit objects as RapidOCR. It is an optional performance path; failure falls
back to the prior RapidOCR/Tesseract implementation.
"""
from __future__ import annotations
from fast_shop_match import candidates, pick_unique


def winocr_hits(data: dict, target: str, offset_x: int=0, offset_y: int=0):
    lines=[]; boxes=[]; scores=[]
    for line in data.get('lines', ()) or ():
        if not isinstance(line, dict):
            continue
        words = line.get('words') or ()
        rects=[]
        for word in words:
            r = word.get('bounding_rect') or {}
            try:
                x=float(r['x']) + offset_x
                y=float(r['y']) + offset_y
                w=float(r['width']); h=float(r['height'])
            except (KeyError, ValueError, TypeError):
                continue
            if w <= 0 or h <= 0:
                continue
            rects.append((x,y,x+w,y+h))
        if not rects:
            continue
        x0=min(v[0] for v in rects); y0=min(v[1] for v in rects)
        x1=max(v[2] for v in rects); y1=max(v[3] for v in rects)
        line_text = str(line.get('text') or ' '.join(str(w.get('text','')) for w in words))
        # Test each exact word FIRST to produce the tightest possible box.
        # Only then consider the whole line (for joined/split words).
        for word in words:
            r = word.get('bounding_rect') or {}
            try:
                x=float(r['x'])+offset_x; y=float(r['y'])+offset_y
                w=float(r['width']); h=float(r['height'])
            except (KeyError, TypeError, ValueError):
                continue
            txt = str(word.get('text') or '').strip()
            if txt and w>0 and h>0:
                lines.append(txt);scores.append(1.0)
                boxes.append(((x,y),(x+w,y),(x+w,y+h),(x,y+h)))
        if line_text.strip():
            lines.append(line_text); scores.append(1.0)
            boxes.append(((x0,y0),(x1,y0),(x1,y1),(x0,y1)))
    # WinOCR returns both a full line and its words.  The same IGN may appear
    # in both: de-duplicate overlapping hits or pick_unique would reject it.
    hits = candidates(lines,boxes,scores,target)
    unique = []
    for hit in hits:
        a=hit.box
        cx=(a[0]+a[2])/2;cy=(a[1]+a[3])/2
        if any(b.box[0]-4<=cx<=b.box[2]+4 and b.box[1]-4<=cy<=b.box[3]+4
               and hit.text.casefold() in b.text.casefold() for b in unique):
            continue
        unique.append(hit)
    return unique


def scan_native(bgr, target: str):
    """Return a best unique match, or None. Native OCR is on-demand only."""
    import winocr
    h,w=bgr.shape[:2]
    # Exclude minimap and bottom buttons/chat; preserve near-full shop rows.
    y0=max(0,round(h*.065)); y1=max(y0+1,round(h*.91))
    result=winocr.recognize_cv2_sync(bgr[y0:y1], 'en')
    return pick_unique(winocr_hits(result, target, 0, y0))
