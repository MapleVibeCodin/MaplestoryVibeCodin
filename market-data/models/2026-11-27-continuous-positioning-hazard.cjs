function experiment(raw){
 const start=Date.parse("2026-11-27T19:36:00+08:00")/1000, times=["20:35:05.774","21:02:59.731","21:19:37.057"].map(x=>Date.parse("2026-11-27T"+x+"+08:00")/1000-start);
 const all=raw.split(/\r?\n/).slice(1).filter(Boolean).map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("invalid record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-start,c:+m[6]-1,f:+m[7]};}).filter(x=>x.t>=0).sort((a,b)=>a.t-b.t);
 const seen=new Map(),ev=all.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true});
 const bins=[2,5,10,20,40,60,120,300,600,900,1800,Infinity],bin=a=>bins.findIndex(b=>a<b);
 const stats=Array.from({length:2},()=>Array.from({length:36},()=>({n:0,y:0}))),global=Array.from({length:2},()=>({n:0,y:0}));
 const last=Array(40).fill(-100000),onset=last.slice(),cnt=Array(40).fill(1),grid=[],end=Math.floor(times[2]), counts=Array.from({length:40},()=>new Int32Array(end+16));
 for(const e of ev) counts[e.c][Math.floor(e.t)+1]++;
 for(const a of counts)for(let i=1;i<a.length;i++)a[i]+=a[i-1];
 let j=0;
 for(let t=0;t<=end;t++){
  while(j<ev.length&&ev[j].t<t){let e=ev[j++];if(e.t-last[e.c]>60)onset[e.c]=e.t;last[e.c]=e.t;cnt[e.c]++;}
  let keys=last.map((v,c)=>{let age=t-onset[c],d=Math.abs(age-855*Math.max(1,Math.round(age/855)));return bin(t-v)*3+(age>200&&d<120?0:age>200&&d<240?1:2);});
  let freq=cnt.map(n=>n/cnt.reduce((a,b)=>a+b,0));
  if(t+12<=times[0]){
   for(let c=0;c<40;c++)for(let h=0;h<2;h++){let lo=h?2:0,hi=h?12:2,y=counts[c][t+hi]-counts[c][t+lo];let s=stats[h][keys[c]];s.n++;s.y+=y;global[h].n++;global[h].y+=y;}
  }else if(t>=Math.ceil(times[0])){
   let rates=keys.map((k,c)=>stats.map((s,h)=>{let g=global[h].y/global[h].n;return (s[k].y+120*g)/(s[k].n+120)*Math.sqrt(freq[c]*40);}));
   grid[t]={rates,freq};
  }
 }
 function sim(lo,hi,policy){
  let es=ev.filter(e=>e.t>lo&&e.t<=hi),current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,prevSpec=-Infinity,sp=0,react=0,lat=0,early=0,occupied=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo;
  function move(c,t,spec){if(c===current)return;target=c;done=t+2;occupied+=Math.min(2,hi-t);if(spec){sp++;prevSpec=t}else react++;}
  while(i<es.length||tick<=hi){
   let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);
   if(!isFinite(t)||t>hi)break;clock=t;
   if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
   if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push(cost);if(busy)queued=e.c;else move(e.c,t,false);}
   if(tt===t){tick++;if(policy&&done<=t&&t-prevSpec>=policy.cool&&grid[t]){let {rates,freq}=grid[t],v=rates.map((p,c)=>policy.model==="frequency"?freq[c]:p[1]-policy.risk*p[0]),best=v.reduce((b,x,c)=>x>v[b]?c:b,current);if(best!==current&&v[best]-v[current]>policy.threshold)move(best,t,true);}}
  }
  return {n:es.length,lat,early,sp,react,occupied,rows};
 }
 const valbase=sim(times[0],times[1],null),testbase=sim(times[1],times[2],null),candidates=[];
 for(let model of ["hazard","frequency"])for(let risk of [0,1,2,4])for(let threshold of [.005,.015,.03,.06,.1,.2,.4])for(let cool of [5,15,30,60]){let p={model,risk,threshold,cool};let v=sim(times[0],times[1],p);candidates.push({p,net:valbase.lat-v.lat,sp:v.sp,early:v.early});}
 candidates.push({p:null,net:0,sp:0,early:valbase.early});candidates.sort((a,b)=>b.net-a.net||a.sp-b.sp);
 const best=candidates[0],val=sim(times[0],times[1],best.p),test=sim(times[1],times[2],best.p);
 const summarize=(base,run)=>({n:base.n,baselineLatency:base.lat,policyLatency:run.lat,net:base.lat-run.lat,baselineEarly:base.early,policyEarly:run.early,speculative:run.sp,baselineReactive:base.react,reactive:run.react,baselineOccupied:base.occupied,occupied:run.occupied,gain:run.rows.filter((v,i)=>base.rows[i]-v>=1-1e-8).length,loss:run.rows.filter((v,i)=>v-base.rows[i]>=1-1e-8).length});
 return {raw:all.length,consolidated:ev.length,cutoffs:times,trainingExposure:global,selected:best,validation:summarize(valbase,val),test:summarize(testbase,test),top:candidates.slice(0,10),candidateCount:candidates.length,note:"Retrospective, not prospective; simulator earliest possible arrival if alert prioritized, latest queued reactive event; no walking or profit labels, filename timing proxy. Initial state reset at split only. Ties in grid: process alert before speculative decision. Forecast features only strict past; train windows end before training cutoff."};
}
if(typeof require!=='undefined'&&require.main===module){console.log(JSON.stringify(experiment(require('fs').readFileSync(process.argv[2],'utf8')),null,2));}
