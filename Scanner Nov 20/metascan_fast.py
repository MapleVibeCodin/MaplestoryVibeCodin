"""Dependency-free, exact-equivalent pixel operations for MetaScanner."""
from functools import lru_cache

@lru_cache(maxsize=64)
def ink_table(cutoff):
    return bytes(0 if value//3<cutoff else 255 for value in range(766))

@lru_cache(maxsize=64)
def selected_table(delta):
    return bytes(0 if value<145+delta else 255 for value in range(256))

def row_mask(pixels, cutoff, selected=False, delta=0):
    if selected:
        return pixels[2::3].translate(selected_table(delta))
    table=ink_table(cutoff)
    return bytes(map(table.__getitem__,map(sum,zip(pixels[0::3],pixels[1::3],pixels[2::3]))))

def scale3(line):
    result=bytearray(len(line)*3)
    result[0::3]=result[1::3]=result[2::3]=line
    return bytes(result)

def negative_retry_due(existing, last_ocr_at, now, interval=2.0):
    return bool(existing is not None and not existing.get('hits') and now-last_ocr_at>=interval)

# Red below 145 is necessary (not sufficient) for every tooltip pixel.
_LOW_RED=bytes(int(i<145) for i in range(256))
_RUN12=b'\x01'*12

def purple_run(pixels):
    """Exact old predicate; skip lines without a possible 12-pixel run."""
    if _RUN12 not in pixels[2::3].translate(_LOW_RED):return False
    run=0
    for i in range(0,len(pixels),3):
        b,g,r=pixels[i:i+3]
        run=run+1 if 40<b and r<145 and g<145 and b-r>28 and b-g>23 else 0
        if run>=12:return True
    return False

def crop_bgr(frame,x,y,w,h):
    """Extract a validated packed crop from a single immutable captured frame."""
    if frame is None:return None
    buf,fw,fh,stride=frame
    if w<=0 or h<=0 or x<0 or y<0 or x+w>fw or y+h>fh or stride<fw*3 or len(buf)!=stride*fh:return None
    return (b''.join(buf[i*stride+x*3:i*stride+(x+w)*3] for i in range(y,y+h)),w,h,w*3)
