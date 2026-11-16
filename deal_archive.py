"""Durable listings indexed by IGN; only pending work is kept in memory."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import threading
import time
from deal_parser import Deal
from profit_filter import ProfitDecision

_UNCHANGED=object()
LIVE_PAGE_LEASE_SECONDS=45.0


class DealArchive:
    def __init__(self,path):
        self.path=Path(path);self.lock=threading.RLock()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS listings (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE, ign TEXT, done INTEGER, data TEXT NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS pending_listings ON listings(done,seq)')
        self.db.execute('CREATE INDEX IF NOT EXISTS seller_listings ON listings(ign)')
        self.db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        self._pending={key:json.loads(value) for key,value in self.db.execute(
            'SELECT id,data FROM listings WHERE done=0 ORDER BY seq')}
        self.focus=self._setting('focus')
        self.last_completed=self._setting('last_completed')
        self._live_keys=();self._live_seen=None;self._live_generation=0;self._live_revisions={}
        if self.focus not in self._pending:self.focus=next(iter(self._pending),None)

    def _setting(self,key):
        row=self.db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else None

    @property
    def records(self):
        with self.lock:
            return {key:json.loads(value) for key,value in self.db.execute('SELECT id,data FROM listings ORDER BY seq')}

    def _save(self,key,record,focus,last_completed=_UNCHANGED):
        # Update caches only AFTER durable commit, so failed delivery can retry.
        with self.db:
            self.db.execute('INSERT INTO listings(id,ign,done,data) VALUES (?,?,?,?) '
                'ON CONFLICT(id) DO UPDATE SET ign=excluded.ign,done=excluded.done,data=excluded.data',
                (key,record['deal']['ign'].casefold(),int(record['done']),json.dumps(record,ensure_ascii=False)))
            self.db.execute("INSERT OR REPLACE INTO settings VALUES ('focus',?)",(json.dumps(focus),))
            if last_completed is not _UNCHANGED:
                self.db.execute("INSERT OR REPLACE INTO settings VALUES ('last_completed',?)",(json.dumps(last_completed),))
        if record['done']:self._pending.pop(key,None)
        else:self._pending[key]=record
        self.focus=focus
        if last_completed is not _UNCHANGED:self.last_completed=last_completed

    def record(self,deal):
        payload=asdict(deal)
        identity=[deal.listing_id,deal.ign.casefold(),deal.cc,deal.fm,deal.item,deal.stats,deal.buy_mesos]
        key=sha256(json.dumps(identity,ensure_ascii=False).encode()).hexdigest()[:24]
        with self.lock:
            existing=self._pending.get(key)
            if existing is None:
                row=self.db.execute('SELECT data FROM listings WHERE id=?',(key,)).fetchone()
                existing=json.loads(row[0]) if row else None
            new=existing is None
            if existing is not None and existing['deal']==payload:return key,False
            record={'deal':payload,'first_seen':time.time(),'last_seen':time.time(),'done':False} if new else {
                **existing,'deal':payload,'last_seen':time.time()}
            focus=self.focus or (key if not record['done'] else None)
            self._save(key,record,focus)
            return key,new

    def apply_visible(self,deals,session,revision,now=None):
        """Replace the live scan set after all listings have been durably archived."""
        with self.lock:
            if revision<=self._live_revisions.get(session,-1):return False
            first_page=self._live_seen is None
            keys=tuple(dict.fromkeys(self.record(deal)[0] for deal in deals))
            self._live_keys=keys;self._live_seen=time.monotonic() if now is None else now
            self._live_generation+=1
            self._live_revisions[session]=revision
            if len(self._live_revisions)>32:self._live_revisions.pop(next(iter(self._live_revisions)))
            if self.focus is None or (first_page and self.focus not in keys):
                first=next((key for key in keys if key in self._pending),None)
                if first:self.select(first)
            return True

    def live_state(self,now=None):
        with self.lock:
            now=time.monotonic() if now is None else now
            return self._live_generation,self._live_seen is not None and now-self._live_seen<LIVE_PAGE_LEASE_SECONDS

    def live_pending(self,now=None):
        with self.lock:
            if not self.live_state(now)[1]:return []
            return [(key,dict(self._pending[key]['deal'])) for key in self._live_keys if key in self._pending]

    def live_names(self):
        with self.lock:
            names={}
            for _,deal in self.live_pending():names.setdefault(deal['ign'].casefold(),deal['ign'])
            return tuple(names.values())

    def _next_pending(self,key):
        # Retain legacy archive operations before a live page has ever connected.
        keys=self._pending if self._live_seen is None else [item for item,_ in self.live_pending()]
        return next((item for item in keys if item!=key),None)

    def pending(self):
        with self.lock:return [(key,dict(value['deal'])) for key,value in self._pending.items()]

    def names(self):
        with self.lock:
            rows=self.pending();rows.sort(key=lambda row:row[0]!=self.focus)
            seen=set();names=[]
            for _,deal in rows:
                name=deal['ign']
                if name.casefold() not in seen:names.append(name);seen.add(name.casefold())
            return tuple(names)

    def current(self):
        with self.lock:
            if self.focus is None:return None
            data=dict(self._pending[self.focus]['deal']);data['profit']=ProfitDecision(**data['profit'])
            return self.focus,Deal(**data)

    def select(self,key):
        with self.lock:
            if key not in self._pending or key==self.focus:return
            self._save(key,self._pending[key],key)

    def complete_current(self):
        with self.lock:
            key=self.focus
            if key is None:return
            record={**self._pending[key],'done':True}
            following=self._next_pending(key)
            self._save(key,record,following,last_completed=key)

    def mark_bought(self,key,screenshot):
        with self.lock:
            if key not in self._pending:return False
            record={**self._pending[key],'done':True,'bought_at':time.time(),
                    'bought_screenshot':str(screenshot)}
            following=self._next_pending(key) if self.focus==key else self.focus
            self._save(key,record,following,last_completed=key)
            return True

    def undo_complete(self):
        with self.lock:
            key=self.last_completed
            if key is None:return
            row=self.db.execute('SELECT data FROM listings WHERE id=?',(key,)).fetchone()
            if row is None:return
            record={**json.loads(row[0]),'done':False}
            self._save(key,record,key,last_completed=None)

    def export_json(self,path):
        with self.lock:
            grouped={}
            for key,value in self.records.items():
                grouped.setdefault(value['deal']['ign'],[]).append({'id':key,**value})
            Path(path).write_text(json.dumps({'by_ign':grouped},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def close(self):
        with self.lock:self.db.close()
