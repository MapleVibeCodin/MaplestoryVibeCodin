"""Incremental notification replay helpers; passive observations only."""
import json
import os
import math
from collections import Counter
from pathlib import Path

class SourceTail:
    """Read completed new lines once. Never consume an unfinished append."""
    def __init__(self, path):
        self.path=Path(path)
        self.offset=0
        self.identity=None
        self.rows=[]
    def poll(self):
        if not self.path.is_file():
            if self.offset: raise ValueError('notification source disappeared')
            return self.rows
        with self.path.open('rb') as f:
            st=os.fstat(f.fileno())
            identity=(st.st_dev,st.st_ino)
            if self.identity is not None and identity!=self.identity:
                raise ValueError('notification source replaced')
            if st.st_size<self.offset:raise ValueError('notification source truncated')
            self.identity=identity
            f.seek(self.offset)
            while True:
                line=f.readline()
                if not line or not line.endswith(b'\n'):break
                try:
                    row=json.loads(line)
                    if not isinstance(row,dict):raise ValueError('not an object')
                except (ValueError,UnicodeError):row={'invalid_source':True}
                self.rows.append(row)
                self.offset=f.tell()
        return self.rows

def consensus(a,b,c=None):
    """Require two matching parses, but never accept a contradictory parsed event."""
    valid=[x for x in (a,b,c) if x is not None]
    if len(valid)>=2 and all(x==valid[0] for x in valid):return valid[0]
    return None

MOB_DROPS={
    'echopus leg':'Echopus','jr. boogie horn':'Jr. Boogie',
    'aqumander tail':'Aqumander','duskmander tail':'Duskmander',
    'glowing mushroom spore':'Glowshroom','raffle petal':'Raffle',
    'golden stirge wing':'Golden Stirge','curse eye tail':'Curse Eye',
    'evil eye tail':'Evil Eye',
}

def breakdown(events,start=None,end=None):
    """Counts observed notifications and items, never inferred monster kills."""
    rows=[]
    for r in events:
        t=r.get('born')
        if not isinstance(t,(int,float)) or isinstance(t,bool) or not math.isfinite(t):continue
        if start is not None and t<start:continue
        if end is not None and t>end:continue
        rows.append(r)
    if start is None:start=min((r['born'] for r in rows),default=None)
    bins={};mobs=Counter();types=Counter();items=Counter()
    for r in rows:
        e=r.get('event');i=int((r['born']-start)//60)
        b=bins.setdefault(i,{'minute':i+1,'delivered_rows':0,'accepted_rows':0,'own_exp':0,'shared_exp':0,'party_bonus_exp':0,'mesos':0,'item_units':0})
        b['delivered_rows']+=1
        if not e:continue
        b['accepted_rows']+=1;types[e[0]]+=1
        if e[0] in ('own_exp','shared_exp','party_bonus_exp','mesos'):b[e[0]]+=e[1]
        elif e[0]=='item':
            items[(e[1],e[3])]+=e[2];b['item_units']+=e[2]
            mob=MOB_DROPS.get(e[1].casefold())
            if mob and e[3]=='etc':mobs[mob]+=e[2]
    return {'minute_bins':[bins[i] for i in sorted(bins)],'event_type_counts':dict(types),
            'species_drop_units':dict(mobs),'known_item_units':sum(items.values()),
            'party_evidence':bool(types['shared_exp'] or types['party_bonus_exp']),
            'personal_kills':None,'note':'Observed item units linked to species; not kill counts. Missing rows and capture gaps are not zero.'}
