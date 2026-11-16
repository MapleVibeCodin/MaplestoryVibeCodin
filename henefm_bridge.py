"""Optional, localhost-only HeneFM browser-extension bridge.

Receives only one HeneFM Flips deal at a time (as shown on the user's
browser page) and hands it to the GUI. No API key, no network requests,
no shop listing/price data downloaded or saved.
"""
from __future__ import annotations
import json
import math
import queue
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from deal_parser import Deal
from profit_filter import ProfitDecision

MIN_MESOS = 15_000
MIN_PERCENT = 15.0

HOST = '127.0.0.1'
PORT = 18773
MAX_REQUEST_BYTES = 10_240


def parse_browser_deal(raw: dict) -> Deal | None:
    """Strict fail-closed validation of a single browser-visible flip."""
    if not isinstance(raw, dict):
        return None
    try:
        cc = int(raw['cc'])
        fm = int(raw['fm'])
        buy = int(raw['buy_mesos'])
        gain = int(raw['profit_mesos'])
        pct = float(raw['profit_percent'])
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    # Do not allow coercion of nonintegers, enormous values or percentages.
    if not (1 <= cc <= 40 and 1 <= fm <= 20 and 1 <= buy <= 1_000_000_000_000):
        return None
    if not (0 <= gain <= 1_000_000_000_000 and math.isfinite(pct) and 0 <= pct <= 100_000_000_000_000):
        return None
    unusually_cheap = raw.get('unusually_cheap') is True
    if not unusually_cheap and not (gain >= MIN_MESOS and pct >= MIN_PERCENT):
        return None
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
                profit=ProfitDecision(True, gain, pct, 'unusually cheap' if unusually_cheap else 'passed'))


class BrowserBridge:
    """Small receiver on 127.0.0.1; posts accepted deals into an existing queue."""
    def __init__(self, out: queue.Queue):
        self.out = out
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        out = self.out

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
                    self._send(200, {'ok': True, 'name': 'FM Rush v22.2'});
                else:
                    self._send(404, {'ok': False})

            def do_POST(self):
                if self.path != '/deal':
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
                    if size < 2 or size > MAX_REQUEST_BYTES:
                        raise ValueError('invalid request size')
                    data = json.loads(self.rfile.read(size).decode('utf-8'))
                    deal = parse_browser_deal(data)
                except (ValueError, UnicodeError, json.JSONDecodeError):
                    deal = None
                if deal is None:
                    self._send(422, {'ok': False, 'error': 'deal_must_pass_filter'})
                    return
                try:
                    out.put_nowait(('browser_deal', deal))
                except queue.Full:
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
