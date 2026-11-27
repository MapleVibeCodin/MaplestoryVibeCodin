function experiment(raw){
const origin=Date.parse("2026-11-27T19:36:00+08:00")/1000,cut=["20:35:05.774","21:02:59.731","21:19:37.057"].map(x=>Date.parse("2026-11-27T"+x+"+08:00")/1000-origin);
const all=raw.split(/\r?\n/).slice(1).filter(Boolean).map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("invalid record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6]-1,f:+m[7]};}).filter(e=>e.t>=0).sort((a,b)=>a.t-b.t);
const seen=new Map(),ev=all.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true});
const dt=.5,ageBins=[1,2,5,10,20,40,60,120,300,600,1200,Infinity],gapBins=[.5,1,2,5,10,30,60,Infinity],bin=(x,b)=>b.findIndex(v=>x<v),A=ageBins.length,G=gapBins.length;
const stats=Array.from({length:A*G},()=>[0,0]),ages=Array.from({length:A},()=>[0,0]),gaps=Array.from({length:G},()=>[0,0]),ch=Array(40).fill(0);let exposure=0,events=0;
let last=Array(40).fill(-1e6),globalLast=-1e6,j=0;
for(let t=0;t+dt<=cut[0];t+=dt){
 while(j<ev.length&&ev[j].t<t){let e=ev[j++];last[e.c]=e.t;globalLast=e.t;}
 let counts=Array(40).fill(0),k=j;while(k<ev.length&&ev[k].t<t+dt){counts[ev[k].c]++;k++;}
 let g=bin(t-globalLast,gapBins);
 for(let c=0;c<40;c++){let a=bin(t-last[c],ageBins),y=counts[c];for(let s of [stats[a*G+g],ages[a],gaps[g]]){s[0]+=dt;s[1]+=y;}ch[c]+=y;events+=y;exposure+=dt;}
}
const base=events/exposure;
const freq=ch.map(v=>(v+10)/(events+400)*40);
function rate(a,g,c,shrink){let aa=ages[a],gg=gaps[g],s=stats[a*G+g],pa=(aa[1]+100*base)/(aa[0]+100),pg=(gg[1]+100*base)/(gg[0]+100),prior=Math.sqrt(pa*pg);return Math.max(1e-6,(s[1]+shrink*prior)/(s[0]+shrink)*Math.sqrt(freq[c]));}
const grids={};last=Array(40).fill(-1e6);globalLast=-1e6;j=0;
for(let t=0;t<=cut[2];t+=1){
 while(j<ev.length&&ev[j].t<t){let e=ev[j++];last[e.c]=e.t;globalLast=e.t;}
 if(t<Math.ceil(cut[0]))continue;
 let variants={};
 for(let shrink of [30,120,480]){
 let surv=1,prob=Array(40).fill(0),early=Array(40).fill(0),weighted=Array(40).fill(0),remaining=0,step0=null;
 for(let u=0;u<30;u+=dt){let g=bin(t+u-globalLast,gapBins),rates=last.map((v,c)=>rate(bin(t+u-v,ageBins),g,c,shrink)),total=rates.reduce((a,b)=>a+b,0),mass=surv*(-Math.expm1(-dt*total)),mid=u+dt/2;
 if(!step0)step0=rates;
 for(let c=0;c<40;c++){let p=mass*rates[c]/total;prob[c]+=p;early[c]+=mid<2?p:0;weighted[c]+=p*Math.min(2,mid);}
 remaining+=mass*Math.max(0,2-mid);surv-=mass;
 }
 variants[shrink]={prob,weighted,remaining,surv,step0};
 }
 grids[t]=variants;
}
function sim(lo,hi,policy){
 let es=ev.filter(e=>e.t>lo&&e.t<=hi),current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,prevSpec=-Infinity,sp=0,react=0,lat=0,early=0,occupied=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo;
 function move(c,t,spec){if(c===current)return;target=c;done=t+2;occupied+=Math.min(2,hi-t);if(spec){sp++;prevSpec=t}else react++;}
 while(i<es.length||tick<=hi){let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
 if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
 if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push(cost);if(busy)queued=e.c;else move(e.c,t,false);}
 if(tt===t){tick++;if(policy&&done<=t&&t-prevSpec>=policy.cool&&grids[t]){let p=grids[t][policy.shrink],best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,current);
 // Exact first-event expected gain under 2s noncancelable switch: 2*(Ptarget-Pcurrent)-expected remaining in-flight time.
 let gain=2*(p.prob[best]-p.prob[current])-p.remaining;
 if(best!==current&&gain>policy.margin)move(best,t,true);}}
 }
 return {n:es.length,lat,early,sp,react,occupied,rows};
}
const valbase=sim(cut[0],cut[1],null),testbase=sim(cut[1],cut[2],null);
function compare(b,p){return {n:b.n,baseline:b.lat,policy:p.lat,net:b.lat-p.lat,earlyBase:b.early,early:p.early,switches:p.sp,reactive:p.react,baselineReactive:b.react,gain:p.rows.filter((v,i)=>b.rows[i]-v>=1-1e-8).length,loss:p.rows.filter((v,i)=>v-b.rows[i]>=1-1e-8).length};}
let trials=[{p:null,val:compare(valbase,valbase)}];
for(let shrink of [30,120,480])for(let margin of [0,.005,.01,.02,.04,.08,.15])for(let cool of [0,5,15,30,60]){let p={shrink,margin,cool};trials.push({p,val:compare(valbase,sim(cut[0],cut[1],p))});}
trials.sort((a,b)=>b.val.net-a.val.net||a.val.switches-b.val.switches);
const best=trials[0],active=trials.filter(x=>x.val.switches>0),bestActive=active[0];
function scores(lo,hi,shrink){let n=0,hit=0,baseHit=0,log=0,baseLog=0,leadN=0,leadHit=0;let k=0;for(let t=Math.ceil(lo);t<hi;t++){while(k<ev.length&&ev[k].t<=t)k++;let e=ev[k];if(!e||e.t>hi||e.t-t>30)continue;let p=grids[t][shrink],mass=1-p.surv,best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,0),fb=freq.reduce((b,x,c)=>x>freq[b]?c:b,0);n++;hit+=best===e.c;baseHit+=fb===e.c;log-=Math.log(p.prob[e.c]/mass);baseLog-=Math.log(freq[e.c]/40);if(e.t-t>=2){leadN++;leadHit+=best===e.c;}}return {n,hit,baseHit,logLoss:log/n,baselineLogLoss:baseLog/n,leadN,leadHit};}
return {raw:all.length,consolidated:ev.length,train:{events,exposure,base,channelCounts:ch},policyCount:trials.length,selected:best,test:compare(testbase,sim(cut[1],cut[2],best.p)),bestActive:bestActive?{...bestActive,test:compare(testbase,sim(cut[1],cut[2],bestActive.p))}:null,activeCount:active.length,scoreByShrink:[30,120,480].map(shrink=>({shrink,validation:scores(cut[0],cut[1],shrink),test:scores(cut[1],cut[2],shrink)})),top5:trials.slice(0,5),notes:"Retrospective; conditional intensity histogram with empirical shrinkage, 0.5s integration, 30s horizon; counts conditioned on strict past at bin left edge; expected first-alert gain uses exact noncancelable 2s cost for any mark; scores per second correlated and conditional on event within 30s; lead subset descriptive, not live gating; stateful same earlier simulator, no room travel/profit/true timestamps; no prospective test."};
}
if(require.main===module)console.log(JSON.stringify(experiment(require('node:fs').readFileSync(process.argv[2],'utf8')),null,2));
module.exports=experiment;
