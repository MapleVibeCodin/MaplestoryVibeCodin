"""Click-through channel destination marker anchored to the real game menu."""
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np
from shop_pin import ShopPin

@lru_cache(maxsize=1)
def reference():
    with np.load(Path(__file__).with_name('assets')/'channel_menu.npz') as data:
        return data['header'].copy()

def locate_channel(frame,channel):
    if not isinstance(channel,int) or not 1<=channel<=40:return None
    h,w=frame.shape[:2]
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY);original=reference()
    # Find the menu rather than assuming the window's screen position/titlebar.
    l,t,r,b=round(w*.12),round(h*.18),round(w*.88),round(h*.82)
    region=gray[t:b,l:r];best=None
    for scale in dict.fromkeys((1.,round(w/1366,2))):
        template=cv2.resize(original,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        th,tw=template.shape
        if th>region.shape[0] or tw>region.shape[1]:continue
        _,score,_,(dx,dy)=cv2.minMaxLoc(cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED))
        if score<.86 or best is not None and score<=best[0]:continue
        row,col=divmod(channel-1,8)
        x,y=l+dx,t+dy
        box=tuple(round(v) for v in (x+(1+70*col)*scale,y+(61+22*row)*scale,
                                    x+(68+70*col)*scale,y+(81+22*row)*scale))
        if box[0]<0 or box[1]<0 or box[2]>w or box[3]>h:continue
        best=(score,box)
    return best[1] if best else None

class ChannelPin(ShopPin):
    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all');sx,sy=w/sw,h/sh
        for name,hit in hits.items():
            x,y,r,b=hit['box'];x*=sx;y*=sy;r*=sx;b*=sy
            for color,width in [('#000000',9),('#ffffff',6),('#ff1744',3)]:
                c.create_rectangle(x-2,y-2,r+2,b+2,outline=color,width=width)
            cx=(x+r)/2
            for color,width in [('#000000',12),('#ffffff',8),('#ff1744',5)]:
                c.create_line(cx,y-42,cx,y-5,fill=color,width=width,arrow='last',arrowshape=(12,15,8))
            c.create_text(cx,y-52,text=name,fill='#ff1744',font=('Segoe UI',14,'bold'))
