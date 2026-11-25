"""Fixed-anchor shop evidence. No platform dependencies or identity inference."""
WIDTH, HEIGHT = 204, 334
AX, AY = 140, 1

def _valid(frame):
    if frame is None:return False
    b,w,h,s=frame
    return w==WIDTH and h==HEIGHT and s>=w*3 and len(b)==s*h

def button_evidence(frame):
    """Verify expected horizontal button strips; allow color drift, not a moved crop."""
    if not _valid(frame):return False
    b,w,h,s=frame
    def pixel(x,y):
        i=y*s+x*3
        return b[i:i+3]
    def green(p):
        B,G,R=p
        return G>=190 and R>=175 and B<=115 and G-B>=85 and abs(G-R)<=40
    def orange(p):
        B,G,R=p
        return R>=190 and 115<=G<=195 and B<=155 and R-G>=35 and R-B>=65
    def strip(y, pred):
        return sum(pred(pixel(x,y)) for x in range(AX+2,AX+24))>=19
    def dark_above(y):
        return sum(max(pixel(x,y-1))<=100 for x in range(AX+2,AX+24))>=18
    if not (strip(AY,green) and dark_above(AY)):return False
    return sum(strip(AY+dy,orange) and dark_above(AY+dy) for dy in (31,51))>=1

def geometry_present(frame):
    """Require fixed button layout AND repeated independent row backgrounds."""
    if not button_evidence(frame):return False
    b,w,h,s=frame
    def pixel(x,y):
        i=y*s+x*3
        return b[i:i+3]
    def orange(p):
        B,G,R=p
        return R>=190 and 115<=G<=195 and B<=155 and R-G>=35 and R-B>=65
    def row_bg(p):
        B,G,R=p
        return (abs(B-227)<=20 and abs(G-217)<=20 and abs(R-205)<=20 or
                min(p)>=225 and max(p)-min(p)<=28 or
                B<=110 and G>=95 and R>=185 and R-G>=35 and G-B>=35)
    strips=sum(sum(orange(pixel(x,AY+dy)) for x in range(AX+2,AX+24))>=19 for dy in (31,51))
    rows=0
    for i in range(6):
        y=AY+93+i*40
        columns=sum(sum(row_bg(pixel(AX+dx,yy)) for yy in range(y+4,y+36))>=22
                    for dx in (-100,-55,-10,54))
        rows+=columns>=2
    return rows>=3 if strips==2 else rows>=4

def conservative_hits(hits, strict):
    """Geometry is supporting evidence only: never grant an exact match."""
    if strict or len(hits)!=1:return []
    row,mode=hits[0]
    if mode=='MATCH':mode='ROW_CHECK'
    elif mode=='SOLD':mode='SOLD_CHECK'
    return [(row,mode)] if mode in ('ROW_CHECK','PRICE_CHECK','SOLD_CHECK') else []
