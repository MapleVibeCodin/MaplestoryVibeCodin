"""Target-specific visual search with tiny-strip verification, no text detector.

The target is rendered once per name/viewport. OpenCV searches the letter shapes;
only the best patches are sent to a prewarmed single-line recognizer. No whole
screen OCR, orientation classifier, cloud calls, Tesseract or Windows OCR.
"""
from pathlib import Path
from functools import lru_cache
from difflib import SequenceMatcher
import time
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fast_shop_match import Hit, norm


def confusable(s):
    return norm(s).replace('rn','m').replace('l','i')


@lru_cache(maxsize=128)
def templates(target,width,expand_case=False,primary=False):
    font=ImageFont.truetype(str(Path(__file__).with_name('assets')/'name_font.ttf'),12)
    names=[target]
    if target[:1] in ('I','i','l','L'):
        names.extend(char+target[1:] for char in ('I','i','l'))
    if expand_case:
        names.extend([target.lower(),target.upper(),target.title()])
        names.extend(target[:i]+char.swapcase()+target[i+1:] for i,char in enumerate(target) if char.isalpha())
    scales=((1.,1.04,1366/1280) if width<1024 else (1.,))+(width/1280,width/1280*1.04,width/1366,width/1366*1.04)
    if primary:scales=(1.,width/1280,width/1366*1.04)
    result=[];seen=set()
    for name in dict.fromkeys(names):
        bounds=font.getbbox(name)
        canvas=Image.new('L',(bounds[2]-bounds[0]+6,bounds[3]-bounds[1]+6),0)
        ImageDraw.Draw(canvas).text((3-bounds[0],3-bounds[1]),name,font=font,fill=255)
        base=np.array(canvas)
        for scale in scales:
            scale=max(.5,min(1.6,scale))
            w=max(8,round(base.shape[1]*scale));h=max(7,round(base.shape[0]*scale))
            key=(name,w,h)
            if key in seen:continue
            seen.add(key)
            result.append(cv2.resize(base,(w,h),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC))
    return tuple(result)


class NameFinder:
    def __init__(self):
        import onnxruntime
        onnxruntime.disable_telemetry_events()
        # Pinned package supplies the model; instantiate ONLY recognition.
        from rapidocr_onnxruntime import main
        from rapidocr_onnxruntime.ch_ppocr_rec import TextRecognizer
        config=main.update_model_path(main.read_yaml(main.DEFAULT_CFG_PATH))['Rec']
        config.update(intra_op_num_threads=1,inter_op_num_threads=1,rec_batch_num=6,rec_img_shape=[3,48,320])
        self.recognizer=TextRecognizer(config)
        self.recognizer([np.full((20,80,3),255,np.uint8)])
        self.last_diagnostic={}

    def room_number(self,bgr,quick=False):
        """One tiny header read at entry; never polls whole-screen OCR."""
        h,w=bgr.shape[:2]
        previous=self.recognizer.rec_image_shape
        def remember(number):
            if h>=62 and w>=160:
                self._room_cache=(number,bgr.shape,cv2.cvtColor(bgr[38:59,110:156],cv2.COLOR_BGR2GRAY).copy())
            return number
        cached=getattr(self,'_room_cache',None)
        if cached is not None and cached[1]==bgr.shape:
            patch=cv2.cvtColor(bgr[38:59,110:156],cv2.COLOR_BGR2GRAY)
            if float(patch.std())>5 and float(cv2.matchTemplate(patch,cached[2],cv2.TM_CCOEFF_NORMED)[0,0])>=.96:
                return cached[0]
        def numeric_header():
            # A calibrated common label establishes where the two-digit field
            # sits. Two independent number reads must agree; a clipped digit
            # cannot become a one-digit room because this path accepts 10–20.
            path=Path(__file__).with_name('assets')/'room_label_prefix.npz'
            if not path.exists():return None
            if not hasattr(self,'_room_prefix'):
                with np.load(path) as data:self._room_prefix=data['prefix'].copy()
            region=cv2.cvtColor(bgr[:min(h,100),:min(w,190)],cv2.COLOR_BGR2GRAY)
            best=(-1,None)
            for scale in (.90,.95,1.,1.05,1.1):
                template=cv2.resize(self._room_prefix,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
                if min(region.shape)<min(template.shape) or region.shape[1]<template.shape[1]:continue
                _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED))
                if score>best[0]:best=(score,(scale,x,y))
            if best[0]<.65:return None
            scale,x,y=best[1];crops=[]
            for top,bottom in ((-4,16),(-2,15)):
                left=round(x+82*scale);right=round(left+16*scale)
                a=max(0,round(y+top*scale));b=min(h,round(y+bottom*scale))
                crop=bgr[a:b,left:min(w,right)]
                if crop.size:
                    crop=self._contrast(crop)
                    crops.append(cv2.resize(crop,None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST))
            reads,_=self.recognizer(crops) if crops else ([],0)
            votes=[];confidence=[]
            for text,certainty in reads:
                match=re.fullmatch(r'(1[0-9]|20)[:>)]?',text.strip())
                if match and certainty>=.80:votes.append(int(match[1]));confidence.append(certainty)
            if len(votes)==2 and votes[0]==votes[1] and max(confidence)>=.95:return votes[0]
            return None
        def compressed_header():
            # Compression can merge the small minimap letters. Require two
            # independent, bounded header strips to agree before recovering a
            # one/two-letter label error. Never truncate an out-of-range number.
            crops=[]
            for top,bottom,left,right,interpolation in [
                    (36,62,45,150,cv2.INTER_CUBIC),
                    (36,62,50,155,cv2.INTER_NEAREST),
                    (35,60,45,155,cv2.INTER_NEAREST)]:
                crop=bgr[top:min(h,bottom),left:min(w,right)]
                if crop.size:crops.append(cv2.resize(crop,None,fx=3,fy=3,interpolation=interpolation))
            reads,_=self.recognizer(crops) if crops else ([],0)
            votes=[]
            for text,confidence in reads:
                found=re.fullmatch(r'([a-z ]+)[<c(\[]?\s*([0-9]{1,2})[>s)\]]?',text.strip(),re.I)
                if not found or confidence<.65:continue
                label=re.sub('[^a-z]','',found[1].lower())
                previous_row=list(range(11))
                for i,char in enumerate(label,1):
                    row=[i]
                    for j,other in enumerate('freemarket',1):
                        row.append(min(row[-1]+1,previous_row[j]+1,previous_row[j-1]+(char!=other)))
                    previous_row=row
                number=int(found[2])
                if previous_row[-1]<=2 and 1<=number<=20:votes.append(number)
            return votes[0] if votes and votes.count(votes[0])>=2 and len(set(votes))==1 else None
        try:
            self.recognizer.rec_image_shape=[3,48,320]
            # Try the common expanded header first; avoid padding several wide
            # blank crops into a costly batch. Fall back to collapsed/title layouts.
            for top,bottom,left,right in [(36,62,0,160),(0,24,0,255),(80,104,25,160),(40,64,25,190)]:
                crop=bgr[top:min(h,bottom),left:min(w,right)]
                if not crop.size:continue
                crop=cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
                reads,_=self.recognizer([crop])
                for text,confidence in reads:
                    found=re.search(r'fre[e]?\s*market\s*[<(\[]?\s*([0-9OIlg]{1,2})(?![0-9OIlg])\s*[>)\]]?',text,re.I)
                    if not found:
                        found=re.search(r'\bmarket\s*[<(\[]\s*([0-9OIlg]{1,2})(?![0-9OIlg])\s*[>)\]]',text,re.I)
                    if found and confidence>=.65:
                        value=found[1].lower().translate(str.maketrans({'o':'0','i':'1','l':'1','g':'9'}))
                        try:number=int(value)
                        except ValueError:continue
                        if 1<=number<=20:return remember(number)
                if (top,bottom,left,right)==(36,62,0,160):
                    recovered=numeric_header()
                    if recovered is None and not quick:recovered=compressed_header()
                    if recovered is not None:return remember(recovered)
                    if quick:return None
            return None
        finally:self.recognizer.rec_image_shape=previous

    def numbered_header_visible(self,bgr):
        """Detect the label and opening angle, without guessing its number.

        This only permits a provisional search for the explicitly selected
        seller. Actual room OCR remains the fallback for the rest of the queue.
        """
        path=Path(__file__).with_name('assets')/'room_label_prefix.npz'
        if not path.exists():return False
        if not hasattr(self,'_room_visual'):
            with np.load(path) as data:
                self._room_visual=[(scale,cv2.resize(data['prefix'],None,fx=scale,fy=scale,
                    interpolation=cv2.INTER_CUBIC),cv2.resize(data['bracket'],None,fx=scale,fy=scale,
                    interpolation=cv2.INTER_CUBIC)) for scale in (.90,.95,1.,1.05,1.1)]
        gray=cv2.cvtColor(bgr[:100,:190],cv2.COLOR_BGR2GRAY);best=(-1,None)
        for scale,prefix,bracket in self._room_visual:
            if gray.shape[0]<prefix.shape[0] or gray.shape[1]<prefix.shape[1]:continue
            _,score,_,(x,y)=cv2.minMaxLoc(cv2.matchTemplate(gray,prefix,cv2.TM_CCOEFF_NORMED))
            if score>best[0]:best=(score,(scale,x,y,bracket))
        if best[0]<.64:return False
        scale,x,y,bracket=best[1]
        patch=gray[max(0,y-1):round(y+15*scale),round(x+74*scale):round(x+84*scale)]
        if patch.shape[0]<bracket.shape[0] or patch.shape[1]<bracket.shape[1]:return False
        return cv2.minMaxLoc(cv2.matchTemplate(patch,bracket,cv2.TM_CCOEFF_NORMED))[1]>=.40

    @staticmethod
    def _contrast(crop):
        # A fade can dim otherwise legible letters. Local contrast is enough;
        # never wait for the entire animated scene to stop changing brightness.
        low,high=np.percentile(crop,(2,98))
        if high-low>8 and high<160:
            return np.clip((crop.astype(np.float32)-low)*(255./(high-low)),0,255).astype(np.uint8)
        return crop

    def entry_room_number(self,bgr,full=False):
        return self.room_number(bgr,quick=not full)

    def prepare(self,target,width=1366):
        templates(target,width)

    def _candidates(self,bgr,target,dark=False,fast=False,min_score=.56,limit=6,peak_limit=24,cache=None,expand_case=False,primary=False):
        h,w=bgr.shape[:2]
        # Search from the top: camera scroll can put nameplates above 12% height.
        top=0;bottom=round(h*.92)
        cache={} if cache is None else cache
        if 'gray' not in cache:
            cache['gray']=cv2.cvtColor(bgr[top:bottom],cv2.COLOR_BGR2GRAY)
        if ('feature',dark) not in cache:
            kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
            cache['feature',dark]=cv2.morphologyEx(cache['gray'],
                cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT,kernel)
        feature=cache['feature',dark]
        if fast and ('small',dark) not in cache:
            cache['small',dark]=cv2.resize(feature,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
        small=cache.get(('small',dark))
        proposals=[]
        for template in templates(target,w,expand_case,primary):
            th,tw=template.shape
            if th>feature.shape[0] or tw>feature.shape[1]:continue
            if fast:
                template_key=(template.shape,template.tobytes())
                peak_key=('peaks',dark,template_key)
                if peak_key not in cache:
                    mini=cv2.resize(template,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
                    scores=cv2.matchTemplate(small,mini,cv2.TM_CCOEFF_NORMED)
                    peaks=(scores>=.32)&(scores==cv2.dilate(scores,np.ones((5,5),np.uint8)))
                    ys,xs=np.where(peaks)
                    order=np.argsort(scores[ys,xs])[-96:][::-1]
                    cache[peak_key]=[(int(xs[j])*2,int(ys[j])*2) for j in order]
                for x,y in cache[peak_key][:peak_limit]:
                    refinement_key=('refined',dark,template_key,x,y)
                    if refinement_key not in cache:
                        l=max(0,x-4);t=max(0,y-4)
                        patch=feature[t:min(feature.shape[0],y+th+5),l:min(w,x+tw+5)]
                        if patch.shape[0]<th or patch.shape[1]<tw:continue
                        full=cv2.matchTemplate(patch,template,cv2.TM_CCOEFF_NORMED)
                        _,score,_,(dx,dy)=cv2.minMaxLoc(full)
                        cache[refinement_key]=(score,(l+dx,t+dy+top,l+dx+tw,t+dy+top+th))
                    score,box=cache[refinement_key]
                    if score>=min_score:proposals.append((score,box))
            else:
                scores=cv2.matchTemplate(feature,template,cv2.TM_CCOEFF_NORMED)
                for _ in range(3):
                    _,score,_,(x,y)=cv2.minMaxLoc(scores)
                    if score<min_score:break
                    proposals.append((score,(x,y+top,x+tw,y+top+th)))
                    scores[max(0,y-th):y+th,max(0,x-tw):x+tw]=-1
        unique=[]
        for score,box in sorted(proposals,reverse=True):
            cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
            if any(abs(cx-(b[0]+b[2])/2)<max(6,(b[2]-b[0])*.6) and abs(cy-(b[1]+b[3])/2)<12 for _,b in unique):continue
            unique.append((score,box))
        return unique[:limit]

    def _verify(self,bgr,target,candidates,dark=False,normalize=False,entry=False):
        if not candidates:return []
        contexts=[];tight_crops=[]
        for _,(x,y,r,b) in candidates:
            pad=max(3,round((b-y)*.3))
            # Context includes adjacent lettering so a prefix cannot prove identity.
            for horizontal,crops in ((pad,contexts),(0,tight_crops)):
                crop=bgr[max(0,y-2):min(bgr.shape[0],b+2),
                         max(0,x-horizontal):min(bgr.shape[1],r+horizontal)]
                if normalize:crop=self._contrast(crop)
                if not dark:crop=255-crop
                crops.append(cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
        words,_=self.recognizer(contexts)
        wanted=norm(target)
        tight_indices=[]
        for i,((score,_),(text,confidence)) in enumerate(zip(candidates,words)):
            expanded=norm(text)
            extra=(len(expanded)==len(wanted)+1 and
                   (expanded.startswith(wanted) or expanded.endswith(wanted)))
            if ((len(wanted)<5 and expanded==wanted and score>=.56 and confidence>=.95) or
                (score<.56 and len(wanted)>=5 and expanded==wanted and confidence>=.85) or
                (len(wanted)>=6 and score>=.60 and extra and confidence>=.80)):
                tight_indices.append(i)
        tight={}
        if tight_indices:
            reads,_=self.recognizer([tight_crops[i] for i in tight_indices])
            tight=dict(zip(tight_indices,reads))
        matches=[]
        for i,((score,box),(text,confidence)) in enumerate(zip(candidates,words)):
            variants=[('context',(text,confidence))]
            if i in tight:variants.append(('tight',tight[i]))
            for variant,(read,certainty) in variants:
                self.last_diagnostic['candidates'].append({'text':read,'variant':variant,
                    'ocr_confidence':float(certainty),'visual_score':round(score,3),'box':box})
            same=norm(text)==wanted
            glyph=confusable(text)==confusable(target)
            near=(len(target)>=6 and 'rm' in wanted and
                  norm(text)==wanted.replace('rm','m') and score>=.70)
            valid=confidence>=.80 and (same or glyph or near)
            mode='EXACT' if same else 'CONFUSABLE'
            tight_text,tight_confidence=tight.get(i,('',0.))
            if len(wanted)<5:
                valid=(valid and same and score>=.56 and confidence>=.95 and
                       norm(tight_text)==wanted and tight_confidence>=.95)
            if not valid and len(wanted)>=6 and score>=.60:
                expanded=norm(text)
                extra=(len(expanded)==len(wanted)+1 and
                       (expanded.startswith(wanted) or expanded.endswith(wanted)))
                if extra and norm(tight_text)==wanted and tight_confidence>=.95 and confidence>=.80:
                    valid=True;text=tight_text;mode='CONFUSABLE'
            if score<.56:
                valid=(same and norm(tight_text)==wanted and
                       confidence>=.85 and tight_confidence>=.85 and len(wanted)>=5)
                mode='EXACT'
            if valid:matches.append(Hit(text.strip(),box,float(score),mode))
        if not matches:matches=self._label_recovery(bgr,target,candidates,words,dark)
        if not matches:
            matches=(self._entry_reads(bgr,target,candidates,words,dark) if entry else
                     self._recover_read(bgr,target,candidates,words,dark))
        return matches

    def _label_recovery(self,bgr,target,candidates,words,dark):
        """Bounded recovery for repeated tails, adjacent tags and occluded gaps.

        Expanded strips must read the complete requested name twice. A visible
        internal gap can produce CHECK only; its covered letter is not inferred.
        """
        wanted=norm(target);run=re.search(r'([a-z0-9])\1{2,}$',wanted)
        hits=[]
        for (score,box),(text,confidence) in zip(candidates[:2],words[:2]):
            if score<.56 or confidence<.70:continue
            x,y,r,b=box;read=norm(text);crops=[];repeat=False;gap=False
            if run and run.start()>=3 and wanted[:run.start()][1:] in read:
                repeat=True
                shift=max(1,round((r-x)/len(wanted)/2))
                # Follow the visible run to its end. A fixed target-width crop
                # would otherwise verify a shorter prefix of a longer Z run.
                top=max(0,y+2);bottom=min(bgr.shape[0],b-2)
                end=min(bgr.shape[1],r+60);start=max(x,r-3)
                line=bgr[top:bottom,start:end]
                if not line.size:continue
                ink=((line.min(axis=2)>150)&(np.ptp(line,axis=2)<55)).any(axis=0)
                blank=0;right=end
                for offset,present in enumerate(ink):
                    blank=0 if present else blank+1
                    if blank>=2:
                        right=min(bgr.shape[1],start+offset+4);break
                for inset in (0,2):
                    sample=bgr[max(0,y-2)+inset:min(bgr.shape[0],b+1),x+shift:right]
                    if not sample.size:continue
                    sample=sample if dark else 255-sample
                    sample=cv2.resize(sample,None,fx=6,fy=3,interpolation=cv2.INTER_CUBIC)
                    crops.append(cv2.copyMakeBorder(sample,8,8,12,12,cv2.BORDER_CONSTANT,value=(255,255,255)))
            elif len(wanted)>=6 and len(read)==len(wanted)+1 and read[0] in 'il1' and read[1:]==wanted:
                for inset in (2,3):
                    sample=bgr[max(0,y-1):min(bgr.shape[0],b+1),x+inset:r]
                    if sample.size:crops.append(cv2.resize(sample if dark else 255-sample,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
            elif len(wanted)>=8 and score>=.60 and confidence>=.90:
                parts=text.strip().split()
                if len(parts)==2:
                    left,right=map(norm,parts)
                    gap=(len(left)>=2 and len(right)>=3 and len(left)+len(right)==len(wanted)-1 and
                         wanted.startswith(left) and wanted.endswith(right))
                if gap and b-y>=15:
                    for pad,threshold in ((0,180),(2,210)):
                        sample=bgr[y+3:b-3,max(0,x-pad):min(bgr.shape[1],r+pad)]
                        gray=cv2.cvtColor(sample,cv2.COLOR_BGR2GRAY)
                        mask=cv2.threshold(gray,110 if dark else threshold,255,cv2.THRESH_BINARY)[1]
                        if not dark:mask=255-mask
                        crops.append(cv2.cvtColor(cv2.resize(mask,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC),cv2.COLOR_GRAY2BGR))
            if len(crops)!=2:continue
            previous=self.recognizer.rec_image_shape
            try:
                self.recognizer.rec_image_shape=[3,48,320]
                reads,_=self.recognizer(crops)
            finally:self.recognizer.rec_image_shape=previous
            for value,certainty in reads:
                self.last_diagnostic['candidates'].append(dict(text=value,variant='label-recovery',
                    ocr_confidence=float(certainty),visual_score=round(score,3),box=box))
            if gap:
                verified=sum(value.strip().split()==text.strip().split() and certainty>=.90 for value,certainty in reads)==2
            else:
                verified=sum(norm(value)==wanted and certainty>=.90 for value,certainty in reads)==2
            if verified:hits.append(Hit(target if not gap else text.strip(),box,float(score),'CHECK'))
        return hits

    def _entry_reads(self,bgr,target,candidates,words,dark):
        """Only two extra raw strips per plausible name; no threshold sweep."""
        wanted=norm(target);hits=[]
        if len(wanted)<6:return hits
        for (score,box),(text,confidence) in zip(candidates,words):
            read=norm(text)
            if score<.60 or confidence<.65 or abs(len(read)-len(wanted))>2:continue
            # Cheap overlap gates extra OCR, not acceptance of a similar name.
            if SequenceMatcher(None,read,wanted).ratio()<.70:continue
            x,y,r,b=box;crops=[]
            if np.percentile(bgr[y:b,x:r],98)<140:
                self.last_diagnostic['wait_for_contrast']=box
                self.last_diagnostic['candidate_hint']=(score,box,text,confidence,dark)
                continue
            for pad in (0,3):
                sample=bgr[y:b,max(0,x-pad):min(bgr.shape[1],r+pad)]
                gray=cv2.cvtColor(sample,cv2.COLOR_BGR2GRAY)
                crops.append(cv2.resize(cv2.cvtColor(gray if dark else 255-gray,cv2.COLOR_GRAY2BGR),
                    None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
            previous=self.recognizer.rec_image_shape
            try:
                self.recognizer.rec_image_shape=[3,48,320]
                reads,_=self.recognizer(crops)
            finally:self.recognizer.rec_image_shape=previous
            exact=[certainty for value,certainty in reads if norm(value)==wanted and certainty>=.75]
            if len(exact)==2 and max(exact)>=.82:
                hits.append(Hit(target,box,float(score),'CHECK'));continue
            # One missing internal narrow glyph is visibly uncertain.
            narrow={wanted[:i]+wanted[i+1:] for i in range(1,len(wanted)-1) if wanted[i] in 'il'}
            if len(wanted)>=8 and score>=.64 and read in narrow and confidence>=.88:
                if sum(norm(value)==read and certainty>=.88 for value,certainty in reads)==2:
                    hits.append(Hit(text.strip(),box,float(score),'CHECK'))
        return hits

    def _recover_read(self,bgr,target,candidates,words,dark):
        """Retry a few name strips, preserving CHECK for unresolved glyphs.

        Edit distance gates extra recognition work only. Acceptance requires
        repeated whole-name reads or one of the explicit ambiguity classes;
        a nearby spelling is never accepted solely by edit distance.
        """
        wanted=norm(target)
        if getattr(self.recognizer,'rec_image_shape',[3,48,0])[2]<320:return []
        cache=getattr(self,'_recovery_cache',{})
        def distance(a,b):
            row=list(range(len(b)+1))
            for i,char in enumerate(a,1):
                nxt=[i]
                for j,other in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(char!=other)))
                row=nxt
            return row[-1]
        matches=[]
        for (score,box),(text,confidence) in zip(candidates,words):
            key=(box,dark,round(score,2))
            if key in cache:
                if cache[key] is not None:matches.append(cache[key])
                continue
            x,y,r,b=box;read=norm(text);patch=bgr[y:b,x:r]
            selected=False
            if dark and patch.size:
                colors=patch.astype(np.int16);level=float(np.median(colors))
                blue=np.mean((colors[:,:,0]>colors[:,:,2]+20)&(colors[:,:,1]>colors[:,:,2]+10))
                selected=100<level<220 and blue>.08 and np.mean(np.ptp(colors,axis=2)<35)>.35
            minimum=.56 if len(wanted)<5 and selected else .70 if len(wanted)<5 else .60
            if confidence<.80 or score<minimum:continue
            bound=3 if len(wanted)>=6 and score>=.64 else 2
            if abs(len(read)-len(wanted))>1 or distance(wanted,read)>bound:continue
            if len(read)>len(wanted) and not (read[0] in 'il1' and read[1:]==wanted):continue
            contexts=[norm(c['text']) for c in self.last_diagnostic['candidates']
                      if c['variant']=='context' and c['ocr_confidence']>=.90 and
                      abs((c['box'][0]+c['box'][2])-(x+r))<6 and abs(c['box'][1]-y)<3]
            partial=(len(wanted)>=6 and score>=.74 and wanted[0] in 'fijl' and contexts.count(wanted[1:])>=2)
            joined=(score>=.74 and wanted.startswith(('iv','lv')) and any(contexts.count(v)>=2 for v in
                    ('w'+wanted[2:],'iw'+wanted[2:],'lw'+wanted[2:])))
            stray=(len(wanted)>=6 and score>=.64 and any(contexts.count(c+wanted)>=2 for c in 'il1'))
            if partial or joined or stray:
                hit=Hit(text.strip(),box,float(score),'CHECK');cache[key]=hit;matches.append(hit);continue
            missing_narrow=(len(wanted)>=8 and score>=.64 and confidence>=.88 and
                            len(read)==len(wanted)-1 and any(wanted[:i]+wanted[i+1:]==read
                            for i in range(1,len(wanted)-1) if wanted[i] in 'il'))
            if missing_narrow:
                strips=[bgr[y:b,x:r],bgr[max(0,y-2):min(bgr.shape[0],b+2),x:r]]
                strips=[cv2.resize(255-v if not dark else v,None,fx=3,fy=3,
                                  interpolation=cv2.INTER_CUBIC) for v in strips if v.size]
                confirmations,_=self.recognizer(strips)
                if sum(norm(value)==read and certainty>=.88 for value,certainty in confirmations)>=2:
                    hit=Hit(text.strip(),box,float(score),'CHECK');cache[key]=hit;matches.append(hit);continue
            crops=[]
            for vp in (1,2,3):
                if b-y-2*vp<9:continue
                for hp,threshold in [(0,180),(2,210)]:
                    sample=bgr[y+vp:b-vp,max(0,x-hp):min(bgr.shape[1],r+hp)]
                    gray=cv2.cvtColor(sample,cv2.COLOR_BGR2GRAY)
                    mask=cv2.threshold(gray,threshold if not dark else 110,255,cv2.THRESH_BINARY)[1]
                    if not dark:mask=255-mask
                    mask=cv2.resize(mask,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
                    crops.append(cv2.cvtColor(mask,cv2.COLOR_GRAY2BGR))
            if len(read)>len(wanted) and read[0] in 'il1':
                for inset in (2,3):
                    sample=bgr[y+2:b-2,x+inset:r]
                    if sample.size:crops.append(cv2.resize(255-sample if not dark else sample,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
            if not crops:continue
            reads,_=self.recognizer(crops)
            for value,certainty in reads:
                self.last_diagnostic['candidates'].append({'text':value,'variant':'clean-strip',
                    'ocr_confidence':float(certainty),'visual_score':round(score,3),'box':box})
            confident=[norm(value) for value,certainty in reads if certainty>=(.95 if len(wanted)<5 else .90)]
            hit=None
            if confident.count(wanted)>=2:
                hit=Hit(target,box,float(score),'CONFUSABLE')
            elif len(wanted)>=5 and score>=.66 and sum(confusable(value)==confusable(wanted) for value in confident)>=2:
                hit=Hit(target,box,float(score),'CONFUSABLE')
            if hit is None and selected and 4<=len(wanted)<=8 and wanted.startswith(('vl','vi')):
                merged='m'+wanted[2:];partial_word='v'+wanted[2:]
                seen=[norm(c['text']) for c in self.last_diagnostic['candidates'] if c['variant']=='context'
                      and c['ocr_confidence']>=.84 and abs(c['box'][0]-x)<3 and abs(c['box'][1]-y)<3]
                clean=[norm(value) for value,certainty in reads if certainty>=.80]
                if seen.count(merged)>=2 and clean.count(partial_word)>=2:
                    hit=Hit(text.strip(),box,float(score),'CHECK')
            if hit is None and len(wanted)>=6 and score>=.66:
                for value in set(confident):
                    if confident.count(value)<2 or len(value)!=len(wanted):continue
                    differences=[{a,z} for a,z in zip(wanted,value) if a!=z]
                    if len(differences)==1 and differences[0] in ({'0','u'},{'0','o'}):
                        hit=Hit(value,box,float(score),'CHECK');break
            # A missing narrow first glyph or a merged leading l/I+v remains
            # a CHECK candidate, never an exact identity claim.
            context_reads=[norm(c['text']) for c in self.last_diagnostic['candidates']
                           if c['box']==box and c['variant']=='context' and c['ocr_confidence']>=.90]
            if hit is None and score>=.74:
                narrow=(len(wanted)>=6 and wanted[0] in 'fijl' and context_reads.count(wanted[1:])>=2)
                joined=(wanted.startswith(('iv','lv')) and context_reads.count('w'+wanted[2:])>=2)
                if narrow or joined:hit=Hit(text.strip(),box,float(score),'CHECK')
            if hit is None and len(wanted)>=6 and score>=.64:
                observed=[norm(c['text']) for c in self.last_diagnostic['candidates']
                          if c['variant']=='context' and c['ocr_confidence']>=.84 and
                          abs((c['box'][0]+c['box'][2])-(x+r))<12 and abs(c['box'][1]-y)<4]
                canonical=confusable(wanted)
                for value in set(observed):
                    other=confusable(value)
                    if observed.count(value)<2 or len(other)!=len(canonical):continue
                    differences=[{a,z} for a,z in zip(canonical,other) if a!=z]
                    if 1<=len(differences)<=2 and all(pair=={'o','n'} for pair in differences):
                        hit=Hit(value,box,float(score),'CHECK');break
            cache[key]=hit
            if hit is not None:matches.append(hit)
        return matches

    def scan(self,bgr,target,cancelled=None,fast_only=False,quick_only=False,entry_only=False,candidate_hint=None):
        started=time.perf_counter()
        self._recovery_cache={}
        self.last_diagnostic={'method':'coarse proposals + full-resolution verification','target':target,'candidates':[]}
        if not target or not (3<=len(target)<=24):return None
        if cancelled is not None and cancelled():
            self.last_diagnostic['cancelled']=True;return None
        if entry_only:
            if candidate_hint is not None:
                score,box,text,confidence,dark=candidate_hint
                found=self._entry_reads(bgr,target,[(score,box)],[(text,confidence)],dark)
                if len(found)==1:
                    self.last_diagnostic.update(method='fresh-frame candidate verification',
                        elapsed_ms=round((time.perf_counter()-started)*1000,1))
                    return found[0]
            # Two polarities cover ordinary white labels and selected gray
            # labels. Avoid the multi-pass recovery search during the race.
            cache={};matches=[]
            for dark in ((True,False) if len(target)<5 else (False,True)):
                if cancelled is not None and cancelled():return None
                candidates=self._candidates(bgr,target,dark=dark,fast=True,
                    min_score=.56,limit=3,peak_limit=96 if len(target)<5 else 24,cache=cache,primary=True)
                if not candidates:
                    candidates=self._candidates(bgr,target,dark=dark,fast=True,
                        min_score=.52,limit=2,peak_limit=24,cache=cache,primary=True)
                if cancelled is not None and cancelled():return None
                self.recognizer.rec_image_shape=[3,48,160]
                found=self._verify(bgr,target,candidates,dark=dark,normalize=True,entry=True)
                matches.extend(found)
                if matches:break
                # A likely label during fade-in gets a fresh frame next, rather
                # than another polarity sweep of the same dim pixels.
                if any(c['variant']=='context' and c['visual_score']>=.64 and
                       c['ocr_confidence']>=.75 and len(norm(target))>=6 and
                       SequenceMatcher(None,norm(c['text']),norm(target)).ratio()>=.75
                       for c in self.last_diagnostic['candidates']):break
            self.last_diagnostic.update(method='bounded room-entry sweep',
                elapsed_ms=round((time.perf_counter()-started)*1000,1))
            return matches[0] if len(matches)==1 else None
        if quick_only:
            # A cheap sweep across the queue must not spend recovery OCR on
            # absent sellers before reaching a clearly visible one.
            candidates=self._candidates(bgr,target,dark=False,fast=True,
                min_score=.60,limit=2,peak_limit=24)
            if cancelled is not None and cancelled():return None
            self.recognizer.rec_image_shape=[3,48,160]
            matches=self._verify(bgr,target,candidates,dark=False)
            if not matches and candidates and not (cancelled is not None and cancelled()):
                self.recognizer.rec_image_shape=[3,48,320]
                matches=self._verify(bgr,target,candidates,dark=False)
            self.last_diagnostic.update(method='strong-candidate queue sweep',
                elapsed_ms=round((time.perf_counter()-started)*1000,1))
            return matches[0] if len(matches)==1 else None
        matches=[]
        coarse={};search_cache={};verified=set()
        # Coarse proposals are ALWAYS refined and recognized at original resolution.
        # If no candidate verifies, retain the full-resolution recovery search.
        def verify(candidates,dark,width):
            fresh=[c for c in candidates if (dark,width,c[0],c[1]) not in verified]
            verified.update((dark,width,c[0],c[1]) for c in fresh)
            self.recognizer.rec_image_shape=[3,48,width]
            return self._verify(bgr,target,fresh,dark=dark)

        # Half-size tiny lettering aliases heavily; retain the wide first pass.
        initial_peaks=96 if min(t.shape[0] for t in templates(target,bgr.shape[1]))<12 else 24
        passes=[(True,.56,initial_peaks)]
        if len(norm(target))>=5:passes.append((True,.48,initial_peaks))
        if initial_peaks<96:
            passes.append((True,.56,96))
            if len(norm(target))>=5:passes.append((True,.48,96))
        if not fast_only:passes.append((False,.56,96))
        for fast,min_score,peak_limit in passes:
            for dark in (False,True):
                if cancelled is not None and cancelled():
                    self.last_diagnostic['cancelled']=True
                    return None
                if fast:
                    key=(dark,peak_limit)
                    if key not in coarse:
                        coarse[key]=self._candidates(bgr,target,dark=dark,fast=True,
                            min_score=.48,limit=12,peak_limit=peak_limit,cache=search_cache)
                    candidates=[c for c in coarse[key]
                                if (c[0]>=.56 if min_score==.56 else c[0]<.56)][:6]
                else:
                    candidates=self._candidates(bgr,target,dark=dark,cache=search_cache)
                self.last_diagnostic['proposal_threshold']=min_score
                self.last_diagnostic['peak_limit']=peak_limit
                matches=verify(candidates,dark,160 if fast else 320)
                if fast and min_score==.56 and not matches and candidates:
                    matches=verify(candidates,dark,320)
                if matches:break
            if matches:break
        if not matches and not fast_only:
            for dark in (False,True):
                if cancelled is not None and cancelled():return None
                candidates=self._candidates(bgr,target,dark=dark,fast=True,min_score=.56,
                    limit=6,peak_limit=96,expand_case=True,cache={})
                matches=verify(candidates,dark,320)
                if matches:break
        self.last_diagnostic['elapsed_ms']=round((time.perf_counter()-started)*1000,1)
        if len(matches)!=1:return None
        return matches[0]
