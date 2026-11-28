"""Cash Overlay v1: offline extension of the pinned Javipen overlay."""
import os
import sys
import time
import threading
import ctypes
import hashlib
from evidence_journal import Journal, classify_messages, potion_delta, trusted_scope, scope
from map_reader_fix import stable_map_timestamp
from compact_capture import EvidencePolicy, export_session
from minimap_tracker import viewport, observe
from datetime import datetime, timezone
from pathlib import Path
from cash_core import CashLedger, NPC, append_snapshot
from screenshots import ScreenshotStore, INTERVAL_SECONDS, encode_lossless
from inventory_ui import InventoryDetector
from hybrid_capture import Reminders, context_at, evidence_regions, save_crops, png_bytes, jpeg_bytes

os.environ["MAPLE_EXP_DATA"] = str(Path(os.environ["LOCALAPPDATA"]) / "MapleCashOverlayV1")
import maple_exp as base

base.WINDOW_TITLE = "Maple Cash Overlay"
base.OLD_TITLES = ()
base.VERSION = "Cash 2.4.1"
base.DEFAULTS.update(hud_layout="full", hud_repot=False, hud_scale=0.45,
                     hud_theme="steel", hotkeys_on=False, gap_seconds=120)
base.LOGGING = True
base.LOOT_PRICES.update(NPC)
OriginalApp = base.App

def fmt(v):
    return "—" if v is None else f"{v:,}"

class CashApp(OriginalApp):
    def __init__(self, root, templates):
        self.cash = CashLedger()
        self.last_export = 0.0
        self.last_signature = None
        self.scene_context = None
        self.exp_message_total = 0
        self.reminders = Reminders()
        self.inventory_detector = InventoryDetector()
        self.last_saved_pages = ()
        self.last_reference = -1e9
        self.last_rich = -1e9
        self.last_capture_time = None
        self.last_exp_marker = None
        self.cached_inventory_windows = []
        self.base_interval = .5
        self.combat_interval = .25
        self.burst_until = 0.0
        self.last_capture_map = None
        self.relocated = False
        self.capture_notice = ''
        self.last_capture_state = None
        self.capture_state_at = -1e9
        self.party_confirmed_at = None
        self.journal = None
        self.potion_scope_by_id = {}
        self.hud_enabled = False
        self.recording_epoch = 0
        self.last_map_observation = None
        self.control_state = "visible"
        self.auto_hide = True
        self.auto_started = False
        self.evidence_policy = EvidencePolicy()
        self.full_evidence = os.environ.get("MAPLE_FULL_EVIDENCE") == "1"
        self.last_level_saved = None
        super().__init__(root, templates)
        self._original_show = self.hud.show
        self.hud.show = self._show_cash
        root.title(base.WINDOW_TITLE)
        self.reminder_label = base.tk.Label(root, text='Preparing evidence reminders', bg='#263238', fg='white', wraplength=420, padx=8, pady=5)
        self.reminder_label.grid(row=1,column=0,columnspan=2,sticky='ew')
        controls=base.tk.Frame(root)
        controls.grid(row=2,column=0,columnspan=2,sticky='ew')
        base.tk.Button(controls,text='Hide / keep recording',command=self.hide_recording).pack(side='left',expand=True,fill='x')
        self.hud_button=base.tk.Button(controls,text='Show game HUD',command=self.toggle_game_hud)
        self.hud_button.pack(side='left',expand=True,fill='x')
        self.auto_hide_var=base.tk.BooleanVar(value=True)
        base.tk.Checkbutton(root,text='Auto-hide controls when game is foreground',variable=self.auto_hide_var,command=self._change_auto_hide).grid(row=3,column=0,columnspan=2,sticky='w')
        self.screenshot_store = ScreenshotStore(base.DATA_DIR / 'screenshots')
        self.journal = Journal(self.screenshot_store.folder/'evidence_journal.jsonl')
        self._journal('launch',time.monotonic(),version=base.VERSION,full_evidence=self.full_evidence)
        self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True, name='game-screenshots')
        self.screenshot_thread.start()
        self.minimap_thread=threading.Thread(target=self._minimap_loop,daemon=True,name="minimap-observations")
        self.minimap_thread.start()
        from notification_report import worker
        self.notification_stop=threading.Event()
        self.notification_thread=threading.Thread(target=worker,args=(self.screenshot_store.folder,base.find_tesseract(),Path(__file__).with_name('assets'),self.notification_stop,base.log_error),daemon=True,name='notification-replay')
        self.notification_thread.start()

    def _journal(self,kind,at,**fields):
        if self.journal is None: return
        try:
            if self.screenshot_store.has_space(): self.journal.append(kind,at,**fields)
        except Exception as e: base.log_error('saving evidence journal',e)

    def _window_rect(self):
        # A minimized window has no visible screen rectangle to black out.
        try:
            if self.root.state() in ('iconic','withdrawn'): return None
        except Exception: pass
        return super()._window_rect()

    def _change_auto_hide(self):
        self.auto_hide=bool(self.auto_hide_var.get())

    def hide_recording(self):
        self.hud_enabled=False
        self.hud.hide()
        self.reader.hud_rects=()
        self.reader.own_rect=None
        self.hud_button.configure(text='Show game HUD')
        self._journal('visibility',time.monotonic(),hud=False,control='minimized')
        self.root.iconify()
        self.control_state='minimized' if self.root.state()=='iconic' else self.root.state()

    def toggle_game_hud(self):
        self.hud_enabled=not self.hud_enabled
        self.hud_button.configure(text='Hide game HUD' if self.hud_enabled else 'Show game HUD')
        if not self.hud_enabled:
            self.hud.hide()
            self.reader.hud_rects=()
        self._journal('visibility',time.monotonic(),hud=self.hud_enabled,control='visible')

    def _update_hud(self,*args,**kwargs):
        if not self.hud_enabled or self.root.state() in ('iconic','withdrawn'):
            self.hud.hide()
            self.reader.hud_rects=()
            return
        return super()._update_hud(*args,**kwargs)

    def _minimap_loop(self):
        # Independent 10 Hz target, no input injection, no saved high-frequency images.
        import json
        with base.mss.mss() as sct, (self.screenshot_store.folder/'minimap_observations.jsonl').open('x',encoding='utf-8') as out:
            while not self.stop_evt.is_set():
                t=time.monotonic()
                try:
                    hwnd=self.reader.hwnd
                    if self.reader.mode=='window' and hwnd and ctypes.windll.user32.GetForegroundWindow()==hwnd and self.screenshot_store.has_space():
                        rect=base.PLATFORM.client_rect(hwnd)
                        if rect:
                            x,y,w,h=rect
                            ctx=self.scene_context
                            at=time.monotonic()
                            shot=base.grab(sct,x,y,int(w*.38),int(h*.30))
                            if shot and shot[1:]==(x,y) and shot[0].shape[:2]==(int(h*.30),int(w*.38)) and ctypes.windll.user32.GetForegroundWindow()==hwnd and base.PLATFORM.client_rect(hwnd)==rect:
                                im=shot[0]
                                row=observe(im,viewport(im))
                                c,age=context_at(ctx,at)
                                c=c or {}
                                trusted=age is not None and age<=1 and not c.get('map_uncertain') and c.get('map')
                                row.update(monotonic=at,context_at=c.get('monotonic'),map=c.get('map') if trusted else None,
                                           epoch=c.get('recording_epoch'),segment=c.get('segment'),level=c.get('level'),
                                           exp=c.get('exp') if c.get('exp_confident') and not c.get('exp_estimated') and age is not None and age<=1 else None,
                                           party=c.get('party') if c.get('party_confirmed') and age is not None and age<=1 else None,
                                           rect=list(rect))
                                out.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
                                out.flush()
                except Exception as e:
                    base.log_error('minimap observation',e)
                self.stop_evt.wait(max(.005,.1-(time.monotonic()-t)))

    def _screenshot_loop(self):
        # Passive foreground-only capture. Metadata is frozen before acquisition.
        warned = False
        next_due = 0.0
        with base.mss.mss() as sct:
            while not self.stop_evt.is_set():
                started = time.monotonic()
                try:
                    hwnd = self.reader.hwnd
                    state = ('foreground' if self.reader.mode == 'window' and hwnd and
                             ctypes.windll.user32.GetForegroundWindow() == hwnd else 'not_foreground')
                    if state == 'foreground' and not self.screenshot_store.has_space():
                        state = 'low_disk'
                    if state != self.last_capture_state or started-self.capture_state_at >= 30:
                        if self.screenshot_store.has_space():
                            import json
                            with (self.screenshot_store.folder/'capture_status.jsonl').open('a',encoding='utf-8') as log:
                                log.write(json.dumps(dict(monotonic=started,utc=datetime.now(timezone.utc).isoformat(),state=state))+'\n')
                        self._journal('capture_state',started,state=state)
                        self.last_capture_state=state
                        self.capture_state_at=started
                    if (self.reader.mode == 'window' and hwnd and
                            ctypes.windll.user32.GetForegroundWindow() == hwnd):
                        rect = base.PLATFORM.client_rect(hwnd)
                        if rect and self.screenshot_store.has_space():
                            ctx0 = self.scene_context
                            capture_at = time.monotonic()
                            when = datetime.now(timezone.utc)
                            shot = base.grab(sct, *rect)
                            elapsed = time.monotonic()-capture_at
                            if (shot and ctypes.windll.user32.GetForegroundWindow() == hwnd and
                                    base.PLATFORM.client_rect(hwnd) == rect and
                                    shot[1:] == rect[:2] and shot[0].shape[:2] == (rect[3], rect[2])):
                                img = shot[0]
                                ctx, age = context_at(ctx0,capture_at)
                                rich = capture_at-self.last_rich>=.95
                                if rich:
                                    self.cached_inventory_windows = self.inventory_detector.detect(img)
                                windows = self.cached_inventory_windows if rich else []
                                pages = tuple(sorted(v['page'] for v in windows if v['page']))
                                map_name = ctx.get('map') if ctx and not ctx.get('map_uncertain') and age<=3 else None
                                changed = bool(rich and pages and pages != self.last_saved_pages)
                                marker = (ctx.get('level'),ctx.get('exp')) if ctx and ctx.get('exp_confident') else None
                                exp_changed = bool(marker and self.last_exp_marker and marker != self.last_exp_marker)
                                if marker: self.last_exp_marker = marker
                                if exp_changed: self.burst_until = max(self.burst_until,capture_at+8)
                                map_changed = bool(map_name and map_name != self.last_capture_map)
                                if changed or map_changed: self.burst_until = capture_at+8
                                level=ctx.get('level') if ctx and ctx.get('exp_confident') else None
                                level_changed=bool(level and level!=self.last_level_saved)
                                if level: self.last_level_saved=level
                                reference = changed or map_changed or level_changed or capture_at-self.last_reference>=60
                                keep=self.evidence_policy.scene(capture_at,reference,self.full_evidence)
                                encoded=(png_bytes(img) if reference else jpeg_bytes(img)) if keep else None
                                path = self.screenshot_store.save_scene(encoded,when) if keep else self.screenshot_store.reserve_metadata_frame(when)
                                if path is not None:
                                    regions = evidence_regions(img,rect,self.reader,windows,base.stack_area) if rich or reference else []
                                    if not self.full_evidence:
                                        regions=self.evidence_policy.regions(regions,capture_at,reference,changed)
                                    crops = save_crops(self.screenshot_store,img,regions)
                                    data = dict(image=path.name,utc=when.isoformat(),monotonic=capture_at,
                                                acquisition_seconds=round(elapsed,4),rect=list(rect),context=ctx,
                                                context_age_seconds=age,codec=path.suffix[1:] if keep else None,image_bytes=len(encoded) if keep else 0,
                                                image_retained=keep,retention_policy='full' if self.full_evidence else 'compact',
                                                reference=reference,ui=crops,inventory_windows=windows,
                                                burst=capture_at<self.burst_until,rich=bool(rich or reference),
                                                frame_gap_seconds=None if self.last_capture_time is None else round(capture_at-self.last_capture_time,4),
                                                capture_schema=5,sequence=self.screenshot_store.sequence,
                                                hud_enabled=self.hud_enabled,control_state=self.control_state,
                                                inventory_windows_current=rich,
                                                inventory_last_known=self.cached_inventory_windows)
                                    self.screenshot_store.metadata(path,data)
                                    self._journal('frame',capture_at,file=path.name,
                                        image_sha256=hashlib.sha256(encoded).hexdigest() if keep else None,image_retained=keep,
                                        sidecar_sha256=hashlib.sha256(path.with_suffix('.json').read_bytes()).hexdigest(),
                                        scope=trusted_scope(ctx,capture_at),capture_sequence=self.screenshot_store.sequence)
                                    # Only acknowledge a page with saved lossless panel evidence.
                                    saved={v['kind'] for v in crops}
                                    self.reminders.observe(capture_at,[p for p in pages if 'inventory_'+p in saved],map_name)
                                    if rich:
                                        self.last_saved_pages=pages
                                        self.last_rich=capture_at
                                    self.last_capture_time=capture_at
                                    if map_name: self.last_capture_map=map_name
                                    if reference: self.last_reference=capture_at
                                    self.capture_notice=''
                                    warned=False
                        elif rect and not warned:
                            self.capture_notice='Capture paused: less than 5 GiB free'
                            base.log_error(self.capture_notice)
                            warned=True
                except Exception as e:
                    self.capture_notice='Capture error — see errors.log'
                    base.log_error('saving periodic game screenshot',e)
                live=self.scene_context
                interval=self.combat_interval if (time.monotonic()<self.burst_until or (live and live.get('tracking_enabled') and 0<=time.monotonic()-live['monotonic']<=3)) else self.base_interval
                self.stop_evt.wait(max(.02,interval-(time.monotonic()-started)))

    def _handle(self, reading):
        # Keep the last observation, not pixels from a different foreground app.
        if self.reader.hwnd and self.reader.mode=='window' and ctypes.windll.user32.GetForegroundWindow()!=self.reader.hwnd:
            return
        super()._handle(reading)
        t, m = self.tracker, self.meso
        now = time.monotonic()
        if hasattr(self,'screenshot_store') and not self.auto_started and self.reader.hwnd and self.reader.mode=='window' and reading.confident and type(t.exp) is int:
            self.auto_started=True
            if not self.session.started and not self.session.on: self.toggle()
        if reading.party is not None and reading.party == self.party and self._party_seen[1]>=2:
            self.party_confirmed_at=now
        self.last_map_observation=stable_map_timestamp(self.reader,self.map_name,now)
        self._state_cash(now)
        # Immutable copy from the UI thread. Values are latest OCR state, not a simultaneous screenshot reading.
        self.scene_context = dict(monotonic=now, map=self.map_name, map_read=reading.map,
            map_uncertain=bool(self.map_hidden or self.reader.map_unread or not self.reader.map_box or self.last_map_observation is None or now-self.last_map_observation>3),
            map_observed_at=self.last_map_observation,recording_epoch=self.recording_epoch,
            level=self.level, exp=t.exp, exp_pct=t.pct, exp_estimated=bool(t.hidden),
            exp_candidates=[list(x) for x in reading.candidates], exp_confident=bool(reading.confident and any(e==t.exp for e,p in reading.candidates if e is not None)),
            exp_gained=t.gained, exp_message_total=self.exp_message_total, party=self.party,
            party_observed=reading.party, party_confirmed=bool(self.party is not None and self.party>1 and self.party_confirmed_at is not None and now-self.party_confirmed_at<=3 and self._party_seen[0]==self.party and self._party_seen[1]>=2),
            party_confirmed_at=self.party_confirmed_at, job=self.job, wallet=m.value, wallet_read=reading.mesos,
            wallet_age=None if m.seen_at is None else round(now-m.seen_at,3),
            raw_mesos=self.picked_mesos, items=[[name,qty] for name,qty in self.loot.values()],
            potion_cost_excluded=True, potion_counts=dict(self.pots.counts), potion_counted_at=dict(self.pots.counted_at), active=bool(t.running and self.session.on and self.session.map==self.session.here and not self.in_town and not self.map_hidden),
            tracker_running=bool(t.running), tracking_enabled=bool(self.session.on), waiting=self.session.waiting,
            in_town=bool(self.in_town), cash_ledger=self.cash.snapshot(), wallet_observed_at=m.seen_at,
            segment=self.cash.segment)

    def _message_worker(self):
        # Foreground and geometry must be valid before advancing the stack watcher.
        self.message_thread=threading.current_thread()
        turn=0
        with base.mss.mss() as sct:
            while not self.stop_evt.is_set():
                t0=time.monotonic()
                try:
                    hwnd=self.reader.hwnd
                    rect,g=self.reader.last_rect,self.reader.gh
                    good=bool(hasattr(self,'screenshot_store') and self.messages and hwnd and rect and g and self.reader.mode=='window' and ctypes.windll.user32.GetForegroundWindow()==hwnd and base.PLATFORM.client_rect(hwnd)==rect)
                    shot=self.reader._hide_own(base.grab(sct,*base.stack_area(rect,g))) if good else None
                    if shot and ctypes.windll.user32.GetForegroundWindow()==hwnd and base.PLATFORM.client_rect(hwnd)==rect:
                        found=self._said(self.messages.look(shot[0],g,t0),g)
                        if found:self.q.put(('messages',(found,t0)))
                        turn=(turn+1)%base.POT_EVERY
                        if self.pot_reader and not turn:self._look_for_pots(sct,rect,g)
                    elif self.messages:self.messages.reset()
                except Exception as exc:base.log_error('watching foreground messages',exc)
                self.stop_evt.wait(max(.02,base.MESSAGE_POLL-(time.monotonic()-t0)))

    def _said(self, lines, gh):
        # Never retain background-window message crops from an obscured game.
        if self.stop_evt.is_set() or self.reader.mode!='window' or not self.reader.hwnd or ctypes.windll.user32.GetForegroundWindow()!=self.reader.hwnd:
            return []
        # Preserve raw line pixels and the upstream recognition attempts, even if unreadable.
        # Only lines delivered by the watcher can be recorded by this hook.
        import json, hashlib
        from hybrid_capture import atomic_write
        if lines and hasattr(self,'screenshot_store') and self.screenshot_store.has_space():
            try:
                folder=self.screenshot_store.folder/'message_evidence'
                folder.mkdir(exist_ok=True)
                with (folder/'lines.jsonl').open('a',encoding='utf-8') as out:
                    for line in lines:
                        image=None
                        if line.band is not None and line.band.size:
                            data=png_bytes(line.band)
                            image=hashlib.sha256(data).hexdigest()+'.png'
                            atomic_write(folder/image,data)
                        ctx=self.scene_context or {}
                        age=time.monotonic()-ctx.get('monotonic',-1e9)
                        out.write(json.dumps(dict(born=line.born,observed=time.monotonic(),epoch=ctx.get('recording_epoch'),
                                                  map=ctx.get('map') if 0<=age<=2 and not ctx.get('map_uncertain') else None,
                                                  tracking_enabled=ctx.get('tracking_enabled') if 0<=age<=2 else None,kind=line.kind,amount=line.amount,
                                                  colour=line.colour,tries=line.tries,span=line.span,image=image),default=str)+'\n')
            except Exception as e: base.log_error('saving raw message evidence',e)
        if lines:
            ctx=self.scene_context
            now=time.monotonic()
            for entry in classify_messages(lines):
                born=entry.get('born')
                at=born if isinstance(born,(float,int)) and 0<=now-born<=2 else now
                self._journal('visual_messages',at,scope=trusted_scope(ctx,at),lines=[entry])
        return super()._said(lines,gh)

    def _messages(self, found, when):
        self.exp_message_total += sum(p[1] for p in found if p[0]=='exp')
        if hasattr(self,'screenshot_store'):
            import json
            try:
                with (self.screenshot_store.folder/'recognized_messages.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps({'monotonic':when,'map':self.map_name,'map_uncertain':self.map_hidden or self.reader.map_unread,'messages':found},ensure_ascii=False)+'\n')
            except OSError as e: base.log_error('saving recognized messages',e)
        super()._messages(found, when)

    def _export(self, force=False):
        if self.cash.map is None or not (self.cash.seconds or self.cash.messages):
            return
        now = time.monotonic()
        if not force and now - self.last_export < 30:
            return
        s = self.cash.snapshot()
        sig = tuple(s.values())
        if sig == self.last_signature:
            return
        try:
            append_snapshot(base.DATA_DIR / "cash-sessions.csv", self.cash,
                            exp_gained=getattr(self.tracker,"gained",None),
                            level=getattr(self,"level",None), party=getattr(self,"party",None))
            self.last_export, self.last_signature = now, sig
        except OSError as e:
            base.log_error("saving cash snapshots", e)

    def _state_cash(self, now):
        name = self.session.map
        here = self.session.here
        active = bool(self.tracker.running and self.session.on and name and name == here
                      and not self.in_town and not self.map_hidden and stable_map_timestamp(self.reader,self.map_name,now) is not None
                      and self.reader.hwnd and ctypes.windll.user32.GetForegroundWindow()==self.reader.hwnd)
        if name and self.cash.map and name != self.cash.map:
            self._export(True)
            self.cash = CashLedger()
            self.last_signature = None
        self.cash.tick(now, active, name)
        self.cash.wallet(self.meso.value, self.meso.seen_at, now)

    def _pickups(self, found, when):
        now = time.monotonic()
        self._state_cash(now)
        # Reject delayed queued messages rather than assigning them to a later map.
        if 0 <= now-when <= 2:
            prices = {k.casefold():v for k,v in base.LOOT_PRICES.items()}
            prices.update({k.casefold():v for k,v in (self.cfg.get("loot_prices") or {}).items()})
            sc=trusted_scope(self.scene_context,when)
            accepted=self.cash.active and sc is not None and sc['segment']==self.cash.segment
            if accepted: self.cash.add(found, prices)
            self._journal('accepted_pickups' if accepted else 'unassigned_pickups',when,
                          scope=sc if accepted else None,messages=found)
        else:
            self._journal('unassigned_pickups',when,scope=None,messages=found,reason='delayed')
        super()._pickups(found, when)

    def _pots(self,slots,when):
        # Reuse upstream icon matching and count confirmation, without any meso conversion.
        items=self.cfg.setdefault('pots',[])
        counts={}; changed=False; ambiguous=set(); raw_slots=[]
        for look,count in slots:
            if look is None or count is None: continue
            item=next((it for it in items if base.same_icon(base.np.asarray(it['look'],base.np.float32),look)),None)
            if item is None:
                name,price=base.guess_item(look)
                item={'id':max([it['id'] for it in items]+[0])+1,'name':name,'price':price,
                      'look':base.np.round(look,3).tolist()}
                items.append(item); changed=True
            k=item['id']; raw_slots.append(dict(item_id=k,count=count))
            if k in counts: ambiguous.add(k)
            counts[k]=count
        # Repeated icons may point at the same inventory stack: refuse to sum.
        for k in ambiguous: counts.pop(k,None)
        before=dict(self.pots.counts)
        corrections=self.pots.observe(counts,when,self.session.on,self.in_town)
        sc=trusted_scope(self.scene_context,when)
        deltas=potion_delta(before,self.pots.counts)
        for d in deltas:
            k=d['item_id']; previous=self.potion_scope_by_id.get(k)
            assigned=sc if sc is not None and previous==sc else None
            self._journal('potion_counts',when,scope=assigned,changes=[d],
                          item_label=next((it['name'] for it in items if it['id']==k),None),
                          label_status='configured_or_icon_guess',upstream_usage_candidate=corrections.get(k))
        for k in counts:
            if k in self.pots.counts and self.pots.counts[k]==counts[k]:
                self.potion_scope_by_id[k]=sc
        if raw_slots:
            self._journal('potion_read',when,scope=sc,raw_slots=raw_slots,ambiguous_item_ids=sorted(ambiguous),observed=counts,confirmed=dict(self.pots.counts))
        if changed: base.save_config(self.cfg)

    def _update_display(self):
        self._state_cash(time.monotonic())
        super()._update_display()
        self._export()
        if hasattr(self,'reminder_label'):
            if self.auto_hide and self.reader.hwnd and ctypes.windll.user32.GetForegroundWindow()==self.reader.hwnd and self.root.state()=='normal':
                self.hide_recording()
            self.control_state='minimized' if self.root.state()=='iconic' else self.root.state()
            now=time.monotonic()
            self.reminder_label.configure(text=self.capture_notice or self.reminders.text(now))
            # Repair known minimap obstruction on launch, without moving an already safe window.
            if not self.relocated and self.reader.hwnd:
                rect=base.PLATFORM.client_rect(self.reader.hwnd)
                own=self._window_rect()
                if rect and own:
                    x,y,w,h=rect; ox,oy,ow,oh=own
                    if ox<x+w*.38 and ox+ow>x and oy<y+h*.30 and oy+oh>y:
                        self.root.geometry(f'{max(x,int(x+w/2-ow/2)):+d}{y+8:+d}')
                    self.relocated=True

    def _show_cash(self, rect, content):
        s = self.cash.snapshot()
        c = dict(content)
        c.update(mesos_rate=fmt(s["raw_hr"]), net_label="RAW + NPC / HR",
                 mesos_net=fmt(s["raw_plus_known_npc_hr"]),
                 mesos_gained=fmt(s["observed_raw"]),
                 mesos_spent=fmt(s["wallet_change"]),
                 rate_label="OBS. MESOS / HR", gain_label="OBS. PICKUPS",
                 spent_label="WALLET CHANGE")
        # Never silently call an estimated or partially observed amount net profit.
        if s["unknown_units"]:
            c["net_label"] = "RAW + NPC* / HR"
        return self._original_show(rect, c)

    def reset(self):
        self._journal('reset',time.monotonic(),scope=scope(self.scene_context))
        self.potion_scope_by_id.clear()
        self.recording_epoch+=1
        self.last_map_observation=None
        self.scene_context=None
        self._export(True)
        self.cash = CashLedger()
        self.last_signature = None
        super().reset()

    def close(self):
        if getattr(self,'auto_started',False) and not self.stop_evt.is_set():
            missing=[k for k in ('etc','use','pet') if time.monotonic()-self.reminders.seen.get(k,-1e9)>90]
            if missing:
                from tkinter import messagebox
                if not messagebox.askyesno('Finish recording?', 'Recent inventory evidence missing: '+', '.join(missing)+'. Pickup tracking does not require inventory. Finish anyway?'):
                    return
        self._export(True)
        self.stop_evt.set()
        if hasattr(self, 'screenshot_thread'):
            self.screenshot_thread.join(timeout=2)
        if hasattr(self,'minimap_thread'):self.minimap_thread.join(timeout=3)
        if hasattr(self,'message_thread'):self.message_thread.join(timeout=6)
        if hasattr(self,'notification_stop'):
            self.notification_stop.set()
            self.notification_thread.join(timeout=25)
        mini=self.screenshot_store.folder/'minimap_observations.jsonl'
        if hasattr(self,'minimap_thread') and not self.minimap_thread.is_alive() and mini.is_file():
            self._journal('minimap_file',time.monotonic(),file=mini.name,file_sha256=hashlib.sha256(mini.read_bytes()).hexdigest())
        if (not hasattr(self,'message_thread') or not self.message_thread.is_alive()) and (not hasattr(self,'notification_thread') or not self.notification_thread.is_alive()):
            for kind,name in (('notification_source_file','message_evidence/lines.jsonl'),('notification_result_file','notification_events.jsonl')):
                p=self.screenshot_store.folder/name
                if p.is_file():self._journal(kind,time.monotonic(),file=name,file_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        self._journal('close',time.monotonic())
        if hasattr(self,'screenshot_store') and (not hasattr(self,'screenshot_thread') or not self.screenshot_thread.is_alive()) and (not hasattr(self,'minimap_thread') or not self.minimap_thread.is_alive()) and (not hasattr(self,'message_thread') or not self.message_thread.is_alive()) and (not hasattr(self,'notification_thread') or not self.notification_thread.is_alive()):
            try:
                import json
                from quick_report import report_folder
                refs=json.loads(Path(__file__).with_name('meow_reference.json').read_text(encoding='utf-8'))
                report_folder(self.screenshot_store.folder,refs=refs)
                from minimap_report import report_minimap
                report_minimap(self.screenshot_store.folder)
                from notification_report import summarize
                summarize(self.screenshot_store.folder)
            except Exception as e: base.log_error('saving quick report',e)
            try:
                from species_report import report_folder
                report_folder(self.screenshot_store.folder)
            except Exception as exc: base.log_error("species report",exc)
            try:
                # Actual Windows Downloads known-folder path when redirected; fallback to home.
                downloads=Path.home()/'Downloads'
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                        downloads=Path(os.path.expandvars(winreg.QueryValueEx(key,'{374DE290-123F-4565-9164-39C4925E467B}')[0]))
                except OSError: pass
                archive=export_session(self.screenshot_store.folder,downloads)
                print('Session ZIP:',archive,flush=True)
                import subprocess
                subprocess.Popen(['explorer.exe','/select,',str(archive)])
            except Exception as e: base.log_error('exporting session ZIP',e)
        super().close()

if __name__ == "__main__":
    base.App = CashApp
    base.main()
