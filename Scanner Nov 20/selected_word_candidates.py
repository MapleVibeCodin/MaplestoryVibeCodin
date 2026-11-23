"""Selected-name location hints. Text recognition must verify every hint."""
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

@lru_cache(maxsize=48)
def shapes(name,width):
    font=ImageFont.truetype(str(Path(__file__).with_name('assets')/'name_font.ttf'),12)
    x,y,r,b=font.getbbox(name)
    canvas=Image.new('L',(r-x+6,b-y+6),0)
    ImageDraw.Draw(canvas).text((3-x,3-y),name,font=font,fill=255)
    base=np.asarray(canvas);result=[];seen=set()
    for scale in (1.,width/1280,width/1366*1.04):
        scale=max(.5,min(1.6,scale));size=(max(8,round(base.shape[1]*scale)),max(7,round(base.shape[0]*scale)))
        if size in seen:continue
        seen.add(size);result.append(cv2.resize(base,size,interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC))
    return result

def propose(frame,name,limit=24,fast=False,polarity=None,scale_index=0):
    h,w=frame.shape[:2];gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    high=max(1.,float(np.percentile(frame[::16,::16],98)));groups=[]
    templates=shapes(name,w)
    if fast:
        # Most labels are close to native pixel size. Check one plausible
        # scale first and allow later attempts to search the full scale set.
        # The previous fast path always used the last DPI scale for names
        # 5+ characters long. On many Maple windows that is NOT the font's
        # actual size, causing the fast search to miss until slow recovery.
        index=scale_index%len(templates)
        templates=templates[index:index+1]
    polarities=(True,False) if polarity is None else (polarity,)
    # Dim labels tend to rank lower in the downsampled search. Refine more
    # peaks there, but still require text recognition before marking a shop.
    dim=polarity is not None and high<125
    peak_limit=24 if len(name)<=5 or dim else 12
    min_score=(.44 if dim else .50) if len(name)<=5 else .45
    for dark in polarities:
        feature=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT,np.ones((3,3),np.uint8))
        small=cv2.resize(feature,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA);candidates=[]
        for shape in templates:
            th,tw=shape.shape
            if th>feature.shape[0] or tw>feature.shape[1]:continue
            mini=cv2.resize(shape,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
            scores=cv2.matchTemplate(small,mini,cv2.TM_CCOEFF_NORMED)
            peaks=(scores>=.28)&(scores==cv2.dilate(scores,np.ones((5,5),np.uint8)))
            ys,xs=np.where(peaks);order=np.argsort(scores[ys,xs])[-peak_limit:][::-1]
            for i in order:
                x=int(xs[i])*2;y=int(ys[i])*2;l=max(0,x-4);t=max(0,y-4)
                patch=feature[t:min(feature.shape[0],y+th+5),l:min(w,x+tw+5)]
                if patch.shape[0]<th or patch.shape[1]<tw:continue
                _,score,_,(dx,dy)=cv2.minMaxLoc(cv2.matchTemplate(patch,shape,cv2.TM_CCOEFF_NORMED))
                if score<min_score:continue
                box=(l+dx,t+dy,l+dx+tw,t+dy+th);a,b,r,d=box
                pixels=frame[b:d,a:r];level=float(np.median(gray[b:d,a:r]))/high
                if dark:
                    if not(.22<=level<=.80 and np.mean(pixels.max(2)-pixels.min(2)<80)>=.60):continue
                elif level>=.65:continue
                if any(abs((a+r)-(q[1][0]+q[1][2]))<max(14,r-a) and abs((b+d)-(q[1][1]+q[1][3]))<18 for q in candidates):continue
                # Follow observed ink to the complete word boundary. A query
                # template must never crop a prefix/suffix out of another IGN.
                band_top=b+2
                band_bottom=max(b+3,d-2)
                band_left=max(0,a-60)
                band_right=min(w,r+61)
                band=feature[band_top:band_bottom,band_left:band_right]
                rgb=frame[band_top:band_bottom,band_left:band_right]
                neutral=rgb.max(2)-rgb.min(2)<80
                columns=np.zeros(w,dtype=bool)
                columns[band_left:band_right]=((band>30)&neutral).sum(0)>=2
                left=a;right=r
                if columns[a:min(w,a+6)].any():
                    blank=0
                    for col in range(min(w-1,a+3),max(-1,a-61),-1):
                        blank=0 if columns[col] else blank+1
                        if blank>=3:left=max(0,col);break
                        left=max(0,col-1)
                if columns[max(0,r-6):r].any():
                    blank=0
                    for col in range(max(0,r-4),min(w,r+61)):
                        blank=0 if columns[col] else blank+1
                        if blank>=3:right=min(w,col+1);break
                        right=min(w,col+2)
                # A shop title popup has long horizontal borders that can
                # correlate surprisingly well with a white-font name template.
                # Require text-like broken strokes, not a 70%+ solid row.
                ink=feature[b:d,max(0,left):min(w,right)]>25
                if ink.size and np.max(np.mean(ink,axis=1))>.70:continue
                # Maple seller IGNs are rendered in bright lettering on a
                # dark nameplate immediately beneath the character. The older
                # matcher treated a coincidental popup-border correlation as
                # better than a slightly weaker *actual* nameplate. Favor the
                # verified visual context without making it a hard filter:
                # sellers outside normal nameplate lighting must still work.
                plate_pixels=gray[max(0,b-1):min(h,d+1),max(0,left):min(w,right)]
                nameplate=(plate_pixels.size>0 and high>=125 and
                           np.median(plate_pixels)<115 and
                           np.mean(plate_pixels<115)>=.65)
                ranked_score=float(score)+(.25 if nameplate else 0.)
                candidates.append((ranked_score,(left,b,right,d),dark))
        groups.append(sorted(candidates,reverse=True))
    # Rank both text polarities together; a weak signboard must not delay
    # stronger player-name candidates merely because its text is dark.
    if len(groups)==1:return groups[0][:limit]
    if len(name)<=5:
        # Very short names have many incidental white-shape matches; give a
        # highlighted gray nameplate an immediate chance too.
        first=[group.pop(0) for group in groups if group]
        return (first+sorted(groups[0]+groups[1],reverse=True))[:limit]
    return sorted(groups[0]+groups[1],reverse=True)[:limit]
