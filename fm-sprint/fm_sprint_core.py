"""FM Sprint shared lifecycle and native bitmap-key recognizer. No platform I/O."""
from dataclasses import dataclass
from collections import OrderedDict
import hashlib
import numpy as np

@dataclass(frozen=True)
class Scene:
    focus: bool = True
    entrance: bool = False
    room: bool = False
    black: bool = False
    menu: bool = False
    selected: bool = False
    shop: bool = False
    hit: bool = False
    pin: bool = False
    confirm: bool = False

class Lifecycle:
    """One lock = one run. Emit bounded actions, never replay old actions."""
    def __init__(self):
        self.reset(None, False)
    def reset(self, key, same_channel=False):
        self.key=key; self.same=same_channel; self.stage='route' if key else 'idle'
        self.seen_entrance=False; self.menu_seen=False; self.black_count=0
        self.cell_sent=False; self.confirm_sent=False; self.shop_sent=False
    def step(self, key, scene, *, same_channel=False, navigate=False):
        if key != self.key: self.reset(key,same_channel)
        if not key or not scene.focus:
            self.black_count=0; return []
        if self.stage in ('idle','stopped'): return []
        self.black_count=self.black_count+1 if scene.black and not scene.room and not scene.menu else 0
        blackout=self.black_count>=2
        out=[]
        if self.stage=='route':
            self.seen_entrance |= scene.entrance
            if self.seen_entrance and (blackout or scene.room):
                self.stage='portal_loading' if blackout else ('shop' if self.same else 'channel')
                if self.same:
                    if scene.pin: out.append('park_shop_normal')
                else: out.append('park_channel')
        elif self.stage=='portal_loading' and scene.room:
            self.stage='shop' if self.same else 'channel'
        if self.stage=='channel':
            if scene.menu:
                self.menu_seen=True
                if navigate and not scene.selected and not self.cell_sent:
                    self.cell_sent=True;out.append('select_channel')
                elif navigate and scene.selected and scene.confirm and not self.confirm_sent:
                    self.confirm_sent=True;out.append('confirm_channel')
            elif blackout and self.menu_seen:
                self.stage='cc_loading'
                if scene.pin:out.append('park_shop_cc')
        if self.stage=='cc_loading' and scene.room:
            self.stage='shop'
        if self.stage=='shop':
            if scene.shop:
                self.stage='scan';out.append('park_clear')
            elif scene.room and scene.pin and not scene.menu and not self.shop_sent:
                # One speculative shop click at first return, opt-in. A pin is
                # an estimate, not an independently verified seller sign.
                self.shop_sent=True
                if navigate:out.append('open_projected_shop')
        if self.stage=='scan':
            if not scene.shop and scene.room:self.stage='shop'
            elif scene.hit:self.stage='item_ready'
        if self.stage=='item_ready' and not scene.shop:
            self.stage='stopped'
        return out
    def stop(self):self.stage='stopped';self.black_count=0

def channel_points(channel, size=(1366,768)):
    if size!=(1366,768) or not 1<=channel<=40:return None
    row,col=divmod(channel-1,8)
    return (437+70*col,353+22*row),(837,473)

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

class VisualBank:
    """Learn only OCR-observed names; conflicting evidence permanently abstains."""
    def __init__(self,limit=2048):self.entries=OrderedDict();self.limit=limit
    def learn(self,key,name):
        if key is None or not name or not name.strip() or name.rstrip().endswith(('...','…')):return
        if key in self.entries and self.entries[key]!=name:self.entries[key]=None
        elif key not in self.entries:self.entries[key]=name
        self.entries.move_to_end(key)
        while len(self.entries)>self.limit:self.entries.popitem(last=False)
    def get(self,key):return self.entries.get(key)

class RuneCache:
    """Native exact bitmap/sprite reuse; unknowns go to the existing OCR cache.
    The result remains advisory, and strict scroll verification stays upstream.
    """
    def __init__(self,base):self.base=base;self.bank=VisualBank()
    def recognize(self,frame,rows,ocr):
        rows=tuple(rows);keys={r:visual_key(frame,r) for r in rows}
        names={r:n for r,k in keys.items() if (n:=self.bank.get(k)) is not None}
        missing=[r for r in rows if r not in names]
        if not missing:return names,len(rows),0,False
        fresh,h,m,used=self.base.recognize(frame,missing,ocr)
        for r,n in fresh.items():self.bank.learn(keys[r],n)
        names.update(fresh)
        return names,len(rows)-len(missing)+h,m,used

def menu_evidence(frame,header,channel):
    """Fixed native change-channel header + independently colored selection/confirm."""
    a=bgr_array(frame)
    if a.shape[:2]!=(200,565) or header.shape!=(51,164):return False,False,False,0.
    g=(a[:51,:164,0]*.114+a[:51,:164,1]*.587+a[:51,:164,2]*.299).astype(np.float32).ravel()
    t=header.astype(np.float32).ravel();g-=g.mean();t-=t.mean()
    score=float(np.dot(g,t)/max(float(np.linalg.norm(g)*np.linalg.norm(t)),1e-6))
    if score<.95:return False,False,False,score
    row,col=divmod(channel-1,8)
    def blue(p):
        b,g,r=p.astype(np.int16).transpose(2,0,1)
        return float(np.mean((b>=155)&(g>=80)&(g<=210)&(r<=145)&(b-r>=45)))>.70
    selected=blue(a[65+22*row:69+22*row,10+70*col:22+70*col])
    confirm=blue(a[185:189,387:399])
    return True,selected,confirm,score

@dataclass(frozen=True)
class PurchaseProof:
    same_lock: bool=False
    exact_gate: bool=False
    verified_channel: bool=False
    exact_identity: bool=False
    exact_unit_price: bool=False
    quantity: int=0
    statless_verified: bool=False
    selected_row: bool=False
    no_tooltip: bool=False
    fresh_frame: bool=False
    transaction_ui_verified: bool=False
    receipt_detector_qualified: bool=False

def purchase_ready(proof):
    return proof.quantity==1 and all(getattr(proof,k) for k in proof.__dataclass_fields__ if k!='quantity')
