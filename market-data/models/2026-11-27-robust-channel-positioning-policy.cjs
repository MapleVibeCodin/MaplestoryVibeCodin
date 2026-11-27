
function analyze(raw,specs){
const base=Date.parse("2026-11-27T22:34:00+08:00"), route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],ix=Object.fromEntries(route.map((f,i)=>[f,i])), cut1=(Date.parse("2026-11-27T22:55:03.028+08:00")-base)/1000, cut2=(Date.parse("2026-11-27T23:13:51.174+08:00")-base)/1000;
const records=raw.map((l,i)=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {id:i+1,t:(Date.parse(m[1]+"T"+m[2]+":"+m[3]+":"+m[4]+"."+m[5]+"+08:00")-base)/1000,c:+m[6]-1,f:+m[7],price:+(l.match(/_(\d+)mesos_/)||[])[1]};});
const seen=new Map(),ev=[],groups=[];for(let r of records){let k=r.c*100+r.f,p=seen.get(k);if(p!==undefined&&r.t-ev[p].t<2){groups[p].push(r.id);continue;}seen.set(k,ev.length);ev.push(r);groups.push([r.id]);}
const end=ev.at(-1).t, med=a=>{if(!a.length)return null;let x=a.slice().sort((a,b)=>a-b),n=x.length;return (x[(n-1)>>1]+x[n>>1])/2;}, sum=a=>a.reduce((s,x)=>s+x,0), norm=a=>{let s=sum(a);return s?a.map(x=>x/s):a.map(()=>1/40)},rank=a=>Array.from({length:40},(_,i)=>i).sort((i,j)=>a[j]-a[i]||i-j), gauss=(x,s)=>Math.exp(-.5*(x/s)**2), phase=t=>t<=cut1?"train":t<=cut2?"val":"test", step=(a,b)=>(ix[b.f]-ix[a.f]+20)%20;
const stats={raw:raw.length,anchors:ev.length,base,cut1,cut2,end};
const delays=records.slice(1).map((e,i)=>e.t-records[i].t),burstSame=records.slice(1).filter((e,i)=>e.c===records[i].c&&e.f===records[i].f&&e.t-records[i].t<.5).length,burstDiff=records.slice(1).filter((e,i)=>e.c!==records[i].c&&e.t-records[i].t<.5).length;
let groupSpans=groups.map(g=>records[g.at(-1)-1].t-records[g[0]-1].t);
stats.delivery={rawAdjacentBelowHalfSecond:delays.filter(d=>d<.5).length,rawAdjacentTotal:delays.length,medianAdjacentSeconds:med(delays),sameCellBelowHalf:burstSame,differentChannelBelowHalf:burstDiff,multiGroups:groups.filter(g=>g.length>1).length,medianMultiGroupSpan:med(groupSpans.filter(s=>s>0)),maxGroupSpan:Math.max(...groupSpans),note:"Delivery burst proxies only; absolute scan-to-delivery latency not identifiable."};
const ch=Array.from({length:40},()=>({last:null,events:[],ep:null,qualified:[],intervals:[],count:0}));let roomCounts=Array(20).fill(1),globalIntervals=[],dwellSamples=[],qualified=[],linkCounts=Array.from({length:40},()=>Array(40).fill(0)),links=[],nextEp=0;
const models=[{name:"track0",lag:0,n:7},{name:"track2",lag:2,n:7},{name:"track8",lag:8,n:7},{name:"track6",lag:2,n:6},{name:"track8workers",lag:2,n:8}].map(m=>({...m,beam:[{w:[],cost:0}],skips:0}));
function updateBeam(m,e,j){let pool=[];for(let s of m.beam){for(let z=0;z<=s.w.length;z++){let a=s.w[z];if(!a&&s.w.length>=m.n)continue;let cost=s.cost,t=e.t-m.lag,streak=1;if(!a)cost+=3;else{let p=ev[a.j],gap=e.t-p.t,k=step(p,e),sw=p.c!==e.c,dist=sw?0:Math.min(k,20-k),min=sw?2:2*dist;t=Math.max(t,a.t+min);if(t>e.t+1e-7)continue; if(sw){let exit=ix[p.f],entry=ix[e.f];cost+=7+Math.min(gap,180)*.018+Math.min(20-exit,exit)*.08+Math.min(entry,20-entry)*.06;streak=1;}else{let ideal=7*(k===0?0:k);cost+=Math.min(12,Math.abs(gap-ideal)/7)*.45+(k>10?2:0);streak=Math.min(a.streak+1,12);}}
let w=s.w.slice();w[z]={j,t,streak};pool.push({w,cost});}pool.push({w:s.w,cost:s.cost+18});}
pool.sort((a,b)=>a.cost-b.cost);let keys=new Set(),beam=[];for(let s of pool){let key=s.w.map(x=>x.j+":"+Math.round(x.t*1000)+":"+x.streak).sort().join("|");if(keys.has(key))continue;keys.add(key);beam.push(s);if(beam.length>=16)break;}let low=beam[0].cost;m.beam=beam.map(s=>({...s,cost:s.cost-low}));}
function ingest(e,j){roomCounts[e.f-1]++;let s=ch[e.c],p=s.last;if(p&&step(p,e)===1&&e.t-p.t>=2&&e.t-p.t<=20)dwellSamples.push(e.t-p.t);
if(!s.ep||e.t-s.ep.end>40){s.ep={id:nextEp++,c:e.c,start:e.t,end:e.t,rooms:new Set(),n:0,confirmed:false};}
let ep=s.ep;ep.end=e.t;ep.rooms.add(e.f);ep.n++;
if(!ep.confirmed&&ep.rooms.size>=4){ep.confirmed=true;ep.confirm=e.t;let prior=s.qualified.at(-1);if(prior){let g=ep.start-prior.start;if(g>=240&&g<=2400){s.intervals.push(g);globalIntervals.push(g);}}
let cand=qualified.filter(q=>q.c!==e.c&&q.end<=ep.start&&ep.start-q.end<=45);
let weights=cand.map(q=>Math.exp(-(ep.start-q.end)/15)),z=sum(weights);cand.forEach((q,i)=>{let w=weights[i]/Math.max(z,1);linkCounts[q.c][e.c]+=w;links.push({from:q.c+1,to:e.c+1,gap:ep.start-q.end,weight:w,learned:e.t});});
s.qualified.push(ep);qualified.push(ep);}
s.events.push(e);s.last=e;s.count++;for(let m of models)updateBeam(m,e,j);}
function timerState(t){let g=med(globalIntervals)||800;return ch.map(s=>{let last=s.qualified.at(-1);let a=s.intervals.map(x=>{let n=Math.max(1,Math.round(x/g));return x/n;}).filter(x=>x>=300&&x<=1500);let local=med(a),period=local===null?g:(local*a.length+g*4)/(a.length+4);let age=last?t-last.start:Infinity;let recent=s.last?t-s.last.t:Infinity;return {period,age,recent,last:last?.start??null};});}
function tracker(t,h,m){let sc=Array(40).fill(.002),room=Array.from({length:40},()=>Array(20).fill(0));let ws=m.beam.map(s=>Math.exp(-s.cost/3)),z=sum(ws);for(let q=0;q<m.beam.length;q++){let s=m.beam[q],w=ws[q]/z;for(let a of s.w){let e=ev[a.j],age=t-e.t;if(age>180)continue;let delta=Math.max(0,t+h/2-a.t),k=Math.max(0,Math.round(delta/7)),p=Math.exp(-age/40)*(1+Math.min(a.streak,8)*.08),weight=w*p;sc[e.c]+=weight;for(let dd=-1;dd<=1;dd++)room[e.c][route[(ix[e.f]+k+dd+40)%20]-1]+=weight*(dd===0?.6:.2);}}return {sc:norm(sc),room};}
function features(t,h){let timers=timerState(t),recent=[],persist=[],routeAct=[],freq=[],revisit=[],episode=[],phase2=[],phase5=[],phase10=[],phaseRoom=[],handoff=Array(40).fill(.001);let latest=-1,latestT=-Infinity,dwell=med(dwellSamples)||7;
for(let c=0;c<40;c++){let s=ch[c],v=timers[c],age=v.recent; if(s.last&&s.last.t>latestT){latestT=s.last.t;latest=c;}
let rec=0;for(let q=s.events.length-1;q>=0&&t-s.events[q].t<150;q--)rec+=Math.exp(-(t-s.events[q].t)/15);recent.push(rec+.01);freq.push((s.count+2)/(t+80));
let arr=s.events.slice(-5),ok=0;for(let i=1;i<arr.length;i++){let k=step(arr[i-1],arr[i]),dt=arr[i].t-arr[i-1].t;if(k>=1&&k<=5&&dt/k>=3&&dt/k<=13)ok++;}
routeAct.push(.01+Math.exp(-age/20)*(1+ok));
let a=v.age+h/2,p=v.period,r=0;if(Number.isFinite(a)&&a>p*.4){for(let k=1;k<=4;k++)r+=gauss(a-k*p,Math.max(60,.17*p))*Math.exp(-.4*(k-1));}
revisit.push(.04+r*(1-Math.exp(-age/35)));
let ep=s.ep,epAge=ep?t-ep.start:999,remain=ep?Math.max(0,140-epAge):0;
let pr=Array(20).fill(0),v2=.002,v5=.002,v10=.002;
if(s.last&&age<150){let last=s.last,a0=[last.t];for(let q of s.events.slice(-8,-1)){let k=step(q,last),dt=last.t-q.t;if(k>=1&&k<=12&&Math.abs(dt-k*dwell)<=Math.max(5,1.5*k))a0.push(q.t+k*dwell);}
let center=.45*last.t+.55*med(a0),strength=Math.exp(-age/32)*(1+Math.min(ok,4)*.12),sigma=Math.min(6,1.8+age*.035+1.5/Math.sqrt(a0.length));
for(let k=0;k<=20;k++){let f=route[(ix[last.f]+k)%20],when=center+k*dwell-t;if(when<-6||when>Math.max(18,h+5))continue;let wt=strength*Math.sqrt(roomCounts[f-1]/(sum(roomCounts)/20))*Math.exp(-k*.09),p2=wt*gauss(when-2,sigma),p5=wt*(gauss(when-3,sigma+1)+gauss(when-6,sigma+1))*.5,p10=wt*(gauss(when-3,sigma+1)+gauss(when-7,sigma+1)+gauss(when-11,sigma+1))/3;v2+=p2;v5+=p5;v10+=p10;pr[f-1]+=p2;}}
phase2.push(v2);phase5.push(v5);phase10.push(v10);phaseRoom.push(pr);
let active=ep?Math.exp(-age/22)*(1+Math.min(ep.rooms.size,8)*.16)*(.35+.65*Math.min(1,remain/35))*(.7+.3*gauss((age+h/2)%dwell,dwell/2)):0;episode.push(.015+active);
if(ep&&ep.confirmed&&age<=80){let exit=ix[s.last.f],endProb=Math.exp(-Math.abs(age-12)/22)*(exit>=15?1:.25)*(.3+.7*Math.min(1,epAge/100));let row=linkCounts[c],z=sum(row)+40*.25;for(let j=0;j<40;j++)if(j!==c)handoff[j]+=endProb*(row[j]+.25)/z;}
}
persist=Array(40).fill(.001);if(latest>=0)persist[latest]=1;
let f={uniform:Array(40).fill(.025),persistence:norm(persist),recency:norm(recent),route:norm(routeAct),frequency:norm(freq),revisit:norm(revisit),episode:norm(episode),handoff:norm(handoff),phase2:norm(phase2),phase5:norm(phase5),phase10:norm(phase10)};
let rooms={phase:phaseRoom};for(let m of models){let v=tracker(t,h,m);f[m.name]=v.sc;rooms[m.name]=v.room;}
return {f,rooms,timers};}
const horizon=[5,10,30,60],names=["uniform","persistence","recency","route","frequency","revisit","episode","handoff","track0","track2","track8","track6","track8workers"],featureNames=["recency","route","frequency","revisit","episode","handoff","track0","track2","track8","track6","track8workers"];
names.push('phase2','phase5','phase10');featureNames.push('phase2','phase5','phase10');let origins=[];for(let t=60;t<=end-62;t+=5)origins.push({t,kind:"grid"});for(let t=60;t<=end-2;t+=1)origins.push({t,kind:"policy"});for(let e of ev)if(e.t>=62)origins.push({t:e.t-2,kind:"event",target:e});origins.sort((a,b)=>a.t-b.t||a.kind.localeCompare(b.kind));
let ptr=0,grid=[],eventRows=[],policyRows=[],lastT=null,cached=null,calibration={};
for(let o of origins){let t=o.t;while(ptr<ev.length&&ev[ptr].t<t){ingest(ev[ptr],ptr);ptr++;}
let phaseName=phase(o.target?o.target.t:t+2);if(lastT!==t){cached=features(t,5);lastT=t;}let f=cached.f;
if(o.kind==="event"){eventRows.push({t,phase:phaseName,c:o.target.c,f:o.target.f,features:f,rooms:cached.rooms});continue;}
let q=ptr;while(q<ev.length&&ev[q].t<t+2)q++;let e=ev[q];if(!e)continue;let row={t,phase:phaseName,c:e.c,f:e.f,features:f};
if(o.kind==="policy"){policyRows.push(row);continue;}if(e.t>t+62||phase(e.t)!==phaseName||phase(t+62)!==phaseName)continue;row.h={};row.hf={};for(let h of horizon){let targets=Array(40).fill(0);for(let k=q;k<ev.length&&ev[k].t<t+2+h;k++)targets[ev[k].c]=1;row.h[h]=targets;row.hf[h]=h===5?f:features(t,h).f;}grid.push(row);}

const scoresFrom=(x,c)=>{if(!c.weights)return x.features[c.name];let a;if(c.name.startsWith("loglinear")){a=Array.from({length:40},(_,k)=>sum(c.weights.map((v,i)=>v*Math.log(Math.max(1e-6,x.features[featureNames[i]][k])))));let m=Math.max(...a);a=a.map(v=>Math.exp(v-m));}else a=Array.from({length:40},(_,k)=>sum(c.weights.map((v,i)=>v*x.features[featureNames[i]][k])));return norm(a);};
let modelsToTest=specs.map(c=>({name:c.name,rows:policyRows.map(x=>{let p=scoresFrom(x,c);return {t:x.t,p,top:rank(p)[0]};})}));
let fractions=[.1,.25,.5,1], seeds=[11,37,73], split=(cut1+cut2)/2;
function qualifies(e,f,s){return (Math.imul(e.id+s*65537,2654435761)>>>0)/4294967296<f;}
function simulate(start,stop,model,rule,cc,f,seed){let es=ev.filter(e=>e.t>start&&e.t<=stop&&qualifies(e,f,seed)),rs=model?model.rows.filter(x=>x.t>start&&x.t<=stop):[],prev=ev.filter(e=>e.t<=start&&qualifies(e,f,seed)).at(-1);let current=prev?.c??0,dest=current,arrival=-Infinity,lastSpec=-Infinity,i=0,j=0,latency=0,spec=0,react=0,ready=0,correct=0,wrong=0,pending=null;function advance(t){if(arrival<=t){current=dest;arrival=-Infinity;}}
while(i<es.length||j<rs.length){let e=es[i],x=rs[j],isE=e&&(!x||e.t<=x.t),t=isE?e.t:x.t;advance(t);if(isE){i++;if(pending!==null){if(pending===e.c)correct++;else wrong++;pending=null;}if(arrival===-Infinity&&current===e.c){ready++;continue;}if(arrival!==-Infinity&&dest===e.c){latency+=arrival-t;continue;}latency+=cc;dest=e.c;arrival=t+cc;react++;}else{j++;if(arrival!==-Infinity||t-lastSpec<rule.cooldown)continue;let k=x.top,p=x.p;if(k!==current&&p[k]>=rule.threshold&&p[k]-p[current]>=rule.margin){dest=k;arrival=t+cc;spec++;lastSpec=t;pending=k;}}}return {n:es.length,latency,spec,react,ready,correct,wrong};}
function agg(xs){return Object.fromEntries(Object.keys(xs[0]).map(k=>[k,sum(xs.map(x=>x[k]))]));}
let report=[];
for(let f of fractions)for(let cc of [1,2,3]){
let sd=f===1?[11]:seeds,windows=[[cut1,split],[split,cut2],[cut2,end]],base=windows.map(([a,b])=>agg(sd.map(s=>simulate(a,b,null,{},cc,f,s)))),trials=[];
for(let m of modelsToTest)for(let threshold of [.08,.12,.16,.2,.3,.45])for(let margin of [.02,.06,.12])for(let cooldown of [3,10,30,60]){let rule={threshold,margin,cooldown};let val=windows.slice(0,2).map(([a,b])=>agg(sd.map(s=>simulate(a,b,m,rule,cc,f,s)))), gains=val.map((v,i)=>base[i].latency-v.latency),extra=val.map((v,i)=>v.spec+v.react-base[i].react),utility=gains.map((g,i)=>g-.5*Math.max(0,extra[i]));trials.push({name:m.name,rule,gains,extra,utility,val});}
let robust=trials.filter(x=>x.utility.every(u=>u>1)&&sum(x.gains)>0).sort((a,b)=>sum(b.utility)-sum(a.utility)||sum(a.extra)-sum(b.extra));let best=robust[0], m=best&&modelsToTest.find(x=>x.name===best.name),test=best?agg(sd.map(s=>simulate(cut2,end,m,best.rule,cc,f,s))):base[2];let bestAny=trials.slice().sort((a,b)=>sum(b.utility)-sum(a.utility))[0];report.push({fraction:f,cc,base,selected:best??{name:"reactive"},test,netTest:base[2].latency-test.latency,extraTest:test.spec+test.react-base[2].react,robustCount:robust.length,trials:trials.length,bestAny});}
return {stats,split,report,notes:"Precomputed causal predictions from archived v2 model coefficients; selected on two validation halves only. Candidate must beat reactive utility by >1 sec in both halves, extra moves penalized 0.5 sec each. Sparse targets are deterministic hash subsamples, not verified profitable deals; 3 seeds pooled. Each segment begins on last qualifying prior target channel. Immediate interruption model; no gameplay timings."};}

module.exports=analyze;
