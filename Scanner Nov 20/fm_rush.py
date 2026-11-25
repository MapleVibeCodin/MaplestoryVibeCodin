"""FM Rush — HeneFM route and shop-position overlays."""
from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import time
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from game_window import (
    chase_shortcut_state, cursor_on_client, move_cursor_on_screen, window_client_rect, window_has_focus, window_rect,
    windows as list_game_windows,
)
from deal_archive import DealArchive
from channel_overlay import ChannelPin, preview_channel
from shop_pin import ShopPreviewPin, EntranceGuidePin, entrance_marker
from camera_alignment import EntranceCameraTracker, room_title_present
from shop_inventory import ShopInventoryTracker
from shop_pin import ItemInventoryPin
from shop_position import ENTRY_CLIENTS, entry_shop_point, shop_marker, shop_offscreen_notice, channel_entry_portal
from trade_hotkeys import TradeHotkeys
from performance_recorder import PerformanceRecorder
from camera_alignment import capture_client, enable_capture_cache, release_capture_cache
from game_window import window_at_point, cursor_screen_position

from deal_parser import parse_deal
from henefm_bridge import BrowserBridge
from route_logic import parse_alert, plan, arrows, PORTALS, START_POINT, ROW_Y, ROPE_X, BOTTOM_WARP, START_CHANNEL

BASE = Path(__file__).resolve().parent
CONFIG = BASE / 'config.json'
ARCHIVE_DIR=(Path(os.environ['LOCALAPPDATA'])/'FM_Rush'/'archives'
             if os.name=='nt' and os.environ.get('LOCALAPPDATA') else BASE/'archives')
BG = '#091222'; CARD='#152338'; CARD2='#1c314a'
FG='#f5fbff'; MUTED='#a9bfd6'; TEAL='#25e5b5'; YELLOW='#ffdf72'; RED='#f37d8c'


def settings():
    try:
        data=json.loads(CONFIG.read_text('utf-8'))
    except (OSError,ValueError):
        data={}
    return {
        'version': 17,
        'start_channel': int(data.get('start_channel',START_CHANNEL)) if int(data.get('version',0)) >= 4 else START_CHANNEL,
        'strip_geom':data.get('strip_geom',''),
        'grid_geom':data.get('grid_geom',''),
        'map_geom':data.get('map_geom',''),
        'topmost':bool(data.get('topmost',True)),
        'channel_entry':bool(data.get('channel_entry',True)),
    }


class GameWindow:
    """Automatically select MapleStory; no manual HWND control."""
    def __init__(self, app):
        self.app = app
        self.notice = tk.StringVar(value='Waiting for MapleStory window')
        self.offscreen_notice = tk.StringVar(value='')
        self._hwnd = None
        self._next_search = 0.0

    def selected_hwnd(self):
        if self.app.web_only:
            return None
        now = time.monotonic()
        if now >= self._next_search:
            self._next_search = now + 1.0
            candidates = [hwnd for hwnd, title in list_game_windows()
                          if 'maplestory' in title.casefold() or 'maple story' in title.casefold()]
            # Prefer the focused game; otherwise keep the existing valid game.
            self._hwnd = next((hwnd for hwnd in candidates if window_has_focus(hwnd)),
                              self._hwnd if self._hwnd in candidates else next(iter(candidates), None))
        return self._hwnd


class FMApp:
    def __init__(self):
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:pass
        self.conf=settings()
        self.web_only=os.environ.get('FM_RUSH_WEB_ONLY') == '1'
        self.root=tk.Tk()
        self.root.title('FM Rush v24.62.0 - Room-only exact item scanner')
        self.root.config(bg=BG)
        self.root.resizable(True,True)

        self.root.attributes('-topmost',self.conf['topmost'])
        self.current_cc=20
        self.current_fm=13
        self.ccfm=tk.StringVar(value='Choose a deal')
        self.keys=tk.StringVar(value='')
        self.item=tk.StringVar(value='ITEM: —')
        self.stats=tk.StringVar(value='STATS: —')
        self.ign=tk.StringVar(value='IGN: —')
        self.profit=tk.StringVar(value='PROFIT: —')
        self.buy=tk.StringVar(value='BUY AT: —')
        self.status=tk.StringVar(value='ARMED · waiting for a HeneFM listing')
        self.chase_label=tk.StringVar(value='ARMED · auto-lock next')
        self.manual=tk.StringVar(value='CC 22 FM 13')
        self.events=queue.Queue()
        self._trade_events=queue.Queue()
        self._pointer_serial=0
        self._pointer_pending=None
        self.root.bind('<<FMRushTradeWake>>', self.drain_trade_events, add='+')
        self.browser_bridge=None
        self.grid=None
        self.map=None
        self.displayed_listing=None
        self.archive=DealArchive(ARCHIVE_DIR/'deal_archive.sqlite3',manual_selection=True,auto_lock=True)
        self.manual_override_at=None
        self._pending_after=set()
        self._closing=False
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.channel_pin=ChannelPin(self.root)
        self.shop_pin = ShopPreviewPin(self.root, interval_ms=25)
        self.entrance_pin = EntranceGuidePin(self.root, interval_ms=50)
        self._entrance_camera = EntranceCameraTracker()
        self._entrance_preview = None
        self.item_pin = ItemInventoryPin(self.root, interval_ms=50)
        self._inventory = ShopInventoryTracker()
        self.performance = PerformanceRecorder(ARCHIVE_DIR.parent/'performance', capture=capture_client,
            focused=window_has_focus, geometry=window_client_rect, point_window=window_at_point,
            init_capture=enable_capture_cache, release_capture=release_capture_cache)
        self._item_preview = None
        self._shop_preview = None
        self._portal_alignment = None
        self._cc_entry_mode = bool(self.conf['channel_entry'])
        self._channel_preview = None
        self._chase_keys_down = None
        self.shop=GameWindow(self)
        self._make_bottom()
        self.root.update_idletasks()
        self.root.minsize(max(640,self.control_bar.winfo_reqwidth()+24),self.root.winfo_reqheight())
        self.snap(restore=True)
        self.sync_archive()
        self.schedule(35,self.pump)
        self.schedule(50,self.follow_overlays)
        try:
            self.browser_bridge=BrowserBridge(self.events,self.archive)
            self.browser_bridge.start()
            self.status.set('ARMED · auto-lock next new listing')
        except OSError as exc:
            self.status.set('HeneFM bridge not available: '+str(exc)[:100])
        self.trade_keys=TradeHotkeys(self.post_trade_event);self.trade_keys.start()
        self.schedule(1000,self.resume_first_listing)

    def schedule(self, delay, callback):
        if self._closing:return
        token=[None]
        def wrapped():
            self._pending_after.discard(token[0])
            if not self._closing:
                callback()
        token[0]=self.root.after(delay,wrapped)
        self._pending_after.add(token[0])

    def lbl(self,p,text=None,var=None,size=12,color=FG,bold=False):
        return tk.Label(p,text=text,textvariable=var,bg=p['bg'],fg=color,
                        font=('Segoe UI',size,'bold' if bold else 'normal'),anchor='w',justify='left')

    def btn(self,p,text,cmd,accent=False):
        return tk.Button(p,text=text,command=cmd,relief='flat',padx=7,pady=4,
                         bg=TEAL if accent else '#334866',fg=BG if accent else FG,
                         font=('Segoe UI',9,'bold'))

    def _make_bottom(self):
        details=tk.Frame(self.root,bg=BG)
        details.pack(fill='x',padx=12,pady=(5,0))
        details.columnconfigure(2,weight=1)
        self.lbl(details,var=self.ccfm,size=16,color=TEAL,bold=True).grid(row=0,column=0,sticky='w')
        tk.Frame(details,bg=CARD2,width=1).grid(row=0,column=1,rowspan=3,sticky='ns',padx=12)
        self.lbl(details,var=self.ign,size=12,color=YELLOW,bold=True).grid(row=0,column=2,sticky='ew')
        self.lbl(details,var=self.item,size=12,color=YELLOW,bold=True).grid(row=1,column=2,sticky='ew')
        self.lbl(details,var=self.stats,size=9,color=MUTED).grid(row=2,column=2,sticky='ew')
        self.lbl(details,var=self.buy,size=13,color=YELLOW,bold=True).grid(row=0,column=3,sticky='e',padx=(8,0))
        self.lbl(details,var=self.profit,size=10,color=TEAL).grid(row=1,column=3,sticky='e',padx=(8,0))

        controls=self.control_bar=tk.Frame(self.root,bg=BG)
        controls.pack(fill='x',padx=12,pady=(4,0))
        self.btn(controls,'Skip',self.complete_deal).pack(side='left')
        tk.Button(controls,textvariable=self.chase_label,command=self.toggle_chase,bg=YELLOW,fg=BG,relief='flat').pack(side='left',padx=4)
        tools=tk.Menubutton(controls,text='Tools ▾',relief='flat',bg=CARD2,fg=FG,padx=8,pady=4)
        menu=self.tools_menu=tk.Menu(tools,tearoff=False)
        tools.configure(menu=menu)
        for title,action in [('Move pointer to shop',self.move_pointer_to_shop),
                             ('Move pointer to channel',self.move_pointer_to_channel),
                             ('Place under game',self.snap),('Enter route',self.enter_route),
                             ('Channel grid',self.open_grid),('FM map',self.open_map),
                             ('Export deal archive',self.export_archive),
                             ('Export performance report',self.export_performance),
                             ('Pause/resume performance recording',self.toggle_performance),
                             ('Reopen last skipped deal',self.undo_deal)]:
            menu.add_command(label=title,command=action)
        menu.add_separator()
        self._cc_entry_var=tk.BooleanVar(value=self._cc_entry_mode)
        menu.add_checkbutton(label='Channel-change entry profile (1366x768)', variable=self._cc_entry_var,
                             command=self.change_entry_profile)
        tools.pack(side='right')

        footer=tk.Frame(self.root,bg=BG)
        footer.pack(fill='x',padx=12,pady=(2,3))
        footer.columnconfigure(0,weight=3,uniform='status')
        footer.columnconfigure(1,weight=2,uniform='status')
        status=self.lbl(footer,var=self.status,size=9,color=MUTED)
        status.configure(width=1)
        status.grid(row=0,column=0,sticky='ew',padx=(0,12))
        preview_status=self.lbl(footer,var=self.shop.notice,size=9,color=MUTED)
        preview_status.configure(width=1,anchor='e')
        preview_status.grid(row=0,column=1,sticky='ew')

    def change_entry_profile(self):
        self._cc_entry_mode=bool(self._cc_entry_var.get())
        self.conf['channel_entry']=self._cc_entry_mode
        self._pointer_serial+=1
        self._pointer_pending=None
        self._portal_alignment=None
        self.refresh_overlays(self.archive.current())

    def enter_route(self):
        value=simpledialog.askstring('Enter route','Enter a channel and room, such as CH 22 FM 13.',
                                     initialvalue=self.manual.get(),parent=self.root)
        if value is not None:
            self.manual.set(value)
            self.manual_go()

    def open_grid(self):
        if self.grid is not None and self.grid.winfo_exists():
            self.grid.deiconify();self.grid.lift();return
        self.grid=tk.Toplevel(self.root)
        self.grid.title('FM Rush — Channel grid')
        if self.conf['grid_geom']:self.grid.geometry(self.conf['grid_geom'])
        self.grid.config(bg=BG)
        self.grid.resizable(True,True)
        self.grid.minsize(260,175)
        self.grid.attributes('-topmost',self.conf['topmost'])
        self.grid.protocol('WM_DELETE_WINDOW',self.grid.withdraw)
        tk.Label(self.grid,text='CHANNEL GRID · START CH20',font=('Segoe UI',13,'bold'),bg=BG,fg=TEAL).pack(anchor='w',padx=10,pady=(8,0))
        self.grid_canvas=tk.Canvas(self.grid,bg=CARD,highlightthickness=0)
        self.grid_canvas.pack(fill='both',expand=True,padx=8,pady=(5,8))
        self.grid_canvas.bind('<Configure>',lambda _:self.draw_grid())
        self.grid_canvas.bind('<Button-1>',self.click_grid)
        self.draw_grid()

    def draw_grid(self):
        c=self.grid_canvas
        W=max(230,c.winfo_width());H=max(135,c.winfo_height())
        key=(c,W,H,self.current_cc,self.conf['start_channel'])
        if key==getattr(self,'_grid_draw_key',None):return
        self._grid_draw_key=key;c.delete('all')
        gap=min(7,max(2,W//110))
        padx=max(5,W*.02);pady=max(3,H*.025)
        cw=(W-2*padx-7*gap)/8
        ch=(H-2*pady-4*gap)/5
        fsize=max(8,min(21,int(min(cw*.24,ch*.53))))
        for cc in range(1,41):
            r,col=divmod(cc-1,8)
            x=padx+col*(cw+gap);y=pady+r*(ch+gap)
            fill='#2d415d';stroke='#587795';txt=FG
            if cc==self.conf['start_channel']:fill='#166c5e';stroke=TEAL
            if cc==self.current_cc:fill=YELLOW;stroke='#ffffff';txt=BG
            c.create_rectangle(x,y,x+cw,y+ch,fill=fill,outline=stroke,width=2,tags=(f'c{cc}',))
            c.create_text(x+cw/2,y+ch/2,text=f'{cc}',fill=txt,font=('Segoe UI',fsize,'bold'),tags=(f'c{cc}',))

    def click_grid(self,event):
        hits=self.grid_canvas.find_overlapping(event.x,event.y,event.x,event.y)
        for hit in reversed(hits):
            for tag in self.grid_canvas.gettags(hit):
                if re.fullmatch(r'c\d+',tag):
                    self.set_target(int(tag[1:]),self.current_fm,keep_deal=True)
                    return

    def open_map(self):
        if self.map is not None and self.map.winfo_exists():
            self.map.deiconify();self.map.lift();return
        self.map=tk.Toplevel(self.root)
        self.map.title('FM Rush — FM entrance map')
        if self.conf['map_geom']:self.map.geometry(self.conf['map_geom'])
        self.map.config(bg=BG)
        self.map.resizable(True,True)
        self.map.minsize(300,180)
        self.map.attributes('-topmost',self.conf['topmost'])
        self.map.protocol('WM_DELETE_WINDOW',self.map.withdraw)
        tk.Label(self.map,text='FM ENTRANCE · 4 ROWS / 20 PORTALS',font=('Segoe UI',13,'bold'),bg=BG,fg=TEAL).pack(anchor='w',padx=10,pady=(8,0))
        tk.Label(self.map,textvariable=self.ccfm,font=('Segoe UI',18,'bold'),bg=BG,fg=YELLOW).pack(anchor='w',padx=10)
        tk.Label(self.map,textvariable=self.item,bg=BG,fg=YELLOW,font=('Segoe UI',12,'bold')).pack(anchor='w',padx=10)
        tk.Label(self.map,textvariable=self.ign,bg=BG,fg=YELLOW).pack(anchor='w',padx=10)
        actions = tk.Frame(self.map, bg=BG)
        actions.pack(fill='x', padx=10)
        tk.Button(actions,textvariable=self.chase_label,command=self.toggle_chase,bg=YELLOW,fg=BG,relief='flat').pack(side='left')
        self.lbl(actions, var=self.shop.offscreen_notice, size=9, color=YELLOW).pack(side='left', padx=(8, 0))
        self.map_canvas=tk.Canvas(self.map,bg=CARD,highlightthickness=0)
        self.map_canvas.pack(fill='both',expand=True,padx=8,pady=(5,8))
        self.map_canvas.bind('<Configure>',lambda _:self.draw_map())
        self.map_canvas.bind('<Button-1>',self.click_map)
        self.draw_map()

    def _scale_map(self):
        W=max(200,self.map_canvas.winfo_width())
        H=max(120,self.map_canvas.winfo_height())
        return W/760, H/294

    def draw_map(self):
        c=self.map_canvas
        sx,sy=self._scale_map()
        key=(c,sx,sy,self.current_fm,self.displayed_listing is not None)
        if key==getattr(self,'_map_draw_key',None):return
        self._map_draw_key=key;c.delete('all')
        def p(x,y):return x*sx,y*sy
        for row,first,last,label in [('ROW4',17,20,'ROW 4 · FM 17–20'),
                                     ('ROW3',13,16,'ROW 3 · FM 13–16'),
                                     ('ROW2',7,12,'ROW 2 · FM 7–12'),
                                     ('ROW1',1,6,'ROW 1 · FM 1–6')]:
            y=ROW_Y[row]
            left=PORTALS[first][0]-65;right=PORTALS[last][0]+65
            c.create_line(*p(left,y+19),*p(right,y+19),fill='#58728e',width=max(2,4*min(sx,sy)))
            c.create_text(*p(12,y-28),text=label,anchor='w',fill=MUTED,
                          font=('Segoe UI',max(7,int(11*min(sx,sy))),'bold'))
        # One aligned central rope: 18|19, 14|15, 9|10 and 3|4.
        c.create_line(*p(ROPE_X,ROW_Y['ROW4']+19),*p(ROPE_X,ROW_Y['ROW1']),
                      fill='#dec387',width=max(2,3*sx),dash=(3,2),tags=('central_rope',))
        for n,(x,y,_) in PORTALS.items():
            xx,yy=p(x,y)
            r=max(9,min(25,17*min(sx,sy)))
            active=(self.displayed_listing is not None and n==self.current_fm)
            c.create_oval(xx-r,yy-r,xx+r,yy+r,fill=YELLOW if active else '#2c425f',
                          outline=FG if active else '#8098ad',width=2,tags=(f'fm{n}',))
            c.create_text(xx,yy,text=str(n),fill=BG if active else FG,
                          font=('Segoe UI',max(9,min(20,int(r*.9))),'bold'),tags=(f'fm{n}',))
        xx,yy=p(*START_POINT)
        c.create_oval(xx-5,yy-5,xx+5,yy+5,fill=TEAL,outline=FG)
        c.create_text(xx+10,yy,text='START',anchor='w',fill=TEAL,font=('Segoe UI',max(8,int(10*min(sx,sy))),'bold'))

    def click_map(self,event):
        hits=self.map_canvas.find_overlapping(event.x,event.y,event.x,event.y)
        for hit in reversed(hits):
            for tag in self.map_canvas.gettags(hit):
                if re.fullmatch(r'fm\d+',tag):
                    self.set_target(self.current_cc,int(tag[2:]),keep_deal=True)
                    return

    def set_target(self,cc,fm,deal=None,keep_deal=False,source='MANUAL'):
        if source=='MANUAL' and self.archive.chase_locked:
            self.status.set('LOCKED · click UNLOCK before changing destination');return
        if source=='MANUAL':self.manual_override_at=time.monotonic()
        self.current_cc=cc;self.current_fm=fm
        p=plan(cc,fm,start_channel=self.conf['start_channel'])
        self.ccfm.set(f'CH {cc:02d}  /  FM {fm:02d}')
        self.keys.set(arrows(p.channel_keys))
        if deal is not None:
            self.item.set('ITEM: '+(deal.item or '—')+(' · SOLD' if deal.sold else ''))
            self.stats.set('STATS: '+(deal.stats or '—'))
            self.ign.set('IGN: '+(deal.ign or '—'))
            self.profit.set(deal.profit.label)
            self.buy.set(deal.buy_label)
        elif not keep_deal:
            self.item.set('ITEM: —');self.stats.set('STATS: —')
            self.ign.set('IGN: —');self.profit.set('PROFIT: —');self.buy.set('BUY AT: —')
        if self.grid is not None and self.grid.winfo_exists():self.draw_grid()
        if self.map is not None and self.map.winfo_exists():self.draw_map()

    def sync_archive(self):
        with self.archive.lock:
            if not self.archive.chase_locked:
                self.archive.preview_latest()
            current = self.archive.current()
            self.live_stamp = self.archive.live_state()
        if self.archive.chase_locked:self.restore_chase_route()
        self.refresh_overlays(current)
        self.chase_label.set('LOCKED · UNLOCK (Shift+2)' if self.archive.chase_locked else 'ARMED · auto-lock next')
        key,deal=current if current else (None,None)
        if key!=self.displayed_listing:
            self.displayed_listing=key
            if deal is not None:
                if deal.cc is not None and deal.fm is not None:
                    self.set_target(deal.cc,deal.fm,deal=deal,source='ARCHIVE')
                else:
                    self.ign.set('IGN: '+deal.ign);self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
                    self.stats.set('STATS: '+deal.stats);self.profit.set(deal.profit.label)
                    self.buy.set(deal.buy_label);self.ccfm.set('CH / FM: not shown')
                self.open_map()
            else:
                self.ccfm.set('Choose a deal');self.keys.set('')
                self.ign.set('IGN: —');self.item.set('ITEM: —');self.stats.set('STATS: —')
                self.buy.set('BUY AT: —');self.profit.set('PROFIT: —')
        elif deal is not None:
            self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
            self.profit.set(deal.profit.label)
        if self.map is not None and self.map.winfo_exists():self.draw_map()

    def export_archive(self):
        path=filedialog.asksaveasfilename(title='Export listings grouped by seller IGN',
            defaultextension='.json',initialfile='FM_Rush_IGN_Archive.json',filetypes=[('JSON archive','*.json')])
        if path:
            try:self.archive.export_json(path);self.status.set('Archive saved: '+path)
            except OSError as exc:messagebox.showerror('Archive export',str(exc))

    def export_performance(self):
        path=filedialog.asksaveasfilename(title='Export FM Rush performance report',
            defaultextension='.json',initialfile='FM_Rush_Performance.json',filetypes=[('JSON report','*.json')])
        if path:
            try:self.performance.export(path);self.status.set('Performance report saved: '+path)
            except (OSError,ValueError) as exc:messagebox.showerror('Performance export',str(exc))

    def toggle_performance(self):
        self.performance.set_enabled(not self.performance.enabled)
        self.status.set('Performance recorder '+('active' if self.performance.enabled else 'paused'))

    def next_live_deal(self):
        # Skip current target; auto-lock remains armed for a new listing.
        self.complete_deal()

    def refresh_overlays(self, current):
        """Update both guides from the selected listing and game geometry."""
        hwnd = None if self.web_only else self.shop.selected_hwnd()
        deal = current[1] if current and self.archive.chase_locked else None
        window = window_rect(hwnd) if hwnd else None
        client = window_client_rect(hwnd) if window else None

        supported = bool(deal and client and client[2:] in ENTRY_CLIENTS and window_has_focus(hwnd))
        # Only a positive minimap room-title signature permits inventory OCR.
        # Entrance/black frames/unknown titles never start inventory scans.
        room_confirmed=False
        if supported:
            x,y,w,h=client
            title=capture_client((x,y,min(w,200),min(h,120)),allow_crop=True)
            room_confirmed=bool(title and room_title_present(*title))
        inventory = self._inventory.get(hwnd,client,deal) if room_confirmed else None
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
            else:self.item_pin.show_many(*item_preview)
        scene = self._entrance_camera.get(hwnd, client) if supported and not room_confirmed else None
        if not supported or room_confirmed:self._entrance_camera.reset()
        in_entrance = bool(scene and scene[0])
        recorder=getattr(self,'performance',None)
        if recorder is not None:
            recorder.observe(current[0] if deal else None,deal,hwnd,client,supported,in_entrance,inventory)
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

        preview = None
        offscreen_notice = ''
        if self.web_only:
            status = 'Web-only mode'
        elif client is None:
            status = 'Waiting for MapleStory window'
        elif deal is None:
            status = 'Waiting for next auto-lock'
        elif in_shop:
            status = inventory['status']
            offscreen_notice = 'Shop OCR error' if status.startswith('Shop OCR unavailable') else status
        elif in_entrance:
            status = f'Entrance guide · FM {deal.fm}'
        elif not room_confirmed:
            status = 'Waiting for confirmed FM room'
        elif deal.shop_position is None:
            status = 'No map pin on this HeneFM deal'
        else:
            cc_profile = self._cc_entry_mode and channel_entry_portal(deal.fm, client[2:]) is not None
            point = entry_shop_point(deal.shop_position, deal.fm, client[2:], aligned_portal, channel_entry=cc_profile)
            if point is None:
                status = 'Shop preview requires 1280 × 720 or 1366 × 768'
            else:
                box = shop_marker(point, client, window)
                if box is None:
                    status = offscreen_notice = shop_offscreen_notice(point, client[2:])
                else:
                    preview = (hwnd, window[2:], box)
                    status = ('Shop aligned to entry portal' if aligned_portal else
                              'CC entry · first-frame preview' if cc_profile else
                              'Portal entry · CC profile unmeasured' if self._cc_entry_mode else 'Shop preview ready')

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

    def post_trade_event(self, event):
        # Called by the Windows hotkey thread. Tk dispatches virtual events on
        # the GUI thread; the normal pump also drains this FIFO as a fallback.
        if self._closing:return
        if not event[0].startswith('trade_'):
            self.events.put_nowait(event)
            return
        self._trade_events.put_nowait((time.perf_counter(),event))
        try:self.root.event_generate('<<FMRushTradeWake>>',when='tail')
        except (RuntimeError,tk.TclError):pass

    def drain_trade_events(self, _event=None):
        handled=set()
        if self._closing:return handled
        for _ in range(16):
            try:received,evt=self._trade_events.get_nowait()
            except queue.Empty:break
            action=evt[0]
            if action in ('trade_move_pointer','trade_move_channel'):
                # Never move a cursor long after its physical shortcut.
                if time.perf_counter()-received>.150:
                    recorder=getattr(self,'performance',None)
                    if recorder is not None:recorder.marker('pointer_expired')
                    self.status.set('Pointer shortcut expired · try again')
                    continue
                self.move_pointer_to_target('shop' if action=='trade_move_pointer' else 'channel',
                                            received=received)
            elif action=='trade_find':
                self._pointer_serial+=1
                self.align_shop_preview()
            elif action=='trade_next':
                self._pointer_serial+=1
                self.next_live_deal()
            elif action in ('trade_lock','trade_unlock'):
                self._pointer_serial+=1
                locked=action=='trade_lock'
                self.set_chase_locked(locked)
                handled.add(locked)
        if not self._trade_events.empty():self.schedule(0,self.drain_trade_events)
        return handled

    def move_pointer_to_shop(self):
        self.move_pointer_to_target('shop')

    def move_pointer_to_channel(self):
        self.move_pointer_to_target('channel')

    def _pointer_context(self, current, hwnd):
        if not current or not self.archive.chase_locked or not hwnd:return None
        deal=current[1]
        return (current[0], deal.cc, deal.fm, repr(deal.shop_position), deal.sold,
                hwnd, window_rect(hwnd), window_client_rect(hwnd), self._portal_alignment,
                getattr(self,'_cc_entry_mode',False))

    def move_pointer_to_target(self, kind, *, received=None):
        received=time.perf_counter() if received is None else received
        started=time.perf_counter()
        recorder=getattr(self,'performance',None)
        if not self.archive.lock.acquire(blocking=False):
            self.status.set('Pointer target updating · try again')
            return
        try:
            current=self.archive.current()
            locked=self.archive.chase_locked
        finally:self.archive.lock.release()
        if not current or not locked:
            self._pointer_serial+=1
            self._pointer_pending=None
            self.status.set('Lock a listing before moving the pointer')
            return
        pending=getattr(self,'_pointer_pending',None)
        if pending is not None:
            old_serial,old_kind,old_snapshot,deadline=pending
            if (old_serial==self._pointer_serial and kind==old_kind and started<deadline
                    and self._pointer_context(current,old_snapshot[5])==old_snapshot
                    and self.shop.selected_hwnd()==old_snapshot[5]):
                if recorder is not None:recorder.marker('pointer_duplicate',at=received,kind=kind)
                return
        self._pointer_serial+=1
        serial=self._pointer_serial
        self._pointer_pending=None
        if recorder is not None:recorder.marker('pointer_requested',at=received,kind=kind)
        # Refresh the scene gate once, while game focus is still intact.
        # Do not recompute/reset entrance or inventory state after focus loss.
        self.refresh_overlays(current)
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
            return
        hwnd,size,box=preview
        snapshot=self._pointer_context(current,hwnd)
        if snapshot is None or snapshot[6] is None or snapshot[7] is None or snapshot[6][2:]!=size:
            self.status.set('Game window changed. Try the shortcut again.')
            return
        # Capture a single validated box and recheck lock, listing, alignment,
        # and exact window/client geometry immediately before cursor movement.
        focus_started=None
        self._pointer_pending=(serial,kind,snapshot,min(received+.150,started+.085))
        def clear_pending():
            pending=getattr(self,'_pointer_pending',None)
            if pending is not None and pending[0]==serial:self._pointer_pending=None
        def fail(message,reason):
            clear_pending()
            if recorder is not None:
                recorder.marker('pointer_failure',kind=kind,reason=reason)
            self.status.set(message)
        def finish():
            if self._closing or serial!=self._pointer_serial:
                clear_pending()
                return
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
            finally:self.archive.lock.release()
            clear_pending()
            finished=time.perf_counter()
            dispatch_ms=(started-received)*1000
            total_ms=(finished-received)*1000
            focus_ms=0 if focus_started is None else (now-focus_started)*1000
            if recorder is not None:
                recorder.marker('pointer_result',at=finished,kind=kind,ok=not bool(problem),
                    total_ms=round(total_ms,1),queue_ms=round(dispatch_ms,1),focus_ms=round(focus_ms,1))
            message=problem or f'Pointer moved · {total_ms:.1f} ms (queue {dispatch_ms:.1f}, focus {focus_ms:.1f})'
            self.status.set(message)
            if not problem:
                self._watch_pointer(serial,kind,snapshot,box,finished,message)
        if window_has_focus(hwnd):
            if self.root.state() in ('iconic','withdrawn'):self.root.deiconify()
            focus_started=time.perf_counter()
            self.root.focus_force()
            # Check readiness instead of always sleeping 25 ms. The first
            # deferred check gives the game a chance to process focus loss.
            self.schedule(5,finish)
        else:finish()

    def _watch_pointer(self, serial, kind, snapshot, box, moved_at, message):
        """Read-only, bounded post-move observation; never reposition or click."""
        hwnd=snapshot[5]
        origin=snapshot[6]
        left,top,right,bottom=box
        bounds=(origin[0]+left,origin[1]+top,origin[0]+right,origin[1]+bottom)
        state={'focused':False,'drift':False,'samples':0,'max_drift':0.0}
        recorder=getattr(self,'performance',None)
        attempt=getattr(recorder,'active',None)
        def emit(event,**fields):
            if recorder is not None and getattr(recorder,'active',None)==attempt:
                recorder.marker(event,kind=kind,**fields)
        def status(text):
            # Never overwrite a newer scanner message.
            nonlocal message
            if self.status.get()==message:
                self.status.set(text)
                message=text
        def sample():
            if self._closing or serial!=self._pointer_serial:return
            now=time.perf_counter()
            elapsed=round((now-moved_at)*1000,1)
            if not self.archive.lock.acquire(blocking=False):return
            try:
                valid=(self.archive.chase_locked and self.archive.focus==snapshot[0])
            finally:self.archive.lock.release()
            if not valid or window_client_rect(hwnd)!=snapshot[7]:return
            # Shop confirmation is observed by existing inventory telemetry.
            # Once a new shop is visible, subsequent motion is not target drift.
            if getattr(self,'_item_preview',None) is not None:return
            pos=cursor_screen_position()
            focused=window_has_focus(hwnd)
            if pos is not None:
                state['samples']+=1
                x,y=pos;l,t,r,b=bounds
                dx=max(l-x,0,x-(r-1));dy=max(t-y,0,y-(b-1))
                drift=(dx*dx+dy*dy)**.5
                state['max_drift']=max(state['max_drift'],drift)
                if drift>0 and not state['drift']:
                    state['drift']=True
                    emit('pointer_displaced',elapsed_ms=elapsed,outside_px=round(drift,1),game_focused=focused)
                    status('Cursor left target · verify before retrying')
                if focused and not state['focused']:
                    state['focused']=True
                    emit('pointer_game_focus',elapsed_ms=elapsed,on_target=drift==0)
                    if drift==0 and not state['drift']:status('Game focused · pointer on target')
            if now-moved_at<.180:
                self.schedule(10,sample)
            else:
                emit('pointer_watch_complete',elapsed_ms=elapsed,focus_observed=state['focused'],
                     displaced=state['drift'],max_outside_px=round(state['max_drift'],1),samples=state['samples'])
                if not state['focused'] and not state['drift']:status('Pointer positioned · game focus not observed')
        self.schedule(10,sample)

    def align_shop_preview(self):
        current = self.archive.current()
        if not current or not self.archive.chase_locked or current[1].shop_position is None:
            return
        hwnd = None if self.web_only else self.shop.selected_hwnd()
        client = window_client_rect(hwnd) if hwnd else None
        portal = cursor_on_client(hwnd, client) if client and client[2:] in ENTRY_CLIENTS else None
        if portal is None:
            self.status.set('Hover over the bottom center of the FM doorway and press Ctrl+Alt+F')
            return
        self._portal_alignment = ((current[0], hwnd, client[2:]), portal)
        self.refresh_overlays(current)

    def follow_overlays(self):
        if self.archive.lock.acquire(blocking=False):
            try:current=self.archive.current()
            finally:self.archive.lock.release()
            self.refresh_overlays(current)
        self.schedule(50, self.follow_overlays)

    def toggle_chase(self):
        self.set_chase_locked(not self.archive.chase_locked)

    def set_chase_locked(self, locked):
        with self.archive.lock:
            if locked == self.archive.chase_locked:
                return
            if locked:
                current = self.archive.current()
                if current is None or not self.archive.choose(current[0]):
                    self.status.set('Waiting for a HeneFM deal to lock')
                    return
            else:
                self.archive.unlock()
        if locked:
            self.restore_chase_route()
        self.sync_archive()
        self.status.set('LOCKED · Shift+2 to unlock' if locked else 'ARMED · waiting for next new listing')

    def restore_chase_route(self):
        if self.manual_override_at is None:
            return
        self.manual_override_at=None
        current=self.archive.current()
        if current:
            _,deal=current
            if deal.cc is not None and deal.fm is not None:
                self.set_target(deal.cc,deal.fm,deal=deal,source='ARCHIVE')

    def undo_deal(self):
        self.archive.undo_complete();self.sync_archive()

    def complete_deal(self):
        self.performance.marker('skip_requested')
        current=self.archive.current()
        if current:self.archive.skip(current[0])
        self.sync_archive()
        self.status.set('Skipped · auto-lock armed for next new listing')

    def manual_go(self):
        raw=self.manual.get().strip()
        if not raw:return
        target=parse_alert(raw)
        if target is None:
            self.status.set('Enter CH 22 FM 13 or paste an HeneFM deal alert.')
            return
        # Navigation-only input is not a deal and never bypasses filter for deals.
        has_profit=('profit' in raw.casefold() or ('%' in raw and '+' in raw))
        if has_profit:
            deal=parse_deal(raw)
            if not deal or not deal.profit.accepted:
                self.status.set('Rejected: deal must be ≥15% AND ≥15,000 mesos profit.')
                return
            self.set_target(*target,deal=deal)
            self.status.set('ACCEPTED: '+deal.profit.label)
        else:
            self.set_target(*target)
            self.status.set('MANUAL NAV: '+self.ccfm.get())

    def poll_game_chase_shortcuts(self, handled):
        hwnd = None if self.web_only else self.shop.selected_hwnd()
        if hwnd is None or not window_has_focus(hwnd):
            self._chase_keys_down = None
            return
        shift_only, keys_down = chase_shortcut_state()
        previous = self._chase_keys_down
        self._chase_keys_down = keys_down
        if shift_only and previous is not None:
            for locked, down, was_down in zip((True, False), keys_down, previous):
                if down and not was_down and locked not in handled:
                    self.set_chase_locked(locked)

    def pump(self):
        handled=self.drain_trade_events()
        if self.archive.lock.acquire(blocking=False):
            try:changed=hasattr(self,'live_stamp') and self.live_stamp!=self.archive.live_state()
            finally:self.archive.lock.release()
            if changed:self.sync_archive()
        for _ in range(20):
            try:evt=self.events.get_nowait()
            except queue.Empty:break
            if evt[0]=='trade_next':
                self.next_live_deal()
            elif evt[0]=='trade_find':
                self.align_shop_preview()
            elif evt[0]=='trade_move_pointer':
                self.move_pointer_to_shop()
            elif evt[0]=='trade_move_channel':
                self.move_pointer_to_channel()
            elif evt[0] in ('trade_lock', 'trade_unlock'):
                locked = evt[0] == 'trade_lock'
                self.set_chase_locked(locked)
                handled.add(locked)
            elif evt[0]=='shop_pointer_shortcuts':
                shortcuts = evt[1]
                self.tools_menu.entryconfigure('Move pointer to shop',
                    accelerator=' / '.join(shortcuts) or 'Hotkeys unavailable')
                if 'Ctrl+Alt+M' not in shortcuts:
                    fallback = shortcuts[0] if shortcuts else 'Tools > Move pointer to shop'
                    self.status.set(f'Ctrl+Alt+M unavailable · use {fallback}')
            elif evt[0]=='browser_choice':
                action,key,session,revision,reply=evt[1:]
                versions=getattr(self,'choice_revisions',{})
                if revision<=versions.get(session,0):
                    reply.put({'ok':False,'error':'stale_choice'});continue
                versions[session]=revision
                if len(versions)>32:versions.pop(next(iter(versions)))
                self.choice_revisions=versions
                if action=='select':
                    if not self.archive.choose(key):
                        reply.put({'ok':False,'error':'LOCKED · click UNLOCK first, or listing completed'})
                        self.status.set('LOCKED · click UNLOCK first, or listing completed');continue
                    self.restore_chase_route()
                elif action=='unlock':self.archive.unlock()
                else:self.archive.skip(key)
                self.sync_archive()
                reply.put({'ok':True})
                self.status.set('LOCKED · UNLOCK to follow new listings' if self.archive.chase_locked else 'ARMED · waiting for next new listing')
            elif evt[0]=='browser_visible':
                # Feed generation already drives sync on the next tick.
                if self.archive.lock.acquire(blocking=False):
                    try:current=self.archive.current()
                    finally:self.archive.lock.release()
                    seller=current[1].ign if current else 'none'
                    self.status.set(f'LOCKED · {seller} · Shift+2 to unlock' if self.archive.chase_locked else 'ARMED · waiting for next new listing')
            elif evt[0]=='status':
                self.status.set(evt[1])
        self.poll_game_chase_shortcuts(handled)
        self.schedule(10 if not self.events.empty() or not self._trade_events.empty() or self._chase_keys_down is not None else 20, self.pump)

    def resume_first_listing(self):
        """Return to the top HeneFM card after 60s, unless CHASE is locked.

        Manual map/channel navigation is a temporary preview. The live feed
        continues to select the first pending card; this timer restores the
        displayed route even if the visible page has not changed.
        """
        if not self.archive.chase_locked:
            if self.manual_override_at is not None and time.monotonic()-self.manual_override_at>=60:
                self.manual_override_at=None
                self.displayed_listing=None  # force route / item / seller repaint
                self.archive.preview_latest()
                self.sync_archive()
            elif self.manual_override_at is None:
                previous=self.archive.focus
                self.archive.preview_latest()
                if self.archive.focus!=previous:self.sync_archive()
        self.schedule(1000,self.resume_first_listing)

    def work_area(self):
        if os.name=='nt':
            from ctypes import wintypes
            area=wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(48,0,ctypes.byref(area),0):
                return area.left,area.top,area.right,area.bottom
        return 0,0,self.root.winfo_screenwidth(),self.root.winfo_screenheight()-40

    def title_margin(self):
        return max(44,round(.46*self.root.winfo_fpixels('1i')))

    def place_window(self,window,default,saved=''):
        left,top,right,bottom=self.work_area()
        geometry=re.fullmatch(r'(\d+)x(\d+)([+-]\d+)([+-]\d+)',saved)
        width,height,x,y=map(int,geometry.groups()) if geometry else default
        min_width,min_height=window.minsize()
        width=min(max(width,min_width),right-left-12)
        height=min(max(height,min_height),bottom-top-self.title_margin()-8)
        x=max(left+4,min(x,right-width-8))
        y=max(top+4,min(y,bottom-height-self.title_margin()-4))
        window.geometry(f'{width}x{height}+{x}+{y}')

    def selected_game_rect(self):
        hwnd=self.shop.selected_hwnd()
        return window_rect(hwnd) if hwnd is not None else None

    def snap(self,restore=False):
        left,top,right,bottom=self.work_area()
        height=self.root.winfo_reqheight()
        margin=self.title_margin()
        game=self.selected_game_rect()
        width=min(900,right-left-12)
        x=left+8
        y=bottom-height-margin-6
        if game:
            gx,gy,gw,gh=game
            if gx<right and gx+gw>left:
                x=max(left+8,gx)
                width=min(width,right-x-8,gw)
                if gy+gh+height+margin+8<=bottom:
                    y=gy+gh+4
                elif gy-height-margin-8>=top:
                    y=gy-height-margin-4
        self.place_window(self.root,(width,height,x,y),self.conf['strip_geom'] if restore else '')

    def save(self):
        self.conf['strip_geom']=self.root.geometry()
        if self.grid is not None and self.grid.winfo_exists():self.conf['grid_geom']=self.grid.geometry()
        if self.map is not None and self.map.winfo_exists():self.conf['map_geom']=self.map.geometry()
        try:CONFIG.write_text(json.dumps(self.conf,indent=2),encoding='utf-8')
        except OSError:pass

    def close(self):
        if self._closing:return
        self._closing=True
        for job in list(self._pending_after):
            try:self.root.after_cancel(job)
            except Exception:pass
        self._pending_after.clear()
        self.save()
        if self.browser_bridge is not None:
            try:self.browser_bridge.stop()
            except Exception:pass
        self.channel_pin.close()
        self.shop_pin.close()
        self.entrance_pin.close()
        self.item_pin.close()
        self.performance.close()
        self._inventory.close()
        self._entrance_camera.close()
        self.archive.close()
        if hasattr(self,'trade_keys'):self.trade_keys.close()
        self.root.destroy()


if __name__=='__main__':
    FMApp().root.mainloop()

