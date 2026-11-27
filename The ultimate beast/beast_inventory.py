"""Pinned FM Rush scan with conservative full-row fallback on a name-only miss.
Source: a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb; no input or seller OCR added.
"""
import time
from shop_inventory import (STEP, normalized, tooltip_blocked_rows, tooltip_prefixes, section_fingerprints, sold_row_mask, exact_name_rows, revalidate_changed_hits, pick_rows, locate_exact_name, SoldRetryCache, prepare_ocr, conservative_hits)

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
            prefixes={} if strict else tooltip_prefixes(frame,blocked)
            sections=tuple((section,fp) for section,fp in section_fingerprints(frame) if section not in blocked or section in prefixes)
            digest=(left,top,sections,geometry,tuple(sorted(prefixes.items())))
            if digest==prev_digest:
                self._publish(key,existing,digest);return
            # 50ms target path: exact item-name recognition only. No seller,
            # price or stats OCR; one captured frame; amber advisory highlight.
            # Scroll targets retain the original independent contrast checks.
            if not strict:
                queued_at=self._request_at or started
                shop_open_at=started
                name_start=time.perf_counter()
                # Name-only highlights must not target visibly sold stock.
                name_rows=tuple(i for i,_ in sections if i>=0 and i not in blocked and not sold_row_mask(frame,i))
                names,cache_hits,cache_misses,used_name_ocr=self._name_cache.recognize(frame,name_rows,self._ocr)
                name_end=time.perf_counter()
                target_rows=exact_name_rows(names,item,blocked)
                target_at=time.perf_counter() if len(target_rows)==1 else None
                fast_timing={
                    'scan_id':started,
                    'total_ms':round(((target_at or name_end)-started)*1000,2),
                    'row_recognition_ms':round((name_end-name_start)*1000,2),
                    'name_ocr_ms':round((name_end-name_start)*1000,2) if used_name_ocr else 0.0,
                    'used_ocr':bool(used_name_ocr),
                    'sold_retry':False,
                    'visible_rows':len(name_rows),
                    'geometry_fallback':geometry,
                    'fast_path':'name_only',
                    'name_cache_hits':cache_hits,
                    'name_cache_misses':cache_misses,
                    'queue_to_target_ms':round((target_at-queued_at)*1000,2) if target_at else None,
                    'shop_open_to_target_ms':round((target_at-shop_open_at)*1000,2) if target_at else None,
                    'target_found_at':target_at,
                    'scan_started_at':shop_open_at,
                    'shop_gate_ms':round((anchor_detected_at-started)*1000,2),
                    'queued_at':queued_at,
                }
                if target_at is not None:
                    row=target_rows[0]
                    box=(left+1,top+23+row*STEP,left+200,top+23+(row+1)*STEP-2)
                    status=('Geometry candidate · exact item name only' if geometry
                            else 'Exact item name · price/stats not checked')
                    self._publish(key,{'status':status,'hits':[('ROW_CHECK',box)],'timing':fast_timing},digest)
                    return
                target=normalized(item)
                duplicate=sum(normalized(value)==target for value in names.values())>1
                status='Multiple exact item names · no highlight' if duplicate else 'Target not visible · name-only scan'
                # Name-only miss is not a final verdict: reuse full row evidence.
                # Full matcher still requires exact text/price or advisory-only result.
            # Strict scroll targets retain the original price and independent
            # contrast verification path below.
            # Hide stale hits immediately unless seller and matched row pixels
            # are identical and the match is still unobstructed.
            verified=dict(sections)
            prior=dict(prev_digest[2]) if prev_digest else {}
            held=[]
            if existing and prev_digest and prev_digest[:2]==digest[:2] and prev_digest[4:]==digest[4:]:
                prior_hits=[((box[1]-top-23)//STEP,mode) for mode,box in existing['hits']]
                for row,mode in revalidate_changed_hits(prior_hits,prior,verified,strict):
                    held.append((mode,(left+1,top+23+row*STEP,left+200,top+23+(row+1)*STEP-2)))
            self._publish(key,{'status':'Shop open · verifying visible rows','hits':held},None)
            with self._lock:
                if self._key!=key:return
            ocr_started=time.perf_counter()
            # Seller pixels remain a cheap shop-change fingerprint only. Never OCR the name.
            row_sections=tuple((i,fp) for i,fp in sections if i>=0)
            lines,unavailable,used_ocr=self._row_cache.recognize(frame,self._ocr,row_sections,prefixes)
            with self._lock:
                if self._key!=key:return
            self._ocr_failures=0
            hits,status=pick_rows(lines,unavailable,None,item,price,buy_step=buy_step)
            # The user wants the item location even when its price differs or
            # is unreadable. Keep exact-price green and scroll rules unchanged.
            if not hits and status in ('Item found · displayed price differs','Item found · price not verified'):
                hits=locate_exact_name(lines,unavailable,item,blocked)
                if hits:status='Exact item name · price not verified'
            used_sold_retry=False
            if not hits and not strict:
                # Primary OCR misses on faded text must not be the sole cached verdict.
                # Mocked/older tracker fixtures may construct the object without __init__.
                if not hasattr(self,'_sold_retry'):self._sold_retry=SoldRetryCache()
                alternate,used_sold_retry=self._sold_retry.recognize(frame,self._ocr,sections,prefixes,None,item,price)
                if alternate:
                    hits=alternate
                    status='Sold candidate · alternate contrast; verify item and price'
            ocr_ms=(time.perf_counter()-ocr_started)*1000
            if hits and 'scroll' in normalized(item):
                # Independently render only the candidate row(s) using
                # a second contrast cutoff. Never use a prefix or fuzzy name.
                selected={row for row,_ in hits}
                check_key=(seller,item,price,tuple((i,v) for i,v in sections if i in selected),tuple(hits))
                checked=self._scroll_checks.get(check_key)
                if checked is None:
                    with self._lock:
                        if self._key!=key:return
                    alt,alt_sold=prepare_ocr(frame,selected,threshold_delta=15)
                    alt_hits,_=pick_rows(self._ocr.recognize(alt),alt_sold,None,item,price)
                    checked=alt_hits==hits
                    if checked:
                        self._scroll_checks[check_key]=True
                        while len(self._scroll_checks)>512:self._scroll_checks.popitem(last=False)
                if not checked:hits=[];status='Scroll text not independently confirmed'
            self._observation=None
            confirmed=self._find_anchor(client)
            if confirmed!=anchor:
                if not geometry or confirmed is not None or self._find_geometry_anchor(client)!=anchor:
                    self._publish(key,None);return
            frame_after=self._inventory_frame(client,anchor)
            if not frame_after:
                self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
            after_blocked=tooltip_blocked_rows(frame_after)
            after_prefixes={} if strict else tooltip_prefixes(frame_after,after_blocked)
            if after_prefixes!=prefixes:
                self._publish(key,{'status':'Tooltip moved · retrying','hits':[]});return
            after=tuple((section,fp) for section,fp in section_fingerprints(frame_after) if section not in after_blocked or section in after_prefixes)
            before_map=dict(sections);after_map=dict(after)
            # Even a newly hidden unrelated row changes the evidence set.
            # A single unchanged non-scroll candidate may survive in amber/orange;
            # never carry a green match or a strict scroll across changed evidence.
            if after!=sections:
                hits=revalidate_changed_hits(hits,before_map,after_map,'scroll' in normalized(item))
                if not hits:
                    self._publish(key,{'status':'Shop open · visible rows changed, retrying','hits':[]});return
                status=('Sold candidate · other rows changed' if hits[0][1]=='SOLD_CHECK'
                        else 'Row verified · other rows changing; check price/stats')
                # Force a new recognition; do not cache partial evidence as complete.
                digest=None
            if blocked and not hits and status=='Target not visible · scroll manually':
                status='Tooltip covers rows · no unverified highlight'
            if any(row in prefixes for row,_ in hits):
                hits=conservative_hits(hits,strict)
                status='Visible text candidate · tooltip overlaps row; verify full item and price' if hits else 'Tooltip overlaps row · no verified highlight'
            if geometry:
                hits=conservative_hits(hits,strict)
                status=('Geometry candidate · verify item and price' if hits
                        else 'Shop geometry detected · '+status)
            hits=[(mode,(left+1,top+23+i*STEP,left+200,top+23+(i+1)*STEP-2)) for i,mode in hits]
            self._publish(key,{'status':status,'hits':hits,
                              'timing':{'scan_id':started,'total_ms':round((time.perf_counter()-started)*1000,2),
                                        'row_recognition_ms':round(ocr_ms+(0 if strict else (name_end-name_start)*1000),2),'used_ocr':bool(used_ocr or used_sold_retry or (not strict and used_name_ocr)),'sold_retry':used_sold_retry,
                                        'fast_path':'strict_scroll' if strict else 'full_fallback',
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
