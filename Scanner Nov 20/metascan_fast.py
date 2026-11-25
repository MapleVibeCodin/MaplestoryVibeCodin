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
