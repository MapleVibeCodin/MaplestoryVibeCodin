"""Cash Overlay v1: offline extension of the pinned Javipen overlay."""
import os
import sys
import time
import threading
import ctypes
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
base.VERSION = "Cash 1.5"
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
        super().__init__(root, templates)
        self._original_show = self.hud.show
        self.hud.show = self._show_cash
        root.title(base.WINDOW_TITLE)
        self.reminder_label = base.tk.Label(root, text='Preparing evidence reminders', bg='#263238', fg='white', wraplength=420, padx=8, pady=5)
        self.reminder_label.grid(row=1,column=0,columnspan=2,sticky='ew')
        self.screenshot_store = ScreenshotStore(base.DATA_DIR / 'screenshots')
        self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True, name='game-screenshots')
        self.screenshot_thread.start()

    def _screenshot_loop(self):
        # Passive foreground-only capture. Metadata is frozen before acquisition.
        warned = False
        next_due = 0.0
        with base.mss.mss() as sct:
            while not self.stop_evt.is_set():
                started = time.monotonic()
                try:
                    hwnd = self.reader.hwnd
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
                                reference = changed or map_changed or capture_at-self.last_reference>=60
                                encoded = png_bytes(img) if reference else jpeg_bytes(img)
                                path = self.screenshot_store.save_scene(encoded,when)
                                if path is not None:
                                    regions = evidence_regions(img,rect,self.reader,windows,base.stack_area) if rich or reference else []
                                    crops = save_crops(self.screenshot_store,img,regions)
                                    data = dict(image=path.name,utc=when.isoformat(),monotonic=capture_at,
                                                acquisition_seconds=round(elapsed,4),rect=list(rect),context=ctx,
                                                context_age_seconds=age,codec=path.suffix[1:],image_bytes=len(encoded),
                                                reference=reference,ui=crops,inventory_windows=windows,
                                                burst=capture_at<self.burst_until,rich=bool(rich or reference),
                                                frame_gap_seconds=None if self.last_capture_time is None else round(capture_at-self.last_capture_time,4),
                                                capture_schema=2,inventory_windows_current=rich,
                                                inventory_last_known=self.cached_inventory_windows)
                                    self.screenshot_store.metadata(path,data)
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
                interval=self.combat_interval if time.monotonic()<self.burst_until else self.base_interval
                self.stop_evt.wait(max(.02,interval-(time.monotonic()-started)))

    def _handle(self, reading):
        super()._handle(reading)
        t, m = self.tracker, self.meso
        now = time.monotonic()
        # Immutable copy from the UI thread. Values are latest OCR state, not a simultaneous screenshot reading.
        self.scene_context = dict(monotonic=now, map=self.map_name, map_read=reading.map,
            map_uncertain=bool(self.map_hidden or self.reader.map_unread or not self.reader.map_box),
            level=self.level, exp=t.exp, exp_pct=t.pct, exp_estimated=bool(t.hidden),
            exp_candidates=[list(x) for x in reading.candidates], exp_confident=bool(reading.confident),
            exp_gained=t.gained, exp_message_total=self.exp_message_total, party=self.party,
            party_observed=reading.party, job=self.job, wallet=m.value, wallet_read=reading.mesos,
            wallet_age=None if m.seen_at is None else round(now-m.seen_at,3),
            raw_mesos=self.picked_mesos, items=[[name,qty] for name,qty in self.loot.values()],
            potion_cost=self.session_pot_cost, active=bool(t.running), segment=self.cash.segment)

    def _said(self, lines, gh):
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
                        out.write(json.dumps(dict(born=line.born,observed=time.monotonic(),kind=line.kind,amount=line.amount,
                                                  colour=line.colour,tries=line.tries,span=line.span,image=image),default=str)+'\n')
            except Exception as e: base.log_error('saving raw message evidence',e)
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
        active = bool(self.tracker.running and name and name == here
                      and not self.in_town and not self.map_hidden)
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
            self.cash.add(found, prices)
        super()._pickups(found, when)

    def _update_display(self):
        self._state_cash(time.monotonic())
        super()._update_display()
        self._export()
        if hasattr(self,'reminder_label'):
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
        self._export(True)
        self.cash = CashLedger()
        self.last_signature = None
        super().reset()

    def close(self):
        self._export(True)
        self.stop_evt.set()
        if hasattr(self, 'screenshot_thread'):
            self.screenshot_thread.join(timeout=2)
        super().close()

if __name__ == "__main__":
    base.App = CashApp
    base.main()
