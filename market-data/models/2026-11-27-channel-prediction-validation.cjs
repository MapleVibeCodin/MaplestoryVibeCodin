
function analyze(raw){
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
function scores(row,weights){let a=Array(40).fill(0);for(let i=0;i<featureNames.length;i++){let k=featureNames[i],w=weights[i]||0;for(let c=0;c<40;c++)a[c]+=w*row.features[k][c];}return norm(a);}
const sets={train:eventRows.filter(x=>x.phase==="train"),val:eventRows.filter(x=>x.phase==="val"),test:eventRows.filter(x=>x.phase==="test")};
function evaluate(rows,get){let hit=0,top3=0,top7=0,log=0,rr=0;for(let x of rows){let p=get(x),r=rank(p),k=r.indexOf(x.c);hit+=k===0;top3+=k<3;top7+=k<7;rr+=1/(k+1);log-=Math.log(Math.max(1e-9,p[x.c]));}return {n:rows.length,hit,top3,top7,mrr:rr/rows.length,logLoss:log/rows.length};}
let candidates=names.map(name=>({name,get:x=>x.features[name]}));
let masks=[["revisit","episode","handoff","track2"],["recency","route","revisit","episode","handoff","track2"],featureNames,["recency","route","episode","track2"],["recency","route","revisit"],["recency","episode","revisit","handoff"],["track0","track2","track8"],["track2","track6","track8workers"],["phase2","phase5","phase10","episode"],["phase2","phase5","phase10","episode","recency","route"],["phase2","phase5","episode","revisit","handoff","track2","recency","route"]];
for(let mask of masks){let w=featureNames.map(k=>mask.includes(k)?1:0);candidates.push({name:"equal:"+mask.join("+"),weights:w,get:x=>scores(x,w)});}
function fitMix(rows,reg,mask){let w=featureNames.map(k=>mask.includes(k)?1:0),z=sum(w);w=w.map(x=>x/z);let prior=w.slice();for(let iter=0;iter<120;iter++){let g=w.map(()=>0);for(let x of rows){let a=featureNames.map(k=>x.features[k][x.c]),p=Math.max(1e-9,sum(a.map((v,i)=>v*w[i])));for(let i=0;i<w.length;i++)if(mask.includes(featureNames[i]))g[i]+=a[i]/p;}
let lr=.08/(1+iter*.025);w=w.map((v,i)=>mask.includes(featureNames[i])?v*Math.exp(lr*(g[i]/rows.length-reg*(v-prior[i]))):0);z=sum(w);w=w.map(v=>v/z);}return w;}
for(let mask of masks.filter((_,i)=>i<6||i>=8))for(let reg of [0,.5,2]){let w=fitMix(sets.train,reg,mask);candidates.push({name:"learned:"+mask.join("+")+":"+reg,weights:w,get:x=>scores(x,w)});}
function productFit(rows,reg,mask){
let idx=featureNames.map((k,i)=>mask.includes(k)?i:-1).filter(i=>i>=0), X=rows.map(r=>({y:r.c,x:Array.from({length:40},(_,c)=>idx.map(i=>Math.log(Math.max(1e-6,r.features[featureNames[i]][c]))))})),w=idx.map(()=>0),mu=w.map(()=>0),v=w.map(()=>0);
for(let it=1;it<=100;it++){let g=w.map(()=>0);for(let row of X){let a=row.x.map(x=>sum(x.map((v,i)=>v*w[i]))),m=Math.max(...a),p=norm(a.map(v=>Math.exp(v-m)));for(let k=0;k<w.length;k++){let ex=0;for(let c=0;c<40;c++)ex+=p[c]*row.x[c][k];g[k]+=ex-row.x[row.y][k];}}for(let k=0;k<w.length;k++){let a=g[k]/rows.length+reg*w[k];mu[k]=.9*mu[k]+.1*a;v[k]=.999*v[k]+.001*a*a;w[k]-=.035*(mu[k]/(1-.9**it))/(Math.sqrt(v[k]/(1-.999**it))+1e-8);}}
let full=featureNames.map(()=>0);idx.forEach((i,k)=>full[i]=w[k]);return full;}
function productScores(row,w){let a=Array.from({length:40},(_,c)=>sum(w.map((v,i)=>v*Math.log(Math.max(1e-6,row.features[featureNames[i]][c]))))),m=Math.max(...a);return norm(a.map(x=>Math.exp(x-m)));}
for(let mask of [featureNames,masks.at(-1),["recency","route","episode","phase2","phase5"]])for(let reg of [.03,.15,.6])for(let trainKind of ["event","grid"]){let tr=trainKind==="event"?sets.train:grid.filter(x=>x.phase==="train"),w=productFit(tr,reg,mask);candidates.push({name:"loglinear:"+trainKind+":"+reg+":"+mask.join("+"),weights:w,get:x=>productScores(x,w)});}
const results=candidates.map(c=>({name:c.name,weights:c.weights||null,train:evaluate(sets.train,c.get),val:evaluate(sets.val,c.get),test:evaluate(sets.test,c.get)}));
let ordered=results.slice().sort((a,b)=>b.val.hit-a.val.hit||b.val.top3-a.val.top3||a.val.logLoss-b.val.logLoss),winner=ordered[0],win=candidates.find(c=>c.name===winner.name);
let mixWinner=ordered.find(c=>c.name.startsWith("learned")||c.name.startsWith("equal")||c.name.startsWith("loglinear")),mix=candidates.find(c=>c.name===mixWinner.name);
let gridResults=candidates.map(c=>({name:c.name,...Object.fromEntries(["train","val","test"].map(p=>[p,evaluate(grid.filter(x=>x.phase===p),c.get)]))}));
let gridRank=gridResults.slice().sort((a,b)=>b.val.hit-a.val.hit||b.val.top3-a.val.top3||a.val.logLoss-b.val.logLoss),gridWinner=candidates.find(c=>c.name===gridRank[0].name);

while(ptr<ev.length){ingest(ev[ptr],ptr);ptr++;}
let rowByTime=new Map(eventRows.map(r=>[Math.round((r.t+2)*1000),r]));
let starts=qualified.map(q=>({start:q.start,confirm:q.confirm,c:q.c,row:rowByTime.get(Math.round(q.start*1000))})).filter(q=>q.row&&phase(q.start)===phase(q.confirm));
let startSets=Object.fromEntries(["train","val","test"].map(p=>[p,starts.filter(x=>phase(x.start)===p).map(x=>x.row)]));
let startCandidates=candidates.slice(0,names.length);for(let mask of [["revisit","handoff","frequency"],["revisit","handoff","frequency","episode"],["revisit","handoff","frequency","phase2","route","recency","episode"],featureNames])for(let reg of [.15,.6]){let w=productFit(startSets.train,reg,mask);startCandidates.push({name:"start:"+reg+":"+mask.join("+"),weights:w,get:x=>productScores(x,w)});}
let startResults=startCandidates.map(c=>({name:c.name,weights:c.weights??null,train:evaluate(startSets.train,c.get),val:evaluate(startSets.val,c.get),test:evaluate(startSets.test,c.get)}));
startResults.sort((a,b)=>b.val.hit-a.val.hit||b.val.top3-a.val.top3||a.val.logLoss-b.val.logLoss);
const startWinner=startResults[0];
function joint(rows,c){let res={n:rows.length,channel:0,room:0,joint:0,jointNear:0,conditionalRoom:0,conditionalNear:0,channelRoomTop3:0};let row=f=>f<=6?0:f<=12?1:f<=16?2:3;
function roomGuess(x,k){let p=ev.filter(e=>e.c===k&&e.t<x.t).at(-1);return p&&x.t-p.t<60?route[(ix[p.f]+Math.max(0,Math.round((x.t-p.t+2)/6.721)))%20]:9;}
for(let x of rows){let p=c.get(x),ord=rank(p),k=ord[0],f=roomGuess(x,k),cf=roomGuess(x,x.c);res.channel+=k===x.c;res.room+=f===x.f;res.joint+=k===x.c&&f===x.f;res.jointNear+=k===x.c&&Math.abs(row(f)-row(x.f))<=1;res.conditionalRoom+=cf===x.f;res.conditionalNear+=Math.abs(row(cf)-row(x.f))<=1;res.channelRoomTop3+=ord.slice(0,3).includes(x.c)&&cf===x.f;}return res;}
let jointResults=[win,mix,gridWinner,...["persistence","recency","route","episode","phase2"].map(n=>candidates.find(c=>c.name===n))].filter((c,i,a)=>a.findIndex(x=>x.name===c.name)===i).map(c=>({name:c.name,val:joint(sets.val,c),test:joint(sets.test,c)}));
function sig(x){return 1/(1+Math.exp(-Math.max(-30,Math.min(30,x))));}
function binaryFit(h,mask,reg){
let train=grid.filter(x=>x.phase==="train"), idx=featureNames.map((k,i)=>mask.includes(k)?i:-1).filter(i=>i>=0), rows=train.flatMap(r=>Array.from({length:40},(_,c)=>({y:r.h[h][c],x:[1,...idx.map(i=>Math.log(Math.max(1e-6,r.hf[h][featureNames[i]][c])*40))]}))),w=Array(idx.length+1).fill(0),mu=w.map(()=>0),vv=w.map(()=>0);w[0]=Math.log((sum(rows.map(r=>r.y))+.5)/(rows.length-sum(rows.map(r=>r.y))+.5));
for(let it=1;it<=100;it++){let g=w.map(()=>0);for(let r of rows){let e=sig(sum(w.map((v,i)=>v*r.x[i])))-r.y;for(let i=0;i<g.length;i++)g[i]+=e*r.x[i];}for(let i=0;i<w.length;i++){let a=g[i]/rows.length+(i?reg*w[i]:0);mu[i]=.9*mu[i]+.1*a;vv[i]=.999*vv[i]+.001*a*a;w[i]-=.025*(mu[i]/(1-.9**it))/(Math.sqrt(vv[i]/(1-.999**it))+1e-8);}}
return {idx,w,base:sum(rows.map(x=>x.y))/rows.length};}
function evaluateH(h,model,adapt){
let result={};let bias=0,queue=[],qi=0,train=grid.filter(r=>r.phase==="train");let base=model.base;function get(r,c){return sum(model.w.map((v,i)=>i?v*Math.log(Math.max(1e-6,r.hf[h][featureNames[model.idx[i-1]]][c])*40):v));}
for(let p of ["train","val","test"]){let rows=grid.filter(x=>x.phase===p),n=rows.length,hit=0,top3=0,brier=0,constant=0,log=0,pred=0,obs=0;for(let r of rows){while(qi<queue.length&&queue[qi].due<=r.t){let q=queue[qi++];if(adapt)bias=Math.max(-2,Math.min(2,bias+.12*(q.actual-q.pred)));}let logits=Array.from({length:40},(_,c)=>get(r,c)),pr=logits.map(v=>sig(v+bias)),ord=rank(pr);hit+=r.h[h][ord[0]];top3+=ord.slice(0,3).some(c=>r.h[h][c]);let y=sum(r.h[h])/40,pp=sum(pr)/40;if(p!=="train")queue.push({due:r.t+2+h,actual:y,pred:pp});for(let c=0;c<40;c++){let y=r.h[h][c],v=pr[c];brier+=(v-y)**2;constant+=(base-y)**2;log-=y*Math.log(Math.max(v,1e-9))+(1-y)*Math.log(Math.max(1-v,1e-9));pred+=v;obs+=y;}}result[p]={n,hit,top3,brier:brier/(n*40),constantBrier:constant/(n*40),logLoss:log/(n*40),meanPred:pred/(n*40),meanTrue:obs/(n*40)};}return result;}
let calibrated=[];for(let h of horizon){let variants=[];for(let mask of [["recency","episode","phase2","phase5","phase10","revisit","handoff"],["recency","route","episode","phase2","phase5","revisit","handoff","track2"],featureNames])for(let reg of [.01,.05,.2]){let model=binaryFit(h,mask,reg);for(let adapt of [false,true])variants.push({mask,reg,adapt,model,scores:evaluateH(h,model,adapt)});}
variants.sort((a,b)=>a.scores.val.brier-b.scores.val.brier);calibrated.push({h,winner:variants[0],variants});}
return {stats,startCounts:Object.fromEntries(Object.entries(startSets).map(([p,x])=>[p,x.length])),startWinner,startResults,jointResults,calibrated,eventWinner:winner.name,gridWinner:gridRank[0].name,notes:"Episode start labels retrospectively confirmed by >=4 distinct rooms, excluded when confirmation crosses split. Prediction features are prefix-only. Binary horizon models trained on boundary-purged grid train, selected on validation Brier. Adaptive calibration uses only matured validation/test labels and never future windows. Joint room scores require exact predicted channel, conditional room extrapolation 6.721s. Previously inspected test segment is not a pristine independent holdout."};}

module.exports=analyze;
