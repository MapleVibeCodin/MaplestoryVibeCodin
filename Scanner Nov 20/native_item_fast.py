"""Native-pixel candidate recognition. No WinRT, seller, stats, input or network.
Atlas: oleg1994/maplestory-classic-tool, MIT; see native_item_glyphs_LICENSE.txt.
A native hit is a visible-name candidate, never authoritative equipment identity.
"""
import base64
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata
from vision_guard import parse_price_line

@lru_cache(maxsize=1)
def load_atlas():
    entries=json.loads(Path(__file__).with_name('native_item_glyphs.json').read_text(encoding='utf-8'))['glyphs']
    atlas={}
    for g in entries:
        w=g['w'];raw=base64.b64decode(g['bits'],validate=True)
        if g['h']!=14 or w<1 or w>16 or len(raw)*8<14*w:
            raise ValueError('Invalid native glyph')
        cols=[]
        for x in range(w):
            column=0
            for y in range(14):
                i=y*w+x
                if raw[i//8]&(128>>(i%8)):column|=1<<y
            cols.append(column)
        atlas.setdefault(tuple(cols),set()).add(g['char'])
    return atlas,tuple(sorted(set(map(len,atlas))))

@lru_cache(maxsize=32)
def threshold(cutoff):
    return bytes(int(i<cutoff) for i in range(256))

def pixel_columns(frame,x,y,w=158,cutoff=120):
    buf,fw,fh,stride=frame
    if x<0 or y<0 or x+w>fw or y+14>fh or stride<fw*3 or len(buf)!=stride*fh:
        return ()
    table=threshold(cutoff);lo=hi=0
    for i in range(14):
        pos=(y+i)*stride+3*x+2
        bits=int.from_bytes(buf[pos:pos+3*w:3].translate(table),'little')
        if i<8:lo|=bits<<i
        else:hi|=bits<<(i-8)
    return tuple(a|(b<<8) for a,b in zip(lo.to_bytes(w,'little'),hi.to_bytes(w,'little')))

@lru_cache(maxsize=2048)
def decode_columns(cols):
    atlas,widths=load_atlas()
    out=[];end=None;i=0
    while i<len(cols):
        if cols[i]==0:i+=1;continue
        j=i
        while j<len(cols) and cols[j]:j+=1
        if end is not None and i-end>=3:out.append(' ')
        ways={j:{''}}
        for k in range(j-1,i-1,-1):
            cand=set()
            for w in widths:
                if k+w>j:break
                for char in atlas.get(cols[k:k+w],()):
                    for suffix in ways.get(k+w,()):
                        cand.add(char+suffix)
                        if len(cand)>1:break
                    if len(cand)>1:break
                if len(cand)>1:break
            ways[k]=cand
        out.append(next(iter(ways[i])) if len(ways[i])==1 else '?')
        end=j;i=j
    return ''.join(out)

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC',str(text)).casefold().split())

def native_price(text):
    # Native font sometimes produces a space inside a sequence of digits.
    # Only remove internal numeric spacing after the whole grammar matches.
    m=re.fullmatch(r'([0-9,]+) for ([0-9, ]+) mesos',text)
    if not m:return None
    return parse_price_line(m[1]+' for '+m[2].replace(' ','')+' mesos')

def native_item_candidates(frame,item,price,sold_mask):
    """Exact visible names, optional numeric price cue, all matching rows.
    Never claim a truncated or ambiguous glyph string is an exact item.
    """
    target=norm(item)
    if not target or '?' in target:return []
    # Scroll variants often share icons and are truncated. Preserve full OCR
    # and its independent contrast verification for scrolls.
    if 'scroll' in target:return []
    hits=[]
    for row in range(6):
        y=23+row*40
        sold=sold_mask(frame,row)
        cutoff=215 if sold else 120
        name=decode_columns(pixel_columns(frame,40,y+4,cutoff=cutoff))
        if '?' in name or norm(name)!=target:continue
        amount=native_price(decode_columns(pixel_columns(frame,40,y+21,cutoff=cutoff)))
        hits.append((row,'FAST_SOLD' if sold else 'FAST_PRICE' if amount is not None and amount==price else 'FAST_NAME'))
    return hits

def ocr_name_candidates(lines,unavailable,item,price,scale=3):
    """Fallback visible-name-only candidates for non-scroll items."""
    target=norm(item)
    if not target or 'scroll' in target:return []
    groups=[[] for _ in range(6)]
    for line in lines:
        y=float(line.get('y',-100))/scale
        if 28<=y<268:groups[int((y-28)//40)].append((y,str(line.get('text','')).strip()))
    hits=[]
    for i,group in enumerate(groups):
        base=28+i*40
        name=norm(' '.join(t for y,t in group if y-base<19))
        if name!=target:continue
        amount=parse_price_line(' '.join(t for y,t in group if y-base>=19))
        hits.append((i,'FAST_SOLD' if unavailable[i] else 'FAST_PRICE' if amount is not None and amount==price else 'FAST_NAME'))
    return hits
