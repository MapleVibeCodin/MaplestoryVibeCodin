"""Step 13 shadow experiment: fixed-ROI color landmarks + known row bitmap masks.
OBS replay only. No production capture integration, mouse or game input.
Calibrated for a 225x344 crop at preview coordinate (425,210), not native window.
"""
import numpy as np

Y_GROUPS=((5,8,12,17),(35,39,44),(56,60,65))
X=np.array([148,154,160,165,171,177,183,189,195,201])
Y=[np.repeat(np.array(y),len(X)) for y in Y_GROUPS]
XX=[np.tile(X,len(y)) for y in Y_GROUPS]

def make_gate(ref):
    return [ref[y,x].astype(np.int16) for y,x in zip(Y,XX)]

def row_features(p):
    c=p[81:344,:204]
    rows=np.stack([c[26+40*r:46+40*r,40:198] for r in range(6)])
    icons=np.stack([c[26+40*r:46+40*r,5:35] for r in range(6)])
    b,g,rr=rows.astype(np.int16).transpose(3,0,1,2)
    purple=(b>40)&(rr<145)&(g<145)&(b-rr>28)&(b-g>23)
    runs=purple[:,:,:147].copy()
    for k in range(1,12):runs &= purple[:,:,k:k+147]
    blocked=(runs.any(axis=2).sum(axis=1)>=3)
    ink=(rows[:,:,:,2]<145)&~purple
    edges=np.stack([c[27+40*r:59+40*r,194] for r in range(6)])
    pale=((edges.min(axis=2)>=230)&((edges.max(axis=2)-edges.min(axis=2))<=22)).sum(axis=1)>=24
    return ink,icons,blocked,pale

def template(p,row):
    m,ic,_,_=row_features(p)
    sprite=ic[row]
    yy,xx=np.indices(sprite.shape[:2])
    bg=(sprite.min(2)>190)&((sprite.max(2)-sprite.min(2))<45)
    sel=(~bg)&((yy%2==0)&(xx%2==0))
    if sel.sum()<8:sel=(yy%2==0)&(xx%2==0)
    return (m[row],sel,sprite[sel].astype(np.int16))

def gate_v2(p,refs):
    scores=[np.mean(np.max(np.abs(p[y,x].astype(np.int16)-v),axis=1)<=42) for y,x,v in zip(Y,XX,refs)]
    if sum(s>=.80 for s in scores)<2 or min(scores)<.45:return False
    band=p[90:116,:200].astype(np.int16)
    if ((band[:,:,0]-band[:,:,2])>45).mean()>.55:return False
    return True

def recognize_v2(p,t):
    ink,ic,blocked,pale=row_features(p);mask,sel,colors=t
    intersection=np.count_nonzero(ink&mask,axis=(1,2))
    union=np.count_nonzero(ink|mask,axis=(1,2))
    similarity=intersection/np.maximum(union,1)
    dist=np.abs(ic[:,sel].astype(np.int16)-colors).mean(axis=(1,2))
    matching_names=np.flatnonzero(similarity>=.80)
    if len(matching_names)>1:return None,'ambiguous_name'
    if len(matching_names)!=1:return None,'no_match'
    r=int(matching_names[0])
    if dist[r]>25:return None,'sprite_not_verified'
    if blocked[r] or pale[r]:return None,'blocked_or_sold'
    return r,'match'
