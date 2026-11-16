"""Tiny, cheap OCR first-pass for brown/orange MapleStory nameplate labels.

A four-letter label such as Mora is only ~35 source pixels wide. Full-frame OCR
misses that text, while a tight 2x crop reads it. This scans only plausible
small orange-brown nameplates, so the user need not process a 1200x700 scene.
Fallback to the existing general OCR remains necessary for other text styles.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import time
from fast_shop_match import candidates, pick_unique


def find_wooden_labels(bgr, limit: int=8):
    import cv2
    import numpy as np
    h,w=bgr.shape[:2]
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV)
    # Orange wood/brown nameplates. Ignore tiny orange decorative objects.
    mask=cv2.inRange(hsv,np.array([5,90,50]),np.array([25,255,240]))
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_RECT,(7,3)))
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    labels=[]
    for contour in contours:
        x,y,bw,bh=cv2.boundingRect(contour)
        if not (55<=bw<=205 and 17<=bh<=55 and 1.8<bw/bh<9.5):
            continue
        if y<round(h*.16) or y>round(h*.90):
            continue
        # The seller name is in the *center* of the plaque; trim wooden tips,
        # platform stones and avatars which confuse Tesseract and WinOCR.
        pad_x=max(7,round(bw*.13))
        l=x+pad_x; r=x+bw-pad_x
        t=y+max(6,round(bh*.29));b=y+bh-max(3,round(bh*.12))
        if r-l<18 or b-t<9:
            continue
        labels.append((l,t,r,b))
    # Prefer complete nameplates with plausible sizes, not the game UI.
    labels=sorted(labels,key=lambda a:(abs((a[2]-a[0])-50),a[1]))
    return labels[:limit]


def read_small_nameplate(bgr,target: str, *, native: bool=False,
                         rapid=None,tesseract=None, time_budget_s:float=.75):
    """Return Hit or None, never a fabricated name or game-world coordinate.

    The crop coordinates are transformed back to *selected window pixels*.
    At most a handful of small ROIs are passed to OCR; never a whole frame.
    """
    import cv2
    import numpy as np
    labels=find_wooden_labels(bgr)
    if not labels:
        return None
    use_tess=tesseract
    if use_tess is None:
        try:
            import pytesseract as pt
            exe=shutil.which('tesseract')
            if not exe:
                candidate=Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
                if candidate.is_file():exe=str(candidate)
            if exe:
                pt.pytesseract.tesseract_cmd=exe
                use_tess=pt
        except Exception:
            use_tess=None
    start=time.perf_counter()
    all_hits=[]
    for l,t,r,b in labels:
        # Guarantee the target IGN remains in the ROI even when a plaque is
        # partially obscured; nearest-neighbor preserves pixel-art lettering.
        crop=cv2.resize(bgr[t:b,l:r],None,fx=2,fy=2,
                        interpolation=cv2.INTER_NEAREST)
        if use_tess is not None:
            try:
                d=use_tess.image_to_data(crop,config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                                          output_type=use_tess.Output.DICT)
                for i,text in enumerate(d.get('text',())):
                    if not str(text).strip():continue
                    try:conf=max(0.,float(d['conf'][i])/100.)
                    except Exception:conf=.8
                    x=int(d['left'][i])/2+l;y=int(d['top'][i])/2+t
                    w=int(d['width'][i])/2;h=int(d['height'][i])/2
                    poly=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
                    all_hits.extend(candidates([text],[poly],[conf],target,min_ocr_score=.15))
            except Exception:
                pass
        elif native:
            try:
                import winocr
                from native_ocr import winocr_hits
                data=winocr.recognize_cv2_sync(crop,'en')
                for hit in winocr_hits(data,target):
                    from fast_shop_match import Hit
                    x0,y0,x1,y1=hit.box
                    all_hits.append(Hit(hit.text,(int(x0/2+l),int(y0/2+t),
                                                  int(x1/2+l),int(y1/2+t)),hit.score,hit.mode))
            except Exception:
                pass
        elif rapid is not None:
            try:
                output=rapid(crop,use_cls=False)
                boxes=getattr(output,'boxes',None)
                if boxes is not None:
                    coords=[[(float(p[0])/2+l,float(p[1])/2+t) for p in poly] for poly in boxes]
                    all_hits+=candidates(getattr(output,'txts',()),coords,
                                         getattr(output,'scores',None),target)
            except Exception:
                pass
        # Only skip other labels after a strong exact match; partial matches
        # need all candidates to rule out ambiguity.
        if len(all_hits)==1 and all_hits[0].mode=='EXACT':
            break
        if time.perf_counter()-start >= time_budget_s:
            break
    return pick_unique(all_hits)
