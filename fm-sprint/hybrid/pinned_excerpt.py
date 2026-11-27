from collections import OrderedDict
import hashlib
import unicodedata
ROWS = 6
STEP = 40
SCALE = 3
NAME_ROW_TOP = 26
NAME_ROW_HEIGHT = 20
NAME_ROW_GAP = 8
NAME_ROW_SLOT = NAME_ROW_HEIGHT + NAME_ROW_GAP

def name_row_fingerprint(frame,row):
    buf,w,h,stride=frame
    y=NAME_ROW_TOP+row*STEP
    if w<198 or h<y+NAME_ROW_HEIGHT or stride<w*3 or len(buf)!=stride*h:
        raise ValueError('Invalid item-name row')
    digest=hashlib.blake2b(digest_size=16)
    for yy in range(y,y+NAME_ROW_HEIGHT):
        digest.update(buf[yy*stride+40*3:yy*stride+198*3])
    return digest.digest()

def normalized(s):
    return ' '.join(unicodedata.normalize('NFKC',str(s)).casefold().split())

def exact_name_rows(names,item,blocked=()):
    """Unique exact full-name match only; no fuzzy/truncated/sprite guessing."""
    target=normalized(item)
    if not target:return []
    matches=[row for row,name in names.items() if row not in blocked and normalized(name)==target]
    # A second ellipsized row could be the same target; do not guess.
    for name in names.values():
        value=normalized(name)
        if value.endswith(('...','…')):
            prefix=value.rstrip('.…').strip()
            if len(prefix)>=12 and target.startswith(prefix):return []
    return matches if len(matches)==1 else []

class NameOCRCache:
    """Target-independent row-name cache; price pixels do not invalidate it."""
    def __init__(self,limit=512):
        self.limit=limit;self.entries=OrderedDict()
    def recognize(self,frame,rows,ocr):
        rows=tuple(sorted(set(rows)))
        names={};keys={}
        for row in rows:
            key=name_row_fingerprint(frame,row);keys[row]=key
            if key in self.entries:
                names[row]=self.entries[key];self.entries.move_to_end(key)
        missing=[row for row in rows if row not in names]
        if missing:
            png,layout=prepare_name_ocr(frame,missing)
            raw=ocr.recognize(png)
            grouped={row:[] for row in missing}
            for line in raw:
                yy=float(line.get('y',-100))/SCALE
                slot=int(yy//NAME_ROW_SLOT)
                if slot in layout and yy-slot*NAME_ROW_SLOT<NAME_ROW_HEIGHT:
                    text=str(line.get('text','')).strip()
                    if text:grouped[layout[slot]].append(text)
            for row in missing:
                value=' '.join(grouped[row])
                names[row]=value
                # A blank OCR read is not evidence of an empty name. Retry it.
                if value:
                    self.entries[keys[row]]=value
                    self.entries.move_to_end(keys[row])
            while len(self.entries)>self.limit:self.entries.popitem(last=False)
        return names,len(rows)-len(missing),len(missing),bool(missing)
