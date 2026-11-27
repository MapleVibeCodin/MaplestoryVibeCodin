function experiment(raw){
const origin=Date.parse("2026-11-27T19:36:00+08:00")/1000,cut=["20:35:05.774","21:02:59.731","21:19:37.057"].map(x=>Date.parse("2026-11-27T"+x+"+08:00")/1000-origin);
const all=raw.split(/\r?\n/).slice(1).filter(Boolean).map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("invalid record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6]-1,f:+m[7]};}).filter(e=>e.t>=0).sort((a,b)=>a.t-b.t);
const seen=new Map(),ev=all.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true});
const C=40,R=20,O=4,D=2,N=44,T=Math.floor(cut[0]),end=Math.floor(cut[2]),route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],index=[];route.forEach((f,i)=>index[f]=i);
const floor=f=>f<=6?0:f<=12?1:f<=16?2:3,sum=a=>a.reduce((s,v)=>s+v,0);
const train=ev.filter(e=>e.t<T),freq=Array(C).fill(10),counts=Array.from({length:C},()=>Array(R).fill(0)),rowCounts=[0,0,0,0],rowSize=[6,6,4,4],bins=Array.from({length:end+1},()=>new Map());
for(let e of train){freq[e.c]++;counts[e.c][index[e.f]]++;rowCounts[floor(e.f)]++;}
for(let c=0;c<C;c++)freq[c]/=train.length+400;
for(let e of ev){let t=Math.floor(e.t);if(t<=end){let x=bins[t].get(e.c)||[];x.push(index[e.f]);bins[t].set(e.c,x);}}
const links=Array.from({length:N},()=>[]),po=4/(855-140),pr=2/7;
for(let k=0;k<O;k++){links[k].push([k,1-po]);if(k<O-1)links[k].push([k+1,po]);else for(let m=0;m<R;m++)links[k].push([O+m*D,po*(.15/R+(m===0?.85:0))]);}
for(let room=0;room<R;room++)for(let j=0;j<D;j++){let k=O+room*D+j;links[k].push([k,1-pr],[j<D-1?k+1:room===R-1?0:k+1,pr]);}
function transition(a,b){b.fill(0);for(let k=0;k<N;k++)for(let [i,w] of links[k])b[i]+=a[k]*w;}
let stat=new Float64Array(N).fill(1/N),tmp=new Float64Array(N);for(let i=0;i<5000;i++){transition(stat,tmp);[stat,tmp]=[tmp,stat];}
const cfg=[{name:"uniform",rank:0,fit:false},{name:"rank prior mild",rank:.25,fit:false},{name:"rank prior stronger",rank:.6,fit:false},{name:"rank plus alert proxy",rank:.25,fit:true}];
function weights(p){let w=Array.from({length:C},(_,c)=>route.map(f=>Math.exp(-p.rank*(c/39*2+floor(f)))));let mean=sum(w.map(sum))/(C*R);w=w.map(a=>a.map(x=>x/mean));if(p.fit){w=w.map((a,c)=>a.map((x,m)=>(counts[c][m]+8*x)/(train.length/(C*R)+8)));mean=sum(w.map(sum))/(C*R);w=w.map(a=>a.map(x=>x/mean));}return w;}
const grids={};
function run(p,mi){let w=weights(p),models=w.map(a=>{let mark=Array.from({length:R},()=>new Float64Array(N)),zero=new Float64Array(N);for(let k=0;k<N;k++){let lam=0;for(let m=0;m<R;m++){let v=.001/R;if(k>=O){let room=Math.floor((k-O)/D),dist=Math.abs(room-m);v+=.04*a[m]*(.20/R+(dist===0?.56:0)+(dist===1?.12:0)+((room===0||room===R-1)&&dist===0?.12:0));}mark[m][k]=v;lam+=v;}zero[k]=Math.exp(-lam);}let surv=[new Float64Array(N).fill(1)];for(let u=1;u<=30;u++){let v=new Float64Array(N);for(let k=0;k<N;k++)v[k]=zero[k]*sum(links[k].map(([i,a])=>a*surv[u-1][i]));surv.push(v);}return {mark,zero,surv};});
let state=Array.from({length:C},()=>stat.slice()),post=new Float64Array(N),next=new Float64Array(N),ll=0;
for(let t=0;t<=end;t++){
 if(t>=Math.ceil(cut[0])){let prob=new Float64Array(C),floorPred=[],remaining=0,totalSurv=1,curves=state.map((s,c)=>models[c].surv.map(q=>{let a=0;for(let k=0;k<N;k++)a+=s[k]*q[k];return a;}));
 for(let c=0;c<C;c++){let f=[0,0,0,0],s=state[c];for(let m=0;m<R;m++){let v=0;for(let k=0;k<N;k++)v+=s[k]*models[c].mark[m][k];f[floor(route[m])]+=v;}let a=0,h=sum(f)/2;floorPred[c]=f.findIndex(v=>(a+=v)>=h);}
 for(let u=0;u<30;u++){let h=curves.map(q=>Math.max(0,-Math.log(Math.max(1e-15,q[u+1]/q[u])))),tot=sum(h),mass=totalSurv*(-Math.expm1(-tot));if(tot>0)for(let c=0;c<C;c++)prob[c]+=mass*h[c]/tot;remaining+=mass*Math.max(0,1.5-u);totalSurv-=mass;}
 (grids[t]??={})[mi]={prob:Array.from(prob),surv:totalSurv,remaining,floorPred};}
 if(t===end)break;
 for(let c=0;c<C;c++){let s=state[c],{mark,zero}=models[c],ms=bins[t].get(c)||[],den=0;for(let k=0;k<N;k++){let v=s[k]*zero[k];for(let m of ms)v*=mark[m][k];post[k]=v;den+=v;}if(t<T)ll+=Math.log(den);for(let k=0;k<N;k++)post[k]/=den;transition(post,next);s.set(next);}
}return {p,ll,minWeight:Math.min(...w.flat()),maxWeight:Math.max(...w.flat())};}
const fits=cfg.map(run);
function sim(lo,hi,policy){
let es=ev.filter(e=>e.t>lo&&e.t<=hi),current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,prevSpec=-Infinity,sp=0,react=0,lat=0,early=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo;
function move(c,t,spec){if(c===current)return;target=c;done=t+2;if(spec){sp++;prevSpec=t}else react++;}
while(i<es.length||tick<=hi){let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push(cost);if(busy)queued=e.c;else move(e.c,t,false);}
if(tt===t){tick++;if(policy&&done<=t&&t-prevSpec>=policy.cool&&grids[t]){let p=grids[t][policy.model],best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,current),gain=2*(p.prob[best]-p.prob[current])-p.remaining;if(best!==current&&gain>policy.margin)move(best,t,true);}}}
return {n:es.length,lat,early,sp,react,rows};}
const vb=sim(cut[0],cut[1],null),tb=sim(cut[1],cut[2],null);
function compare(b,p){return {n:b.n,baseline:b.lat,policy:p.lat,net:b.lat-p.lat,earlyBase:b.early,early:p.early,switches:p.sp,gain:p.rows.filter((v,i)=>b.rows[i]-v>=1-1e-8).length,loss:p.rows.filter((v,i)=>v-b.rows[i]>=1-1e-8).length};}
let trials=[{p:null,val:compare(vb,vb)}];for(let model=0;model<cfg.length;model++)for(let margin of [0,.005,.01,.02,.04,.08,.15])for(let cool of [0,5,15,30,60]){let p={model,margin,cool};trials.push({p,val:compare(vb,sim(cut[0],cut[1],p))});}trials.sort((a,b)=>b.val.net-a.val.net||a.val.switches-b.val.switches);
function scores(lo,hi,m){let n=0,hit=0,log=0,k=0,dist=0,base=0,fn=0;for(let t=Math.ceil(lo);t<hi;t++){while(k<ev.length&&ev[k].t<=t)k++;let e=ev[k];if(!e||e.t>hi||e.t-t>30)continue;let p=grids[t][m],best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,0);n++;hit+=best===e.c;log-=Math.log(p.prob[e.c]/(1-p.surv));}for(let e of ev){if(e.t<=lo||e.t>hi)continue;let p=grids[Math.floor(e.t)]?.[m];if(!p)continue;fn++;dist+=Math.abs(p.floorPred[e.c]-floor(e.f));base+=Math.abs(1-floor(e.f));}return {n,hit,logLoss:log/n,floor:{n:fn,dist,base}};}
return {train:train.length,raw:all.length,consolidated:ev.length,rowCounts,rowPerRoom:rowCounts.map((v,i)=>v/rowSize[i]),channelGroups:[0,1,2,3].map(g=>train.filter(e=>Math.floor(e.c/10)===g).length),fits,policyCount:trials.length,selected:trials[0],test:compare(tb,sim(cut[1],cut[2],trials[0].p)),byModel:cfg.map((p,m)=>{let b=trials.find(x=>x.p?.model===m);return {p,best:b,test:compare(tb,sim(cut[1],cut[2],b.p)),validationScore:scores(cut[0],cut[1],m),testScore:scores(cut[1],cut[2],m)};}),checks:{baselineMatch:vb.lat===560.4429993629456&&tb.lat===196.87800192832947,uniformMatch:Math.abs(fits[0].ll+6973.042784420046)<1e-6,probabilityMass:Object.values(grids).every(g=>Object.values(g).every(p=>Math.abs(sum(p.prob)+p.surv-1)<1e-8))},notes:"Rank prior weights illustrative, not shop counts. Channel and row soft multiplicative prior normalized mean1; rank plus alert proxy uses training-only counts shrinkage 8 pseudo-counts, counts confounded by visits and selection. No strict channel-major ordering assumed. Retrospective same split, no live timestamps, actual shop counts, movement or independent test."};
}
if(require.main===module)console.log(JSON.stringify(experiment(require('node:fs').readFileSync(process.argv[2],'utf8')),null,2));
module.exports=experiment;
