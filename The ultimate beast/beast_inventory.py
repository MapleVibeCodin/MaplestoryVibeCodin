"""Pinned FM Rush scan with exact name AND exact displayed price required.
Source: a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb; no input or seller OCR added.
"""
import time
from shop_inventory import (STEP, normalized, tooltip_blocked_rows, section_fingerprints, sold_row_mask, pick_rows, prepare_ocr)

def exact_active_hits(hits,blocked,frame,sold_mask):
    """Reject rounded/unknown price, sold, ambiguous, blocked and name-only candidates."""
    if len(hits)!=1:return []
    row,mode=hits[0]
    if mode!='MATCH' or row in blocked or sold_mask(frame,row):return []
    return [(row,'MATCH')]


class InventoryFallbackMixin:
    def _scan(self,key):
        started=time.perf_counter()
        try:
            with self._lock:
                if self._key!=key:return
            _,client,_,seller,item,price,buy_step,_=key
            x,y,w,h=client
            self._observation=None
            anchor=self._find_anchor(client)
            geometry=anchor is None
            if geometry:anchor=self._find_geometry_anchor(client)
            anchor_detected_at=time.perf_counter()
            if anchor is None:
                self._publish(key,None);return
            strict='scroll' in normalized(item)
            if geometry and strict:
                self._publish(key,{'status':'Shop geometry detected · waiting for exact scroll gate','hits':[]});return
            ax,ay=anchor
            left,top=ax-140,ay+70
            if left<0 or top<0 or left+204>w or top+263>h:
                self._publish(key,{'status':'Shop open · inventory clipped','hits':[]});return
            with self._lock:
                existing=self._latest if self._key==key else None
                prev_digest=self._digest if self._key==key else None
            if existing is None:self._publish(key,{'status':'Shop open · verifying visible rows','hits':[]})
            frame=self._inventory_frame(client,anchor)
            if not frame:
                self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
            blocked=tooltip_blocked_rows(frame)
            prefixes={}
            sections=tuple((section,fp) for section,fp in section_fingerprints(frame) if section not in blocked or section in prefixes)
            digest=(left,top,sections,geometry,tuple(sorted(prefixes.items())))
            if digest==prev_digest:
                self._publish(key,existing,digest);return
            # Never publish a name-only hit or carry an old positive across changed pixels.
            self._publish(key,{'status':'Shop open · verifying exact name and price','hits':[]},None)
            with self._lock:
                if self._key!=key:return
            ocr_started=time.perf_counter()
            # Seller pixels remain a cheap shop-change fingerprint only. Never OCR the name.
            row_sections=tuple((i,fp) for i,fp in sections if i>=0)
            lines,unavailable,used_ocr=self._row_cache.recognize(frame,self._ocr,row_sections,prefixes)
            with self._lock:
                if self._key!=key:return
            self._ocr_failures=0
            hits,status=pick_rows(lines,unavailable,None,item,price,buy_step=0)
            hits=exact_active_hits(hits,blocked,frame,sold_row_mask)
            if not hits:
                status='No unique active exact name + price match'
            ocr_ms=(time.perf_counter()-ocr_started)*1000
            if hits:
                # Verify candidate independently at another contrast setting.
                selected={row for row,_ in hits}
                alt,alt_sold=prepare_ocr(frame,selected,threshold_delta=15)
                alt_hits,_=pick_rows(self._ocr.recognize(alt),alt_sold,None,item,price,buy_step=0)
                if exact_active_hits(alt_hits,blocked,frame,sold_row_mask)!=hits:
                    hits=[];status='Exact price not independently confirmed'
            self._observation=None
            confirmed=self._find_anchor(client)
            if confirmed!=anchor:
                if not geometry or confirmed is not None or self._find_geometry_anchor(client)!=anchor:
                    self._publish(key,None);return
            frame_after=self._inventory_frame(client,anchor)
            if not frame_after:
                self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
            after_blocked=tooltip_blocked_rows(frame_after)
            after=tuple((section,fp) for section,fp in section_fingerprints(frame_after) if section not in after_blocked)
            if after!=sections or after_blocked!=blocked:
                self._publish(key,{'status':'Shop evidence changed · retrying','hits':[]});return
            hits=exact_active_hits(hits,after_blocked,frame_after,sold_row_mask)
            if hits and geometry:
                # Geometry fallback is advisory, but exact name and price were checked twice.
                hits=[(hits[0][0],'ROW_CHECK')]
                status='Geometry candidate · exact name + displayed price verified'
            elif hits:status='Exact name + displayed price · verify stats'
            hits=[(mode,(left+1,top+23+i*STEP,left+200,top+23+(i+1)*STEP-2)) for i,mode in hits]
            self._publish(key,{'status':status,'hits':hits,
                              'timing':{'scan_id':started,'total_ms':round((time.perf_counter()-started)*1000,2),
                                        'row_recognition_ms':round(ocr_ms,2),'used_ocr':bool(used_ocr or hits),'sold_retry':False,
                                        'fast_path':'exact_price',
                                        'visible_rows':sum(i>=0 for i,_ in sections),'geometry_fallback':geometry}},digest)
        except Exception as exc:
            # A malformed capture/worker response must not kill the capture thread.
            # Report the error class without copying raw OCR or private text.
            self._publish(key,{'status':'Shop OCR unavailable · '+type(exc).__name__,'hits':[]})
            self._ocr_failures+=1
            with self._lock:
                if self._key==key:self._next=time.monotonic()+min(15.0,2.0**min(4,self._ocr_failures-1))
        finally:
            with self._lock:self._busy=False
