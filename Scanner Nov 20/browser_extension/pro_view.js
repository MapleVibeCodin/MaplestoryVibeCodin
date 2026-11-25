/* Local visual layer; never changes listing order, visibility or bridge payloads. */
(() => {
  'use strict';
  const profiles={normal:[15000,15],strict:[20000,20],high:[30000,20],all:[0,0]};
  const css=`
html[data-fm-pro="on"] [data-fm-pro-tier="exceptional"]{box-shadow:inset 4px 0 #a855f7!important}
html[data-fm-pro="on"] [data-fm-pro-tier="excellent"]{box-shadow:inset 4px 0 #22c55e!important}
html[data-fm-pro="on"] [data-fm-pro-tier="good"]{box-shadow:inset 4px 0 #3b82f6!important}
html[data-fm-pro="on"] [data-fm-pro-tier="qualified"]{box-shadow:inset 4px 0 #eab308!important}
html[data-fm-pro="on"] [data-fm-pro-tier="low"]:not(.fm-rush-focus){opacity:.68}
html[data-fm-pro="on"] [data-fm-pro-tier="npc"]:not(.fm-rush-focus){opacity:.58}
html[data-fm-pro="on"] [data-fm-pro-tier="sold"]:not(.fm-rush-focus){opacity:.50}
html[data-fm-pro="on"] [data-fm-rush-controls][data-fm-pro-summary]::before{content:attr(data-fm-pro-summary);flex:1 1 0;min-width:0;align-self:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font:600 12px system-ui;color:inherit;opacity:.94}
html[data-fm-pro="on"] [data-fm-pro-tier="exceptional"] [data-fm-rush-controls]::before,html[data-fm-pro="on"] [data-fm-pro-tier="excellent"] [data-fm-rush-controls]::before{font-weight:800}
`;
  const money=n=>!Number.isFinite(n)?'—':Math.abs(n)>=1e6?`${+(n/1e6).toFixed(2)}M`:Math.abs(n)>=1000?`${+(n/1000).toFixed(1)}K`:`${n}`;
  function model(deal,profile='normal'){
    const [min,pct]=profiles[profile]||profiles.normal;
    const gain=deal.profit_mesos,roi=deal.profit_percent;
    const npc=/NPC shop|no selling fee/i.test(deal.raw_text||'');
    const qualifies=Number.isFinite(gain)&&Number.isFinite(roi)&&gain>=min&&roi>=pct;
    const tier=deal.sold?'sold':!qualifies?'low':gain>=100000?'exceptional':gain>=50000?'excellent':gain>=30000?'good':'qualified';
    const status=deal.sold?'SOLD':npc?'NPC':deal.unusually_cheap?'CHECK PRICE':'';
    const profit=Number.isFinite(gain)?`${gain>=0?'+':''}${money(gain)}`:'—';
    const location=deal.cc&&deal.fm?`CH ${deal.cc} / FM ${deal.fm}`:'Location unknown';
    const summary=[profit,Number.isFinite(roi)?`${roi}%`:null,location,status].filter(Boolean).join(' · ');
    return {tier:npc&&!qualifies&&!deal.sold?'npc':tier,summary};
  }
  function paint(card,deal,profile){
    if(!card?.isConnected)return false;
    const controls=card.querySelector('[data-fm-rush-controls]');
    if(!controls)return false;
    const {tier,summary}=model(deal,profile);
    let changed=false;
    if(card.getAttribute('data-fm-pro-tier')!==tier){card.setAttribute('data-fm-pro-tier',tier);changed=true;}
    if(controls.getAttribute('data-fm-pro-summary')!==summary){controls.setAttribute('data-fm-pro-summary',summary);changed=true;}
    return changed;
  }
  function create(){
    let enabled=false,profile='normal',rows=[],cursor=0,scheduled=false,revision=0;
    const costs=[];let painted=0,changed=0;
    function schedule(){if(!enabled||scheduled||cursor>=rows.length)return;scheduled=true;requestAnimationFrame(batch);}
    function batch(){
      scheduled=false;if(!enabled)return;
      const t=performance.now();let n=0;
      while(cursor<rows.length&&n<20&&performance.now()-t<2){const {card,deal}=rows[cursor++];if(paint(card,deal,profile))changed++;painted++;n++;}
      costs.push(performance.now()-t);if(costs.length>300)costs.shift();schedule();
    }
    function configure(on,p){
      enabled=!!on;profile=profiles[p]?p:'normal';
      if(enabled&&!document.getElementById('fm-rush-pro-style')){const el=document.createElement('style');el.id='fm-rush-pro-style';el.setAttribute('data-fm-rush-controls','true');el.textContent=css;(document.head||document.documentElement).appendChild(el);}
      document.documentElement.setAttribute('data-fm-pro',enabled?'on':'off');cursor=0;revision++;schedule();
    }
    function update(next){if(next===rows)return;rows=next;cursor=0;revision++;schedule();}
    function status(){const a=costs.slice().sort((x,y)=>x-y);const p=q=>a.length?+a[Math.min(a.length-1,Math.ceil(q*a.length)-1)].toFixed(3):null;return {enabled,profile,painted,changed,batches:a.length,p50_ms:p(.5),p95_ms:p(.95),revision};}
    return {configure,update,status};
  }
  globalThis.FMRushPro={create,model,paint,css};
})();
