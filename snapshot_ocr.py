"""Compact nameplate OCR by default. Full-scene recovery is explicit only."""
from fast_shop_match import Hit, norm


def glyph_key(text):
    # Pixel fonts often merge the adjacent strokes of r+n into m.
    return norm(text).replace('rn','m').replace('l','i')


def white_labels(bgr):
    import cv2
    import numpy as np
    lo=bgr.min(axis=2);hi=bgr.max(axis=2)
    mask=np.uint8((lo>125)&((hi.astype(np.int16)-lo)<55))*255
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((2,5),np.uint8))
    contours,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    h,w=bgr.shape[:2];boxes=[]
    for contour in contours:
        x,y,bw,bh=cv2.boundingRect(contour)
        if not (18<=bw<=180 and 6<=bh<=24 and bw/bh>1.8 and .12*h<y<.95*h):continue
        l=max(0,x-4);t=max(0,y-4);r=min(w,x+bw+4);b=min(h,y+bh+4)
        crop=bgr[t:b,l:r]
        darkness=float(np.mean(crop.max(axis=2)<125))
        if darkness>=.72:boxes.append((darkness,(l,t,r,b)))
    return [b for _,b in sorted(boxes,reverse=True)[:32]]


class SnapshotOCR:
    def __init__(self):
        import cv2
        import numpy as np
        self.native=None
        try:
            import winocr
            # Warm WinRT and language initialization before the user enters.
            winocr.recognize_cv2_sync(np.full((64,200,3),255,np.uint8),'en')
            self.native=winocr
        except Exception:
            import pytesseract
            import shutil
            from pathlib import Path
            exe=shutil.which('tesseract') or r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            self.tess=pytesseract if Path(exe).exists() else None
            if self.tess is not None:self.tess.pytesseract.tesseract_cmd=exe

    def map_state(self,bgr):
        """One small header OCR per settled transition, never a polling loop."""
        import cv2
        import re
        crop=bgr[:min(100,bgr.shape[0]),:min(230,bgr.shape[1])]
        crop=cv2.resize(crop,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
        # White map lettering has a shadow on a blue panel. Isolate it so
        # the window title/minimap icons do not drown out the room name.
        crop=255-cv2.inRange(crop,(190,190,190),(255,255,255))
        crop=cv2.cvtColor(crop,cv2.COLOR_GRAY2BGR)
        if self.native:
            data=self.native.recognize_cv2_sync(crop,'en')
            text=' '.join(str(line.get('text','')) for line in data.get('lines',[]))
        elif getattr(self,'tess',None) is not None:
            text=self.tess.image_to_string(crop,config='--psm 6',timeout=.5)
        else:
            return 'unknown'
        return classify_map_text(text)

    def _primary(self,bgr,target):
        import cv2
        import numpy as np
        from nameplate_scan import find_wooden_labels
        from native_ocr import winocr_hits
        from fast_shop_worker import from_tesseract
        if not self.native and getattr(self,'tess',None) is None:
            raise RuntimeError('No primary OCR; using local recovery engine')
        h,w=bgr.shape[:2]
        scale=min(1.5,1800/max(w,h))
        if getattr(self,'deep_scan',False):
            base=cv2.resize(bgr,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
            bh,bw=base.shape[:2]
        else:
            # Only enlarged candidate labels; never append the full game scene.
            bh,bw=0,960
        # White labels get the same enlargement as decorative wooden labels.
        labels=[(box,True) for box in white_labels(bgr)]
        labels += [(box,False) for box in find_wooden_labels(bgr,limit=12)]
        cols=3;rowh=100;colw=bw//cols
        labels=labels[:max(0,(2500-bh)//rowh)*cols]
        extra=((len(labels)+cols-1)//cols)*rowh
        atlas=np.full((bh+extra,bw,3),255,np.uint8)
        if bh:atlas[:bh]=base
        if not labels and not bh:return None
        transforms=[]
        for i,((l,t,r,b),invert) in enumerate(labels):
            factor=min(3.,(colw-16)/max(1,r-l),84/max(1,b-t))
            crop=bgr[t:b,l:r]
            if invert:crop=255-crop
            crop=cv2.resize(crop,None,fx=factor,fy=factor,interpolation=cv2.INTER_CUBIC)
            ch,cw=crop.shape[:2];x=8+(i%cols)*colw;y=bh+(i//cols)*rowh+8
            atlas[y:y+ch,x:x+cw]=crop
            transforms.append((x,y,x+cw,y+ch,l,t,factor))
        aliases={target}
        if 'rn' in target.casefold():aliases.add(target.casefold().replace('rn','m'))
        if 'm' in target.casefold():aliases.add(target.casefold().replace('m','rn'))
        aliases |= {v.casefold().replace('i','l') for v in aliases.copy()}
        aliases |= {v.casefold().replace('l','i') for v in aliases.copy()}
        hits=[]
        if self.native:
            data=self.native.recognize_cv2_sync(atlas,'en')
            for alias in aliases:hits.extend(winocr_hits(data,alias))
        else:
            data=self.tess.image_to_data(atlas,config='--psm 11',
                output_type=self.tess.Output.DICT,timeout=(3 if getattr(self,'deep_scan',False) else .5))
            for alias in aliases:hits.extend(from_tesseract(data,alias))
        self.last_diagnostic['primary_words'] = ([str(w.get('text','')) for line in data.get('lines',[]) for w in line.get('words',[])] if self.native else [str(t) for t in data.get('text',[]) if str(t).strip()])
        exact=[]
        for hit in hits:
            # Never label a substring or fuzzy guess as the seller.
            if glyph_key(hit.text)!=glyph_key(target):continue
            a,b,c,d=hit.box
            if d<=bh:
                box=tuple(round(v/scale) for v in (a,b,c,d))
            else:
                tr=next((v for v in transforms if v[0]<=a and v[1]<=b and c<=v[2] and d<=v[3]),None)
                if tr is None:continue
                x,y,_,_,l,t,f=tr
                box=(round((a-x)/f+l),round((b-y)/f+t),round((c-x)/f+l),round((d-y)/f+t))
            cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
            if any(v.box[0]-8<=cx<=v.box[2]+8 and v.box[1]-8<=cy<=v.box[3]+8 for v in exact):continue
            exact.append(Hit(hit.text,box,hit.score,'EXACT' if norm(hit.text)==norm(target) else 'CONFUSABLE'))
        return exact[0] if len(exact)==1 else None


    def prepare_recovery(self):
        """Warm once while arming; explicit single-thread inference sessions."""
        import numpy as np
        import onnxruntime
        onnxruntime.disable_telemetry_events()
        from rapidocr_onnxruntime import RapidOCR
        self.recovery=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,
                              use_cls=False,text_score=.3)
        self.recovery(np.full((64,200,3),255,np.uint8),use_cls=False)

    def scan(self,bgr,target):
        import time
        import cv2
        from pathlib import Path
        import json
        started=time.perf_counter()
        self.last_diagnostic={'target':target,'frame_size':list(bgr.shape[:2]),
                              'backend':'Windows OCR' if self.native else 'Tesseract',
                              'primary_words':[],'recovery_words':[],'errors':[]}
        hit=None
        try:
            try:
                hit=self._primary(bgr,target)
            except Exception as exc:
                self.last_diagnostic['errors'].append('primary: '+str(exc))
            if hit is not None:
                return hit
            if not getattr(self,'deep_scan',False):
                return None
            engine=getattr(self,'recovery',None)
            if engine is None:
                self.prepare_recovery()
                engine=self.recovery
            if engine is None:
                self.last_diagnostic['errors'].append('Recovery engine unavailable; run installer')
                return None
            # Normalize the scene, rather than allowing the detector to shrink
            # 5-10px name text. Still only ONE additional pass on this snapshot.
            h,w=bgr.shape[:2];factor=1600/max(1,w)
            scene=cv2.resize(bgr,(1600,max(1,round(h*factor))),interpolation=cv2.INTER_CUBIC)
            # Restore contrast after a fade or dim capture without changing geometry.
            scene=cv2.normalize(scene,None,0,255,cv2.NORM_MINMAX)
            callback=getattr(self,'progress',None)
            if callback:callback('FAST SCAN MISSED · checking the same snapshot with recovery OCR')
            output,_=engine(scene,use_cls=False)
            matches=[]
            for polygon,text,score in output or []:
                box=(round(min(pt[0] for pt in polygon)/factor),
                     round(min(pt[1] for pt in polygon)/factor),
                     round(max(pt[0] for pt in polygon)/factor),
                     round(max(pt[1] for pt in polygon)/factor))
                self.last_diagnostic['recovery_words'].append({'text':text,'confidence':float(score),'box':box})
                if score<.65 or glyph_key(text)!=glyph_key(target):continue
                matches.append(Hit(text,box,float(score),'EXACT' if norm(text)==norm(target) else 'CONFUSABLE'))
            # Do not silently select among multiple people with similar names.
            if len(matches)==1:hit=matches[0]
            return hit
        except Exception as exc:
            self.last_diagnostic['errors'].append('recovery: '+str(exc))
            return None
        finally:
            self.last_diagnostic['elapsed_ms']=round((time.perf_counter()-started)*1000,1)
            self.last_diagnostic['result']=None if hit is None else {'text':hit.text,'box':hit.box,'mode':hit.mode}
            # Text only, overwritten per snapshot; no screenshot/video recording.
            try:
                Path(__file__).with_name('last_scan_debug.json').write_text(
                    json.dumps(self.last_diagnostic,indent=2),encoding='utf-8')
            except OSError:pass


def classify_map_text(text):
    import re
    text=' '.join(text.casefold().split())
    if 'entrance' in text:
        return 'entrance'
    match=re.search(r'(?:free\s*)?market\s*[<([{]?\s*(\d{1,2})\b',text)
    if match and 1<=int(match.group(1))<=20:
        return 'room'
    return 'unknown'
