"""FM Rush v24 — HeneFM browser deals + target-specific name finder.

The shop target comes from an accepted HeneFM browser deal or Discord alert. OCR of
MapleStory is HWND window capture, handled in memory; a click-through on-game marker, no recording or input injection.
"""
from __future__ import annotations
from cpu_guard import initialize as _init_cpu_guard
CPU_GUARD_MESSAGE = _init_cpu_guard()  # before NumPy / RapidOCR can import
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from window_capture import windows as list_game_windows, WindowFrames, window_rect
from multi_shop_worker import MultiShopWorker
from deal_archive import DealArchive
from channel_overlay import ChannelPin,locate_channel
from item_locator import IconTarget, ItemScanWorker, decode_reference, download_icon
from shop_pin import ItemPin
from trade_hotkeys import TradeHotkeys

from deal_parser import parse_deal
from henefm_bridge import BrowserBridge
from profit_filter import FILTER_LABEL
FILTER_LABEL = "BROWSER: ALL SHOWN LISTINGS · NO PROFIT FILTER"
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
    # Compatible with v11's `discord_region` and older versions' `region` keys.
    return {
        'version': 17,
        'start_channel': int(data.get('start_channel',START_CHANNEL)) if int(data.get('version',0)) >= 4 else START_CHANNEL,
        'discord_region':data.get('discord_region') or data.get('region'),
        'strip_geom':data.get('strip_geom',''),
        'grid_geom':data.get('grid_geom',''),
        'map_geom':data.get('map_geom',''),
        'topmost':bool(data.get('topmost',True)),
    }


def get_ocr():
    # Prefer a persistent RapidOCR instance to avoid launching Tesseract per frame.
    try:
        from rapidocr import RapidOCR
        import numpy as np
        from PIL import Image, ImageDraw
        engine=RapidOCR()
        warm=Image.new('RGB',(330,80),'white')
        ImageDraw.Draw(warm).text((12,20),'CH 22 FM 13 sample',fill='black')
        engine(np.asarray(warm)[:,:,::-1].copy(),use_cls=False)
        def read(img):
            result=engine(np.asarray(img)[:,:,::-1].copy(),use_cls=False)
            return '\n'.join(result.txts or ())
        return read
    except Exception:
        pass
    try:
        import pytesseract
        from PIL import ImageOps
        for path in [os.environ.get('TESSERACT_PATH',''),
                     r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                     r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe']:
            if path and Path(path).is_file():
                pytesseract.pytesseract.tesseract_cmd=path
                break
        pytesseract.get_tesseract_version()
        return lambda im: pytesseract.image_to_string(ImageOps.autocontrast(ImageOps.grayscale(im)), config='--psm 6')
    except Exception:
        return None


class DiscordWatcher(threading.Thread):
    def __init__(self, get_region, out, stop):
        super().__init__(daemon=True)
        self.get_region=get_region; self.out=out; self.stop=stop

    def run(self):
        ocr=get_ocr()
        if ocr is None:
            self.out.put(('status','OCR missing. Run START_FM_RUSH.bat to install dependencies.'))
            return
        try:
            from PIL import Image
            from mss import mss
            previous_fp=None
            last_accepted_fp=None
            last_ocr_at=0.0
            with mss() as capturer:
                while not self.stop.is_set():
                    rect=self.get_region()
                    if not rect:
                        self.stop.wait(.08);continue
                    try:
                        tick=time.perf_counter()
                        raw=capturer.grab(rect)
                        img=Image.frombytes('RGB',raw.size,raw.rgb)
                        fp=hash(img.resize((80,32),Image.Resampling.BILINEAR).tobytes())
                        # Changed alert is read immediately; retry a missed OCR
                        # briefly without re-alerting for unchanged accepted text.
                        if tick-last_ocr_at >= .30 and (fp!=previous_fp or (fp!=last_accepted_fp and tick-last_ocr_at>1.0)):
                            previous_fp=fp;last_ocr_at=tick
                            txt=ocr(img)
                            deal=parse_deal(txt)
                            if deal and deal.profit.accepted and fp != last_accepted_fp:
                                last_accepted_fp=fp
                                self.out.put(('deal',deal,round((time.perf_counter()-tick)*1000,1)))
                        self.stop.wait(.05)
                    except Exception as exc:
                        self.out.put(('status','Discord capture: '+str(exc)[:90]))
                        self.stop.wait(.35)
        except Exception as exc:
            self.out.put(('status','Discord watcher failed: '+str(exc)[:90]))


class SelectRegion(tk.Toplevel):
    def __init__(self, app):
        from PIL import Image, ImageTk
        from mss import mss
        self.app=app
        app._picker_windows=[window for window in (app.root,app.grid,app.map)
                             if window is not None and window.winfo_exists() and window.state()=='normal']
        for window in app._picker_windows:
            window.withdraw()
        app.root.update()
        time.sleep(.16)
        try:
            with mss() as sct:
                monitor=sct.monitors[0]
                raw=sct.grab(monitor)
            picture=Image.frombytes('RGB',raw.size,raw.rgb)
        except Exception:
            app.restore_windows()
            raise
        super().__init__(app.root)
        self.mon=monitor;self.start=None;self.current=None
        self.overrideredirect(True)
        self.attributes('-topmost',True)
        self.geometry(f'{picture.width}x{picture.height}{monitor["left"]:+d}{monitor["top"]:+d}')
        self.photo=ImageTk.PhotoImage(picture)
        self.canvas=tk.Canvas(self,highlightthickness=0,cursor='crosshair')
        self.canvas.pack(fill='both',expand=True)
        self.canvas.create_image(0,0,anchor='nw',image=self.photo)
        self.canvas.create_rectangle(4,4,900,50,fill=BG,outline=TEAL,width=2)
        self.canvas.create_text(16,26,anchor='w',text='DRAG ONLY OVER HENEFM ALERT TEXT  •  ESC TO CANCEL',fill=FG,font=('Segoe UI',17,'bold'))
        self.canvas.bind('<ButtonPress-1>',self.down)
        self.canvas.bind('<B1-Motion>',self.move)
        self.canvas.bind('<ButtonRelease-1>',self.up)
        self.bind('<Escape>',lambda _:self.finish())
        self.focus_force()

    def down(self,e):
        self.start=(e.x,e.y)
        if self.current:self.canvas.delete(self.current)
        self.current=self.canvas.create_rectangle(e.x,e.y,e.x,e.y,outline=YELLOW,width=4)

    def move(self,e):
        if self.start:self.canvas.coords(self.current,*self.start,e.x,e.y)

    def up(self,e):
        if self.start:
            x0,y0=self.start;x1,y1=e.x,e.y
            w=abs(x1-x0);h=abs(y1-y0)
            if w>60 and h>30:
                self.app.conf['discord_region']={
                    'left':self.mon['left']+min(x0,x1),
                    'top':self.mon['top']+min(y0,y1),
                    'width':w,'height':h}
                self.app.status.set(f'Discord region saved: {w}×{h}. Open Tools > Discord > Start OCR.')
                self.app.save()
        self.finish()

    def finish(self):
        self.destroy()
        self.app.restore_windows()


class ShopHighlighter:
    """Own the game-window picker and the in-game seller marker."""
    def __init__(self,app):
        from shop_pin import ShopPin
        self.app=app
        self.last_size=None
        self.last_box=None
        self.last_name=''
        self.last_item=''
        self.last_mode='SEARCHING'
        self.notice=tk.StringVar(value='Select a MapleStory window.')
        self.pin=ShopPin(app.root)
        self.matches={}
        self.chosen=tk.StringVar()
        self.available=[]

    def add_controls(self,parent):
        self.combo=ttk.Combobox(parent,textvariable=self.chosen,state='readonly',width=23)
        self.combo.bind('<<ComboboxSelected>>',self.change_window)
        self.start_btn=self.app.btn(parent,'Start locator',self.app.toggle_shop_scan,True)
        self.refresh_windows()
        if not self.app.web_only:
            self.combo.pack(side='left',padx=(0,3))
            self.app.btn(parent,'Refresh',self.refresh_windows).pack(side='left',padx=(0,3))
            self.start_btn.pack(side='left',padx=(0,8))

    def refresh_matches(self,names):
        live={name.casefold() for name in names}
        self.matches={name:hit for name,hit in self.matches.items()
                      if name.casefold()==self.last_name.casefold()
                      and (name.casefold() in live or time.monotonic()<hit.get('hold_until',0))}
        if self.last_size and self.app.shop_running:
            self.pin.show_many(self.selected_hwnd(),self.last_size,self.matches)

    def draw_matches(self,size,hits,note):
        self.last_size=size;self.matches={name:{**hit,'item':self.last_item} for name,hit in hits.items()}
        self.pin.show_many(self.selected_hwnd(),size,self.matches)
        if note:self.notice.set(note)

    def change_window(self,event=None):
        self.pin.hide()
        if self.app.shop_running:
            self.app.stop_shop_scan()
            self.app.start_shop_scan()

    def refresh_windows(self):
        current=self.chosen.get()
        old_hwnd=self.selected_hwnd()
        self.available=list_game_windows()
        labels=[f'{title}  [HWND {hwnd}]' for hwnd,title in self.available]
        self.combo['values']=labels
        if current in labels:return
        candidate=next((i for i,(hwnd,title) in enumerate(self.available)
                        if 'maplestory' in title.lower() or 'maple story' in title.lower()),
                       0 if self.available else -1)
        if candidate>=0:self.combo.current(candidate)
        else:self.chosen.set('')
        if self.selected_hwnd()!=old_hwnd:
            self.change_window()

    def selected_hwnd(self):
        index=self.combo.current()
        if 0<=index<len(self.available):
            return self.available[index][0]
        return None


    def set_target(self,name,force=False,item=''):
        if force or name.casefold()!=self.last_name.casefold():
            self.last_size=None;self.last_box=None
            self.last_mode='SEARCHING';self.matches.clear();self.pin.hide()
        self.last_name=name
        self.last_item=item or ''
        self.notice.set('Looking for '+name if name else 'A marker will appear over the matching name in MapleStory.')

    def draw(self,image,source_size,box,mode,seen_text,latency_ms,method):
        self.last_size=source_size;self.last_box=box;self.last_mode=mode
        if box is None:
            self.pin.hide()
            self.notice.set(f'No confident match · {latency_ms:.0f} ms · '+
                            ('retrying automatically' if mode=='RETRYING' else 'press FIND AGAIN or change room'))
        else:
            likely=mode!='FOUND'
            self.notice.set(f'{"CHECK NAME" if likely else "FOUND"} · {latency_ms:.0f} ms · marked in game'+(f' · read: {seen_text}' if likely else ''))
            self.pin.show(self.selected_hwnd(),source_size,box,self.last_name,likely,item=self.last_item)

class FMApp:
    def __init__(self):
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:pass
        self.conf=settings()
        self.web_only=os.environ.get('FM_RUSH_WEB_ONLY') == '1'
        self.root=tk.Tk()
        self.root.title('FM Rush v24.36')
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
        self.status=tk.StringVar(value='LIVE · first visible HeneFM listing')
        self.chase_label=tk.StringVar(value='LIVE · CHASE TO LOCK')
        self.manual=tk.StringVar(value='CC 22 FM 13')
        self.events=queue.Queue()
        self.worker=None
        self.browser_bridge=None
        self.stop=threading.Event()
        self.running=False
        self.grid=None
        self.map=None
        self.shop_frames=None
        self.shop_thread=None
        self.shop_stop=threading.Event()
        self.shop_running=False
        self.shop_target=''
        self.shop_generation=0
        self.shop_session=0
        self.scan_names=()
        self.scan_revisions={}
        self.scan_by_room={}
        self.shop_paused=False
        self.displayed_listing=None
        self.archive=DealArchive(ARCHIVE_DIR/'deal_archive.sqlite3',manual_selection=True)
        self.manual_override_at=None
        self.latency_history=[]
        self.shop_events=queue.Queue(maxsize=32)
        self._pending_after=set()
        self._closing=False
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.channel_pin=ChannelPin(self.root)
        self.item_pin=ItemPin(self.root)
        self.item_reference=IconTarget()
        self.item_thread=None
        self.item_status=tk.StringVar(value='ITEM ICON: waiting for HeneFM image')
        self.item_web_status='ITEM ICON: waiting for HeneFM image'
        self.channel_frame_version=None
        self._channel_scan_results=queue.Queue(maxsize=1)
        self._channel_scan_inflight=False
        self._channel_scan_due=0.
        self._channel_visible_token=None
        self.shop=ShopHighlighter(self)
        self._make_bottom()
        self.root.update_idletasks()
        self.root.minsize(max(640,self.control_bar.winfo_reqwidth()+24),self.root.winfo_reqheight())
        self.snap(restore=True)
        self.sync_archive()
        self.schedule(35,self.pump)
        self.schedule(50,self.update_channel_overlay)
        try:
            self.browser_bridge=BrowserBridge(self.events,self.archive,state_provider=self.svg_route_view)
            self.browser_bridge.start()
            self.status.set('LIVE · following the newest HeneFM listing')
        except OSError as exc:
            self.status.set('HeneFM bridge not available: '+str(exc)[:100]+' • Discord OCR still works')
        if not self.web_only:self.schedule(0,self.try_start_shop)
        self.trade_keys=TradeHotkeys(self.events.put_nowait);self.trade_keys.start()
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
        self.lbl(details,var=self.keys,size=13,color=MUTED).grid(row=1,column=0,sticky='w')
        tk.Frame(details,bg=CARD2,width=1).grid(row=0,column=1,rowspan=3,sticky='ns',padx=12)
        self.lbl(details,var=self.ign,size=12,color=YELLOW,bold=True).grid(row=0,column=2,sticky='ew')
        self.lbl(details,var=self.item,size=12,color=YELLOW,bold=True).grid(row=1,column=2,sticky='ew')
        self.lbl(details,var=self.stats,size=9,color=MUTED).grid(row=2,column=2,sticky='ew')
        self.lbl(details,var=self.buy,size=13,color=YELLOW,bold=True).grid(row=0,column=3,sticky='e',padx=(8,0))
        self.lbl(details,var=self.profit,size=10,color=TEAL).grid(row=1,column=3,sticky='e',padx=(8,0))

        controls=self.control_bar=tk.Frame(self.root,bg=BG)
        controls.pack(fill='x',padx=12,pady=(4,0))
        self.shop.add_controls(controls)
        self.btn(controls,'Skip',self.complete_deal).pack(side='left')
        tk.Button(controls,textvariable=self.chase_label,command=self.toggle_chase,bg=YELLOW,fg=BG,relief='flat').pack(side='left',padx=4)
        if not self.web_only:
            self.btn(controls,'Find again',self.retry_shop_once).pack(side='left',padx=4)
        tools=tk.Menubutton(controls,text='Tools ▾',relief='flat',bg=CARD2,fg=FG,padx=8,pady=4)
        menu=tk.Menu(tools,tearoff=False)
        tools.configure(menu=menu)
        for title,action in [('Place under game',self.snap),('Enter route',self.enter_route),
                             ('Channel grid',self.open_grid),('FM map',self.open_map),
                             ('SVG Map',self.open_svg_map),
                             ('Export scanner timing',self.export_latency),
                             ('Export deal archive',self.export_archive),
                             ('Reopen last skipped deal',self.undo_deal)]:
            menu.add_command(label=title,command=action)
        if not self.web_only:
            menu.add_separator()
            menu.add_command(label='Start or pause locator',command=self.toggle_shop_scan)
            self.ocr_menu=tk.Menu(menu,tearoff=False)
            self.ocr_menu.add_command(label='Choose alert area',command=self.pick_discord)
            self.ocr_menu.add_command(label='Start OCR',command=self.toggle_discord)
            self.ocr_menu_index=self.ocr_menu.index('end')
            menu.add_cascade(label='Discord',menu=self.ocr_menu)
        tools.pack(side='right')

        footer=tk.Frame(self.root,bg=BG)
        footer.pack(fill='x',padx=12,pady=(2,3))
        footer.columnconfigure(0,weight=3,uniform='status')
        footer.columnconfigure(1,weight=2,uniform='status')
        status=self.lbl(footer,var=self.status,size=9,color=MUTED)
        status.configure(width=1)
        status.grid(row=0,column=0,sticky='ew',padx=(0,12))
        scanner_status=self.lbl(footer,var=self.shop.notice,size=9,color=MUTED)
        scanner_status.configure(width=1,anchor='e')
        scanner_status.grid(row=0,column=1,sticky='ew')

    def set_item_status(self, message):
        self.item_web_status=str(message)
        self.item_status.set(message)

    def svg_route_view(self):
        """Plain Python attributes only. Called from the HTTP server thread."""
        return {
            'cc': self.current_cc, 'fm': self.current_fm,
            'manual_override_at': self.manual_override_at,
            'start_channel': self.conf['start_channel'],
            'item_detection': self.item_web_status,
        }

    def open_svg_map(self):
        """SVG runs in a real browser; OCR and the Tk map remain untouched."""
        if self.browser_bridge is None or self.browser_bridge.server is None:
            self.status.set('SVG map needs the local bridge on port 18773');return
        webbrowser.open('http://127.0.0.1:18773/fm-map')
        self.status.set('Live SVG map opened · follows first listing / CHASE / manual preview')

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
        c=self.grid_canvas;c.delete('all')
        W=max(230,c.winfo_width());H=max(135,c.winfo_height())
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
        tk.Button(self.map,textvariable=self.chase_label,command=self.toggle_chase,bg=YELLOW,fg=BG,relief='flat').pack(anchor='w',padx=10)
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
        c=self.map_canvas;c.delete('all')
        sx,sy=self._scale_map()
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
        if deal is not None and source in ('WEB','DISCORD'):
            self.archive.record(deal);self.sync_archive();return
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
        # Receipt runs on HTTP threads: take one consistent UI/search snapshot.
        with self.archive.lock:
            # Default always follows the first *visible, pending* listing.
            # A deliberate CHASE/LOCK overrides this until UNLOCK.
            if not self.archive.chase_locked:self.archive.preview_latest()
            live_rows=self.archive.live_pending()
            names=self.archive.selected_names()
            available_names=self.archive.live_names()
            current=self.archive.current()
            self.live_stamp=self.archive.live_state()
        revisions={}
        for key,deal in live_rows:revisions.setdefault(deal['ign'].casefold(),[]).append(key)
        self.scan_revisions={name:tuple(keys) for name,keys in revisions.items()}
        previous_names=self.scan_names
        self.scan_names=names
        if names and names!=previous_names:
            worker=getattr(self,'shop_thread',None)
            if worker is not None and worker.is_alive():worker.selection_check.set()
        if names and not getattr(self,'live_started',False):
            self.live_started=True
            worker=getattr(self,'shop_thread',None)
            if worker is not None and worker.is_alive():worker.entry_check.set()
        grouped={}
        for _,deal in live_rows:grouped.setdefault(deal['fm'],[]).append(deal['ign'])
        self.scan_by_room={room:tuple(dict.fromkeys(values)) for room,values in grouped.items()}
        self.chase_label.set('LOCKED · UNLOCK' if self.archive.chase_locked else 'LIVE · CHASE TO LOCK')
        key,deal=current if current else (None,None)
        if key!=self.displayed_listing:
            self.displayed_listing=key
            self.item_reference.clear(deal.listing_id if deal is not None else '')
            self.item_pin.hide()
            self.set_item_status('ITEM ICON: waiting for HeneFM image' if deal else 'ITEM ICON: no selected listing')
            if deal is not None:
                if deal.cc is not None and deal.fm is not None:
                    self.set_target(deal.cc,deal.fm,deal=deal,source='ARCHIVE')
                else:
                    self.ign.set('IGN: '+deal.ign);self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
                    self.stats.set('STATS: '+deal.stats);self.profit.set(deal.profit.label)
                    self.buy.set(deal.buy_label);self.ccfm.set('CH / FM: not shown')
                self.accepted_ign(deal.ign,deal.item)
                self.open_map()
            else:
                self.accepted_ign('','')
                self.ccfm.set('Choose a deal');self.keys.set('')
                self.ign.set('IGN: —');self.item.set('ITEM: —');self.stats.set('STATS: —')
                self.buy.set('BUY AT: —');self.profit.set('PROFIT: —')
        elif deal is not None:
            self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
            self.profit.set(deal.profit.label)
            self.shop.last_item=deal.item
        if self.map is not None and self.map.winfo_exists():self.draw_map()
        self.shop.refresh_matches(available_names)

    def export_archive(self):
        path=filedialog.asksaveasfilename(title='Export listings grouped by seller IGN',
            defaultextension='.json',initialfile='FM_Rush_IGN_Archive.json',filetypes=[('JSON archive','*.json')])
        if path:
            try:self.archive.export_json(path);self.status.set('Archive saved: '+path)
            except OSError as exc:messagebox.showerror('Archive export',str(exc))

    def next_live_deal(self):
        # The hotkey skips; accepting the next deal always requires a choice.
        self.complete_deal()

    def update_channel_overlay(self):
        """Never run channel-menu template matching on Tk's UI thread.

        Previously a full 1080p match could consume an entire 50 ms UI tick,
        starving overlay updates and the browser bridge. One daemon worker
        uses the latest image every ~220 ms; old sessions are ignored.
        """
        if self._closing:return
        current=self.archive.current()
        frames=self.shop_frames
        token=(self.shop_session,current[0],self.current_cc) if self.shop_running and current and frames else None
        if token!=self._channel_visible_token:
            self.channel_pin.hide()
            self._channel_visible_token=token
        latest=None
        while True:
            try:latest=self._channel_scan_results.get_nowait()
            except queue.Empty:break
        if latest is not None and token is not None and latest[0]==token:
            _,box,size=latest
            if box:
                self.channel_pin.show_many(self.shop.selected_hwnd(),size,
                    {'CH '+str(self.current_cc):{'box':box,'mode':'EXACT'}})
            else:
                # Keep immediate destination visible; a missing menu is NOT a
                # failed channel selection. The menu cell is highlighted when
                # the menu locator subsequently sees the open panel.
                if frames is not None:
                    snap=frames.peek(-1)
                    if snap is not None:
                        _,_,img=snap;h,w=img.shape[:2]
                        self.channel_pin.show_many(self.shop.selected_hwnd(),(w,h),
                            {'TARGET CH '+str(self.current_cc):{'box':(max(5,w-270),10,w-10,48),'mode':'PRE'}})
        if token is not None and latest is None and self.channel_pin.data is None:
            snap=frames.peek(-1)
            if snap is not None:
                _,_,img=snap;h,w=img.shape[:2]
                self.channel_pin.show_many(self.shop.selected_hwnd(),(w,h),
                    {'TARGET CH '+str(self.current_cc):{'box':(max(5,w-270),10,w-10,48),'mode':'PRE'}})
        if token is None:
            self.channel_frame_version=None
        elif not self._channel_scan_inflight and time.monotonic()>=self._channel_scan_due:
            frame=frames.peek(-1)
            if frame is not None:
                version,stamp,image=frame
                frame_token=(token,version)
                if frame_token!=self.channel_frame_version:
                    self.channel_frame_version=frame_token
                    self._channel_scan_due=time.monotonic()+.10
                    self._channel_scan_inflight=True
                    channel=self.current_cc
                    size=(image.shape[1],image.shape[0])
                    def locate():
                        try:box=locate_channel(image,channel)
                        except Exception:box=None
                        try:self._channel_scan_results.put_nowait((token,box,size))
                        except queue.Full:
                            try:self._channel_scan_results.get_nowait()
                            except queue.Empty:pass
                            try:self._channel_scan_results.put_nowait((token,box,size))
                            except queue.Full:pass
                        finally:self._channel_scan_inflight=False
                    threading.Thread(target=locate,daemon=True,name='FM-ChannelLocator').start()
        self.schedule(50,self.update_channel_overlay)

    def export_latency(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='FM_Rush_Scan_Timings.json')
        if path:
            Path(path).write_text(json.dumps({'scope':'Local page delivery and software room-entry stages; excludes HeneFM server freshness, human travel and compositor display latency.',
                'live_names':list(self.scan_names),'selected_ign':self.shop_target,
                'capture_hwnd':self.shop.selected_hwnd(),
                'capture_error':getattr(self.shop_frames,'error',''),
                'status':self.shop.notice.get(),
                'cpu_guard':CPU_GUARD_MESSAGE,'latest':self.latency_history},indent=2)+'\n',encoding='utf-8')

    def toggle_chase(self):
        if self.archive.chase_locked:
            self.archive.unlock()
        else:
            current=self.archive.current()
            if current:self.archive.choose(current[0])
        self.sync_archive()
        self.status.set('LOCKED · incoming listings cannot replace this target' if self.archive.chase_locked else 'LIVE · first listing restored')

    def undo_deal(self):
        self.archive.undo_complete();self.sync_archive()

    def complete_deal(self):
        current=self.archive.current()
        if current:self.archive.skip(current[0])
        self.sync_archive()
        self.status.set('Skipped · click a HeneFM listing to chase')

    def accepted_ign(self, name, item=''):
        # The selected seller and item update together on every automatic preview.
        name=(name or '').strip()
        self.shop_target=name
        self.shop_generation+=1
        self.shop.set_target(name,item=item)
        worker=getattr(self,'shop_thread',None)
        self.shop.matches.clear()
        self.shop.pin.hide()
        if worker is not None and worker.is_alive():worker.prioritize(name)
        if name and not self.shop_running and not self.web_only and not getattr(self,'shop_paused',False):
            self.schedule(0,self.try_start_shop)

    def try_start_shop(self):
        if self.shop_running or self.shop_paused:return
        index=self.shop.combo.current()
        if index>=0 and any(value in self.shop.available[index][1].lower() for value in ('maplestory','maple story')):
            self.start_shop_scan()
        else:
            self.shop.notice.set('Open MapleStory, then click Refresh.')

    def _post_shop(self, item):
        # Each multi-seller result is a complete marker snapshot, so coalescing is safe.
        try:
            self.shop_events.put_nowait(item)
        except queue.Full:
            try:self.shop_events.get_nowait()
            except queue.Empty:pass
            try:self.shop_events.put_nowait(item)
            except queue.Full:pass

    def start_shop_scan(self):
        if self.shop_running:return
        if self.web_only:
            self.status.set('WEB-ONLY MODE · shop OCR disabled. Run START_FM_RUSH.bat to enable shop scanning.')
            return
        hwnd=self.shop.selected_hwnd()
        if hwnd is None:
            self.shop.notice.set('Select MapleStory, then click Start locator.')
            return
        self.shop_stop=threading.Event()
        self.shop_session+=1
        session=self.shop_session
        try:
            self.shop_frames=WindowFrames(hwnd, interval_ms=16)
            self.shop_frames.start()
            self.shop_thread=MultiShopWorker(self.shop_frames,lambda:self.scan_names,
                                             lambda item:self._post_shop(('shop_epoch',session,item)),
                                             self.shop_stop,lambda:self.scan_revisions,self.names_for_room,
                                             lambda:(self.shop_target,self.current_fm),single_target=True)
            if self.shop_target:self.shop_thread.prioritize(self.shop_target)
            self.shop_thread.start()
            self.item_thread=ItemScanWorker(self.shop_frames,self.item_reference,
                lambda item:self._post_shop(('shop_epoch',session,item)),self.shop_stop)
            self.item_thread.start()
        except Exception as exc:
            if self.shop_frames:
                try:self.shop_frames.stop()
                except Exception:pass
            self.shop_frames=None
            self.shop.notice.set('Window capture failed: '+str(exc)[:150])
            return
        self.shop_running=True
        self.shop.start_btn.config(text='Pause locator',bg=RED)
        self.shop.notice.set('Preparing name finder…')

    def names_for_room(self,room):
        values=self.scan_by_room.get(room,())+self.scan_by_room.get(None,())
        return tuple(dict.fromkeys(values))

    def retry_shop_once(self):
        if self.shop_thread is not None and self.shop_thread.is_alive():
            self.shop_thread.retry.set()

    def toggle_shop_scan(self):
        self.shop_paused=self.shop_running
        if self.shop_running:self.stop_shop_scan()
        else:self.start_shop_scan()

    def stop_shop_scan(self):
        self.shop_session+=1
        self.shop_stop.set()
        if self.shop_frames is not None:
            try:self.shop_frames.stop()
            except Exception:pass
        self.shop_frames=None
        self.shop_running=False
        self.item_pin.hide()
        self.shop.start_btn.config(text='Start locator',bg=TEAL)
        self.shop.matches.clear()
        self.shop.last_size=None
        self.shop.pin.hide()

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

    def pick_discord(self):
        if self.running:self.toggle_discord()
        try:SelectRegion(self)
        except Exception as exc:
            self.restore_windows()
            self.status.set('Region picker failed: '+str(exc)[:100])

    def restore_windows(self):
        for window in getattr(self,'_picker_windows',[self.root]):
            if window.winfo_exists():window.deiconify()
        self._picker_windows=[]

    def toggle_discord(self):
        if self.running:
            self.stop.set();self.running=False
            self.ocr_menu.entryconfigure(self.ocr_menu_index,label='Start OCR')
            self.status.set('Discord OCR stopped.')
            return
        if not self.conf['discord_region']:
            self.status.set('Open Tools > Discord > Choose alert area first.')
            return
        self.stop=threading.Event()
        self.worker=DiscordWatcher(lambda:self.conf['discord_region'],self.events,self.stop)
        self.worker.start();self.running=True
        self.ocr_menu.entryconfigure(self.ocr_menu_index,label='Stop OCR')
        self.status.set('DISCORD: ≥15,000 MESOS AND ≥15% · WATCHING')

    def pump(self):
        if hasattr(self,'live_stamp') and self.live_stamp!=self.archive.live_state():self.sync_archive()
        for _ in range(20):
            try:evt=self.events.get_nowait()
            except queue.Empty:break
            if evt[0]=='trade_next':
                self.next_live_deal()
            elif evt[0]=='trade_find':
                self.retry_shop_once()
            elif evt[0]=='svg_action':
                action,data,reply=evt[1:]
                try:
                    if action=='select':
                        if not self.archive.choose(data['id']):
                            reply.put({'ok':False,'error':'Locked or listing not available'});continue
                        self.manual_override_at=None
                        self.sync_archive()
                        self.retry_shop_once()
                    elif action=='unlock':
                        self.archive.unlock()
                        self.manual_override_at=None
                        self.sync_archive()
                    elif action=='target':
                        if self.archive.chase_locked:
                            reply.put({'ok':False,'error':'UNLOCK before manual navigation'});continue
                        self.set_target(data['cc'],data['fm'],keep_deal=True,source='MANUAL')
                    else:
                        reply.put({'ok':False,'error':'unknown_action'});continue
                    reply.put({'ok':True})
                except (OSError,ValueError,TypeError) as exc:
                    reply.put({'ok':False,'error':str(exc)[:120]})
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
                elif action=='unlock':self.archive.unlock()
                else:self.archive.skip(key)
                self.sync_archive()
                if action=='select':self.retry_shop_once()
                reply.put({'ok':True})
                self.status.set('LOCKED · UNLOCK to follow new listings' if self.archive.chase_locked else 'LIVE · following first listing')
            elif evt[0]=='browser_item_icon':
                listing_id,png,url=evt[1:]
                current=self.archive.current()
                if current and current[1].listing_id==listing_id:
                    icon=decode_reference(listing_id,current[1].item,png) if png else None
                    if icon and self.item_reference.install(icon):
                        self.set_item_status('ITEM ICON: ready · matching visible shop art, stats not verified')
                    elif url:
                        self.set_item_status('ITEM ICON: fetching HeneFM item art in advance…')
                        item=current[1].item
                        def fetch_icon():
                            encoded=download_icon(url)
                            self.events.put(('item_icon_loaded',listing_id,item,encoded))
                        threading.Thread(target=fetch_icon,daemon=True,name='FM-HeneFM-Item-Icon').start()
                    else:
                        self.set_item_status('ITEM ICON: reference unavailable · cannot confirm item')
            elif evt[0]=='item_icon_loaded':
                listing_id,item,encoded=evt[1:]
                current=self.archive.current()
                if current and current[1].listing_id==listing_id and current[1].item==item:
                    icon=decode_reference(listing_id,item,encoded) if encoded else None
                    if icon and self.item_reference.install(icon):
                        self.set_item_status('ITEM ICON: ready · matching visible shop art, stats not verified')
                    else:
                        self.set_item_status('ITEM ICON: HeneFM image unavailable · no confirmed item match')
            elif evt[0]=='browser_visible':
                self.sync_archive()
                self.status.set(f'{len(self.archive.live_pending())} HeneFM listings available · selected: {self.shop_target or "none"}')
            elif evt[0]=='browser_deal':
                deal=evt[1]
                if deal.profit.accepted:
                    self.set_target(deal.cc,deal.fm,deal=deal,source='WEB')
                    self.status.set(f'{len(self.archive.live_pending())} listings available · click one on HeneFM to chase')
            elif evt[0]=='deal':
                deal,ms=evt[1],evt[2]
                # Defense-in-depth: checked in watcher and UI, never show low-profit deals.
                if deal.profit.accepted:
                    self.set_target(deal.cc,deal.fm,deal=deal,source='DISCORD')
                    self.status.set(f'ACCEPTED • DISCORD OCR {ms:.0f} ms • ≥15,000 MESOS AND ≥15%')
                    try:self.root.bell()
                    except Exception:pass
            elif evt[0]=='status':
                self.status.set(evt[1])
        for _ in range(24):
            try:evt=self.shop_events.get_nowait()
            except queue.Empty:break
            if evt[0]=='shop_epoch':
                if evt[1]!=self.shop_session:continue
                evt=evt[2]
            if evt[0]=='shops_frame':
                if self.shop_running:
                    _,size,hits,note=evt
                    hits={name:hit for name,hit in hits.items() if name.casefold()==self.shop_target.casefold() and (name in self.scan_names or
                          time.monotonic()<hit.get('hold_until',0))}
                    self.shop.draw_matches(size,hits,note)
            elif evt[0]=='shop_frame':
                _,key,image,source_size,box,mode,seen,latency,method=evt
                if key==(self.shop_target,self.shop_generation):
                    self.shop.draw(image,source_size,box,mode,seen,latency,method)
            elif evt[0]=='shop_clear':
                if evt[1]==(self.shop_target,self.shop_generation):
                    self.shop.set_target(self.shop_target,force=True)
            elif evt[0]=='item_found':
                revision,listing_id,size,hits,scan_ms=evt[1:]
                selected=self.archive.current()
                if (self.shop_running and selected and selected[1].listing_id==listing_id and
                        self.item_reference.snapshot()[1]==revision):
                    self.item_pin.show_many(self.shop.selected_hwnd(),size,
                        {str(i):hit for i,hit in enumerate(hits)})
                    self.set_item_status(
                        f'ITEM ICON: {len(hits)} visual candidate(s) · {scan_ms:.1f} ms matching · CHECK STATS/PRICE'
                        if hits else f'ITEM ICON: looking in opened shop · {scan_ms:.1f} ms matching')
                else:
                    self.item_pin.hide()
            elif evt[0]=='item_scan_error':
                self.set_item_status('ITEM SCAN ERROR: '+evt[1])
            elif evt[0]=='shop_timing':
                timing={**evt[1]}
                timing['result_to_ui_queue_ms']=round(max(0,time.monotonic()-timing.pop('posted_at'))*1000,1)
                timing['burst_to_ui_request_ms']=round(timing['burst_to_result_ms']+timing['result_to_ui_queue_ms'],1)
                if timing.get('first_readable_to_result_ms') is not None:
                    timing['first_readable_to_ui_queue_ms']=round(
                        timing['first_readable_to_result_ms']+timing['result_to_ui_queue_ms'],1)
                timing['local_page_to_app_ms']=getattr(self.archive,'last_feed_latency_ms',None)
                self.latency_history.append(timing);self.latency_history=self.latency_history[-200:]
            elif evt[0]=='shop_note':
                if self.shop_running:
                    self.shop.notice.set(evt[1])
        self.schedule(5 if self.shop_running and self.scan_names else 10,self.pump)

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
        self.stop.set()
        self.shop_stop.set()
        for job in list(self._pending_after):
            try:self.root.after_cancel(job)
            except Exception:pass
        self._pending_after.clear()
        self.save()
        if self.browser_bridge is not None:
            try:self.browser_bridge.stop()
            except Exception:pass
        self.stop_shop_scan()
        self.item_pin.close()
        self.channel_pin.close()
        self.shop.pin.close()
        self.archive.close()
        if hasattr(self,'trade_keys'):self.trade_keys.close()
        self.root.destroy()


if __name__=='__main__':
    FMApp().root.mainloop()

