"""Read actual room lettering once; match whole OCR words to live sellers.

The selected IGN gets bounded visual location proposals; these never prove
identity. English ONNX recognition verifies actual text, while other sellers
share the generic room index. No room-header OCR blocks an entry search.
"""
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import hashlib
import re
import time
import queue
import threading
import cv2
import numpy as np
from fast_shop_match import Hit,norm
from selected_word_candidates import propose as selected_proposals

MODEL_SHA='c3461add59bb4323ecba96a492ab75e06dda42467c9e3d0c18db5d1d21924be8'


def entry_level(frame):
    h,w=frame.shape[:2]
    levels=[float(frame[int((y-.06)*h):int((y+.06)*h):16,
                        int((x-.06)*w):int((x+.06)*w):16].mean())
            for x,y in ((.25,.25),(.75,.25),(.5,.5),(.25,.7),(.75,.7))]
    return float(np.median(levels))

def entry_readable(frame):
    return entry_level(frame)>=26 and float(np.percentile(frame[::16,::16],98))>=65


def glyph_key(text):
    return norm(text).replace('rn','m').replace('vl','m').replace('l','i')


def text_regions(frame):
    """Generic contrast/connected-letter grouping, independent of any IGN."""
    height,width=frame.shape[:2]
    bottom=round(height*.91) if height>300 else height
    image=frame[:bottom]
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blue,green,red=cv2.split(image)
    low=cv2.min(blue,cv2.min(green,red));high=cv2.max(blue,cv2.max(green,red))
    neutral=cv2.compare(cv2.subtract(high,low),80,cv2.CMP_LT)
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    result=[]
    for dark in (False,):
        contrast=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT,kernel)
        mask=cv2.bitwise_and(cv2.compare(contrast,32,cv2.CMP_GT),neutral)
        mask=cv2.bitwise_and(mask,cv2.compare(gray,175 if dark else 90,cv2.CMP_LT if dark else cv2.CMP_GT))

        ink_mask=mask.copy()
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((2,2),np.uint8))
        words=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_RECT,(9,3)))
        _,_,stats,_=cv2.connectedComponentsWithStats(words)
        for x,y,w,h,area in stats[1:]:
            x,y,w,h,area=map(int,(x,y,w,h,area))
            if not (15<=w<=240 and 5<=h<=26 and w>h*1.3):continue
            l=max(0,x-2);t=max(0,y-2);r=min(width,x+w+3);b=min(bottom,y+h+2)
            patch=gray[t:b,l:r]
            if dark:
                level=float(np.median(patch))
                if not 105<=level<=205 or np.mean(neutral[t:b,l:r]>0)<.60:continue
            elif np.mean(patch<135)<.35:continue
            fill=float(np.mean(mask[y:y+h,x:x+w]>0))
            if fill<.08:continue
            _,_,pieces,_=cv2.connectedComponentsWithStats(mask[y:y+h,x:x+w])
            glyphs=[q for q in pieces[1:] if q[cv2.CC_STAT_AREA]>=3 and q[cv2.CC_STAT_HEIGHT]>=3]
            if len(glyphs)<2:
                _,_,pieces,_=cv2.connectedComponentsWithStats(ink_mask[y:y+h,x:x+w])
                glyphs=[q for q in pieces[1:] if q[cv2.CC_STAT_AREA]>=3 and q[cv2.CC_STAT_HEIGHT]>=3]
            if len(glyphs)<2:continue
            baselines=[int(q[cv2.CC_STAT_TOP]+q[cv2.CC_STAT_HEIGHT]) for q in glyphs]
            if max(sum(abs(a-b)<=3 for a in baselines) for b in baselines)<min(3,len(glyphs)):continue
            border=np.concatenate((patch[0],patch[-1]))
            quality=float(np.mean(border<140)) if not dark else float(np.mean(border>110))
            box=(l,t,r,b)
            # Prefer a single whole line; word hypotheses with the same bounds
            # from opposite polarities must not consume recognition twice.
            if any(abs((l+r)-(q[0][0]+q[0][2]))<6 and abs(t-q[0][1])<3 and abs((r-l)-(q[0][2]-q[0][0]))<6 for q in result):continue
            _,_,raw_pieces,_=cv2.connectedComponentsWithStats(ink_mask[y:y+h,x:x+w])
            letter_count=max(len(glyphs),sum(q[cv2.CC_STAT_AREA]>=3 and q[cv2.CC_STAT_HEIGHT]>=3 for q in raw_pieces[1:]))
            result.append((box,dark,quality,letter_count))
            if b-t>=20 and r-l>=30 and letter_count>=4:
                rows=(ink_mask[t:b,l:r]>0).sum(axis=1)
                density=np.convolve(rows,np.ones(9,dtype=int),'valid')
                peak=int(density.argmax())
                if density[peak]>=(r-l)*1.2:
                    band_top=max(t,t+peak-2);band_bottom=min(b,band_top+13)
                    columns=np.flatnonzero((ink_mask[band_top:band_bottom,l:r]>0).sum(axis=0)>=2)
                    if len(columns):
                        band_left=max(l,l+int(columns[0])-2);band_right=min(r,l+int(columns[-1])+3)
                        if band_right-band_left>=15:
                            result.append(((band_left,band_top,band_right,band_bottom),dark,max(.9,quality),letter_count))
    extra=[]
    for box,dark,quality,count in result:
        l,t,r,b=box
        if dark or b-t<20 or r-l<25:continue
        for local,_,_,letters in letter_regions(frame[t:b,l:r],keep_nested=True):
            x,y,q,d=local
            if q-x>=20 and d-y<=18:
                extra.append(((l+x,t+y,l+q,t+d),False,max(.95,quality),letters,True))
    result.extend(extra)
    return [entry for entry in result if (len(entry)>4 and entry[4]) or not any(other is not entry and
  other[0][0]<=entry[0][0]+3 and other[0][2]>=entry[0][2]-3 and
  abs((other[0][1]+other[0][3])-(entry[0][1]+entry[0][3]))<=8 and
  other[0][2]-other[0][0]>(entry[0][2]-entry[0][0])*1.15 for other in result)]


class EnglishRecognizer:
    def __init__(self):
        import onnxruntime as ort
        ort.disable_telemetry_events()
        model=Path(__file__).with_name('assets')/'english_name_rec.onnx'
        if not model.exists():raise RuntimeError('Missing English OCR model. Extract the entire clean package.')
        if hashlib.sha256(model.read_bytes()).hexdigest()!=MODEL_SHA:raise RuntimeError('English OCR model checksum mismatch; extract a fresh package.')
        options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(model),sess_options=options,providers=['CPUExecutionProvider'])
        self.characters=['']+self.session.get_modelmeta().custom_metadata_map['character'].splitlines()+[' ']
        self.input_name=self.session.get_inputs()[0].name
        self([np.full((16,64,3),255,np.uint8)])

    def __call__(self,crops):
        if not crops:return []
        prepared=[];widths=[]
        for crop in crops:
            h,w=crop.shape[:2];new_width=max(8,min(640,round(48*w/max(1,h))))
            sample=cv2.resize(crop,(new_width,48),interpolation=cv2.INTER_CUBIC)
            prepared.append(sample.transpose(2,0,1).astype(np.float32)/127.5-1.)
            widths.append(new_width)
        # A crop always uses the same padding width. A neighboring longer
        # crop must not change transformer padding and therefore its reading.
        groups={}
        for index,width in enumerate(widths):groups.setdefault(max(160,((width+31)//32)*32),[]).append(index)
        out=[None]*len(crops)
        for size,indices_in_group in groups.items():
            batch=np.zeros((len(indices_in_group),3,48,size),np.float32)
            for row,index in enumerate(indices_in_group):batch[row,:,:,:widths[index]]=prepared[index]
            predictions=self.session.run(None,{self.input_name:batch})[0]
            for index,prediction in zip(indices_in_group,predictions):
                actual_width=widths[index]
                indices=prediction.argmax(axis=1);confidences=prediction.max(axis=1)
                chars=[];last=-1
                for step,(character,confidence) in enumerate(zip(indices,confidences)):
                    character=int(character)
                    if character and character!=last and step*size/len(indices)<=actual_width+4:
                        chars.append((self.characters[character],float(confidence),step*size/len(indices)/actual_width))
                    last=character
                value=''.join(c for c,_,_ in chars)
                confidence=float(np.mean([v for _,v,_ in chars])) if chars else 0.
                out[index]=(value,confidence,chars)
        return out



@dataclass
class Label:
    box: tuple
    dark: bool
    quality: float
    patch: object
    glyphs: int = 0
    reading: object = None
    confirmed: object = None
    used_at: float = 0.
    accepted: bool = False
    neural: bool = False
    segmented: bool = False
    proposed: object = None
    source: object = None
    created: float = 0.
    repeat: bool = False
    direct: bool = False
    ignored: bool = False


class RoomTextReader:
    room_index_engine=True
    def __init__(self):
        self.recognizer=EnglishRecognizer()
        self.labels=[];self.last_diagnostic={};self.detected_at=0.
        self.shape=None;self.last_frame=None;self.targets=()
        self.detector=None;self.recovered=False;self.scene_started=0.
        self.work_frame=None;self.work_started=0.;self.source_frame=None
        self.producer=None;self.hit_sources={}
        self.visual_focus=None;self.visual_attempts=0;self.visual_frame=None
        self.load_detector()

    def reset(self):
        self.labels=[];self.last_frame=None;self.detected_at=0.
        self.recovered=False;self.scene_started=time.monotonic()
        self.visual_focus=None;self.visual_attempts=0;self.visual_frame=None
        self.work_frame=None;self.source_frame=None
        if self.producer:self.producer.reset()

    @staticmethod
    def patch(frame,box):
        x,y,r,b=box;gray=cv2.cvtColor(frame[y:b,x:r],cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray,(64,16),interpolation=cv2.INTER_AREA)

    @staticmethod
    def same(first,second):
        a=float(first.std());b=float(second.std())
        if a<3 or b<3 or not .8<b/a<1.25:return False
        return float(np.mean(np.abs(first.astype(np.int16)-second.astype(np.int16))))<7 or float(cv2.matchTemplate(first,second,cv2.TM_CCOEFF_NORMED)[0,0])>.97

    def close(self):
        if self.producer:
            self.producer.active=False;self.producer.shutdown.set()
            self.producer.join(1.)

    def start_detector(self,frames,stop):
        self.producer=SceneRegions(frames,stop)
        self.producer.start()

    @property
    def pending_regions(self):
        return self.producer is not None and not self.producer.output.empty()

    def set_active(self,value):
        if self.producer:self.producer.active=value

    @staticmethod
    def possible_word(word,name):
        source=norm(word);target=norm(name)
        return RoomTextReader.plausible(word,name) or any(target[i:i+4] in source for i in range(max(0,len(target)-3)))

    def possible_target(self,reading):
        source=norm(reading[0])
        return any(self.plausible(reading[0],name) or
            any(norm(name)[i:i+4] in source for i in range(max(0,len(norm(name))-3)))
            for name in self.targets)

    def ingest(self,frame,regions):
        now=time.monotonic()
        self.labels=[label for label in self.labels if now-label.created<.8]
        if not regions:return
        patches=[self.patch(frame,entry[0]) for entry in regions]
        def features(patches):
            a=np.asarray(patches,dtype=np.float32).reshape(len(patches),-1)
            a-=a.mean(axis=1,keepdims=True)
            a/=np.maximum(1.,np.linalg.norm(a,axis=1,keepdims=True))
            return a
        new=features(patches)
        prior=len(self.labels)
        scores=new@features([label.patch for label in self.labels]).T if prior else np.empty((len(patches),0))
        old_boxes=np.asarray([label.box for label in self.labels],dtype=np.float32).reshape(-1,4)
        # Relaxed matching may consolidate unread regions or cache a clearly
        # unrelated word. It can NEVER supply identity evidence for a marker.
        relaxable=np.asarray([label.reading is None or label.ignored or
            (label.reading[1]>=.90 and len(norm(label.reading[0]))>=3 and not self.possible_target(label.reading))
            for label in self.labels],dtype=bool)
        for i,(entry,patch) in enumerate(zip(regions,patches)):
            box,dark,quality,count=entry[:4];segmented=bool(entry[4]) if len(entry)>4 else False
            previous=None;relaxed=False
            if prior:
                best=int(scores[i].argmax())
                if scores[i,best]>.985:previous=self.labels[best]
                else:
                    x,y,r,b=box
                    intersection=np.maximum(0,np.minimum(r,old_boxes[:,2])-np.maximum(x,old_boxes[:,0]))*np.maximum(0,np.minimum(b,old_boxes[:,3])-np.maximum(y,old_boxes[:,1]))
                    area=(r-x)*(b-y)+(old_boxes[:,2]-old_boxes[:,0])*(old_boxes[:,3]-old_boxes[:,1])-intersection
                    allowed=relaxable&(scores[i]>.84)&(intersection/np.maximum(1,area)>.55)
                    if allowed.any():
                        best=int(np.where(allowed,scores[i],-1).argmax());previous=self.labels[best];relaxed=True
            if previous is not None:
                was_ignored=previous.ignored
                if relaxed and previous.reading is not None:previous.ignored=True;previous.accepted=False
                if previous.reading is not None and (was_ignored or not previous.accepted and now-previous.used_at>.12) and self.possible_target(previous.reading):
                    previous.reading=None;previous.confirmed=None;previous.proposed=None;previous.ignored=False
                previous.box=box;previous.source=frame;previous.patch=patch;previous.created=now
                previous.quality=max(previous.quality,quality);previous.glyphs=max(previous.glyphs,count)
                continue
            self.labels.append(Label(box,dark,quality,patch,glyphs=count,source=frame,created=now,segmented=segmented))
        self.labels=self.labels[-220:]
        self.last_frame=frame;self.shape=frame.shape

    def update(self,frame):
        newest=None
        if self.producer:
            # Never spend the arrival window indexing a backlog of old views.
            # The producer may run during OCR; only its latest valid snapshot
            # matters when recognition resumes.
            while True:
                try:generation,source,regions=self.producer.output.get_nowait()
                except queue.Empty:break
                if generation==self.producer.generation:newest=(source,regions)
            if newest is not None:self.ingest(*newest)
        elif frame is not self.last_frame:
            self.ingest(frame,text_regions(frame))

    def load_detector(self):
        from rapidocr_onnxruntime import main
        from rapidocr_onnxruntime.ch_ppocr_det import TextDetector
        config=main.update_model_path(main.read_yaml(main.DEFAULT_CFG_PATH))['Det']
        config.update(intra_op_num_threads=1,inter_op_num_threads=1,box_thresh=.35,thresh=.25,unclip_ratio=1.4)
        self.detector=TextDetector(config)
        self.detector(np.full((384,640,3),128,np.uint8))

    def recover_regions(self,frame,deep=True):
        """One general detector pass for difficult label geometry, never per IGN."""
        if self.recovered:return
        self.recovered=True
        for box,dark,quality,count in letter_regions(frame):
            self.labels.append(Label(box,dark,max(quality,1.4 if count>=8 else quality),self.patch(frame,box),glyphs=count,neural=True,source=frame,created=time.monotonic()))
        if not deep:return
        boxes,_=self.detector(frame)
        if boxes is None:return
        h,w=frame.shape[:2]
        for points in boxes:
            x,y=np.floor(points.min(axis=0)).astype(int);r,b=np.ceil(points.max(axis=0)).astype(int)
            x=max(0,int(x)-2);y=max(0,int(y)-2);r=min(w,int(r)+3);b=min(h,int(b)+2)
            if not (15<=r-x<=240 and 6<=b-y<=32) or y>h*.91:continue
            box=(x,y,r,b)
            if any(all(abs(a-z)<3 for a,z in zip(box,label.box)) for label in self.labels):continue
            gray=cv2.cvtColor(frame[y:b,x:r],cv2.COLOR_BGR2GRAY)
            dark=float(np.median(gray))>150
            if dark:continue
            self.labels.append(Label(box,dark,1.5,self.patch(frame,box),glyphs=max(3,round((r-x)/max(4,b-y-4)*1.6)),neural=True,source=frame,created=time.monotonic()))

    @staticmethod
    def crop(frame,label,confirm=False,variant=0):
        if label.source is not None:frame=label.source
        x,y,r,b=label.box
        pad=(1 if label.segmented else (4,4,12,16)[variant]) if confirm else (1 if label.segmented else 8)
        patch=frame[max(0,y-1):min(frame.shape[0],b+1),max(0,x-pad):min(frame.shape[1],r+pad)]
        gray=cv2.cvtColor(patch,cv2.COLOR_BGR2GRAY)
        if not confirm:
            low,high=np.percentile(gray,(2,98))
            if high-low>8 and high<160:gray=np.clip((gray.astype(np.float32)-low)*255/(high-low),0,255).astype(np.uint8)
        if label.repeat:
            patch=frame[y:b,max(0,x-pad):min(frame.shape[1],r+pad)]
            gray=cv2.cvtColor(patch,cv2.COLOR_BGR2GRAY)
            if confirm:
                gray=((patch.min(axis=2)>(160 if variant==0 else 190))&(patch.max(axis=2)-patch.min(axis=2)<60)).astype(np.uint8)*255
            if not label.dark:gray=255-gray
            gray=cv2.resize(gray,None,fx=6.,fy=3.,interpolation=cv2.INTER_CUBIC)
            gray=cv2.copyMakeBorder(gray,8,8,12,12,cv2.BORDER_CONSTANT,value=255)
            return cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)
        if confirm:
            low,high=np.percentile(gray,(2,98))
            if not label.segmented and high-low>12:gray=np.clip((gray.astype(np.float32)-low)*255/(high-low),0,255).astype(np.uint8)
            gray=cv2.resize(gray,None,fx=1.35 if variant==0 else 1.8,fy=1.,interpolation=cv2.INTER_CUBIC)
        if not label.dark:gray=255-gray
        return cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)

    @staticmethod
    def tokens(reading,box):
        text,confidence,chars=reading;x,y,r,b=box;words=[]
        # Keep whitespace-delimited words whole, rather than matching arbitrary
        # substrings of another seller's IGN.
        current=[]
        steps=[z[2]-a[2] for a,z in zip(chars,chars[1:]) if not a[0].isspace() and not z[0].isspace() and z[2]>a[2]]
        typical=float(np.median(steps)) if steps else .1
        for character,certainty,position in chars+[(' ',0,1.)]:
            separated=(current and character.isalnum() and (certainty<.70 or current[-1][1]<.70) and
                       position-current[-1][2]>max(typical*2.3,max(8,(b-y)*.6)/max(1,r-x)))
            if separated:
                token=''.join(c for c,_,_ in current).strip('.,:;!\"\'[]()')
                if token:
                    start=max(0.,min(1.,current[0][2]));end=min(1.,current[-1][2]+.04)
                    words.append((token,float(np.mean([v for _,v,_ in current])),(round(x+start*(r-x)),y,round(x+end*(r-x)),b)))
                current=[]
            if character.isspace():
                token=''.join(c for c,_,_ in current).strip('.,:;!\"\'[]()')
                if token:
                    start=max(0.,min(1.,current[0][2]));end=min(1.,max(start+.03,(current[-1][2]+.04)))
                    words.append((token,float(np.mean([v for _,v,_ in current])),(round(x+start*(r-x)),y,round(x+end*(r-x)),b)))
                current=[]
            else:current.append((character,certainty,position))
        if len(words)==1:words[0]=(words[0][0],words[0][1],box)
        if text.strip() and len(text.strip().split())>1:
            words.append((text.strip(),confidence,box))
        return words

    @staticmethod
    def confident_word(reading,word):
        groups=[];current=[]
        for character,score,_ in reading[2]+[(' ',0,1.)]:
            if character.isspace():
                if current:groups.append(current);current=[]
            else:current.append((character,score))
        return any(norm(''.join(c for c,_ in group))==norm(word) and all(score>=.90 for c,score in group if c.isalnum()) for group in groups)

    @staticmethod
    def rank(label,name):
        x,y,r,b=label.box;ratio=(r-x)/max(6,b-y-4)
        if label.glyphs>12 and len(name)>=8:return .15*min(1.,abs(ratio-len(name)*.55))-.8*label.quality
        tall_penalty=0. if len(name)>=7 and label.glyphs>=6 else .15*max(0,b-y-19)
        return .15*abs(ratio-max(1.5,len(name)*.55))-.8*label.quality+tall_penalty+min(.2 if label.neural else 10.,.15*max(0,abs(label.glyphs-len(name))-2))

    def read(self,frame,names,preferred=None,cancelled=lambda:False,budget_ms=160):
        started=time.monotonic();names=tuple(dict.fromkeys(n for n in names if n))
        if not names:return {}
        self.source_frame=frame
        if self.producer and not entry_readable(frame):
            self.last_diagnostic=dict(method='waiting for readable entry contrast',regions=0,recognized=0,words=[],elapsed_ms=0.)
            return {}
        early_fade=self.producer is not None and time.monotonic()-self.scene_started<.45 and entry_level(frame)<85
        focus=preferred if preferred in names else names[0]
        if focus!=self.visual_focus:
            self.visual_focus=focus;self.visual_attempts=0;self.visual_frame=None
        if (self.visual_attempts<1 or time.monotonic()-getattr(self,"visual_at",0)>.06) and frame is not self.visual_frame and not cancelled():
            self.visual_attempts+=1;self.visual_frame=frame;self.visual_at=time.monotonic()
            hints=[]
            for score,box,dark in selected_proposals(frame,focus,fast=self.producer is not None and self.visual_attempts%2==1):
                x,y,r,b=box
                if b-y>=13:box=(x+1,y+2,min(frame.shape[1],r+1),b-2)
                hints.append(Label(box,dark,2.5,self.patch(frame,box),glyphs=len(focus),source=frame,created=time.monotonic(),direct=True))
            for offset in range(len(hints)):
                if cancelled() or time.monotonic()-started>(.075 if early_fade else .22):break
                group=hints[offset:offset+1]
                reads=self.recognizer([self.crop(frame,label) for label in group])
                for label,reading in zip(group,reads):label.reading=reading;label.used_at=time.monotonic()
                self.labels=group+self.labels
                hits=self.lookup(frame,names,preferred,confirm=True,cancelled=cancelled)
                if focus in hits:
                    self.last_diagnostic=dict(method='selected-word English verification',regions=len(hints),recognized=offset+len(group),
                        words=[dict(text=label.reading[0],confidence=round(label.reading[1],3),box=label.box) for label in hints if label.reading],
                        elapsed_ms=round((time.monotonic()-started)*1000,1))
                    return hits
        if early_fade:
            # Try during the first light frames, but do not let an unreadable
            # early view occupy the useful arrival window with recovery work.
            self.hit_sources={}
            self.last_diagnostic=dict(method='early fade quick attempt',regions=len(self.labels),recognized=0,words=[],
                elapsed_ms=round((time.monotonic()-started)*1000,1))
            return {}
        self.targets=names
        self.update(frame)
        self.propose_words(frame,names,list(self.labels),cancelled)
        pending=sorted((label for label in self.labels if label.reading is None),key=lambda label:(not label.neural if self.recovered else False,self.rank(label,focus)))
        for offset in range(0,len(pending),2):
            if cancelled() or (time.monotonic()-started)*1000>=budget_ms:break
            group=pending[offset:offset+2]
            reads=self.recognizer([self.crop(frame,label) for label in group])
            for label,reading in zip(group,reads):label.reading=reading;label.used_at=time.monotonic()
            self.propose_words(frame,names,group,cancelled)
            if self.lookup(frame,names,preferred,confirm=True,cancelled=cancelled):break
        hits=self.lookup(frame,names,preferred,confirm=True,cancelled=cancelled)
        if not hits and not self.recovered and (self.producer is None and not any(label.reading is None for label in self.labels) or time.monotonic()-self.scene_started>=.8) and not cancelled():
            self.recover_regions(frame,deep=self.producer is None)
            if not cancelled():
                fresh=sorted((label for label in self.labels if label.reading is None),key=lambda label:(not label.neural,self.rank(label,focus)))[:4]
                if fresh:
                    reads=self.recognizer([self.crop(frame,label) for label in fresh])
                    for label,reading in zip(fresh,reads):label.reading=reading;label.used_at=time.monotonic()
                    self.propose_words(frame,names,fresh,cancelled)
                    hits=self.lookup(frame,names,preferred,confirm=True,cancelled=cancelled)
        self.last_diagnostic=dict(method='selected-IGN proposals + shared English text index',regions=len(self.labels),
            recognized=sum(label.reading is not None for label in self.labels),
            words=[dict(text=label.reading[0],confidence=round(label.reading[1],3),box=label.box) for label in self.labels if label.reading],
            elapsed_ms=round((time.monotonic()-started)*1000,1))
        return hits

    def propose_words(self,frame,names,labels,cancelled):
        """Separate overlapping OCR lines; a proposal still needs full rereads.

        Only a suffix following an observed word boundary is eligible. Never
        crop a requested prefix out of a longer, clearly read IGN.
        """
        proposals=[]
        for label in labels:
            key=tuple(norm(name) for name in names)
            if label.proposed==key or not label.reading or label.segmented or label.ignored:continue
            label.proposed=key
            text,score,chars=label.reading
            letters=[(c,p) for c,_,p in chars if c.isalnum()]
            source=''.join(c for c,_ in letters).casefold()
            # A single MapleStory IGN is at most 12 letters. Longer readings
            # can contain a pet or an overlapping neighboring name.
            repeated_candidate=any(re.search(r'([a-z0-9])\1{2,}$',norm(name)) and len(re.sub(r'([a-z0-9])\1{2,}$','',norm(name)))>=3 and re.sub(r'([a-z0-9])\1{2,}$','',norm(name)) in source for name in names)
            if len(source)<=12 and not any(character.isspace() for character,_,_ in chars) and not repeated_candidate:continue
            for name in names:
                target=norm(name)
                if len(target)<5:continue
                run=re.search(r'([a-z0-9])\1{2,}$',target)
                prefix=target[:run.start()] if run else ''
                repeated=bool(prefix and len(prefix)>=3 and prefix in source)
                if repeated:
                    start=source.index(prefix)
                elif len(source)>len(target) and self.plausible(source[-len(target):],target):
                    start=len(letters)-len(target)
                else:continue
                position=letters[start][1]
                x,y,r,b=label.box
                left=max(x,round(x+position*(r-x))-4)
                if repeated:
                    actual=label.source if label.source is not None else frame
                    # Select the visible text band; its right edge follows ink,
                    # never the requested number of repeated characters.
                    end=min(actual.shape[1],r+24)
                    sample=actual[y:b,max(0,left):r]
                    white=((sample.min(axis=2)>150)&(sample.max(axis=2)-sample.min(axis=2)<55)).astype(np.uint8)
                    rows=white.sum(axis=1)
                    rows[rows>sample.shape[1]*.65]=0
                    height=min(9,len(rows))
                    top=int(np.convolve(rows,np.ones(height,dtype=int),'valid').argmax()) if len(rows)>=height else 0
                    y=max(0,y+top-5);b=min(actual.shape[0],y+height+8)
                    ink=(actual[y:b,max(0,r-4):end].min(axis=2)>150).any(axis=0)
                    blank=0
                    for offset,present in enumerate(ink):
                        blank=0 if present else blank+1
                        if blank>=3:r=min(end,max(r,r-4+offset+1));break
                    else:r=end
                box=(left,y,r,b)
                if r-left<15 or any(all(abs(a-z)<3 for a,z in zip(box,item.box)) for item in self.labels):continue
                proposals.append(Label(box,label.dark,1.,self.patch(label.source if label.source is not None else frame,box),neural=True,segmented=True,source=label.source,created=time.monotonic(),repeat=repeated))
        if proposals and not cancelled():
            reads=self.recognizer([self.crop(frame,label) for label in proposals])
            for label,reading in zip(proposals,reads):
                label.reading=reading;label.used_at=time.monotonic()
            self.labels.extend(proposals)

    @staticmethod
    def terminal_stem(frame,label):
        if label.source is not None:frame=label.source
        x,y,r,b=label.box
        sample=frame[y:b,max(x,r-max(9,round((r-x)*.18))):r]
        if not sample.size:return False
        gray=cv2.cvtColor(sample,cv2.COLOR_BGR2GRAY)
        if label.dark or float(np.median(gray))>105:
            mask=(gray<float(np.median(gray))-30).astype(np.uint8)
        else:mask=((sample.min(axis=2)>150)&(sample.max(axis=2)-sample.min(axis=2)<70)).astype(np.uint8)
        _,_,stats,_=cv2.connectedComponentsWithStats(mask)
        letters=[q for q in stats[1:] if 6<=q[3]<=12 and q[4]>=5]
        if not letters:return False
        last=max(letters,key=lambda q:q[0]+q[2])
        return last[2]<=2 and last[4]>=last[3]*.55

    @staticmethod
    def compatible(word,name,reading,label=None,frame=None):
        source,target=glyph_key(word),glyph_key(name)
        if source==target:return True
        if label is not None and frame is not None and len(target)>=7 and len(source)==len(target) and source[:-1]==target[:-1] and {source[-1],target[-1]}<={'i','t','1'} and RoomTextReader.terminal_stem(frame,label):return True
        if len(target)>=8 and len(source)==len(target)-1 and target[1:]==source and reading[1]>=.90:return True
        if min(len(source),len(target))<5 or source.startswith(target) or target.startswith(source):return False
        edits=[op for op in SequenceMatcher(None,source,target,autojunk=False).get_opcodes() if op[0]!='equal']
        if len(edits)!=1:return False
        kind,a,b,c,d=edits[0]
        if kind=='replace' and (b==len(source) or a==0 and max(len(source),len(target))<=7):return False
        if kind=='insert' and 0<a<len(source) and d-c<=2 and len(source)>=7 and len(source)/len(target)>=.8 and ' ' in reading[0].strip():return True
        if max(b-a,d-c)>1:return False
        # A clearly read different IGN is not a fuzzy match. A soft character or
        # internal OCR gap can be CHECK, provided an independent crop agrees.
        return any(confidence<.85 for character,confidence,_ in reading[2] if character.isalnum()) or ' ' in reading[0].strip()

    @staticmethod
    def plausible(word,name):
        source,target=norm(word),norm(name)
        if min(len(source),len(target))<3:return source==target
        if abs(len(source)-len(target))>2:return False
        edits=[op for op in SequenceMatcher(None,source,target,autojunk=False).get_opcodes() if op[0]!='equal']
        return sum(max(b-a,d-c) for _,a,b,c,d in edits)<=2

    @staticmethod
    def repeat_ink_count(frame,label):
        """Count periodic strokes in a connected repeated-letter tail.

        The observed ink determines the count; the requested IGN never sets
        the strip width or the number of character cells.
        """
        if label.source is not None:frame=label.source
        x,y,r,b=label.box;sample=frame[y:b,max(0,x-1):min(frame.shape[1],r+1)]
        if not sample.size:return None
        mask=((sample.min(axis=2)>150)&(sample.max(axis=2)-sample.min(axis=2)<55)).astype(np.uint8)
        _,_,stats,_=cv2.connectedComponentsWithStats(mask)
        candidates=[q for q in stats[1:] if 5<=q[3]<=14 and q[2]>=q[3]*1.7]
        if not candidates:return None
        q=max(candidates,key=lambda q:q[0]+q[2]);left,top,width,height=map(int,q[:4]);counts=[]
        for row in mask[top+round(height*.35):top+round(height*.75),left:left+width]:
            starts=np.flatnonzero((row>0)&(np.r_[0,row[:-1]]==0))
            if len(starts)<3 or len(starts)>12:continue
            gaps=np.diff(starts)
            if len(gaps) and 2<=float(np.median(gaps))<=10 and float(gaps.std())<1.6:counts.append(len(starts))
        if not counts:return None
        count=max(set(counts),key=counts.count)
        return count if counts.count(count)>=2 else None

    @staticmethod
    def tail_candidate(word,name):
        source,target=glyph_key(word),glyph_key(name)
        return len(target)>=9 and 6<=len(source)<=len(target)-3 and len(source)>=len(target)*.5 and target.endswith(source)

    def occluded_tail(self,label,word,name):
        """Require a strong suffix AND a separate visible prefix fragment.

        Covered characters remain unverified. This can only produce CHECK.
        """
        if not self.tail_candidate(word,name):return None
        suffix=glyph_key(word);prefix=glyph_key(name)[:-len(suffix)]
        x,y,r,b=label.box
        for other in self.labels:
            if other is label or not other.reading or other.source is not label.source:continue
            l,t,q,d=other.box
            if not 0<=x-q<=45 or abs((t+d)-(y+b))>10:continue
            for fragment,score,_ in self.tokens(other.reading,other.box):
                key=glyph_key(fragment).replace('7','z')
                if score>=.60 and 2<=len(key)<=len(prefix) and key in prefix:
                    return (l,min(t,y),r,max(d,b)),fragment
        return None

    @staticmethod
    def three_letter_match(reading,name,names,box,frame_width,pad=8):
        """User-selected fast mode: three observed, distinctive letters suffice.

        Shared fragments cannot identify one of two simultaneously live sellers.
        Repeated identical letters never count as distinctive evidence.
        """
        target=norm(name)
        allowed={target[i:i+3] for i in range(len(target)-2)
                 if len(set(target[i:i+3]))>=2}
        allowed={part for part in allowed if not any(other!=name and part in norm(other) for other in names)}
        if not allowed:return None
        characters=[(c.casefold() if c.isalnum() else ' ',score if c.isalnum() else 0.,pos) for c,score,pos in reading[2]]
        text=''.join(c for c,_,_ in characters)
        matches=[]
        for index in range(len(characters)-2):
            part=text[index:index+3];evidence=characters[index:index+3]
            confidence=min(item[1] for item in evidence)
            if part in allowed and confidence>=.88:matches.append((confidence,index,part))
        if not matches:return None
        confidence,index,part=max(matches)
        return part,confidence,box

    def lookup(self,frame,names,preferred=None,confirm=False,cancelled=lambda:False):
        hits={};self.hit_sources={};ages={}
        def add(name,hit,label):
            source=label.source if label.source is not None else frame
            if name in hits:
                previous=hits[name]
                if previous is None:return
                a=previous.box;b=hit.box
                separate=(abs((a[0]+a[2])-(b[0]+b[2]))>max(32,a[2]-a[0]) or abs((a[1]+a[3])-(b[1]+b[3]))>max(24,a[3]-a[1]))
                if self.hit_sources[name] is source and separate:
                    hits[name]=None;return
                if label.created<ages[name]:return
            hits[name]=hit;self.hit_sources[name]=source;ages[name]=label.created
        for label in self.labels:
            if not label.reading or label.ignored:continue
            primary=self.tokens(label.reading,label.box)
            relevant=[name for name in names if any(score>=(.60 if len(norm(name))>=8 else .70) and (self.plausible(word,name) or self.tail_candidate(word,name)) for word,score,_ in primary)]
            if label.repeat:
                relevant=list(dict.fromkeys(relevant+[name for name in names if re.sub(r'([a-z0-9])\1{2,}$','',norm(name)) in norm(label.reading[0])]))
            fast=set()
            for name in relevant:
                clean=[(word,score,box) for word,score,box in primary if norm(word)==norm(name) and not any(c.isspace() for c in word.strip()) and score>=.97]
                if clean and not label.repeat and not re.search(r'([a-z0-9])\1{2,}$',norm(name)) and self.confident_word(label.reading,clean[0][0]):
                    word,score,box=max(clean,key=lambda row:row[1])
                    label.accepted=True
                    hit=Hit(word,box,score,'CONFUSABLE' if label.direct or label.segmented or len(primary)>1 else 'EXACT')
                    add(name,hit,label);fast.add(name)
            # Three clear letters are the requested identification threshold.
            # This runs before expensive full-name confirmation and also works
            # when a pet, rope or badge obscures the rest of a label.
            for name in names:
                if name in fast or name in hits:continue
                source=label.source if label.source is not None else frame
                match=self.three_letter_match(label.reading,name,names,label.box,source.shape[1],1 if label.segmented else 8)
                if match is not None:
                    part,score,box=match
                    add(name,Hit(part,box,score,'CONFUSABLE'),label);fast.add(name)
            # Publish the selected shop as soon as its evidence is sufficient.
            # Other live sellers remain queued for the next worker iteration.
            if preferred in hits and hits[preferred] is not None:
                return {preferred:hits[preferred]}
            relevant=[name for name in relevant if name not in fast and (name not in hits or label.confirmed is not None)]
            if not relevant:continue
            if label.confirmed is None and confirm and not cancelled():
                prefix=any(norm(name).endswith(norm(word)) and 0<len(norm(name))-len(norm(word))<=2 for name in relevant for word,_,_ in primary)
                variants=(2,3) if prefix else (0,1)
                label.confirmed=self.recognizer([self.crop(frame,label,confirm=True,variant=variants[0])])
                def good(reading,name):
                    threshold=.70 if len(norm(name))>=8 else .75
                    return any(score>=threshold and self.compatible(word,name,reading,label,frame) for word,score,_ in self.tokens(reading,label.box))
                enough=all(good(label.reading,name) and good(label.confirmed[0],name) and not self.tail_candidate(label.reading[0],name) for name in relevant)
                if (not enough or label.repeat) and not cancelled():
                    label.confirmed+=self.recognizer([self.crop(frame,label,confirm=True,variant=variants[1])])
            if label.confirmed is None:continue
            for name in relevant:
                tails=[(word,score) for reading in [label.reading]+label.confirmed for word,score,_ in self.tokens(reading,label.box) if score>=.90 and self.tail_candidate(word,name)]
                if len(tails)>=2:
                    tail=max(tails,key=lambda row:row[1])[0];candidate=self.occluded_tail(label,tail,name)
                    if candidate is not None:
                        box,fragment=candidate;label.accepted=True
                        add(name,Hit(fragment+' '+tail,box,min(score for _,score in tails),'CONFUSABLE'),label)
                    continue
                run=re.search(r'([a-z0-9])\1{2,}$',norm(name))
                if run and not label.repeat:continue
                if run and label.repeat:
                    count=self.repeat_ink_count(frame,label)
                    if count is not None:
                        expected=len(norm(name))-run.start();stem=norm(name)[:run.start()];character=run.group(1)
                        evidence=[reading for reading in [label.reading]+label.confirmed if reading[1]>=.85 and norm(reading[0]).startswith(stem) and set(norm(reading[0])[len(stem):])=={character} and abs(len(norm(reading[0]))-len(stem)-count)<=2]
                        if count==expected and len(evidence)>=2:
                            label.accepted=True
                            add(name,Hit(evidence[0][0],label.box,min(z[1] for z in evidence),'CONFUSABLE'),label)
                        continue
                evidence=[];exact=[];box=label.box;shown=''
                for reading in [label.reading]+label.confirmed:
                    words=self.tokens(reading,label.box)
                    good=[(word,score,rect) for word,score,rect in words if score>=(.70 if len(norm(name))>=8 else .75) and self.compatible(word,name,reading,label,frame)]
                    if not good:continue
                    word,score,rect=max(good,key=lambda row:row[1]);evidence.append(score);box=rect;shown=word
                    if norm(word)==norm(name) and not any(c.isspace() for c in word.strip()):exact.append(score)
                if len(evidence)<2:continue
                # A shorter/different first word can only recover from two full
                # subsequent reads; resemblance alone never proves a prefix.
                first=any(self.compatible(word,name,label.reading,label,frame) for word,score,_ in primary if score>=.75)
                if any(other!=name and any(norm(word)==norm(other) and score>=.90 for word,score,_ in primary) for other in names):continue
                mode='EXACT' if len(exact)>=2 and min(exact)>=.90 and first and not label.segmented and not label.direct and len(primary)==1 else 'CONFUSABLE'
                label.accepted=True
                hit=Hit(shown,box,min(evidence),mode)
                add(name,hit,label)
        return {name:hit for name,hit in hits.items() if hit is not None}


class SceneRegions(threading.Thread):
    """Cheap region detection continues while the single OCR call is busy.

    A latest-frame queue prevents stale views delaying entry recognition.
    No image processing is performed between entry bursts.
    """
    def __init__(self,frames,stop):
        super().__init__(daemon=True)
        self.frames=frames;self.stop=stop;self.active=False
        self.output=queue.Queue(maxsize=2);self.generation=0;self.shutdown=threading.Event()

    def reset(self):
        self.generation+=1
        while True:
            try:self.output.get_nowait()
            except queue.Empty:break

    def run(self):
        version=-1
        while not self.stop.is_set() and not self.shutdown.is_set():
            if not self.active:
                self.stop.wait(.012);continue
            frame=self.frames.latest(version)
            if frame is None:
                self.stop.wait(.008);continue
            version,stamp,image=frame;generation=self.generation
            if not entry_readable(image):continue
            regions=text_regions(image)
            if generation!=self.generation or not self.active:continue
            try:self.output.put_nowait((generation,image,regions))
            except queue.Full:
                try:self.output.get_nowait()
                except queue.Empty:pass
                try:self.output.put_nowait((generation,image,regions))
                except queue.Full:pass
            # Continue immediately when another captured frame is available.
            # The no-frame path above supplies the idle wait.


def letter_regions(frame,keep_nested=False):
 h,w=frame.shape[:2];bottom=round(h*.91) if h>300 else h
 a=frame[:bottom];g=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)
 b,green,r=cv2.split(a);spread=cv2.subtract(cv2.max(b,cv2.max(green,r)),cv2.min(b,cv2.min(green,r)))
 c=cv2.morphologyEx(g,cv2.MORPH_TOPHAT,np.ones((3,3),np.uint8))
 mask=((c>22)&(g>95)&(spread<85)).astype('uint8')*255
 _,_,stats,_=cv2.connectedComponentsWithStats(mask)
 glyphs=[tuple(map(int,z)) for z in stats[1:] if 1<=z[2]<=16 and 3<=z[3]<=14 and 4<=z[4]<=110]
 result=[]
 for shift in [0,2,4,6]:
  bins={}
  for x,y,q,d,area in glyphs:bins.setdefault((y+d+shift)//8,[]).append((x,y,x+q,y+d,area))
  for values in bins.values():
   values.sort();groups=[];group=[];right=-100
   for z in values:
    if z[0]-right>14:
     if group:groups.append(group)
     group=[]
    group.append(z);right=max(z[2],right) if len(group)>1 else z[2]
   if group:groups.append(group)
   for group in groups:
    if len(group)<3:continue
    l=min(z[0] for z in group);t=min(z[1] for z in group);r=max(z[2] for z in group);b=max(z[3] for z in group)
    if not(15<=r-l<=220 and 6<=b-t<=19 and (r-l)/(b-t)>1.4):continue
    box=(max(0,l-3),max(0,t-2),min(w,r+3),min(bottom,b+2))
    if any(sum(abs(a-z) for a,z in zip(box,x[0]))<8 for x in result):continue
    result.append((box,False,1.,len(group)))
 if keep_nested:return result
 return [entry for entry in result if not any(other is not entry and
  other[0][0]<=entry[0][0]+3 and other[0][2]>=entry[0][2]-3 and
  abs((other[0][1]+other[0][3])-(entry[0][1]+entry[0][3]))<=8 and
  other[0][2]-other[0][0]>(entry[0][2]-entry[0][0])*1.15 for other in result)]
