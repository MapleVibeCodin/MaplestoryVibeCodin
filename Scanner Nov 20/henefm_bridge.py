"""Optional, localhost-only HeneFM browser-extension bridge.

Receives only one HeneFM Flips deal at a time (as shown on the user's
browser page) and hands it to the GUI. No API key, no network requests,
listing metadata can be persisted locally before delivery is acknowledged.
"""
from __future__ import annotations
import json
import math
import queue
import re
import time
from pathlib import Path
import threading
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from deal_parser import Deal
from profit_filter import ProfitDecision
from route_logic import plan, arrows, START_CHANNEL

HOST = '127.0.0.1'
PORT = 18773
MAX_REQUEST_BYTES = 65_536
MAX_VISIBLE_BYTES=4*1024*1024


def parse_browser_deal(raw: dict) -> Deal | None:
    """Validate listing structure; apply no profit or sold-status eligibility gate."""
    if not isinstance(raw, dict):
        return None
    def integer(key,low,high):
        value=raw.get(key)
        if value is None:return None
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or int(value)!=value:
            raise ValueError(key)
        if not low<=value<=high:raise ValueError(key)
        return int(value)
    try:
        cc=integer('cc',1,40);fm=integer('fm',1,20)
        buy=integer('buy_mesos',0,1_000_000_000_000)
        gain=integer('profit_mesos',-1_000_000_000_000,1_000_000_000_000)
        pct=raw.get('profit_percent')
        if pct is not None:
            if isinstance(pct,bool) or not isinstance(pct,(int,float)) or not math.isfinite(pct) or abs(pct)>1e14:
                return None
            pct=float(pct)
    except (ValueError,TypeError,OverflowError):return None
    item = raw.get('item')
    ign = raw.get('ign')
    stats = raw.get('stats', '')
    if not isinstance(item, str) or not isinstance(ign, str) or not isinstance(stats, str):
        return None
    item = item.strip()[:100]
    ign = ign.strip()[:24]
    stats = stats.strip()[:160]
    if not item or not ign or len(ign) < 3 or not ign.replace('_', '').isalnum():
        return None
    return Deal(cc=cc, fm=fm, item=item, stats=stats, ign=ign,
                buy_mesos=buy,
                profit=ProfitDecision(True,gain,pct,'browser listing'),
                listing_id=str(raw.get('listing_id',''))[:120],
                sold=raw.get('sold') is True,raw_text=str(raw.get('raw_text',''))[:6000])


def make_svg_map_state(archive, view=None):
    """Immutable, light-weight snapshot used by the local SVG route viewer.

    Derive paths with the exact existing FM route planner; never ask the OCR
    worker to build a map or access Tk widgets on the HTTP server thread.
    """
    view = view or {}
    with archive.lock:
        current = archive.current()
        listings = archive.live_pending()
        locked = bool(archive.chase_locked)
        generation, fresh = archive.live_state()
    focus, selected = current if current else (None, None)
    top = []
    for key, deal in listings[:40]:
        top.append({
            'id': key, 'cc': deal.get('cc'), 'fm': deal.get('fm'),
            'ign': str(deal.get('ign') or '')[:24],
            'item': str(deal.get('item') or '')[:100],
            'buy_mesos': deal.get('buy_mesos'),
            'profit_mesos': (deal.get('profit') or {}).get('mesos'),
        })
    manual_at = view.get('manual_override_at')
    manual = not locked and isinstance(manual_at, (int, float)) and manual_at > 0
    reset_ms = max(0, int(60000-(time.monotonic()-manual_at)*1000)) if manual else None
    if manual and reset_ms == 0: manual = False
    cc = view.get('cc') if manual else getattr(selected, 'cc', None)
    fm = view.get('fm') if manual else getattr(selected, 'fm', None)
    start_channel = view.get('start_channel', START_CHANNEL)
    if not isinstance(start_channel, int) or not 1 <= start_channel <= 40:
        start_channel = START_CHANNEL
    routing = None
    if isinstance(cc, int) and isinstance(fm, int) and 1 <= cc <= 40 and 1 <= fm <= 20:
        p = plan(cc, fm, start_channel=start_channel)
        routing = {
            'cc': cc, 'fm': fm, 'waypoints': [list(x) for x in p.waypoints],
            'directions': p.route_text,
            'channel_keys': list(p.channel_keys), 'channel_arrows': arrows(p.channel_keys),
            'row': p.tier, 'direction': p.direction,
        }
    return {
        'ok': True, 'feed_fresh': bool(fresh), 'feed_generation': generation,
        'locked': locked, 'manual': manual, 'reset_ms': reset_ms,
        'focused_id': focus, 'start_channel': start_channel,
        'seller': selected.ign if selected else '',
        'item': selected.item if selected else '',
        'selected_listing_id': selected.listing_id if selected else '',
        'route': routing, 'listings': top,
        'item_detection': str(view.get('item_detection') or '')[:160],
    }


class BrowserBridge:
    """Small receiver on 127.0.0.1; posts accepted deals into an existing queue."""
    def __init__(self, out: queue.Queue, archive=None, state_provider=None):
        self.out = out
        self.archive=archive
        self.state_provider=state_provider
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        out = self.out
        archive=self.archive
        state_provider=self.state_provider
        map_path=Path(__file__).with_name('fm_svg_map.html')
        map_html=map_path.read_bytes() if map_path.is_file() else None

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def _send(self, status: int, payload: dict):
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == '/health':
                    self._send(200, {'ok': True, 'name': 'FM Rush SVG Route'});
                elif self.path in ('/fm-map', '/fm-map/'):
                    if map_html is None:
                        self._send(503, {'ok': False, 'error': 'svg_map_file_missing'});return
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('Content-Length', str(len(map_html)))
                    self.end_headers()
                    self.wfile.write(map_html)
                elif self.path == '/fm-map/state':
                    if archive is None:
                        self._send(503, {'ok': False, 'error': 'archive_not_ready'});return
                    try:
                        view=state_provider() if state_provider is not None else None
                        self._send(200, make_svg_map_state(archive, view))
                    except (OSError, ValueError, TypeError) as exc:
                        self._send(503, {'ok': False, 'error': type(exc).__name__})
                else:
                    self._send(404, {'ok': False})

            def do_POST(self):
                if self.path == '/fm-map/action':
                    # Only the locally served map may control the GUI. Web pages
                    # cannot set this custom header without a CORS preflight.
                    if (self.headers.get('Origin') != f'http://{HOST}:{PORT}'
                            or self.headers.get('X-FM-Rush-Map') != 'svg-route-v1'):
                        self._send(403, {'ok': False, 'error': 'same_origin_required'});return
                    if 'application/json' not in self.headers.get('Content-Type', ''):
                        self._send(415, {'ok': False});return
                    try:
                        length=int(self.headers.get('Content-Length', '0'))
                        if not 2 <= length <= 4096: raise ValueError('size')
                        data=json.loads(self.rfile.read(length).decode('utf-8'))
                        if not isinstance(data,dict): raise ValueError('payload')
                        action=data.get('action')
                        if action not in ('select', 'unlock', 'target'): raise ValueError('action')
                        if action=='select':
                            key=data.get('id')
                            if not isinstance(key,str) or not 1 <= len(key) <= 120: raise ValueError('id')
                        elif action=='target':
                            cc, fm = data.get('cc'), data.get('fm')
                            if type(cc) is not int or type(fm) is not int or not (1<=cc<=40 and 1<=fm<=20):
                                raise ValueError('target')
                        if archive is None:
                            self._send(503, {'ok':False, 'error':'archive_not_ready'});return
                        reply=queue.Queue(maxsize=1)
                        out.put_nowait(('svg_action', action, data, reply))
                        try: result=reply.get(timeout=2.5)
                        except queue.Empty: result={'ok':False,'error':'GUI busy','retryable':True}
                        self._send(200 if result.get('ok') else 409, result)
                    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError):
                        self._send(422, {'ok': False, 'error': 'invalid_request'})
                    except queue.Full:
                        self._send(503, {'ok': False, 'error': 'busy'})
                    return
                if self.path not in ('/deal','/visible','/select','/skip','/unlock'):
                    self._send(404, {'ok': False})
                    return
                # This is a local UI bridge, not a remote data service. Require
                # our extension's custom header and restrict the source to an
                # extension or requests with no Origin (background worker).
                origin = self.headers.get('Origin', '')
                if origin and not origin.startswith('chrome-extension://'):
                    self._send(403, {'ok': False, 'error': 'extension_origin_required'})
                    return
                if self.headers.get('X-FM-Rush-Bridge') != 'v17-browser-view':
                    self._send(403, {'ok': False, 'error': 'extension_header_required'})
                    return
                if 'application/json' not in self.headers.get('Content-Type', ''):
                    self._send(415, {'ok': False})
                    return
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if size < 2 or size > (MAX_VISIBLE_BYTES if self.path=='/visible' else MAX_REQUEST_BYTES):
                        raise ValueError('invalid request size')
                    data = json.loads(self.rfile.read(size).decode('utf-8'))
                    if not isinstance(data,dict):raise ValueError('request')
                    if self.path=='/visible':
                        if not isinstance(data,dict):raise ValueError('snapshot')
                        raw=data.get('deals');session=data.get('session');revision=data.get('revision')
                        if not isinstance(raw,list) or len(raw)>500 or not isinstance(session,str) or not 1<=len(session)<=120:
                            raise ValueError('snapshot')
                        if isinstance(revision,bool) or not isinstance(revision,int) or not 0<=revision<=2**53:
                            raise ValueError('revision')
                        icon_payload=data.get('focus_item_icon')
                        if icon_payload is not None:
                            if not isinstance(icon_payload,dict):raise ValueError('icon')
                            lid,png,url=icon_payload.get('listing_id'),icon_payload.get('png'),icon_payload.get('url')
                            if not isinstance(lid,str) or not 1<=len(lid)<=120:
                                raise ValueError('icon-id')
                            if png is not None and (not isinstance(png,str) or
                                not 40<=len(png)<=61000 or
                                not png.startswith('data:image/png;base64,')):
                                raise ValueError('icon-png')
                            if url is not None and (not isinstance(url,str) or
                                not re.fullmatch(r'https://(?:www\.)?henefm\.com/classic/items/\d{5,9}\.png',url)):
                                raise ValueError('icon-url')
                            if png is None and url is None:raise ValueError('icon-source')
                        deals=[parse_browser_deal(item) for item in raw]
                        if any(deal is None or not deal.listing_id for deal in deals):raise ValueError('listing')
                        if archive is None:
                            self._send(503,{'ok':False,'error':'archive_not_ready'});return
                        try:
                            applied=archive.apply_visible(deals,session,revision)
                            observed=data.get('observed_at_ms')
                            if applied and isinstance(observed,(int,float)) and not isinstance(observed,bool) and math.isfinite(observed):
                                import time
                                delay=time.time()*1000-observed
                                archive.last_feed_latency_ms=round(delay,1) if 0<=delay<60000 else None
                            out.put_nowait(('browser_visible',))
                            if applied and icon_payload:
                                # The selected listing is checked once again by the
                                # GUI, after it has synchronized current focus.
                                out.put_nowait(('browser_item_icon',icon_payload['listing_id'],icon_payload.get('png'),icon_payload.get('url')))
                        except (queue.Full,OSError,ValueError,sqlite3.Error):
                            self._send(503,{'ok':False,'error':'busy'});return
                        with archive.lock:
                            current=archive.current()
                            focused_id=current[1].listing_id if current else None
                            chase_locked=archive.chase_locked
                        self._send(200,{'ok':True,'live_listings':len(deals),
                            'focused_listing_id':focused_id,'chase_locked':chase_locked});return
                    deal = parse_browser_deal(data) if self.path!='/unlock' else None
                except (ValueError, UnicodeError, json.JSONDecodeError):
                    self._send(422, {'ok':False,'error':'invalid_request'});return
                if deal is None and self.path!='/unlock':
                    self._send(422, {'ok': False, 'error': 'invalid_listing'})
                    return
                try:
                    new=True
                    key=None
                    if archive is not None and deal is not None:key,new=archive.record(deal)
                    if self.path in ('/select','/skip','/unlock'):
                        if archive is None:
                            self._send(503,{'ok':False,'error':'archive_not_ready'});return
                        # Intent is applied on the GUI thread so click, skip,
                        # receipt and screen updates have one ordered owner.
                        session=data.get('_choice_session');revision=data.get('_choice_revision')
                        if not isinstance(session,str) or not 1<=len(session)<=120 or isinstance(revision,bool) or not isinstance(revision,int) or not 1<=revision<=2**53:
                            self._send(422,{'ok':False,'error':'invalid_choice_sequence'});return
                        reply=queue.Queue(maxsize=1)
                        out.put_nowait(('browser_choice',self.path[1:],key,session,revision,reply))
                        try:result=reply.get(timeout=2.5)
                        except queue.Empty:result={'ok':False,'error':'GUI busy; check lock indicator','retryable':True}
                        self._send(200 if result['ok'] else 409,result);return
                    else:out.put_nowait(('browser_deal', deal,new))
                except (queue.Full,OSError,ValueError,sqlite3.Error):
                    self._send(503, {'ok': False, 'error': 'busy'})
                    return
                self._send(200, {'ok': True, 'ign': deal.ign})

        self.server = ThreadingHTTPServer((HOST, PORT), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True,
                                       name='HeneFM Browser Bridge')
        self.thread.start()
        return HOST, PORT

    def stop(self):
        if self.server:
            try: self.server.shutdown()
            finally: self.server.server_close()
            self.server = None

