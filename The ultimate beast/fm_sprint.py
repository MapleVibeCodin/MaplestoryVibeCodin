"""New FM Sprint launch path; reuses pinned FM Rush modules, never edits them.
Live purchase is deliberately not dispatched: verified transaction evidence absent.
"""
import argparse,base64,os,sys,zlib,time
from pathlib import Path
from fm_sprint_core import Lifecycle,Scene,RuneCache,channel_points,menu_evidence,bgr_array,fresh_inventory,mini_route
import numpy as np

# Historical channel-menu template recovered from the prior project snapshot.
HEADER='eJztl/9r01oUwPtP+Wc0UAaFQdVsTHOtLzV2lmbfnNrgU58+M/UXzQ+KaNQfqtX9sllBxcoUNKi4Wd57ur262TGCwiD79XhOetNmXedQuF2H/XS5uzc5kA8n9+bc5K0rnQ906dLlp4lEItiAfzT1I34T+VEYb2vBwhTDt+I3DPrQuO2mYa2CRThCkAieDv7jZ7YKgyCsnXkkl9CZrcIiwvPYYnLBFvOx1XNfl/QuXX6FnbCnyO+AvVm+y+/EXKdDhtEOJ0+Gu1uxp87eBvJ2gFncx9mPKApj7MCBZDJ58OAfqppKHdLSmezQ8Mjo2NHx8WPHjp9Acrmc0U4wjeompOocakZrK3PRTMczF822gkpQywvbwYeo3gz5+fvADVe2iX/WO9b9vrnLXHJQlmT8x+IxWYozWYr163gGz0rU1f0BNn6QGBbDjhDso93ldzPPuGNfEbJpXY9XPAkqcQm8WDoLxT4Twzxb1lUTB7oEYCVFOVZDjv4X3uq3lbLz5H58V/Cs0dFW1EzM445gqgZq2eBWAOx+xcYBikJpryjHUB7xo2S1ujB148+hQXYYYIlLDhTAkk0W8yrc0UnUHItxE5PqO2IMXhPlmKk7omJ1evIhfHp1GapLH94/bjgWTCihIHcExh37estgKrwDIIlyfBpyXC3inVbK9uKsM9541ihRKILLwAkcC4Ej6Q9QJ+YB6qqCHB8HjpjGr5OfFz7duHLp9BF9frr+6qFFgTPPChw9cAPHpMU7DCqkK8jxdchx3nowdRs+vsxB6dGduqNmQAmT50Cx5ui4UOBq/nOmw4KSifNUkONSyHHhOsCX2Rep/+/17Gq8wdNUdMgycCxApdkRlz4Dt0eQ42rIceXq2zfXLhzWB1MwH6oyNAUNF6chd2QeNM1HWjuSCywjxtELrRn35tQkLPx3HZaehwshOUqYSJs7JpzAEXsW5VKqfWPaihjHtfC7Z/EuVOfzyzPrazUt2l4r5GhCfakAI0cDPMehCSDakSSdW7NX/WoYDunBRTKAOkbgiCfIsVx0sbiQI/4l0LzcK9yRJJ+foXK9PiReAUOjJnAcqK1rWuwJjRxLVKypkot3JMn3Mxv2ZMwwZWxsWTYNhoeaYXY2zWzbziZUnQZ4Dfc/htnfBkeS/HfjvlGjAqLhglC12pFR0ngo2Or+QFPqYeId/a2PoDv9Ok2OevNk7ASaHTuRteimkkMNhreVtUYiuczIyMjo6NjY2FH+0Z87eer0X2fPnfv7/HnTnJiYuIBcbCvouFkmOyiPvmVHs7YD+A6LgQJh'

def header():return np.frombuffer(zlib.decompress(base64.b64decode(HEADER)),np.uint8).reshape(51,164)

def focus_release_pointer(*, schedule, now, valid, game_focused, scanner_focused, focus_scanner, move, done):
    """Previous FM Rush focus-release strategy; bounded pointer move, never a click."""
    deadline=now()+.075
    def finish():
        if now()>=deadline:
            done(False,'focus_timeout');return
        if not valid():
            done(False,'target_changed');return
        if game_focused():
            schedule(5,finish);return
        if not scanner_focused():
            done(False,'other_window_focused');return
        ok=move()
        done(ok,'moved' if ok else 'move_failed')
    if not valid():
        done(False,'target_changed');return
    try:
        focus_scanner()
    except Exception:
        done(False,'focus_request_failed');return
    schedule(5,finish)

def target_context(deal,hwnd,client):
    """Include the listing metadata that can change without a new archive key."""
    if not hwnd or not client:return None
    return (deal.cc,deal.fm,deal.item,deal.buy_mesos,hwnd,tuple(client),
            deal.listing_id,deal.ign,repr(deal.shop_position))


def live_target_matches(current,locked,key,context,hwnd,client):
    return bool(locked and current and current[0]==key and not current[1].sold
                and context is not None and target_context(current[1],hwnd,client)==context)


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
    from shop_pin import OverlayPin
    class RouteMiniPin(OverlayPin):
        """Transparent, click-through client overlay; no separate gaze target."""
        def draw_markers(self,w,h,sw,sh,hits):
            c=self.canvas;c.delete('all');sx=w/sw;sy=h/sh
            for name,hit in hits.items():
                cc,room=map(int,name.split(':'));l,t,r,b=hit['box']
                ox,oy=l*sx,t*sy
                def xy(x,y):return ox+x*sx,oy+y*sy
                def rect(x1,y1,x2,y2,**kw):return c.create_rectangle(*xy(x1,y1),*xy(x2,y2),**kw)
                def line(points,**kw):return c.create_line(*(v for point in points for v in xy(*point)),**kw)
                def text(x,y,label,size,color='#ffffff',bold=False):
                    pos=xy(x,y);font=('Segoe UI',-size,'bold' if bold else 'normal')
                    c.create_text(pos[0]+1,pos[1]+1,text=label,font=font,fill='#101820')
                    c.create_text(*pos,text=label,font=font,fill=color)
                nodes,path,cue=mini_route(room)
                # Only the header/footer and room badges are opaque. The map
                # background is the transparent key inherited from OverlayPin.
                rect(0,0,160,185,outline='#7389a2',width=1)
                rect(1,1,159,24,fill='#142237',outline='')
                text(45,12,f'FM {room:02d}',16,'#ffdf72',True)
                text(120,12,f'CH {cc:02d}',13,'#ffffff',True)
                for first,last in ((17,20),(13,16),(7,12),(1,6)):
                    x1,y=nodes[first];x2,_=nodes[last]
                    line(((x1-10,y+10),(x2+10,y+10)),fill='#182536',width=4)
                    line(((x1-10,y+10),(x2+10,y+10)),fill='#9aadc4',width=1)
                line(((80,50),(80,131)),fill='#d1bb87',width=2,dash=(3,2))
                line(path,fill='#17202b',width=5)
                line(path,fill='#ffdf72',width=2,arrow='last',arrowshape=(6,7,3))
                for n,(x,y) in nodes.items():
                    active=n==room;radius=10 if active else 8
                    c.create_oval(*xy(x-radius,y-radius),*xy(x+radius,y+radius),fill='#ffdf72' if active else '#24374d',outline='#ffffff' if active else '#9aadc4',width=2 if active else 1)
                    c.create_text(*xy(x,y),text=str(n),font=('Segoe UI',-11 if active else -9,'bold'),fill='#101820' if active else '#f5fbff')
                c.create_oval(*xy(76,73),*xy(84,81),fill='#25e5b5',outline='#ffffff')
                rect(1,141,159,184,fill='#142237',outline='')
                text(80,152,cue[0],11,'#ffdf72',True)
                text(80,168,cue[1],11,'#ffffff',True)
    ref=header(); user=ctypes.windll.user32
    class Tracker(shop_inventory.ShopInventoryTracker):
        def __init__(self):
            super().__init__()
            if args.engine=='runescape':self._name_cache=RuneCache(self._name_cache)
    old.ShopInventoryTracker=Tracker
    home=Path(os.environ['LOCALAPPDATA'])/'The ultimate beast'/args.engine
    home.mkdir(parents=True,exist_ok=True);(home/'archives').mkdir(exist_ok=True)
    old.ARCHIVE_DIR=home/'archives';old.CONFIG=home/'config.json'
    class App(old.FMApp):
        def __init__(self):
            self.flow=Lifecycle();self._f12=False;self._f8=False;self._identity=None;self._message=''
            self._parked=False;self._last_tick=0.;self._last_menu=None
            self._route_mini=None;self._route_mini_key=None;self._syncing_archive=False
            self._f9_inhibit=False;self._park_serial=0
            super().__init__();self.conf['start_channel']=args.start_channel
            self._route_mini=RouteMiniPin(self.root,interval_ms=50)
            self.root.title('The ultimate beast R4 — '+args.engine.title()+' — '+('Experimental navigation' if args.navigate else 'Pointer assist'))
        def sync_archive(self):
            # Do not pop the separate old map window on every new alert.
            self._syncing_archive=True
            try:super().sync_archive()
            finally:self._syncing_archive=False
        def open_map(self):
            if not self._syncing_archive:super().open_map()
        def show_route_mini(self,hwnd=None,client=None,deal=None):
            pin=self._route_mini
            if pin is None:return
            window=window_rect(hwnd) if hwnd and client and deal else None
            if window and client[2]>=184 and client[3]>=209:
                x=client[0]-window[0]+client[2]-172;y=client[1]-window[1]+12
                hit={f'{deal.cc}:{deal.fm}':{'box':(x,y,x+160,y+185),'mode':'ROUTE'}}
                key=(hwnd,window[2:],x,y,deal.cc,deal.fm)
                if key!=self._route_mini_key:
                    pin.show_many(hwnd,window[2:],hit);self._route_mini_key=key
            elif self._route_mini_key is not None:
                pin.hide();self._route_mini_key=None
        def cancel_pending_pointers(self):
            self._park_serial+=1
            self._pointer_serial+=1
            self._pointer_pending=None
        def set_chase_locked(self,locked):
            if not locked:
                self.cancel_pending_pointers()
                self.flow.reset(None)
            super().set_chase_locked(locked)
        def complete_deal(self):
            self.cancel_pending_pointers()
            self.flow.reset(None)
            super().complete_deal()
        def move_pointer_to_target(self,kind,*,received=None):
            if self.flow.stage=='stopped' or user.GetAsyncKeyState(0x7B)&0x8000:
                self.cancel_pending_pointers()
                self.status.set('F12 stopped this run — unlock to reset');return
            self._park_serial+=1
            super().move_pointer_to_target(kind,received=received)
        def close(self):
            self.cancel_pending_pointers()
            if self._route_mini is not None:self._route_mini.close()
            super().close()
        def f9_down(self):return bool(user.GetAsyncKeyState(0x78)&0x8000)
        def safe(self,hwnd,client):
            return hwnd and window_has_focus(hwnd) and window_client_rect(hwnd)==client and not (user.GetAsyncKeyState(0x7B)&0x8000)
        def current_target_valid(self,hwnd,client,key,context):
            if not self.archive.lock.acquire(blocking=False):return False
            try:
                return live_target_matches(self.archive.current(),self.archive.chase_locked,
                                           key,context,hwnd,client)
            finally:self.archive.lock.release()
        def release_and_park(self,hwnd,client,sx,sy,serial):
            key,stage,context=self.flow.key,self.flow.stage,self.flow.context
            rec=getattr(self,'performance',None)
            attempt=getattr(rec,'active',None)
            started=time.perf_counter()
            def valid():
                if self._closing or serial!=self._park_serial or self.flow.key!=key or self.flow.stage!=stage:return False
                if user.GetAsyncKeyState(0x7B)&0x8000:return False
                return bool(self.flow.context==context and self.current_target_valid(hwnd,client,key,context)
                    and self.shop.selected_hwnd()==hwnd and window_client_rect(hwnd)==client and window_at_point(sx,sy)==hwnd)
            def focus_scanner():
                if self.root.state() in ('iconic','withdrawn'):self.root.deiconify()
                self.root.focus_force()
            def scanner_focused():
                owner=user.GetAncestor(self.root.winfo_id(),2)
                return bool(owner and window_has_focus(owner))
            def move():
                return bool(valid() and not window_has_focus(hwnd) and scanner_focused()
                    and move_cursor_on_screen(hwnd,sx,sy) is None and cursor_screen_position()==(sx,sy))
            def done(ok,reason):
                if rec is not None and rec.active==attempt:rec.marker('beast_pointer_handoff',ok=ok,reason=reason,total_ms=round((time.perf_counter()-started)*1000,1))
                if not self._closing and serial==self._park_serial and self.flow.key==key:
                    self.status.set('Pointer ready · click manually' if ok else 'Pointer not moved · '+reason.replace('_',' '))
            focus_release_pointer(schedule=self.schedule,now=time.perf_counter,valid=valid,
                game_focused=lambda:window_has_focus(hwnd),scanner_focused=scanner_focused,
                focus_scanner=focus_scanner,move=move,done=done)
        def at(self,hwnd,client,point,click=False,require_f9=False,release_focus=True):
            if point is None or self.flow.stage=='stopped' or not self.safe(hwnd,client) or (require_f9 and not self.f9_down()):return False
            key,context=self.flow.key,self.flow.context
            if not self.current_target_valid(hwnd,client,key,context):return False
            x,y=point;w,h=client[2:]
            if not (2<x<w-2 and 2<y<h-2):return False
            sx,sy=client[0]+x,client[1]+y
            if window_at_point(sx,sy)!=hwnd:return False
            self._park_serial+=1
            serial=self._park_serial
            if cursor_screen_position()!=(sx,sy):
                # Parking uses the proven focus-release path before moving. The
                # shop-open tooltip-clear park must not interrupt recognition.
                if not click and release_focus:
                    self.release_and_park(hwnd,client,sx,sy,serial);return True
                if move_cursor_on_screen(hwnd,sx,sy) is not None or cursor_screen_position()!=(sx,sy):
                    if release_focus:self.release_and_park(hwnd,client,sx,sy,serial)
                    return False
            if click:
                if not self.current_target_valid(hwnd,client,key,context) or not self.safe(hwnd,client) or window_at_point(sx,sy)!=hwnd or cursor_screen_position()!=(sx,sy) or (require_f9 and not self.f9_down()):return False
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
            stop=bool(user.GetAsyncKeyState(0x7B)&0x8000)
            if stop and not self._f12:
                self.cancel_pending_pointers()
                self.flow.stop();self.status.set('F12 stopped this run — unlock to reset')
            self._f12=stop
            now=time.perf_counter()
            if not stop and now-self._last_tick<.008:return
            self._last_tick=now
            if not current or not self.archive.chase_locked:
                self.flow.reset(None);self._identity=None;self.show_route_mini();return
            key,deal=current
            if not deal.cc or not deal.fm or deal.sold:
                self.flow.stop();self.show_route_mini();return
            hwnd=self.shop.selected_hwnd();client=window_client_rect(hwnd) if hwnd else None
            identity=key
            context=target_context(deal,hwnd,client)
            binding=self.flow.bind(identity,context,deal.cc==args.start_channel)
            if binding=='context_changed':
                self.cancel_pending_pointers()
                self.show_route_mini();self.status.set('Target/window changed · unlock before restarting');return
            if binding=='new':
                self.cancel_pending_pointers()
                self._identity=identity;self._f9_inhibit=self.f9_down()
                self._message=plan(deal.cc,deal.fm,args.start_channel).route_text
                self.status.set('LOCKED · Shift+2 to unlock')
            f8=bool(user.GetAsyncKeyState(0x77)&0x8000)
            if f8 and not self._f8:self.status.set(self._message)
            self._f8=f8
            if stop:
                self.flow.stop();self.show_route_mini();return
            if not client or not self.safe(hwnd,client):
                self.flow.black_count=0;self._f9_inhibit=self.f9_down();self.show_route_mini();return
            if self.flow.stage=='stopped':self.show_route_mini();return
            if client[2:]!=(1366,768):
                if self.flow.stage=='route' and not getattr(self,'_inventory_fast_poll',False):self.show_route_mini(hwnd,client,deal)
                else:self.show_route_mini()
                return
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
            f9=self.f9_down()
            if not f9:self._f9_inhibit=False
            channel_request=f9 and not self._f9_inhibit
            previous_stage=self.flow.stage
            actions=self.flow.step(identity,Scene(focus=True,entrance=entrance,room=room,black=black,menu=menu,selected=selected,shop=shop,hit=bool(shop and hit),pin=pin is not None,confirm=confirm),same_channel=deal.cc==args.start_channel,navigate=args.navigate,channel_request=channel_request)
            if self.flow.stage=='route' and not (black or room or menu):self.show_route_mini(hwnd,client,deal)
            else:self.show_route_mini()
            points=channel_points(deal.cc,client[2:]);cell,button=points
            for a in actions:
                if a=='park_channel':self.at(hwnd,client,cell)
                elif a=='park_shop_normal':self.at(hwnd,client,self.pin(deal,client,False))
                elif a=='park_shop_cc':self.at(hwnd,client,self.pin(deal,client,True))
                elif a=='park_clear':self.at(hwnd,client,(client[2]-30,100),release_focus=False)
                elif a=='select_channel':
                    # Refresh the header immediately before an experimental click.
                    m,s,c,_=self.menu(client,deal.cc)
                    if not (m and (s or self.at(hwnd,client,cell,click=True,require_f9=not args.navigate))):self.flow.channel_failed(a)
                elif a=='confirm_channel':
                    m,s,c,_=self.menu(client,deal.cc)
                    if not (m and s and c and self.at(hwnd,client,button,click=True,require_f9=not args.navigate)):self.flow.channel_failed(a)
                elif a=='open_projected_shop':
                    # Projection is not proof of seller identity. One bounded click.
                    self.at(hwnd,client,pin,click=True)
            if self.flow.channel_blocked:self.status.set('Channel action interrupted · release F9, then hold again (manual mode)')
            elif actions:self.status.set(self.flow.stage.upper()+' · '+', '.join(actions))
            elif self.flow.stage=='channel' and previous_stage!='channel':self.status.set('Open channel menu · hold F9 to select + confirm')
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
