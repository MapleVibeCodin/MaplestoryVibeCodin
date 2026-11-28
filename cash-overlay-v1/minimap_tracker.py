"""Passive minimap observations; screen pixels, not game/world coordinates."""
import math
import cv2
import numpy as np

def viewport(img):
    # Look for the bright rectangular inner minimap frame at the top left.
    h,w=img.shape[:2]
    white=img.min(axis=2)>=235
    candidates=[]
    for y in range(22,min(h-22,160)):
        xs=np.flatnonzero(white[y])
        if len(xs)<65:continue
        for run in np.split(xs,np.flatnonzero(np.diff(xs)>1)+1):
            if len(run)<65 or run[0]>15:continue
            l,r=int(run[0]),int(run[-1]); width=r-l+1
            for b in range(y+30,min(h,y+220)):
                if white[b,l:r+1].mean()<.95:continue
                left=white[y:b+1,l:min(l+3,r)].any(axis=1).mean()
                right=white[y:b+1,max(l,r-2):r+1].any(axis=1).mean()
                if min(left,right)<.90:continue
                inner=img[y+1:b,l+1:r]
                if inner.size and (inner.max(axis=2)<70).mean()>.35:
                    candidates.append((width*(b-y),l+1,y+1,r-l-1,b-y-1))
                    break
    if not candidates:return None
    _,x,y,w,h=max(candidates)
    return x,y,w,h

def markers(img):
    b,g,r=img.astype(np.int16).transpose(2,0,1)
    masks=[(r>=220)&(g>=180)&(b<=90)&(r-b>=140),(r>=210)&(g<=45)&(b<=45)]
    out=[]
    for mask in masks:
        n,_,stats,centers=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
        hits=[]
        for (x,y,w,h,a), (cx,cy) in zip(stats[1:],centers[1:]):
            if 4<=w<=8 and 4<=h<=8 and 14<=a<=50 and .45<=a/(w*h)<=1:
                hits.append([round(float(cx),1),round(float(cy),1)])
        out.append(hits)
    return out

def observe(img,box):
    if box is None:return dict(status='no_viewport',self_xy=None,red_xy=None)
    x,y,w,h=box
    if x<0 or y<0 or x+w>img.shape[1] or y+h>img.shape[0]:return dict(status='invalid_viewport',self_xy=None,red_xy=None)
    own,red=markers(img[y:y+h,x:x+w]); point=own[0] if len(own)==1 else None
    return dict(status='candidate' if point else 'ambiguous_self',box=list(box),self_xy=point,red_xy=red,
                nearest_red_px=round(min(math.dist(point,p) for p in red),2) if point and red else None,
                normalized_xy=[round(point[0]/w,4),round(point[1]/h,4)] if point else None)
