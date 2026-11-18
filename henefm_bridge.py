"""Optional, localhost-only HeneFM browser-extension bridge.

Receives only one HeneFM Flips deal at a time (as shown on the user's
browser page) and hands it to the GUI. No API key, no network requests,
listing metadata can be persisted locally before delivery is acknowledged.
"""
from __future__ import annotations
import json
import math
import queue
import threading
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from deal_parser import Deal
from profit_filter import ProfitDecision

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


class BrowserBridge:
    """Small receiver on 127.0.0.1; posts accepted deals into an existing queue."""
    def __init__(self, out: queue.Queue, archive=None):
        self.out = out
        self.archive=archive
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        out = self.out
        archive=self.archive

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
                    self._send(200, {'ok': True, 'name': 'FM Rush v24.17'});
                else:
                    self._send(404, {'ok': False})

            def do_POST(self):
                if self.path not in ('/deal','/visible','/select','/skip'):
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
                    if self.path=='/visible':
                        if not isinstance(data,dict):raise ValueError('snapshot')
                        raw=data.get('deals');session=data.get('session');revision=data.get('revision')
                        if not isinstance(raw,list) or len(raw)>500 or not isinstance(session,str) or not 1<=len(session)<=120:
                            raise ValueError('snapshot')
                        if isinstance(revision,bool) or not isinstance(revision,int) or not 0<=revision<=2**53:
                            raise ValueError('revision')
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
                        except (queue.Full,OSError,ValueError,sqlite3.Error):
                            self._send(503,{'ok':False,'error':'busy'});return
                        self._send(200,{'ok':True,'live_listings':len(deals)});return
                    deal = parse_browser_deal(data)
                except (ValueError, UnicodeError, json.JSONDecodeError):
                    deal = None
                if deal is None:
                    self._send(422, {'ok': False, 'error': 'invalid_listing'})
                    return
                try:
                    new=True
                    key=None
                    if archive is not None:key,new=archive.record(deal)
                    if self.path in ('/select','/skip'):
                        if archive is None:
                            self._send(503,{'ok':False,'error':'archive_not_ready'});return
                        # Intent is applied on the GUI thread so click, skip,
                        # receipt and screen updates have one ordered owner.
                        session=data.get('_choice_session');revision=data.get('_choice_revision')
                        if not isinstance(session,str) or not 1<=len(session)<=120 or isinstance(revision,bool) or not isinstance(revision,int) or not 1<=revision<=2**53:
                            self._send(422,{'ok':False,'error':'invalid_choice_sequence'});return
                        out.put_nowait(('browser_choice',self.path[1:],key,session,revision))
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
