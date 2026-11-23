"""Click-through channel destination marker anchored to the real game menu."""
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np
from shop_pin import ShopPin
from window_capture import window_at_point

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

def preview_channel(channel, window, client):
    """Project the 1280×720 menu cell into the overlay's window coordinates."""
    if not 1 <= channel <= 40 or window is None or client is None:
        return None
    left, top, width, height = window
    client_left, client_top, client_width, client_height = client
    if (client_width, client_height) != (1280, 720):
        return None
    row, column = divmod(channel - 1, 8)
    # First cell is (361, 319) in the game client in the supplied screenshot.
    x = client_left - left + 361 + 70 * column
    y = client_top - top + 319 + 22 * row
    if not (0 <= x < x + 68 <= width and 0 <= y < y + 20 <= height):
        return None
    return x, y, x + 68, y + 20


class ChannelPin(ShopPin):
    def __init__(self, master):
        super().__init__(master,interval_ms=25)

    def can_show(self, hwnd, rect, size, hits):
        if super().can_show(hwnd, rect, size, hits):
            return True
        left, top, width, height = rect
        sw, sh = size
        # A CHASE click can leave HeneFM in front. Show over exposed game
        # pixels only, including the space occupied by the arrow and label.
        for hit in hits.values():
            if hit['mode'] not in ('GUIDE', 'CHASE_CELL'):
                return False
            l, t, r, b = hit['box']
            x1, x2 = left + l * width / sw, left + r * width / sw
            y1, y2 = top + t * height / sh, top + b * height / sh
            mid = (x1 + x2) / 2
            points = [(x, y) for x in (x1-6, mid, x2+6) for y in (y1-6, y2+6)]
            points.extend((x, y) for x in (mid-35, mid, mid+35) for y in (y1-66, y1-19))
            if any(window_at_point(round(x), round(y)) != hwnd for x, y in points):
                return False
        return bool(hits)

    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all');sx,sy=w/sw,h/sh
        for name,hit in hits.items():
            x,y,r,b=hit['box'];x*=sx;y*=sy;r*=sx;b*=sy
            if hit.get('mode')=='PRE':
                # No visual search needed: show the channel destination as
                # soon as HeneFM chooses it, even before menu appears.
                label=name+' · OPEN CHANNEL MENU'
                for color,width in [('#000000',9),('#ffffff',6),('#ffdb3d',3)]:
                    c.create_rectangle(x,y,r,b,outline=color,width=width)
                c.create_text((x+r)/2,(y+b)/2,text=label,fill='#ffe979',
                              font=('Segoe UI',11,'bold'))
                continue
            guide=hit['mode']=='GUIDE'
            accent='#ffdb3d' if guide else '#ff1744'
            for color,width in [('#000000',9),('#ffffff',6),(accent,3)]:
                c.create_rectangle(x-2,y-2,r+2,b+2,outline=color,width=width)
            cx=(x+r)/2
            for color,width in [('#000000',12),('#ffffff',8),(accent,5)]:
                c.create_line(cx,y-42,cx,y-5,fill=color,width=width,arrow='last',arrowshape=(12,15,8))
            c.create_text(cx,y-52,text=name,fill=accent,font=('Segoe UI',14,'bold'))
