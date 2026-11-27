"""Passive spatial guidance and bounded shortcut diagnostics.

The two inherited methods below are adapted from pinned FM Rush
a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb. No additional input dispatch.
"""
import time
import uuid


def sign_bounds(point):
    x, feet = point
    return x-50, feet-125, x+50, feet-94


def edge_directions(point, size):
    l,t,r,b=sign_bounds(point)
    w,h=size
    return tuple(v for v,yes in (('ABOVE',b<=2),('BELOW',t>=h-2),
                                ('LEFT',r<=2),('RIGHT',l>=w-2)) if yes)


def clipped_directions(point, size):
    l,t,r,b=sign_bounds(point)
    w,h=size
    return tuple(v for v,yes in (('ABOVE',t<2),('BELOW',b>h-2),
                                ('LEFT',l<2),('RIGHT',r>w-2)) if yes)


class CameraModeLatch:
    """Once current target has landmark evidence, never fall back to entry guesses."""
    def __init__(self):
        self.scope=None
        self.landmark_seen=False
    def choose(self,scope,live):
        if scope!=self.scope:
            self.scope=scope
            self.landmark_seen=False
        if live is not None:
            self.landmark_seen=True
            return 'landmark_estimate',live
        return ('waiting_landmark',None) if self.landmark_seen else ('none',None)


class PointerAudit:
    """One correlated result per invocation in an observed locked segment."""
    def __init__(self, recorder, kind, received):
        self.rec=recorder
        self.attempt=getattr(recorder,'active',None) if getattr(recorder,'scope',None)=='locked' else None
        self.kind=kind
        self.received=received
        self.id=uuid.uuid4().hex
        self.closed=False
        self.emit('beast_pointer_request',at=received)
    def emit(self,event,**data):
        if self.attempt is not None:
            self.rec._emit(event,attempt=self.attempt,request_id=self.id,kind=self.kind,**data)
    def done(self,reason,ok=False,**data):
        if self.closed:return
        self.closed=True
        self.emit('beast_pointer_outcome',reason=reason,ok=ok,**data)


def spatial_mixin(old):
    from camera_alignment import GrassCameraTracker, capture_client, room_title_present
    from game_window import window_rect, window_client_rect, window_has_focus, move_cursor_on_screen
    from channel_overlay import preview_channel
    from shop_pin import OverlayPin, entrance_marker
    from shop_position import ENTRY_CLIENTS, entry_shop_point, shop_marker, channel_entry_portal
    class ScopedGrassTracker(GrassCameraTracker):
        def __init__(self):
            self._generation=0
            super().__init__(interval=.10,max_age=.20)
        def reset_scoped(self):
            with self._lock:
                if self._requested is not None:self._generation+=1
                self._requested=None;self._latest=None;self._next=0.
        def get_scoped(self,hwnd,client,scope):
            now=time.monotonic()
            with self._lock:
                identity=(hwnd,tuple(client),scope)
                if self._requested is None or self._requested[:3]!=identity:
                    self._generation+=1
                    self._requested=identity+(self._generation,);self._latest=None;self._next=0.
                key=self._requested
                if not self._closed and not self._busy and now>=self._next:
                    self._busy=True;self._next=now+self.interval;self._jobs.put_nowait(key)
                if self._latest is not None:
                    saved,at,point=self._latest
                    if saved==key and now-at<=self.max_age:return point
            return None
    class EdgePin(OverlayPin):
        def draw_markers(self,w,h,sw,sh,hits):
            self.canvas.delete('all')
            for label,hit in hits.items():
                l,t,r,b=hit['box']
                box=(l*w/sw,t*h/sh,r*w/sw,b*h/sh)
                self.canvas.create_rectangle(*box,fill='#142237',outline='#ffdf72',width=2)
                self.canvas.create_text((box[0]+box[2])/2,(box[1]+box[3])/2,
                    text=label,fill='#ffdf72',font=('Segoe UI',-14,'bold'))
    class SpatialMixin:
        def beast_spatial_init(self):
            self._beast_grass=ScopedGrassTracker()
            self._beast_camera_mode=CameraModeLatch()
            self._beast_edge=EdgePin(self.root,interval_ms=50)
            self._beast_edge_key=None
            self._beast_projection=None
            self._beast_projection_state=None
        def beast_spatial_close(self):
            tracker=getattr(self,'_beast_grass',None)
            if tracker is not None:tracker.close()
            pin=getattr(self,'_beast_edge',None)
            if pin is not None:pin.close()
        def beast_cancel_audit(self,reason):
            audit=getattr(self,'_beast_pending_audit',None)
            if audit is not None:
                audit.done(reason);self._beast_pending_audit=None
        def beast_reject(self,kind,reason,received=None):
            audit=PointerAudit(getattr(self,'performance',None),kind,time.perf_counter() if received is None else received)
            audit.done(reason)
        def _pointer_context(self,current,hwnd):
            snap=super()._pointer_context(current,hwnd)
            return None if snap is None else snap+(getattr(self,'_beast_projection',None),)
        def beast_publish_projection(self,projection,edge,hwnd,client,window,focused,status):
            # Preserve last snapshot during the inherited bounded focus handoff only.
            if projection is not None or focused or getattr(self,'_pointer_pending',None) is None:
                self._beast_projection=projection
            rec=getattr(self,'performance',None)
            state=(getattr(rec,'active',None),projection,edge,status)
            if state!=getattr(self,'_beast_projection_state',None):
                self._beast_projection_state=state
                if rec is not None and projection is not None:
                    _,_,geometry,camera,point,box=projection
                    rec.marker('beast_projection',camera=camera,point=list(point),
                               client_size=list(geometry[2:]),box=list(box) if box else None,
                               edge=list(edge),status=status)
            pin=getattr(self,'_beast_edge',None)
            if pin is None:return
            key=None
            if edge and focused and client and window:
                x=client[0]-window[0]+(client[2]-280)//2
                y=client[1]-window[1]+12
                label='EST. SHOP '+ '/'.join(edge)
                key=(hwnd,window[2:],x,y,label)
            if key!=getattr(self,'_beast_edge_key',None):
                self._beast_edge_key=key
                if key is None:pin.hide()
                else:
                    hwnd,size,x,y,label=key
                    pin.show_many(hwnd,size,{label:{'box':(x,y,x+280,y+32),'mode':'EDGE'}})

        def refresh_overlays(self, current):
            """Keep navigation chase-locked; recognize displayed inventory in either mode."""
            hwnd = None if self.web_only else self.shop.selected_hwnd()
            deal = current[1] if current and self.archive.chase_locked else None
            inventory_deal = self.inventory_target(current)
            window = window_rect(hwnd) if hwnd else None
            client = window_client_rect(hwnd) if window else None
    
            valid_size=bool(client and client[2:] in ENTRY_CLIENTS)
            focused=bool(valid_size and hwnd and window_has_focus(hwnd))
            screenshots=getattr(self,'_shop_capture',None)
            if screenshots is not None:screenshots.observe(hwnd if focused else None,client if focused else None)
            supported=bool(deal and focused)
            inventory_supported=bool(inventory_deal and focused)
            # Only a positive minimap room-title signature permits inventory OCR.
            # Entrance/black frames/unknown titles never start inventory scans.
            room_confirmed=False
            gate_state=('no_target' if not inventory_deal else 'no_window' if not client else
                        'unsupported_resolution' if not valid_size else 'game_not_focused' if not focused else 'title_unconfirmed')
            if inventory_supported:
                x,y,w,h=client
                title=capture_client((x,y,min(w,200),min(h,120)),allow_crop=True)
                if title is None:gate_state='title_capture_failed'
                else:
                    room_confirmed=room_title_present(*title)
                    if room_confirmed:gate_state='room_confirmed'
            # Fast poll only after the FM room-title gate confirms the room.
            self._inventory_fast_poll=room_confirmed
            inventory = self._inventory.get(hwnd,client,inventory_deal) if room_confirmed else None
            if not room_confirmed:self._inventory.reset()
            in_shop = inventory is not None
            item_preview = None
            if in_shop and inventory['hits']:
                dx,dy=client[0]-window[0],client[1]-window[1]
                hits={str(i):{'mode':mode,'box':(l+dx,t+dy,r+dx,b+dy)}
                      for i,(mode,(l,t,r,b)) in enumerate(inventory['hits'])}
                item_preview=(hwnd,window[2:],hits)
            if item_preview!=self._item_preview:
                self._item_preview=item_preview
                if item_preview is None:self.item_pin.hide()
                else:
                    self.item_pin.show_many(*item_preview)
                    timing=inventory.get('timing') if inventory else None
                    if timing and timing.get('target_found_at') is not None:
                        overlay_at=time.perf_counter()
                        timing['overlay_ms']=round((overlay_at-timing['target_found_at'])*1000,2)
                        timing['shop_open_to_overlay_ms']=round((overlay_at-timing['scan_started_at'])*1000,2)
                        timing['queue_to_overlay_ms']=round((overlay_at-timing['queued_at'])*1000,2)
            scene = self._entrance_camera.get(hwnd, client) if supported and not room_confirmed else None
            if not supported or room_confirmed:self._entrance_camera.reset()
            in_entrance = bool(scene and scene[0])
            recorder=getattr(self,'performance',None)
            if recorder is not None:
                # Passive telemetry shares existing observations; navigation and recognition gates above are unchanged.
                recorder.observe(current[0] if inventory_deal or deal else None,
                                 deal if deal is not None else inventory_deal,hwnd,client,
                                 focused,in_entrance,inventory,unlocked=deal is None)
                recorder.observe_gate('entrance' if in_entrance else gate_state, client[2:] if client else None)
                marker=(getattr(recorder,'active',None), 'entrance' if in_entrance else gate_state)
                if marker!=getattr(self,'_last_gate_marker',None):
                    self._last_gate_marker=marker
                    recorder.marker('scanner_gate',state=marker[1],client_size=list(client[2:]) if client else None)
            entrance_preview = None
            if in_entrance and deal.fm:
                hits = entrance_marker(deal.fm, scene[1], client, window)
                if hits:entrance_preview = (hwnd, window[2:], hits)
            if entrance_preview != self._entrance_preview:
                self._entrance_preview = entrance_preview
                if entrance_preview is None:self.entrance_pin.hide()
                else:self.entrance_pin.show_many(*entrance_preview)
    
            channel_preview = None
            if deal and deal.cc and window and not in_entrance and not in_shop:
                _, _, width, height = window
                box = preview_channel(deal.cc, window, client)
                mode = 'GUIDE' if box else 'PRE'
                if box is None:
                    box = (max(5, width - 270), 10, width - 10, 48)
                channel_preview = (hwnd, (width, height), deal.cc, box, mode)
            if channel_preview != self._channel_preview:
                self._channel_preview = channel_preview
                if channel_preview is None:
                    self.channel_pin.hide()
                else:
                    _, size, channel, box, mode = channel_preview
                    self.channel_pin.show_many(hwnd, size, {f'CH {channel}': {'box': box, 'mode': mode}})
    
            alignment_key = (current[0], hwnd, client[2:]) if deal and client else None
            aligned_portal = None
            if self._portal_alignment is not None:
                saved_key, portal = self._portal_alignment
                if saved_key == alignment_key:
                    aligned_portal = portal
                else:
                    self._portal_alignment = None
    
            projection = None
            edge = ()
            camera = 'none'
            tracker = getattr(self,'_beast_grass',None)
            # A manual alignment always takes precedence. Only current room observations
            # can request read-only grass scenery tracking. No cave landmark guesses.
            grass = bool(deal and room_confirmed and not in_shop and focused and
                         deal.shop_position and deal.shop_position.get('theme')=='grass')
            if tracker is not None:
                if grass and aligned_portal is None:
                    scope=(current[0],deal.fm,hwnd,tuple(client),self._cc_entry_mode)
                    live = tracker.get_scoped(hwnd,client,scope)
                    camera,aligned_portal=self._beast_camera_mode.choose(scope,live)
                else:tracker.reset_scoped()
            if aligned_portal is not None and camera=='none':camera='manual'
            preview = None
            offscreen_notice = ''
            if self.web_only:
                status = 'Web-only mode'
            elif client is None:
                status = 'Waiting for MapleStory window'
            elif in_shop:
                status = inventory['status']
                offscreen_notice = 'Shop OCR error' if status.startswith('Shop OCR unavailable') else status
            elif in_entrance:
                status = f'Entrance guide · FM {deal.fm}'
            elif inventory_deal and not room_confirmed:
                status = {'unsupported_resolution':'Scanner paused · unsupported client size',
                          'game_not_focused':'Scanner paused · game not focused',
                          'title_capture_failed':'Scanner paused · minimap capture failed',
                          'title_unconfirmed':'Scanner paused · FM room title not recognized'}.get(gate_state,'Waiting for FM room')
            elif deal is None:
                status = 'ARMED · waiting for shop' if room_confirmed else 'Waiting for next auto-lock'
            elif not room_confirmed:
                status = 'Waiting for confirmed FM room'
            elif deal.shop_position is None:
                status = 'No map pin on this HeneFM deal'
            elif camera=='waiting_landmark':
                status = offscreen_notice = 'Camera landmarks temporarily unavailable · verify shop manually'
            else:
                cc_profile = self._cc_entry_mode and channel_entry_portal(deal.fm, client[2:]) is not None
                if camera=='none':camera='cc_entry_estimate' if cc_profile else 'entry_estimate'
                point = entry_shop_point(deal.shop_position, deal.fm, client[2:], aligned_portal, channel_entry=cc_profile)
                if point is None:
                    status = 'Shop preview requires 1280 × 720 or 1366 × 768'
                else:
                    box = shop_marker(point, client, window)
                    edge = edge_directions(point,client[2:])
                    projection = (current[0],hwnd,tuple(client),camera,point,box)
                    if box is None or box[2]-box[0]<12 or box[3]-box[1]<10:
                        if not edge:edge=clipped_directions(point,client[2:])
                        status = offscreen_notice = ('Estimated shop '+ '/'.join(edge) + ' · move manually' if edge else 'Shop marker too small · move manually')
                    else:
                        preview = (hwnd, window[2:], box)
                        status = {'landmark_estimate':'Grass landmark-aligned estimate', 'manual':'Manual portal alignment', 'cc_entry_estimate':'CC entry estimate · verify sign', 'entry_estimate':'Portal entry estimate · verify sign'}[camera]
                        edge=()
    
            self.beast_publish_projection(projection,edge,hwnd,client,window,focused,status)
            if self.shop.notice.get() != status:
                self.shop.notice.set(status)
            if self.shop.offscreen_notice.get() != offscreen_notice:
                self.shop.offscreen_notice.set(offscreen_notice)
            if preview != self._shop_preview:
                self._shop_preview = preview
                if preview is None:
                    self.shop_pin.hide()
                else:
                    hwnd, size, box = preview
                    self.shop_pin.show_many(hwnd, size, {'shop': {'box': box, 'mode': 'SHOP'}})

        def move_pointer_to_target(self, kind, *, received=None):
            received=time.perf_counter() if received is None else received
            started=time.perf_counter()
            recorder=getattr(self,'performance',None)
            audit=PointerAudit(recorder,kind,received)
            if not self.archive.lock.acquire(blocking=False):
                self.status.set('Pointer target updating · try again')
                audit.done('archive_busy');return
            try:
                current=self.archive.current()
                locked=self.archive.chase_locked
            finally:self.archive.lock.release()
            if not current or not locked:
                self._pointer_serial+=1
                self._pointer_pending=None
                self.beast_cancel_audit('unlocked')
                self.status.set('Lock a listing before moving the pointer')
                audit.done('unlocked');return
            pending=getattr(self,'_pointer_pending',None)
            if pending is not None:
                old_serial,old_kind,old_snapshot,deadline=pending
                if (old_serial==self._pointer_serial and kind==old_kind and started<deadline
                        and self._pointer_context(current,old_snapshot[5])==old_snapshot
                        and self.shop.selected_hwnd()==old_snapshot[5]):
                    if recorder is not None:recorder.marker('pointer_duplicate',at=received,kind=kind)
                    audit.done('duplicate');return
            self.beast_cancel_audit('superseded')
            self._pointer_serial+=1
            serial=self._pointer_serial
            self._pointer_pending=None
            if recorder is not None:recorder.marker('pointer_requested',at=received,kind=kind)
            # Refresh the scene gate once, while game focus is still intact.
            # Do not recompute/reset entrance or inventory state after focus loss.
            try:self.refresh_overlays(current)
            except Exception:
                audit.done('refresh_error');raise
            if kind=='shop':
                preview=self._shop_preview
                unavailable='Shop pointer · '+self.shop.notice.get()
            elif self._channel_preview is None:
                preview=None
                unavailable='Open MapleStory and lock a deal with a destination channel.'
            else:
                hwnd,size,_,box,mode=self._channel_preview
                preview=(hwnd,size,box) if mode=='GUIDE' else None
                unavailable='Channel pointer requires a 1280 × 720 or 1366 × 768 game window.'
            if preview is None:
                self.status.set(unavailable)
                audit.done('preview_unavailable',detail=unavailable);return
            hwnd,size,box=preview
            snapshot=self._pointer_context(current,hwnd)
            if snapshot is None or snapshot[6] is None or snapshot[7] is None or snapshot[6][2:]!=size:
                self.status.set('Game window changed. Try the shortcut again.')
                audit.done('window_changed');return
            # Capture a single validated box and recheck lock, listing, alignment,
            # and exact window/client geometry immediately before cursor movement.
            focus_started=None
            self._pointer_pending=(serial,kind,snapshot,min(received+.150,started+.085))
            self._beast_pending_audit=audit
            def clear_pending():
                pending=getattr(self,'_pointer_pending',None)
                if pending is not None and pending[0]==serial:self._pointer_pending=None
                if getattr(self,'_beast_pending_audit',None) is audit:self._beast_pending_audit=None
            def fail(message,reason):
                clear_pending()
                if recorder is not None:
                    recorder.marker('pointer_failure',kind=kind,reason=reason)
                audit.done(reason)
                self.status.set(message)
            def finish():
                if self._closing or serial!=self._pointer_serial:
                    clear_pending()
                    audit.done('cancelled');return
                now=time.perf_counter()
                if now-received>.150:
                    fail('Pointer shortcut expired · try again','expired')
                    return
                if window_has_focus(hwnd):
                    if focus_started is not None and now-focus_started<.075:
                        self.schedule(5,finish)
                    else:fail('MapleStory kept focus. Switch to FM Rush and try again.','focus_not_released')
                    return
                if not self.archive.lock.acquire(blocking=False):
                    fail('Pointer target updating · try again','archive_busy')
                    return
                try:
                    if self._pointer_context(self.archive.current(),hwnd)!=snapshot or self.shop.selected_hwnd()!=hwnd:
                        fail('Pointer target changed · try again','target_changed')
                        return
                    # Do not move if focus has returned while checking the target.
                    if window_has_focus(hwnd):
                        fail('Game focus changed · try again','focus_changed')
                        return
                    left,top,right,bottom=box
                    window=snapshot[6]
                    problem=move_cursor_on_screen(hwnd,window[0]+(left+right)//2,window[1]+(top+bottom)//2)
                except Exception:
                    clear_pending();audit.done('move_error');raise
                finally:self.archive.lock.release()
                clear_pending()
                finished=time.perf_counter()
                dispatch_ms=(started-received)*1000
                total_ms=(finished-received)*1000
                focus_ms=0 if focus_started is None else (now-focus_started)*1000
                if recorder is not None:
                    recorder.marker('pointer_result',at=finished,kind=kind,ok=not bool(problem),
                        total_ms=round(total_ms,1),queue_ms=round(dispatch_ms,1),focus_ms=round(focus_ms,1))
                audit.done('move_failed' if problem else 'moved',ok=not bool(problem),total_ms=round(total_ms,1))
                message=problem or f'Pointer moved · {total_ms:.1f} ms · verify sign before clicking'
                self.status.set(message)
                if not problem:
                    self._watch_pointer(serial,kind,snapshot,box,finished,message)
            if window_has_focus(hwnd):
                if self.root.state() in ('iconic','withdrawn'):self.root.deiconify()
                focus_started=time.perf_counter()
                try:self.root.focus_force()
                except Exception:
                    clear_pending();audit.done('focus_request_error');raise
                # Check readiness instead of always sleeping 25 ms. The first
                # deferred check gives the game a chance to process focus loss.
                self.schedule(5,finish)
            else:finish()
    return SpatialMixin
