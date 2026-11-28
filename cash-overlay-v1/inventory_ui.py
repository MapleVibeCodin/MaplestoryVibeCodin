"""Read-only inventory window detection using generic title glyphs and red selected tab.
Reference templates contain UI titles only, not player holdings or account information."""
import base64
import cv2
import numpy as np

ITEM_TITLE = "iVBORw0KGgoAAAANSUhEUgAAAFUAAAAMCAAAAAA2H665AAAAhklEQVQ4EbXBgW0EQRAEITr/oOtHsi+EheWB5YHlgeWB5aw5zWmxsBZrsea0WHMyMmSx/FnOYrGcacKarMVazmSxWKzFspZ/y1kshqy1sNZaizVkrcVisYawfJazWCxnsbCWyVqWs0wsFmuxWD7LWSzmtFhYi8ViTovFwshisXyWB5YHlgd+AYZrAeHBFMMAAAAASUVORK5CYII="
EQUIP_TITLE = "iVBORw0KGgoAAAANSUhEUgAAAG4AAAAMCAAAAACmDNd2AAAAq0lEQVQ4Eb3BwUHAABAEIab/oteLeViBgeZLzZeaLzVfanImptFamEbLWaPlDK3RGi1njZYzMWEazaNpTqM1Wmu0LGtOptE8WqY1WnMyjUajNZrW/GrCNFqjtTCttTCtNZpHa601WpjWGo1GC0PzaprTaI3WmtNozWkymkdrMq1pTpPRaLRGo3k1ORMjpjWn0XLWaDSP1mg0ctZoNMQ0Gs2r+dP8s+ZLzZd+ANz5kwHAcP7NAAAAAElFTkSuQmCC"

def clip(rect, shape):
    x,y,w,h=map(int,rect); H,W=shape[:2]
    x0,y0=max(0,x),max(0,y); x1,y1=min(W,x+w),min(H,y+h)
    return (x0,y0,x1-x0,y1-y0) if x1>x0 and y1>y0 else None

class InventoryDetector:
    def __init__(self):
        self.titles=[(kind,cv2.imdecode(np.frombuffer(base64.b64decode(data),np.uint8),0),ox,oy,wh)
                     for kind,data,ox,oy,wh in [('item',ITEM_TITLE,5,6,(205,290)),('equip',EQUIP_TITLE,7,8,(173,310))]]
        self.cached={}
    def detect(self, frame):
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        results=[]
        for kind,tpl,ox,oy,(w,h) in self.titles:
            best=None
            # Native UI scale is tried first; use other common DPI scales only when necessary.
            for scale in (1,.75,1.25,1.5,2):
                key=(kind,scale)
                if key not in self.cached:
                    self.cached[key]=cv2.resize(tpl,None,fx=scale,fy=scale,interpolation=cv2.INTER_LINEAR)
                t=self.cached[key]
                if t.shape[0]>gray.shape[0] or t.shape[1]>gray.shape[1]: continue
                _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(gray,t,cv2.TM_CCOEFF_NORMED))
                if score>=.94 and (best is None or score>best[0]):
                    best=(score,scale,round(x-ox*scale),round(y-oy*scale))
                if score>=.985: break
            if best is None: continue
            score,s,x,y=best
            names=['equip','use','setup','etc','cash','deco'] if kind=='item' else ['equip','deco','beauty']
            votes=[]
            for i,n in enumerate(names):
                rect=clip((round(x+(5+33*i)*s),round(y+26*s),round(29*s),round(16*s)),frame.shape)
                if not rect: votes.append((0,n)); continue
                xx,yy,ww,hh=rect
                B,G,R=cv2.split(frame[yy:yy+hh,xx:xx+ww].astype(np.int16))
                votes.append((float(((R>G+45)&(R>B+30)).mean()),n))
            votes.sort(reverse=True)
            active=votes[0][1] if votes[0][0]>=.30 and votes[0][0]-votes[1][0]>=.18 else None
            # Extra margin includes the wallet footer and variable crop borders.
            box=clip((x-3,y-3,round(w*s)+8,round(h*s)+8),frame.shape)
            if box is not None:
                results.append(dict(kind=kind,tab=active,box=list(box),score=round(score,4),
                                    page=('pet' if kind=='equip' and active=='deco' else active if kind=='item' and active in ('use','etc') else None)))
        return results
