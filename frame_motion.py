"""Small image-only motion helpers shared by capture and the room reader."""
import cv2
import numpy as np


def signature(bgr):
    h,w=bgr.shape[:2];step=max(1,min(h//112,w//192))
    return cv2.resize(bgr[::step,::step],(48,28),interpolation=cv2.INTER_AREA).astype(np.int16)


def name_region_changed(before,after,box):
    if before.shape!=after.shape:return True
    x,y,r,b=box;a=before[max(0,y):b,max(0,x):r];fresh=after[max(0,y):b,max(0,x):r]
    return not a.size or float(np.mean(np.abs(a.astype(np.int16)-fresh.astype(np.int16))))>24


def relocate_label(before,after,box):
    """Use scene translation before matching a verified word locally."""
    if before.shape!=after.shape:return None
    h,w=before.shape[:2];size=(256,144)
    first=cv2.resize(cv2.cvtColor(before,cv2.COLOR_BGR2GRAY),size).astype(np.float32)
    second=cv2.resize(cv2.cvtColor(after,cv2.COLOR_BGR2GRAY),size).astype(np.float32)
    shift,response=cv2.phaseCorrelate(first,second)
    if response<.35:return None
    dx=round(shift[0]*w/size[0]);dy=round(shift[1]*h/size[1])
    x,y,r,b=box;template=cv2.cvtColor(before[y:b,x:r],cv2.COLOR_BGR2GRAY)
    if not template.size or template.std()<5:return None
    l=max(0,x+dx-5);t=max(0,y+dy-5);q=min(w,r+dx+5);d=min(h,b+dy+5)
    region=cv2.cvtColor(after[t:d,l:q],cv2.COLOR_BGR2GRAY)
    if region.shape[0]<template.shape[0] or region.shape[1]<template.shape[1]:return None
    _,score,_,(ox,oy)=cv2.minMaxLoc(cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED))
    if score<.65:return None
    return l+ox,t+oy,l+ox+template.shape[1],t+oy+template.shape[0]


def follow_word(before,after,box):
    """Track local lettering edges through fade and label-color changes."""
    if before.shape!=after.shape:return None
    x,y,r,b=box;h,w=after.shape[:2]
    template=before[y:b,x:r]
    l=max(0,x-100);t=max(0,y-145);q=min(w,r+100);d=min(h,b+145)
    region=after[t:d,l:q]
    if not template.size or region.shape[0]<b-y or region.shape[1]<r-x:return None
    def edges(image):
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        return cv2.add(cv2.morphologyEx(gray,cv2.MORPH_TOPHAT,kernel),cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT,kernel))
    template=edges(template);region=edges(region)
    if template.std()<4:return None
    scores=cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED)
    _,score,_,(ox,oy)=cv2.minMaxLoc(scores)
    if score<.62:return None
    scores[max(0,oy-8):oy+9,max(0,ox-template.shape[1]//2):ox+template.shape[1]//2+1]=-1
    if scores.max()>score-.08:return None
    return l+ox,t+oy,l+ox+template.shape[1],t+oy+template.shape[0]
