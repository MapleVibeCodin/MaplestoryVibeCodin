"""New FM Sprint launch path; reuses pinned FM Rush modules, never edits them.
Live purchase is deliberately not dispatched: verified transaction evidence absent.
"""
import argparse,base64,os,sys,zlib,time
from pathlib import Path
from fm_sprint_core import Lifecycle,Scene,RuneCache,channel_points,menu_evidence,bgr_array,fresh_inventory
import numpy as np

# Historical channel-menu template recovered from the prior project snapshot.
HEADER='eJztl/9r01oUwPtP+Wc0UAaFQdVsTHOtLzV2lmbfnNrgU58+M/UXzQ+KaNQfqtX9sllBxcoUNKi4Wd57ur262TGCwiD79XhOetNmXedQuF2H/XS5uzc5kA8n9+bc5K0rnQ906dLlp4lEItiAfzT1I34T+VEYb2vBwhTDt+I3DPrQuO2mYa2CRThCkAieDv7jZ7YKgyCsnXkkl9CZrcIiwvPYYnLBFvOx1XNfl/QuXX6FnbCnyO+AvVm+y+/EXKdDhtEOJ0+Gu1uxp87eBvJ2gFncx9mPKApj7MCBZDJ58OAfqppKHdLSmezQ8Mjo2NHx8WPHjp9Acrmc0U4wjeompOocakZrK3PRTMczF822gkpQywvbwYeo3gz5+fvADVe2iX/WO9b9vrnLXHJQlmT8x+IxWYozWYr163gGz0rU1f0BNn6QGBbDjhDso93ldzPPuGNfEbJpXY9XPAkqcQm8WDoLxT4Twzxb1lUTB7oEYCVFOVZDjv4X3uq3lbLz5H58V/Cs0dFW1EzM445gqgZq2eBWAOx+xcYBikJpryjHUB7xo2S1ujB148+hQXYYYIlLDhTAkk0W8yrc0UnUHItxE5PqO2IMXhPlmKk7omJ1evIhfHp1GapLH94/bjgWTCihIHcExh37estgKrwDIIlyfBpyXC3inVbK9uKsM9541ihRKILLwAkcC4Ej6Q9QJ+YB6qqCHB8HjpjGr5OfFz7duHLp9BF9frr+6qFFgTPPChw9cAPHpMU7DCqkK8jxdchx3nowdRs+vsxB6dGduqNmQAmT50Cx5ui4UOBq/nOmw4KSifNUkONSyHHhOsCX2Rep/+/17Gq8wdNUdMgycCxApdkRlz4Dt0eQ42rIceXq2zfXLhzWB1MwH6oyNAUNF6chd2QeNM1HWjuSCywjxtELrRn35tQkLPx3HZaehwshOUqYSJs7JpzAEXsW5VKqfWPaihjHtfC7Z/EuVOfzyzPrazUt2l4r5GhCfakAI0cDPMehCSDakSSdW7NX/WoYDunBRTKAOkbgiCfIsVx0sbiQI/4l0LzcK9yRJJ+foXK9PiReAUOjJnAcqK1rWuwJjRxLVKypkot3JMn3Mxv2ZMwwZWxsWTYNhoeaYXY2zWzbziZUnQZ4Dfc/htnfBkeS/HfjvlGjAqLhglC12pFR0ngo2Or+QFPqYeId/a2PoDv9Ok2OevNk7ASaHTuRteimkkMNhreVtUYiuczIyMjo6NjY2FH+0Z87eer0X2fPnfv7/HnTnJiYuIBcbCvouFkmOyiPvmVHs7YD+A6LgQJh'

def header():return np.frombuffer(zlib.decompress(base64.b64decode(HEADER)),np.uint8).reshape(51,164)

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',choices=['runescape','maplestory'],required=True)
    p.add_argument('--navigate',action='store_true',help='EXPERIMENTAL live channel and projected-shop clicks; no buying')
    p.add_argument('--start-channel',type=int,default=20);p.add_argument('--route',type=int)
    args=p.parse_args()
    from route_logic import plan
    if not 1<=args.start_channel<=40:p.error('start channel must be 1–40')
    if args.route is not None:
        print(plan(args.start_channel,args.route,args.start_channel).route_text);return
    if os.name!='nt':raise SystemExit('Live launcher requires Windows; replay tests are platform independent.')
    import ctypes
    import fm_rush as old
    from game_window import window_rect,window_client_rect,window_has_focus,window_at_point,move_cursor_on_screen,cursor_screen_position
    from camera_alignment import capture_client
    from shop_position import entry_shop_point,shop_marker
    import shop_inventory
    ref=header(); user=ctypes.windll.user32
    class Tracker(shop_inventory.ShopInventoryTracker):
        def __init__(self):
            super().__init__()
            if args.engine=='runescape':self._name_cache=RuneCache(self._name_cache)
    old.ShopInventoryTracker=Tracker
    home=Path(os.environ['LOCALAPPDATA'])/'FM_Sprint'/args.engine
    home.mkdir(parents=True,exist_ok=True);(home/'archives').mkdir(exist_ok=True)
    old.ARCHIVE_DIR=home/'archives';old.CONFIG=home/'config.json'
    class App(old.FMApp):
        def __init__(self):
            self.flow=Lifecycle();self._f12=False;self._f8=False;self._identity=None;self._message=''
            self._parked=False;self._last_tick=0.;self._last_menu=None
            super().__init__();self.conf['start_channel']=args.start_channel
            self.root.title('FM Sprint — '+args.engine.title()+' — '+('Experimental navigation' if args.navigate else 'Pointer assist'))
        def safe(self,hwnd,client):
            return hwnd and window_has_focus(hwnd) and window_client_rect(hwnd)==client and not (user.GetAsyncKeyState(0x7B)&0x8000)
        def at(self,hwnd,client,point,click=False):
            if point is None or not self.safe(hwnd,client):return False
            x,y=point;w,h=client[2:]
            if not (2<x<w-2 and 2<y<h-2):return False
            sx,sy=client[0]+x,client[1]+y
            if window_at_point(sx,sy)!=hwnd:return False
            if move_cursor_on_screen(hwnd,sx,sy) is not None:return False
            if click:
                if not self.safe(hwnd,client) or window_at_point(sx,sy)!=hwnd or cursor_screen_position()!=(sx,sy):return False
                user.mouse_event(0x0002,0,0,0,0);user.mouse_event(0x0004,0,0,0,0)
            return True
        def menu(self,client,cc):
            if client[2:]!=(1366,768):return False,False,False,0.
            x,y,_,_=client;f=capture_client((x+403,y+282,565,200),allow_crop=True)
            return menu_evidence(f,ref,cc) if f else (False,False,False,0.)
        def black(self,client):
            x,y,w,h=client
            for dx,dy in ((w//2,h//3),(w//4,h//2),(3*w//4,h//2)):
                f=capture_client((x+dx,y+dy,12,12),allow_crop=True)
                if not f or int(bgr_array(f).max())>=25:return False
            return True
        def pin(self,deal,client,cc):
            if not deal.shop_position:return None
            x,y,w,h=client
            pt=entry_shop_point(deal.shop_position,deal.fm,(w,h),channel_entry=cc)
            b=shop_marker(pt,client,client) if pt is not None else None
            if not b:return None
            l,t,r,bb=b
            if r-l<12 or bb-t<10:return None
            return (l+r)//2,(t+bb)//2
        def refresh_overlays(self,current):
            super().refresh_overlays(current)
            if not hasattr(self,'flow') or not getattr(self,'archive',None):return
            now=time.perf_counter()
            if now-self._last_tick<.008:return
            self._last_tick=now
            stop=bool(user.GetAsyncKeyState(0x7B)&0x8000)
            if stop and not self._f12:self.flow.stop();self.status.set('F12 stopped this run — unlock to reset')
            self._f12=stop
            if not current or not self.archive.chase_locked:
                self.flow.reset(None);self._identity=None;return
            key,deal=current
            if not deal.cc or not deal.fm or deal.sold:
                self.flow.stop();return
            hwnd=self.shop.selected_hwnd();client=window_client_rect(hwnd) if hwnd else None
            identity=key
            context=(deal.cc,deal.fm,deal.item,deal.buy_mesos,hwnd,client) if hwnd and client else None
            binding=self.flow.bind(identity,context,deal.cc==args.start_channel)
            if binding=='context_changed':
                self.status.set('Target/window changed · unlock before restarting');return
            if binding=='new':
                self._identity=identity
                self._message=plan(deal.cc,deal.fm,args.start_channel).route_text
                self.status.set(self._message)
            f8=bool(user.GetAsyncKeyState(0x77)&0x8000)
            if f8 and not self._f8:self.status.set(self._message)
            self._f8=f8
            if stop:
                self.flow.stop();return
            if not client or not self.safe(hwnd,client) or client[2:]!=(1366,768):
                self.flow.black_count=0;return
            if self.flow.stage=='stopped':return
            entrance=bool(getattr(self,'_entrance_preview',None));room=bool(getattr(self,'_inventory_fast_poll',False))
            with self._inventory._lock:
                inv=self._inventory._latest
                inv_key=self._inventory._key
                observed_at=self._inventory._observed_at
            expected=(hwnd,tuple(client),deal.listing_id,deal.ign,deal.item,deal.buy_mesos)
            shop,hit=fresh_inventory(inv,inv_key,expected,observed_at,time.monotonic())
            shop=room and shop
            menu,selected,confirm,_=self.menu(client,deal.cc) if self.flow.stage=='channel' else (False,False,False,0.)
            expect_fade=(self.flow.stage=='route' and self.flow.seen_entrance) or (self.flow.stage=='channel' and self.flow.menu_seen)
            black=expect_fade and not room and not entrance and not menu and self.black(client)
            pin=self.pin(deal,client,not self.flow.same)
            previous_stage=self.flow.stage
            actions=self.flow.step(identity,Scene(focus=True,entrance=entrance,room=room,black=black,menu=menu,selected=selected,shop=shop,hit=bool(shop and hit),pin=pin is not None,confirm=confirm),same_channel=deal.cc==args.start_channel,navigate=args.navigate)
            points=channel_points(deal.cc,client[2:]);cell,button=points
            for a in actions:
                if a=='park_channel':self.at(hwnd,client,cell)
                elif a=='park_shop_normal':self.at(hwnd,client,self.pin(deal,client,False))
                elif a=='park_shop_cc':self.at(hwnd,client,self.pin(deal,client,True))
                elif a=='park_clear':self.at(hwnd,client,(client[2]-30,100))
                elif a=='select_channel':
                    # Refresh the header immediately before an experimental click.
                    m,s,c,_=self.menu(client,deal.cc)
                    if m and not s:self.at(hwnd,client,cell,click=True)
                elif a=='confirm_channel':
                    m,s,c,_=self.menu(client,deal.cc)
                    if m and s and c:self.at(hwnd,client,button,click=True)
                elif a=='open_projected_shop':
                    # Projection is not proof of seller identity. One bounded click.
                    self.at(hwnd,client,pin,click=True)
            if actions:self.status.set(self.flow.stage.upper()+' · '+', '.join(actions))
            if self.flow.stage=='item_ready':self.status.set('ITEM LOCATED · verify price/quantity; purchase remains manual')
            elif previous_stage=='item_ready':self.status.set('Item evidence changed · waiting for fresh recognition')
        def follow_overlays(self):
            if self.archive.lock.acquire(blocking=False):
                try:current=self.archive.current()
                finally:self.archive.lock.release()
                self.refresh_overlays(current)
            self.schedule(10 if self.archive.chase_locked else 50,self.follow_overlays)
    App().root.mainloop()
if __name__=='__main__':main()
