"""Target-specific visual search with tiny-strip verification, no text detector.

The target is rendered once per name/viewport. OpenCV searches the letter shapes;
only the best patches are sent to a prewarmed single-line recognizer. No whole
screen OCR, orientation classifier, cloud calls, Tesseract or Windows OCR.
"""
from pathlib import Path
from functools import lru_cache
import time
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

    def prepare(self,target,width=1366):
        templates(target,width)

    def _candidates(self,bgr,target,dark=False,fast=False,min_score=.56,limit=6):
        h,w=bgr.shape[:2]
        # Search from the top: camera scroll can put nameplates above 12% height.
        top=0;bottom=round(h*.92)
        gray=cv2.cvtColor(bgr[top:bottom],cv2.COLOR_BGR2GRAY)
        kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        feature=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT,kernel)
        proposals=[]
        # Half-size correlation proposes locations only. No coordinates or OCR
        # are accepted from the low-resolution image. Bound work in busy rooms.
        small=cv2.resize(feature,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA) if fast else None
        for template in templates(target,w):
            th,tw=template.shape
            if th>feature.shape[0] or tw>feature.shape[1]:continue
            if fast:
                mini=cv2.resize(template,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA)
                scores=cv2.matchTemplate(small,mini,cv2.TM_CCOEFF_NORMED)
                peaks=(scores>=.32)&(scores==cv2.dilate(scores,np.ones((5,5),np.uint8)))
                ys,xs=np.where(peaks)
                order=np.argsort(scores[ys,xs])[-96:]
                for j in order:
                    x=int(xs[j])*2;y=int(ys[j])*2
                    l=max(0,x-4);t=max(0,y-4)
                    patch=feature[t:min(feature.shape[0],y+th+5),l:min(w,x+tw+5)]
                    if patch.shape[0]<th or patch.shape[1]<tw:continue
                    full=cv2.matchTemplate(patch,template,cv2.TM_CCOEFF_NORMED)
                    _,score,_,(dx,dy)=cv2.minMaxLoc(full)
                    if score>=min_score:
                        proposals.append((score,(l+dx,t+dy+top,l+dx+tw,t+dy+top+th)))
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
        crops=[]
        for _,(x,y,r,b) in candidates:
            pad=max(3,round((b-y)*.3))
            # Keep ascenders/descenders; compare both tag context and tight text.
            # Context prevents a target prefix from matching a longer seller name.
            for horizontal in (pad,0):
                crop=bgr[max(0,y-2):min(bgr.shape[0],b+2),
                         max(0,x-horizontal):min(bgr.shape[1],r+horizontal)]
                if not dark:crop=255-crop
                crops.append(cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC))
        words,_=self.recognizer(crops)
        matches=[]
        wanted=norm(target)
        for i,(score,box) in enumerate(candidates):
            context,tight=words[2*i:2*i+2]
            for variant,(text,confidence) in zip(('context','tight'),(context,tight)):
                self.last_diagnostic['candidates'].append({'text':text,'variant':variant,
                    'ocr_confidence':float(confidence),'visual_score':round(score,3),'box':box})
            text,confidence=context
            same=norm(text)==wanted
            glyph=confusable(text)==confusable(target)
            near=(len(target)>=6 and 'rm' in wanted and
                  norm(text)==wanted.replace('rm','m') and score>=.70)
            valid=confidence>=.80 and (same or glyph or near)
            mode='EXACT' if same else 'CONFUSABLE'
            if len(wanted)<5:
                # Short names need strong shapes AND a second agreeing crop.
                valid=(valid and same and score>=.70 and
                       norm(tight[0])==wanted and tight[1]>=.95)
            if not valid and len(wanted)>=6 and score>=.60:
                # A tag ornament or overlapping neighbour can add ONE glyph.
                # Never silently call that an exact identity; no loose substring search.
                expanded=norm(context[0])
                extra=(len(expanded)==len(wanted)+1 and
                       (expanded.startswith(wanted) or expanded.endswith(wanted)))
                if extra and norm(tight[0])==wanted and tight[1]>=.95 and context[1]>=.80:
                    valid=True;text=tight[0];mode='CONFUSABLE'
            # Weak shape proposals need two exact reads; never relax identity checks.
            if score < .56:
                valid=(same and norm(tight[0])==wanted and
                       confidence>=.85 and tight[1]>=.85 and len(wanted)>=5)
                mode='EXACT'
            if valid:matches.append(Hit(text.strip(),box,float(score),mode))
        return matches

    def scan(self,bgr,target,cancelled=None):
        started=time.perf_counter()
        self.last_diagnostic={'method':'coarse proposals + full-resolution verification','target':target,'candidates':[]}
        if not target or not (3<=len(target)<=24):return None
        matches=[]
        coarse={}
        # Coarse proposals are ALWAYS refined and recognized at original resolution.
        # If no candidate verifies, retain the full-resolution recovery search.
        passes=((True,.56),(True,.48),(False,.56)) if len(norm(target))>=5 else ((True,.56),(False,.56))
        for fast,min_score in passes:
            for dark in (False,True):
                if cancelled is not None and cancelled():
                    self.last_diagnostic['cancelled']=True
                    return None
                if fast:
                    if dark not in coarse:
                        coarse[dark]=self._candidates(bgr,target,dark=dark,fast=True,
                                                       min_score=.48,limit=12)
                    candidates=[c for c in coarse[dark]
                                if (c[0]>=.56 if min_score==.56 else c[0]<.56)][:6]
                else:
                    candidates=self._candidates(bgr,target,dark=dark,fast=False)
                self.last_diagnostic['proposal_threshold']=min_score
                self.recognizer.rec_image_shape=[3,48,160 if fast else 320]
                matches=self._verify(bgr,target,candidates,dark=dark)
                if fast and min_score==.56 and not matches and candidates:
                    # Some overlapping tags need the model's original right padding.
                    # Retry only these small patches, not the whole image search.
                    self.recognizer.rec_image_shape=[3,48,320]
                    matches=self._verify(bgr,target,candidates,dark=dark)
                if matches:break
            if matches:break
        self.last_diagnostic['elapsed_ms']=round((time.perf_counter()-started)*1000,1)
        if len(matches)!=1:return None
        return matches[0]
