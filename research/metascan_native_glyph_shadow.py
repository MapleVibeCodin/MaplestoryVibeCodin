"""Offline research: exact native-glyph shadow replay, not production recognition.
Uses the existing MIT-licensed Classic Tool atlas preserved in the upstream archive.
Requires NumPy/OpenCV only for this standalone experiment.
Usage: python research/metascan_native_glyph_shadow.py path/to/private-checkpoint.zip
Never publishes a highlight, accesses the game, or modifies source images.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import statistics
import time
import zipfile
import cv2
import numpy as np

ATLAS_PATH=Path(__file__).parent/'upstream-scanners/2026-11-26/classic-tool-source.json'
PRICE_RE=re.compile(r'^[1-9][0-9,]* for [0-9][0-9,]* mesos$')
def load_atlas():
    bundle=json.loads(ATLAS_PATH.read_text(encoding='utf-8'))
    raw=next(f for f in bundle['files'] if f['path']=='maplestory_classic_tool/assets/glyphs.json')
    if raw['sha']!='5e049f7585dfe1aac171fbd66b158d62f6ac9c08':raise ValueError('unexpected atlas ref')
    entries=json.loads(raw['content'])['glyphs']
    atlas={}
    for g in entries:
        bits=np.unpackbits(np.frombuffer(base64.b64decode(g['bits']),np.uint8))[:14*g['w']].reshape(14,g['w'])
        cols=tuple(map(int,(bits*(1<<np.arange(14))[:,None]).sum(0)))
        atlas.setdefault(cols,set()).add(g['char'])
    return atlas

def read_native(ink,atlas,widths):
    cols=tuple(map(int,(ink*(1<<np.arange(14))[:,None]).sum(0)))
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

def locate_exact(img):
    h,w=img.shape[:2]
    if h<53:return None
    a=np.flatnonzero(np.all(img[:-52]==[67,223,208],axis=2))
    hits=[]
    for v in a:
        y,x=divmod(int(v),w)
        if x<1 or x+72>=w:continue
        if not np.array_equal(img[y,x-1],[17,179,151]):continue
        if not np.all(img[y,x:x+24]==[67,223,208]):continue
        if all(np.array_equal(img[y+d,x-1],[28,117,216]) and np.all(img[y+d,x:x+24]==[92,159,255]) for d in (31,51)):hits.append((x,y))
    return hits[0] if len(hits)==1 else None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    atlas=load_atlas();widths=sorted(set(map(len,atlas)))
    images=shops=names=prices=pairs=0
    timings=[]
    with zipfile.ZipFile(args.archive) as z:
        for file in z.namelist():
            if not file.lower().endswith('.png'):continue
            images+=1
            im=cv2.imdecode(np.frombuffer(z.read(file),np.uint8),cv2.IMREAD_COLOR)
            if im is None:continue
            anchor=locate_exact(im)
            if not anchor:continue
            x,y=anchor
            c=im[y+70:y+333,x-140:x+64]
            if c.shape!=(263,204,3):continue
            shops+=1
            started=time.perf_counter()
            for row in range(6):
                t=23+row*40
                name=read_native(cv2.cvtColor(c[t+4:t+18,40:198],cv2.COLOR_BGR2GRAY)<120,atlas,widths)
                price=re.sub(r'(?<=[0-9,]) (?=[0-9,])','',read_native(cv2.cvtColor(c[t+21:t+35,40:198],cv2.COLOR_BGR2GRAY)<120,atlas,widths))
                a=len(name)>2 and '?' not in name
                b=bool(PRICE_RE.fullmatch(price))
                names+=a;prices+=b;pairs+=a and b
            timings.append((time.perf_counter()-started)*1000)
    print(json.dumps({'pngs':images,'exact_complete_shop_crops':shops,'row_positions':shops*6,
          'complete_name_strings':names,'price_syntax_matches':prices,'pairs':pairs,
          'median_six_row_ms':statistics.median(timings) if timings else None,
          'warning':'Exploratory fixed offsets; no independent labels, no accuracy claim.'},indent=2))

if __name__=='__main__':main()
