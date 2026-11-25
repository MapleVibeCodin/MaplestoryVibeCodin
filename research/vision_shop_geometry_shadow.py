"""Offline research prototype; never import into production scanner.
Requires numpy and OpenCV. Returns approximate shop evidence, NOT a crop anchor
or item identity. Native geometry only. Calibrated on the existing corpus.
"""
import cv2
import numpy as np

def shadow(im, region=None):
    h,w=im.shape[:2]
    if region is None: x0,y0,x1,y1=0,0,w,h
    else:x0,y0,x1,y1=region
    roi=im[y0:y1,x0:x1].astype(np.int16)
    green=(np.max(np.abs(roi-[67,223,208]),axis=2)<=20).astype(np.uint8)
    run=cv2.boxFilter(green,cv2.CV_32S,(24,1),anchor=(0,0),normalize=False,borderType=cv2.BORDER_CONSTANT)
    yy,xx=np.where((run>=22)&(np.pad(green[:,:-1],((0,0),(1,0)))==0))
    hits=[]
    for a,b in zip(xx+x0,yy+y0):
        if a<140 or a+54>=w or b+70+23+5*40+36>=h:continue
        strips=0
        for dy in (31,51):
            scores=[]
            for off in (-1,0,1):
                q=im[b+dy+off,a:a+24].astype(int)
                scores.append(np.sum(np.max(np.abs(q-[92,159,255]),axis=1)<=22))
            strips+=max(scores)>=20
        if strips<1:continue
        row_hits=0
        for i in range(6):
            y=b+70+23+i*40
            columns=0
            for dx in (-100,-55,-10,54):
                q=im[y+4:y+36,a+dx].astype(int)
                normal=(np.max(np.abs(q-[227,217,205]),axis=1)<=20)
                sold=(q.min(1)>=225)&(q.max(1)-q.min(1)<=28)
                selected=(q[:,0]<=110)&(q[:,1]>=95)&(q[:,2]>=185)&(q[:,2]-q[:,1]>=35)&(q[:,1]-q[:,0]>=35)
                columns+=np.count_nonzero(normal|sold|selected)>=22
            row_hits+=columns>=2
        if row_hits>=3 and (strips==2 or row_hits>=4): hits.append((int(a),int(b),int(strips),int(row_hits)))
    if not hits:return None
    best=max(hits,key=lambda p:(p[2],p[3]))
    return best if all(abs(z[0]-best[0])<=3 and abs(z[1]-best[1])<=3 for z in hits) else None
