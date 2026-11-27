import hashlib
import numpy as np

def bgr_array(frame):
    buf,w,h,stride=frame
    if w<=0 or h<=0 or stride<w*3 or len(buf)!=stride*h:raise ValueError('bad frame')
    return np.frombuffer(buf,np.uint8).reshape(h,stride)[:,:w*3].reshape(h,w,3)

def visual_key(frame,row):
    """Exact name-mask + icon foreground fingerprint, not fuzzy OCR or stats."""
    p=bgr_array(frame)
    if p.shape[0]<263 or p.shape[1]<204 or not 0<=row<6:return None
    y=26+40*row
    n=p[y:y+20,40:198];icon=p[y:y+20,5:35]
    e=p[27+40*row:59+40*row,194].astype(np.int16)
    b,g,r=e.T
    selected=np.sum((b>=20)&(b<=100)&(g>=100)&(g<=205)&(r>=195)&(r-g>=45)&(g-b>=45))>=24
    mask=n[:,:,2]<145 if selected else n.sum(2,dtype=np.uint16)//3<145
    if np.count_nonzero(mask)<8:return None
    # Discard the normal and orange row background, retain actual sprite colors.
    v=icon.astype(np.int16); bg=(np.max(np.abs(v-[227,217,205]),axis=2)<=30)
    bg |= (v[:,:,0]<110)&(v[:,:,1]>=95)&(v[:,:,2]>=185)&(v[:,:,2]-v[:,:,1]>=35)&(v[:,:,1]-v[:,:,0]>=35)
    sprite=icon.copy();sprite[bg]=0
    if np.count_nonzero(sprite)<12:return None
    return hashlib.blake2b(np.packbits(mask).tobytes()+sprite.tobytes(),digest_size=20).digest()
