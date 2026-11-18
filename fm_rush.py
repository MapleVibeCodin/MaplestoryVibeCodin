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
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
from window_capture import windows as list_game_windows, WindowFrames, window_rect
from multi_shop_worker import MultiShopWorker
from deal_archive import DealArchive
from channel_overlay import ChannelPin,locate_channel
from trade_ledger import TradeLedger
from trade_hotkeys import TradeHotkeys
from bought_screenshots import downloads_folder, save_bought_screenshot

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
        'shop_geom':data.get('shop_geom',''),
        'screenshot_folder':data.get('screenshot_folder',''),
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
        app._picker_windows=[window for window in (app.root,app.grid,app.map,app.shop)
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
                self.app.status.set(f'Discord region saved: {w}×{h}. Press START OCR.')
                self.app.save()
        self.finish()

    def finish(self):
        self.destroy()
        self.app.restore_windows()


class ShopHighlighter(tk.Toplevel):
    """Compact controls; the result is marked directly on the game window."""
    def __init__(self,app):
        super().__init__(app.root)
        self.withdraw()
        from shop_pin import ShopPin
        self.app=app
        self.title('FM RUSH — TRADE DESK')
        self.config(bg=BG)
        self.resizable(True,True)
        self.minsize(1000,480)
        self.attributes('-topmost',app.conf['topmost'])
        self.protocol('WM_DELETE_WINDOW',self.withdraw)
        self.bind('<Configure>',self.remember_geometry)
        self.last_image=None;self.last_size=None;self.last_box=None;self.last_name='';self.last_mode='SEARCHING'
        self.target=tk.StringVar(value='Waiting for a deal')
        self.notice=tk.StringVar(value='A marker will appear over the matching name in MapleStory.')
        self.pin=ShopPin(app.root)
        self.matches={}
        top=tk.Frame(self,bg=BG);top.pack(fill='x',padx=10,pady=(7,3))
        tk.Label(top,textvariable=self.target,bg=BG,fg=YELLOW,font=('Segoe UI',17,'bold'),anchor='w').pack(side='left',fill='x',expand=True)
        tk.Button(top,text='Hide desk',command=self.withdraw,bg=CARD2,fg=FG,relief='flat').pack(side='right',padx=4)
        tk.Button(top,text='SKIP (Ctrl+Alt+N)',command=app.next_live_deal,bg=CARD2,fg=FG,relief='flat').pack(side='right',padx=4)
        tk.Button(top,text='FIND AGAIN',command=app.retry_shop_once,bg=CARD2,fg=FG,relief='flat').pack(side='right')
        row=tk.Frame(self,bg=BG);row.pack(fill='x',padx=10,pady=3)
        self.chosen=tk.StringVar(value='');self.available=[]
        self.combo=ttk.Combobox(row,textvariable=self.chosen,state='readonly',width=28)
        self.combo.pack(side='left',fill='x',expand=True)
        self.combo.bind('<<ComboboxSelected>>',self.change_window)
        tk.Button(row,text='↻',command=self.refresh_windows,bg=CARD2,fg=FG,relief='flat').pack(side='left',padx=4)
        self.start_btn=tk.Button(row,text='START',command=app.toggle_shop_scan,bg=TEAL,fg=BG,relief='flat')
        self.start_btn.pack(side='left')
        tk.Label(self,textvariable=self.notice,bg=BG,fg=MUTED,font=('Segoe UI',10),wraplength=490,anchor='w',justify='left').pack(fill='x',padx=10,pady=(5,8))
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=5,pady=4)
        hunt=ttk.Frame(self.tabs);self.tabs.add(hunt,text='Chase · current page')
        queue_frame=tk.Frame(hunt,bg=BG);queue_frame.pack(fill='both',expand=True,padx=10,pady=5)
        self.queue=ttk.Treeview(queue_frame,columns=('ign','room','item','list','return','state'),show='headings',height=5)
        for column,label,width in [('ign','Seller IGN',120),('room','Location',100),('item','Item',180),('list','HeneFM list',90),('return','Est. profit / hour',110),('state','Watch',180)]:
            self.queue.heading(column,text=label);self.queue.column(column,width=width,minwidth=50)
        self.queue.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(queue_frame,orient='vertical',command=self.queue.yview)
        scroll.pack(side='right',fill='y');self.queue.configure(yscrollcommand=scroll.set)
        self.queue_rows={}
        self.queue.bind('<<TreeviewSelect>>',self.select_queue)
        buttons=tk.Frame(hunt,bg=BG);buttons.pack(fill='x',padx=10,pady=(0,8))
        tk.Button(buttons,text='EXPORT ARCHIVE',command=app.export_archive,bg=CARD2,fg=FG,relief='flat').pack(side='left')
        tk.Button(buttons,text='REOPEN LAST DEAL',command=app.undo_deal,bg=CARD2,fg=FG,relief='flat').pack(side='left',padx=8)
        tk.Button(buttons,text='SKIP DEAL',command=app.complete_deal,bg=TEAL,fg=BG,relief='flat').pack(side='right')
        purchases=tk.Frame(self,bg=BG);purchases.pack(fill='x',padx=10,pady=(0,8))
        tk.Label(purchases,text='Bought qty:',bg=BG,fg=FG).pack(side='left',padx=5)
        ttk.Spinbox(purchases,from_=1,to=999,textvariable=app.buy_quantity,width=4).pack(side='left')
        tk.Button(purchases,text='BOUGHT · LOG / CLEAR (Ctrl+Alt+B)',command=app.log_purchase,bg=YELLOW,fg=BG,relief='flat').pack(side='right')
        from trade_desk import TradePanels
        self.trade_panels=TradePanels(app,self.tabs)
        self.refresh_windows()

    def remember_geometry(self,event):
        if event.widget is self and self.state()=='normal':
            self.app.conf['shop_geom']=self.geometry()

    def render_queue(self,rows,focus,names):
        position=self.queue.yview()[0]
        updated={}
        for key,deal in rows:
            location=f"CH {deal['cc'] or '?'} / FM {deal['fm'] or '?'}"
            from deal_parser import Deal
            from profit_filter import ProfitDecision
            from trade_desk import money
            live_deal=Deal(**{**{k:v for k,v in deal.items() if k!='off_page'},'profit':ProfitDecision(**deal['profit'])})
            estimate=self.app.ledger.recommendation(live_deal)
            watch='OFF PAGE' if deal.get('off_page') else ('SOLD' if deal.get('sold') else '; '.join(estimate['notes']))
            values=(deal['ign'],location,deal['item'],money(estimate['list_price']),money(estimate['profit_per_hour']),watch)
            updated[key]=values
            if key not in self.queue_rows:self.queue.insert('', 'end',iid=key,values=values)
            elif self.queue_rows[key]!=values:self.queue.item(key,values=values)
        for key in set(self.queue_rows)-set(updated):self.queue.delete(key)
        self.queue_rows=updated
        if focus:self.queue.selection_set(focus)
        if focus and focus!=getattr(self,'queue_focus',None):self.queue.see(focus)
        else:self.queue.yview_moveto(position)
        self.queue_focus=focus
        live_focus=bool(self.last_name) and self.last_name.casefold() in {name.casefold() for name in names}
        priority=('priority '+self.last_name if live_focus else 'selected deal is off page' if self.last_name else 'click a listing to choose')
        self.target.set(f'{len(names)} sellers · {priority}')
        self.matches={name:hit for name,hit in self.matches.items() if name.casefold()==self.last_name.casefold() and (name in names or time.monotonic()<hit.get('hold_until',0))}
        if self.last_size and self.app.shop_running:self.pin.show_many(self.selected_hwnd(),self.last_size,self.matches)

    def select_queue(self,event=None):
        selected=self.queue.selection()
        if selected and selected[0]!=self.app.archive.focus:self.app.select_archived(selected[0])

    def set_focus(self,name):
        self.last_name=name

    def draw_matches(self,size,hits,note):
        self.last_size=size;self.matches=hits
        self.pin.show_many(self.selected_hwnd(),size,hits)
        if note:self.notice.set(note)

    def change_window(self,event=None):
        self.pin.hide()
        if self.app.shop_running:
            self.app.stop_shop_scan()
            self.app.start_shop_scan()

    def refresh_windows(self):
        self.available=list_game_windows()
        labels=[f'{title}  [HWND {hwnd}]' for hwnd,title in self.available]
        self.combo['values']=labels
        current=self.chosen.get()
        if current in labels:return
        candidate=next((i for i,(hwnd,title) in enumerate(self.available)
                        if 'maplestory' in title.lower() or 'maple story' in title.lower()),
                       0 if self.available else -1)
        if candidate>=0:self.combo.current(candidate)
        else:self.chosen.set('')

    def selected_hwnd(self):
        index=self.combo.current()
        if 0<=index<len(self.available):
            return self.available[index][0]
        return None


    def set_target(self,name,force=False):
        if force or name.casefold()!=self.last_name.casefold():
            self.last_image=None;self.last_size=None;self.last_box=None
            self.last_mode='SEARCHING';self.matches.clear();self.pin.hide()
        self.last_name=name
        self.target.set(name or 'Waiting for a deal')
        self.notice.set('Looking for '+name if name else 'A marker will appear over the matching name in MapleStory.')

    def draw(self,image,source_size,box,mode,seen_text,latency_ms,method):
        self.last_image=None;self.last_size=source_size;self.last_box=box;self.last_mode=mode
        if box is None:
            self.pin.hide()
            self.notice.set(f'No confident match · {latency_ms:.0f} ms · '+
                            ('retrying automatically' if mode=='RETRYING' else 'press FIND AGAIN or change room'))
        else:
            likely=mode!='FOUND'
            self.notice.set(f'{"CHECK NAME" if likely else "FOUND"} · {latency_ms:.0f} ms · marked in game'+(f' · read: {seen_text}' if likely else ''))
            self.pin.show(self.selected_hwnd(),source_size,box,self.last_name,likely)

    def redraw(self):
        pass


class FMApp:
    def __init__(self):
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:pass
        self.conf=settings()
        self.web_only=os.environ.get('FM_RUSH_WEB_ONLY') == '1'
        self.root=tk.Tk()
        self.root.title('FM Rush v24.25')
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
        self.buy_quantity=tk.StringVar(value='1')
        self.status=tk.StringVar(value='Choose a listing on HeneFM')
        self.manual=tk.StringVar(value='CC 22 FM 13')
        self.events=queue.Queue()
        self.worker=None
        self.browser_bridge=None
        self.stop=threading.Event()
        self.running=False
        self.grid=None
        self.map=None
        self.shop=None
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
        self.ledger=TradeLedger(ARCHIVE_DIR/'trade_ledger.sqlite3')
        self.latency_history=[]
        self.shop_events=queue.Queue(maxsize=3)
        self._pending_after=set()
        self._closing=False
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.channel_pin=ChannelPin(self.root)
        self.channel_frame_version=None
        self.open_shop(show=False)
        self._make_bottom()
        self.root.update_idletasks()
        self.root.minsize(max(640,self.control_bar.winfo_reqwidth()+24),self.root.winfo_reqheight())
        self.snap(restore=True)
        self.sync_archive()
        self.schedule(35,self.pump)
        self.schedule(50,self.update_channel_overlay)
        try:
            self.browser_bridge=BrowserBridge(self.events,self.archive)
            self.browser_bridge.start()
            self.status.set('Choose a listing on HeneFM')
        except OSError as exc:
            self.status.set('HeneFM bridge not available: '+str(exc)[:100]+' • Discord OCR still works')
        if not self.web_only:self.schedule(0,self.try_start_shop)
        self.trade_keys=TradeHotkeys(self.events.put_nowait);self.trade_keys.start()
        self.schedule(30000,self.refresh_trade_panels)

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
        self.lbl(details,var=self.item,size=11).grid(row=1,column=2,sticky='ew')
        self.lbl(details,var=self.stats,size=9,color=MUTED).grid(row=2,column=2,sticky='ew')
        self.lbl(details,var=self.buy,size=13,color=YELLOW,bold=True).grid(row=0,column=3,sticky='e',padx=(8,0))
        self.lbl(details,var=self.profit,size=10,color=TEAL).grid(row=1,column=3,sticky='e',padx=(8,0))

        controls=self.control_bar=tk.Frame(self.root,bg=BG)
        controls.pack(fill='x',padx=12,pady=(4,0))
        self.btn(controls,'Trade Desk',self.open_shop).pack(side='left')
        self.btn(controls,'Inventory',self.open_inventory).pack(side='left',padx=4)
        self.lbl(controls,text='Qty',size=9,color=MUTED).pack(side='left',padx=(10,3))
        ttk.Spinbox(controls,from_=1,to=999,textvariable=self.buy_quantity,width=4).pack(side='left')
        self.btn(controls,'Bought',self.log_purchase,True).pack(side='left',padx=4)
        self.btn(controls,'Skip',self.complete_deal).pack(side='left')
        if not self.web_only:
            self.btn(controls,'Find again',self.retry_shop_once).pack(side='left',padx=4)
        tools=tk.Menubutton(controls,text='Tools ▾',relief='flat',bg=CARD2,fg=FG,padx=8,pady=4)
        menu=tk.Menu(tools,tearoff=False)
        tools.configure(menu=menu)
        for title,action in [('Place under game',self.snap),('Enter route',self.enter_route),
                             ('Channel grid',self.open_grid),('FM map',self.open_map),
                             ('Export scanner timing',self.export_latency)]:
            menu.add_command(label=title,command=action)
        if not self.web_only:
            menu.add_separator()
            menu.add_command(label='Start or pause locator',command=self.toggle_shop_scan)
            menu.add_command(label='Choose Discord alert area',command=self.pick_discord)
            self.ocr_menu_index=menu.index('end')+1
            menu.add_command(label='Start Discord OCR',command=self.toggle_discord)
            self.ocr_menu=menu
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

    def enter_route(self):
        value=simpledialog.askstring('Enter route','Enter a channel and room, such as CH 22 FM 13.',
                                     initialvalue=self.manual.get(),parent=self.root)
        if value is not None:
            self.manual.set(value)
            self.manual_go()

    def open_inventory(self):
        self.open_shop()
        self.shop.tabs.select(self.shop.trade_panels.inventory)

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
            active=(n==self.current_fm)
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

    def open_shop(self,show=True):
        if self.shop is None or not self.shop.winfo_exists():
            self.shop=ShopHighlighter(self)
            self.shop.set_target(self.shop_target)
        if show:
            if self.shop.state()=='withdrawn':
                self.place_desk()
            self.shop.deiconify()
            self.shop.lift()

    def place_desk(self):
        left,top,right,bottom=self.work_area()
        width=min(1100,right-left-16)
        height=min(650,bottom-top-self.title_margin()-16)
        x=left+(right-left-width)//2
        y=top+(bottom-top-height-self.title_margin())//2
        game=self.selected_game_rect()
        if game:
            gx,gy,gw,gh=game
            x=gx+(gw-width)//2
            y=gy+(gh-height-self.title_margin())//2
        self.place_window(self.shop,(width,height,x,y),self.conf['shop_geom'])

    def sync_archive(self):
        # Receipt runs on HTTP threads: take one consistent UI/search snapshot.
        with self.archive.lock:
            live_rows=self.archive.live_pending()
            names=self.archive.selected_names()
            available_names=self.archive.live_names()
            current=self.archive.current()
            rows=list(live_rows)
            if current and current[0] not in {key for key,_ in rows}:
                from dataclasses import asdict
                rows.append((current[0],{**asdict(current[1]),'off_page':True}))
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
        key,deal=current if current else (None,None)
        if key!=self.displayed_listing:
            self.displayed_listing=key
            if deal is not None and hasattr(self,'buy_quantity'):
                from trade_ledger import quote
                self.buy_quantity.set(str(quote(deal.raw_text)['offered_quantity'] or 1))
            if deal is not None:
                if deal.cc is not None and deal.fm is not None:
                    self.set_target(deal.cc,deal.fm,deal=deal,source='ARCHIVE')
                else:
                    self.ign.set('IGN: '+deal.ign);self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
                    self.stats.set('STATS: '+deal.stats);self.profit.set(deal.profit.label)
                    self.buy.set(deal.buy_label);self.ccfm.set('CH / FM: not shown')
                self.accepted_ign(deal.ign)
            else:
                self.accepted_ign('')
                self.ccfm.set('Choose a deal');self.keys.set('')
                if hasattr(self,'buy_quantity'):self.buy_quantity.set('1')
                self.ign.set('IGN: —');self.item.set('ITEM: —');self.stats.set('STATS: —')
                self.buy.set('BUY AT: —');self.profit.set('PROFIT: —')
        elif deal is not None:
            self.item.set('ITEM: '+deal.item+(' · SOLD' if deal.sold else ''))
            self.profit.set(deal.profit.label)
        if self.shop is not None and self.shop.winfo_exists():
            self.shop.render_queue(rows,key,available_names)

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
        if self._closing:return
        current=self.archive.current()
        frames=self.shop_frames
        if not self.shop_running or not current or not frames:
            self.channel_pin.hide();self.channel_frame_version=None
        else:
            frame=frames.peek(-1)
            if frame is not None:
                version,stamp,image=frame
                token=(self.shop_session,version,current[0],self.current_cc)
                if token!=self.channel_frame_version:
                    self.channel_frame_version=token
                    box=locate_channel(image,self.current_cc)
                    if box:
                        h,w=image.shape[:2]
                        self.channel_pin.show_many(self.shop.selected_hwnd(),(w,h),
                            {'CH '+str(self.current_cc):{'box':box,'mode':'EXACT'}})
                    else:self.channel_pin.hide()
        self.schedule(50,self.update_channel_overlay)

    def refresh_trade_panels(self):
        if self._closing:return
        if self.shop is not None and self.shop.winfo_exists():self.shop.trade_panels.refresh()
        self.schedule(30000,self.refresh_trade_panels)

    def export_latency(self):
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='FM_Rush_Scan_Timings.json')
        if path:
            Path(path).write_text(json.dumps({'scope':'Local page delivery and software room-entry stages; excludes HeneFM server freshness, human travel and compositor display latency.',
                'live_names':list(self.scan_names),'selected_ign':self.shop_target,
                'capture_hwnd':self.shop.selected_hwnd() if self.shop is not None else None,
                'capture_error':getattr(self.shop_frames,'error',''),
                'status':self.shop.notice.get() if self.shop is not None else '',
                'cpu_guard':CPU_GUARD_MESSAGE,'latest':self.latency_history},indent=2)+'\n',encoding='utf-8')

    def log_purchase(self):
        if time.monotonic()-getattr(self,'last_receipt_at',float('-inf'))<.5:return
        current=self.archive.current()
        if current is None:
            self.status.set('Choose the deal you bought before using Ctrl+Alt+B.');return
        key,deal=current
        try:
            quantity=int(self.shop.trade_panels.quantity.get()) if self.shop is not None else 1
            paid=None
            if deal.buy_mesos is None:
                paid=simpledialog.askstring('Price paid','The alert has no Buy price. Enter the actual unit price paid:')
                if paid is None:return
            receipt,new=self.ledger.purchase(key,deal,quantity=quantity,unit_cost=paid)
            self.archive.complete_current()
        except (ValueError,OSError) as exc:
            messagebox.showerror('Purchase not logged',str(exc));return
        except Exception as exc:
            messagebox.showerror('Purchase recording needs retry',str(exc)+'\nRetrying will not double-charge a recorded receipt.');return
        self.last_receipt_at=time.monotonic()
        self.sync_archive()
        if self.shop is not None and self.shop.winfo_exists():
            self.shop.trade_panels.refresh()
        price='—' if receipt['list_price'] is None else f"{receipt['list_price']:,}"
        self.status.set(f"RECORDED {quantity} × {receipt['item']} · paid {receipt['unit_cost']:,} each · list {price} · seller {receipt['target_store'] or 'unassigned'}")

    def bought_deal(self):
        current=self.archive.current()
        if current is None:
            self.status.set('Select a pending listing before clicking BOUGHT.');return
        key,deal=current
        source=Path(self.conf.get('screenshot_folder') or downloads_folder()/'FM_Rush_Item_Screenshots')
        destination=downloads_folder()/'Bought'
        try:
            try:path=save_bought_screenshot(deal,key,source,destination)
            except FileNotFoundError:
                folder=filedialog.askdirectory(title='Choose FM_Rush_Item_Screenshots — Cancel to wait for capture',
                    initialdir=str(source if source.exists() else downloads_folder()))
                if not folder:return
                path=save_bought_screenshot(deal,key,folder,destination)
                self.conf['screenshot_folder']=folder;self.save()
            self.archive.mark_bought(key,path)
        except (OSError,ValueError) as exc:
            messagebox.showerror('Purchase screenshot not saved',str(exc)+'\n\nThe deal remains pending.');return
        except Exception as exc:
            messagebox.showerror('Purchase not recorded',str(exc)+'\n\nThe screenshot may already be saved. Retry BOUGHT to record it.');return
        self.sync_archive()
        message='Saved purchase PNG: '+str(path)
        self.status.set(message)
        if self.shop is not None and self.shop.winfo_exists():self.shop.notice.set(message)

    def open_bought_folder(self):
        folder=downloads_folder()/'Bought'
        try:
            folder.mkdir(parents=True,exist_ok=True)
            if os.name=='nt':os.startfile(str(folder))
            else:
                import subprocess
                import sys
                subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(folder)])
        except OSError as exc:messagebox.showerror('Open Bought folder',str(exc))

    def select_archived(self,key):
        self.archive.select(key);self.sync_archive()

    def undo_deal(self):
        self.archive.undo_complete();self.sync_archive()

    def complete_deal(self):
        current=self.archive.current()
        if current:self.archive.skip(current[0])
        self.sync_archive()
        self.status.set('Skipped · click a HeneFM listing to chase')

    def accepted_ign(self, name):
        # The working selection is explicit; new archived listings do not replace it.
        name=(name or '').strip()
        self.shop_target=name
        self.shop_generation+=1
        if self.shop is not None and self.shop.winfo_exists():
            self.shop.set_focus(name)
        worker=getattr(self,'shop_thread',None)
        if self.shop is not None:
            self.shop.matches={};self.shop.pin.hide()
        if worker is not None and worker.is_alive():worker.prioritize(name)
        if name and not self.shop_running and not self.web_only and not getattr(self,'shop_paused',False):
            self.schedule(0,self.try_start_shop)

    def try_start_shop(self):
        if self.shop_running or self.shop_paused:return
        if self.shop is None or not self.shop.winfo_exists():
            self.open_shop(show=False)
        index=self.shop.combo.current()
        if index>=0 and any(value in self.shop.available[index][1].lower() for value in ('maplestory','maple story')):
            self.start_shop_scan()
        else:
            self.shop.notice.set('MapleStory not found — open game and click REFRESH')

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
        if self.shop is None or not self.shop.winfo_exists():self.open_shop(show=False)
        hwnd=self.shop.selected_hwnd()
        if hwnd is None:
            self.shop.notice.set('Select the MapleStory window, then ARM LOCATOR')
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
        except Exception as exc:
            if self.shop_frames:
                try:self.shop_frames.stop()
                except Exception:pass
            self.shop_frames=None
            self.shop.notice.set('Window capture failed: '+str(exc)[:150])
            return
        self.shop_running=True
        self.shop.start_btn.config(text='PAUSE',bg=RED)
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
        if self.shop is not None and self.shop.winfo_exists():
            self.shop.start_btn.config(text='START',bg=TEAL)
            self.shop.matches.clear();self.shop.last_size=None
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
            self.ocr_menu.entryconfigure(self.ocr_menu_index,label='Start Discord OCR')
            self.status.set('Discord OCR stopped.')
            return
        if not self.conf['discord_region']:
            self.status.set('First select a Discord alert area using PICK DISCORD.')
            return
        self.stop=threading.Event()
        self.worker=DiscordWatcher(lambda:self.conf['discord_region'],self.events,self.stop)
        self.worker.start();self.running=True
        self.ocr_menu.entryconfigure(self.ocr_menu_index,label='Stop Discord OCR')
        self.status.set('DISCORD: ≥15,000 MESOS AND ≥15% · WATCHING')

    def pump(self):
        if hasattr(self,'live_stamp') and self.live_stamp!=self.archive.live_state():self.sync_archive()
        for _ in range(20):
            try:evt=self.events.get_nowait()
            except queue.Empty:break
            if evt[0]=='trade_buy':
                self.log_purchase()
            elif evt[0]=='trade_next':
                self.next_live_deal()
            elif evt[0]=='trade_find':
                self.retry_shop_once()
            elif evt[0]=='browser_choice':
                action,key,session,revision=evt[1:]
                versions=getattr(self,'choice_revisions',{})
                if revision<=versions.get(session,0):continue
                versions[session]=revision
                if len(versions)>32:versions.pop(next(iter(versions)))
                self.choice_revisions=versions
                if action=='select':
                    if not self.archive.choose(key):
                        self.status.set('Listing already completed · choose another listing');continue
                else:
                    self.archive.skip(key)
                self.sync_archive()
                if action=='select':self.retry_shop_once()
                self.status.set('Chasing selected listing' if action=='select' else 'Skipped · choose any listing')
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
        for _ in range(3):
            try:evt=self.shop_events.get_nowait()
            except queue.Empty:break
            if evt[0]=='shop_epoch':
                if evt[1]!=self.shop_session:continue
                evt=evt[2]
            if evt[0]=='shops_frame':
                if self.shop_running and self.shop is not None and self.shop.winfo_exists():
                    _,size,hits,note=evt
                    hits={name:hit for name,hit in hits.items() if name.casefold()==self.shop_target.casefold() and (name in self.scan_names or
                          time.monotonic()<hit.get('hold_until',0))}
                    self.shop.draw_matches(size,hits,note)
            elif evt[0]=='shop_frame':
                _,key,image,source_size,box,mode,seen,latency,method=evt
                if key==(self.shop_target,self.shop_generation) and self.shop is not None and self.shop.winfo_exists():
                    self.shop.draw(image,source_size,box,mode,seen,latency,method)
            elif evt[0]=='shop_clear':
                if evt[1]==(self.shop_target,self.shop_generation) and self.shop is not None:
                    self.shop.set_target(self.shop_target,force=True)
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
                if self.shop_running and self.shop is not None and self.shop.winfo_exists():
                    self.shop.notice.set(evt[1])
        self.schedule(5 if self.shop_running and self.scan_names else 10,self.pump)

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
        self.channel_pin.close()
        if self.shop is not None:
            self.shop.pin.close()
        self.archive.close()
        if hasattr(self,'trade_keys'):self.trade_keys.close()
        if hasattr(self,'ledger'):self.ledger.close()
        self.root.destroy()


if __name__=='__main__':
    FMApp().root.mainloop()
