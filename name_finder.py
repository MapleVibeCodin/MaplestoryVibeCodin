"""Target-specific visual search with tiny-strip verification, no text detector.

The target is rendered once per name/viewport. OpenCV searches the letter shapes;
only the best patches are sent to a prewarmed single-line recognizer. No whole
screen OCR, orientation classifier, cloud calls, Tesseract or Windows OCR.
"""
from pathlib import Path
from functools import lru_cache
import time
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fast_shop_match import Hit, norm


def confusable(s):
    return norm(s).replace('rn','m').replace('l','i')


@lru_cache(maxsize=24)
def templates(target,width):
    font=ImageFont.truetype(str(Path(__file__).with_name('assets')/'name_font.ttf'),12)
    bounds=font.getbbox(target)
    canvas=Image.new('L',(bounds[2]-bounds[0]+6,bounds[3]-bounds[1]+6),0)
    ImageDraw.Draw(canvas).text((3-bounds[0],3-bounds[1]),target,font=font,fill=255)
    base=np.array(canvas)
    scales=(1.,width/1280,width/1280*1.04,width/1366,width/1366*1.04)
    result=[];seen=set()
    for scale in scales:
        scale=max(.5,min(1.6,scale))
        w=max(8,round(base.shape[1]*scale));h=max(7,round(base.shape[0]*scale))
        if (w,h) in seen:continue
        seen.add((w,h))
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

    def room_number(self,bgr):
        """One tiny header read at entry; never polls whole-screen OCR."""
        h,w=bgr.shape[:2]
        previous=self.recognizer.rec_image_shape
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
                    found=re.search(r'fre[e]?\s*market\s*[<(\[]?\s*([0-9OIlg]{1,2})\s*[>)\]]?',text,re.I)
                    if found and confidence>=.65:
                        value=found[1].lower().translate(str.maketrans({'o':'0','i':'1','l':'1','g':'9'}))
                        try:number=int(value)
                        except ValueError:continue
                        if 1<=number<=20:return number
            return None
        finally:self.recognizer.rec_image_shape=previous

    def prepare(self,target,width=1366):
        templates(target,width)

    def _candidates(self,bgr,target,dark=False,fast=False,min_score=.56,limit=6,peak_limit=24,cache=None):
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
        for template in templates(target,w):
            th,tw=template.shape
            if th>feature.shape[0] or tw>feature.shape[1]:continue
            if fast:
                peak_key=('peaks',dark,template.shape)
                if peak_key not in cache:
                    mini=cv2.resize(template,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
                    scores=cv2.matchTemplate(small,mini,cv2.TM_CCOEFF_NORMED)
                    peaks=(scores>=.32)&(scores==cv2.dilate(scores,np.ones((5,5),np.uint8)))
                    ys,xs=np.where(peaks)
                    order=np.argsort(scores[ys,xs])[-96:][::-1]
                    cache[peak_key]=[(int(xs[j])*2,int(ys[j])*2) for j in order]
                for x,y in cache[peak_key][:peak_limit]:
                    refinement_key=('refined',dark,template.shape,x,y)
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

    def _verify(self,bgr,target,candidates,dark=False):
        if not candidates:return []
        contexts=[];tight_crops=[]
        for _,(x,y,r,b) in candidates:
            pad=max(3,round((b-y)*.3))
            # Context includes adjacent lettering so a prefix cannot prove identity.
            for horizontal,crops in ((pad,contexts),(0,tight_crops)):
                crop=bgr[max(0,y-2):min(bgr.shape[0],b+2),
                         max(0,x-horizontal):min(bgr.shape[1],r+horizontal)]
                if not dark:crop=255-crop
                crops.append(cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
        words,_=self.recognizer(contexts)
        wanted=norm(target)
        tight_indices=[]
        for i,((score,_),(text,confidence)) in enumerate(zip(candidates,words)):
            expanded=norm(text)
            extra=(len(expanded)==len(wanted)+1 and
                   (expanded.startswith(wanted) or expanded.endswith(wanted)))
            if ((len(wanted)<5 and expanded==wanted and score>=.70 and confidence>=.80) or
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
                valid=(valid and same and score>=.70 and
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
        return matches

    def scan(self,bgr,target,cancelled=None,fast_only=False):
        started=time.perf_counter()
        self.last_diagnostic={'method':'coarse proposals + full-resolution verification','target':target,'candidates':[]}
        if not target or not (3<=len(target)<=24):return None
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
        self.last_diagnostic['elapsed_ms']=round((time.perf_counter()-started)*1000,1)
        if len(matches)!=1:return None
        return matches[0]
