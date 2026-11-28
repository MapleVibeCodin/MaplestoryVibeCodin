"""Passive per-species accounting; base-EXP equivalents are conditional, not kills."""
import csv,json,hashlib
from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path

# map ID, species, base EXP, observed species-linked item, known NPC price
Z=('Zombie Mushroom',45,'Charm of the Undead',24)
B=('Jr. Boogie',69,'Jr. Boogie Horn',35)
E=('Echopus',107,'Echopus Leg',44)
D=('Duskmander',133,'Duskmander Tail',49)
L=('Zombie Lupin',89,'Cursed Doll',40)
G=('Golden Stirge',93,'Golden Stirge Wing',42)
R=('Rafflesia',117,'Rafflesia Petal',47)
A=('Aqumander',98,'Aqumander Tail',43)
S=('Glowshroom',82,'Glowing Mushroom Spore',39)
F=('Raffle',85,'Raffle Petal',40)
Y=('Fairy 4',54,"Fairy's Tentacle",None)
M=('Myewood',160,None,None)
T=('Rotten Mushroom',183,None,None)
MAPS={'The Faded Canopy':('010006072',(S,F,E)), 'Perilous Descent I':('010006090',(Z,B,E)), 'Perilous Descent II':('010006100',(Z,B,E,D)), 'Perilous Descent III':('010006110',(E,D)), 'Decayed Tunnel II':('010006130',(B,L,G,R)), 'Lingering Regret':('010006150',(Y,E,M)), 'Precipice of Darkness':('010006160',(Z,L,D,T)), 'Forgotten Entrance I':('010006040',(F,G,A)), 'Primeval Forest I':('010006010',(S,A,E)), 'Primeval Forest II':('010006020',(E,G,A)), 'Primeval Forest III':('010006030',(A,F)), 'The Valley of Death':('010006031',(Z,B,L,R)), 'Decayed Tunnel III':('010006140',(G,R,M))}

def digest(b):return hashlib.sha256(b).hexdigest()
def canon(r):return json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def rate(v,s):return round(v*3600/s,1) if v is not None and s>=60 else None
@lru_cache(maxsize=4096)
def bounds(delta,values):
    # DP: independent minima/maxima per species and total. No exponential enumeration.
    if not 0<delta<=10000:return None
    n=len(values);dp=[None]*(delta+1);dp[0]=((0,)*(n+1),(0,)*(n+1))
    for x in range(1,delta+1):
        for i,v in enumerate(values):
            if x<v or dp[x-v] is None:continue
            lo,hi=dp[x-v];a=tuple(k+(j==i or j==n) for j,k in enumerate(lo));b=tuple(k+(j==i or j==n) for j,k in enumerate(hi))
            if dp[x] is None:dp[x]=(a,b)
            else:dp[x]=(tuple(map(min,zip(dp[x][0],a))),tuple(map(max,zip(dp[x][1],b))))
    return dp[delta]

def analyze(read,exists):
    records=[];prev=None
    for i,line in enumerate(read('evidence_journal.jsonl').splitlines(),1):
        r=json.loads(line);h=r.pop('sha256')
        if digest(canon(r))!=h:
            if r.get('kind')!='minimap_file' or r.get('file')!='minimap_observations.jsonl' or 'file_sha256' in r or digest(canon(dict(r,sha256=digest(read('minimap_observations.jsonl')))))!=h:raise ValueError('journal digest mismatch')
        if r['sequence']!=i or r['previous_sha256']!=prev:raise ValueError('journal chain mismatch')
        prev=h;records.append(r)
    groups=defaultdict(dict)
    for r in records:
        if r['kind']!='frame':continue
        raw=read(r['file'].rsplit('.',1)[0]+'.json')
        if digest(raw)!=r['sidecar_sha256']:raise ValueError('sidecar mismatch')
        f=json.loads(raw);c=f.get('context') or {};age=f.get('context_age_seconds')
        if not isinstance(age,(float,int)) or not 0<=age<=1 or c.get('map_uncertain') or c.get('map') not in MAPS:continue
        if not c.get('exp_confident') or c.get('exp_estimated') or type(c.get('exp')) is not int or not isinstance(c.get('monotonic'),(int,float)):continue
        key=(c['map'],c.get('recording_epoch'),c.get('level'),c.get('segment'))
        groups[key][c['monotonic']]=c
    notifications=[];source='legacy_scoped_journal'
    if exists('notification_events.jsonl'):
        source='secondary_notification_reader'
        raw=read('message_evidence/lines.jsonl');ev=read('notification_events.jsonl')
        for name,b in [('message_evidence/lines.jsonl',raw),('notification_events.jsonl',ev)]:
            seals=[r for r in records if r.get('file')==name and r.get('file_sha256')]
            if not seals or seals[-1]['file_sha256']!=digest(b):raise ValueError('notification seal missing or invalid')
        rows=[json.loads(l) for l in raw.splitlines()];events=[json.loads(l) for l in ev.splitlines()]
        for i,r in enumerate(events):
            if r['index']!=i or digest(canon(rows[i]))!=r['source_sha256']:raise ValueError('notification source mismatch')
            if r.get('status')=='accepted' and r.get('event'):notifications.append((r.get('born'),r.get('map'),r.get('epoch'),None,r['event']))
    else:
        for r in records:
            sc=r.get('scope') or {}
            if r['kind']=='accepted_pickups':
                for e in r.get('messages',[]):notifications.append((r['monotonic'],sc.get('map'),None,sc.get('segment'),e))
    out=[]
    for (name,epoch,level,seg),obs in groups.items():
        obs=sorted(obs.items());a,b=obs[0][0],obs[-1][0];seconds=b-a
        if seconds<10:continue
        specs=MAPS[name][1];values=tuple(s[1] for s in specs);n=len(values)
        lo=[0]*(n+1);hi=lo.copy();matched=unmatched=0;gap_exp=0
        for (t,c),(u,d) in zip(obs,obs[1:]):
            delta=d['exp']-c['exp']
            if delta<=0:continue
            if u-t>3:gap_exp+=delta;continue
            v=bounds(delta,values)
            if v is None:unmatched+=delta;continue
            matched+=delta;lo=[x+y for x,y in zip(lo,v[0])];hi=[x+y for x,y in zip(hi,v[1])]
        w={c['wallet_observed_at']:c['wallet'] for t,c in obs if type(c.get('wallet')) is int and isinstance(c.get('wallet_observed_at'),(float,int)) and isinstance(c.get('wallet_age'),(float,int)) and 0<=c['wallet_age']<=1 and a<=c['wallet_observed_at']<=b}
        w=sorted(w.items());wallet=None;ws=0;wallet_bad=False
        if len(w)>1:
            # Detect drastic digit truncation; do not repair balances from a guessed prefix.
            maxw=max(v for _,v in w);wallet_bad=any(v<maxw/100 for _,v in w) if maxw>=100000 else False
            if not wallet_bad:wallet=w[-1][1]-w[0][1];ws=w[-1][0]-w[0][0]
        events=[e for t,m,ep,s,e in notifications if isinstance(t,(float,int)) and a<=t<=b and m==name and (ep==epoch if source=='secondary_notification_reader' else s==seg)]
        items=Counter();rawmeso=[];awards=Counter();party=False
        for e in events:
            if e[0]=='item' and len(e)==4 and type(e[2]) is int and e[2]>0 and e[3].casefold()=='etc':items[e[1].casefold()]+=e[2]
            elif e[0]=='mesos' and type(e[1]) is int:rawmeso.append(e[1])
            elif e[0]=='own_exp':awards[e[1]]+=1
            elif e[0] in ('shared_exp','party_bonus_exp'):party=True
        coverage=matched/(obs[-1][1]['exp']-obs[0][1]['exp']) if obs[-1][1]['exp']>obs[0][1]['exp'] else None
        reliable_model=coverage is not None and .8<=coverage<=1
        detail=[]
        for i,(mob,xp,item,price) in enumerate(specs):
            qty=items.get(item.casefold()) if item else None;v=qty*price if qty is not None and price is not None else None
            detail.append(dict(monster=mob,base_exp=xp,eq_min=lo[i],eq_max=hi[i],eq_hr_min=rate(lo[i],seconds),eq_hr_max=rate(hi[i],seconds),matching_own_awards=awards.get(xp) if source=='secondary_notification_reader' and awards else None,drop_item=item,observed_drop_units=qty,known_npc= v,known_npc_per_equivalent_min=round(v/hi[i],2) if reliable_model and v is not None and hi[i]>0 else None,known_npc_per_equivalent_max=round(v/lo[i],2) if reliable_model and v is not None and lo[i]>0 else None,attributed_raw_mesos=None,raw_mesos_per_mob=None,combined_mesos_per_mob=None,combined_mesos_hr=None,personal_kills=None))
        # Same elapsed interval for notification-based aggregate equivalent ratios.
        # These are observed receipts per modeled equivalent, not expected drops per kill.
        npc=[s['known_npc'] for s in detail if s['known_npc'] is not None]
        raw=sum(rawmeso) if rawmeso else None
        def per_equivalent(v):
            return [round(v/hi[-1],2),round(v/lo[-1],2)] if reliable_model and v is not None and lo[-1]>0 else None
        # Wallet is a separate window; don't divide it by whole-interval equivalents.
        out.append(dict(map=name,epoch=epoch,seconds=round(seconds,2),exp=obs[-1][1]['exp']-obs[0][1]['exp'],exp_hr=rate(obs[-1][1]['exp']-obs[0][1]['exp'],seconds),matched_exp=matched,match_fraction=coverage,model_coverage_ok=reliable_model,observed_raw_per_equivalent=per_equivalent(raw),observed_known_npc_per_equivalent=per_equivalent(sum(npc) if npc else None),observed_combined_per_equivalent=per_equivalent(raw+sum(npc) if raw is not None and npc else None),unmatched_exp=unmatched,gap_exp=gap_exp,total_eq_min=lo[-1],total_eq_max=hi[-1],eq_hr_min=rate(lo[-1],seconds),eq_hr_max=rate(hi[-1],seconds),wallet_seconds=round(ws,2),wallet_hr=rate(wallet,ws),wallet_suspect=wallet_bad,observed_raw_mesos=sum(rawmeso) if rawmeso else None,unassigned_raw_mesos=sum(rawmeso) if rawmeso else None,party_evidence=party,source=source,species=detail))
    return sorted(out,key=lambda r:(-r['seconds'],r['map']))

def report_folder(folder):
    folder=Path(folder); rows=analyze(lambda n:(folder/n).read_bytes(),lambda n:(folder/n).is_file())
    (folder/'species_report.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    flat=[dict(map=r['map'],epoch=r['epoch'],seconds=r['seconds'],**s) for r in rows for s in r['species']]
    with (folder/'species_report.csv').open('w',encoding='utf-8',newline='') as f:
        if flat:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    # Each immutable local session folder has its own report. Never upload raw session data.
    return rows
