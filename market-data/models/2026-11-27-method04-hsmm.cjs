function experiment(raw){
const origin=Date.parse("2026-11-27T19:36:00+08:00")/1000,cut=["20:35:05.774","21:02:59.731","21:19:37.057"].map(x=>Date.parse("2026-11-27T"+x+"+08:00")/1000-origin);
const all=raw.split(/\r?\n/).slice(1).filter(Boolean).map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("invalid record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6]-1,f:+m[7]};}).filter(e=>e.t>=0).sort((a,b)=>a.t-b.t);
const seen=new Map(),ev=all.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true});
const C=40,O=4,R=20,D=2,N=O+R*D,T=Math.floor(cut[0]),end=Math.floor(cut[2]),route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],index=Array(21);route.forEach((v,i)=>index[v]=i);
const bins=Array.from({length:end+1},()=>new Map());for(let e of ev){let k=Math.floor(e.t);if(k<=end){let a=bins[k].get(e.c)||[];a.push(index[e.f]);bins[k].set(e.c,a);}}
const freq=Array(C).fill(10);let train=0;for(let e of ev)if(e.t<T){freq[e.c]++;train++;}const sum=a=>a.reduce((s,x)=>s+x,0);for(let c=0;c<C;c++)freq[c]/=(train+400);
function build(p){
 let {period,dwell,active,bg,interrupt}=p,po=O/(period-R*dwell),pr=D/dwell,links=Array.from({length:N},()=>[]);
 for(let k=0;k<O;k++){links[k].push([k,1-po]);if(k<O-1)links[k].push([k+1,po]);else {for(let m=0;m<R;m++)links[k].push([O+m*D,po*(.15/R+(m===0?.85:0))]);}}
 for(let room=0;room<R;room++)for(let j=0;j<D;j++){let k=O+room*D+j;links[k].push([k,1-pr]);if(j<D-1)links[k].push([k+1,pr]);else if(room===R-1)links[k].push([0,pr]);else {links[k].push([0,pr*interrupt]);links[k].push([k+1,pr*(1-interrupt)]);}}
 const lambda=new Float64Array(N),zero=new Float64Array(N),mark=Array.from({length:R},()=>new Float64Array(N));for(let k=0;k<N;k++){lambda[k]=bg+(k>=O?active:0);zero[k]=Math.exp(-lambda[k]);for(let m=0;m<R;m++){let v=bg/R;if(k>=O){let room=Math.floor((k-O)/D),dist=Math.abs(room-m);v+=active*(.20/R+(dist===0?.56:0)+(dist===1?.12:0)+((room===0||room===R-1)&&dist===0?.12:0));}mark[m][k]=v;}}
 function transition(a,b){b.fill(0);for(let k=0;k<N;k++){let v=a[k];for(let [i,w] of links[k])b[i]+=v*w;}}
 let stat=new Float64Array(N).fill(1/N),tmp=new Float64Array(N);for(let i=0;i<5000;i++){transition(stat,tmp);let s=stat;stat=tmp;tmp=s;}
 // Backward recursion for P(no observation through u bins | initial state).
 let surv=[new Float64Array(N).fill(1)];for(let u=1;u<=30;u++){let s=new Float64Array(N);for(let k=0;k<N;k++){let q=0;for(let [i,w] of links[k])q+=w*surv[u-1][i];s[k]=zero[k]*q;}surv.push(s);}
 return {p,links,lambda,zero,mark,stat,transition,surv};
}
function run(model,stop,grids=null,mi=0){
 let {zero,mark,stat,transition,surv}=model,state=Array.from({length:C},()=>stat.slice()),tmp=new Float64Array(N),next=new Float64Array(N),ll=0,activeSum=0,activeN=0;
 for(let t=0;t<=stop;t++){
  if(grids&&t>=Math.ceil(cut[0])){let prob=new Float64Array(C),floorPred=new Int8Array(C),totalSurv=1,remaining=0;
   let curves=Array.from({length:C},()=>new Float64Array(31));for(let c=0;c<C;c++){let s=state[c],curve=curves[c];for(let u=0;u<=30;u++){let a=0,q=surv[u];for(let k=0;k<N;k++)a+=s[k]*q[k];curve[u]=a;}
    let floor=[0,0,0,0,0];for(let m=0;m<R;m++){let v=0;for(let k=0;k<N;k++)v+=s[k]*mark[m][k];let f=route[m]<=6?1:route[m]<=12?2:route[m]<=16?3:4;floor[f]+=v;}let half=sum(floor)/2,a=0;for(let f=1;f<=4;f++){a+=floor[f];if(a>=half){floorPred[c]=f;break;}}}
   for(let u=0;u<30;u++){let hazards=curves.map(q=>Math.max(0,-Math.log(Math.max(1e-15,q[u+1]/q[u])))),h=sum(hazards),mass=totalSurv*(-Math.expm1(-h));if(h>0)for(let c=0;c<C;c++)prob[c]+=mass*hazards[c]/h;remaining+=mass*Math.max(0,2-u-.5);totalSurv-=mass;}
   (grids[t]??={})[mi]={prob:Array.from(prob),surv:totalSurv,remaining,floorPred:Array.from(floorPred)};
  }
  if(t===stop)break;
  let observations=bins[t];for(let c=0;c<C;c++){let s=state[c],marks=observations.get(c)||[],den=0;
   for(let k=0;k<N;k++){let v=s[k]*zero[k];for(let m of marks)v*=mark[m][k];tmp[k]=v;den+=v;}
   if(!(den>0))throw Error("nonpositive emission");ll+=Math.log(den); // omitted ordering/count factorial constants common to all fits
   for(let k=0;k<N;k++)tmp[k]/=den;
   transition(tmp,next);s.set(next);
   if(t<T){for(let k=O;k<N;k++)activeSum+=s[k];activeN++;}
  }
 }
 return {ll,meanActive:activeSum/activeN};
}
const models=[];for(let period of [600,855,1200])for(let active of [.04,.08])for(let interrupt of [0,.06]){let p={period,dwell:7,active,bg:.001,interrupt};let m=build(p);models.push({...p,...run(m,T)});}models.sort((a,b)=>b.ll-a.ll);const chosen=models.slice(0,3),grids={};chosen.forEach((p,i)=>run(build(p),end,grids,i));
function sim(lo,hi,policy){
 let es=ev.filter(e=>e.t>lo&&e.t<=hi),current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,prevSpec=-Infinity,sp=0,react=0,lat=0,early=0,occupied=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo;
 function move(c,t,spec){if(c===current)return;target=c;done=t+2;occupied+=Math.min(2,hi-t);if(spec){sp++;prevSpec=t}else react++;}
 while(i<es.length||tick<=hi){let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
 if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
 if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push(cost);if(busy)queued=e.c;else move(e.c,t,false);}
 if(tt===t){tick++;if(policy&&done<=t&&t-prevSpec>=policy.cool&&grids[t]){let p=grids[t][policy.model],best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,current),gain=2*(p.prob[best]-p.prob[current])-p.remaining;if(best!==current&&gain>policy.margin)move(best,t,true);}}
 }
 return {n:es.length,lat,early,sp,react,occupied,rows};
}
const vb=sim(cut[0],cut[1],null),tb=sim(cut[1],cut[2],null);
function compare(b,p){return {n:b.n,baseline:b.lat,policy:p.lat,net:b.lat-p.lat,earlyBase:b.early,early:p.early,switches:p.sp,reactive:p.react,baselineReactive:b.react,gain:p.rows.filter((v,i)=>b.rows[i]-v>=1-1e-8).length,loss:p.rows.filter((v,i)=>v-b.rows[i]>=1-1e-8).length};}
let trials=[{p:null,val:compare(vb,vb)}];for(let model=0;model<chosen.length;model++)for(let margin of [0,.005,.01,.02,.04,.08,.15])for(let cool of [0,5,15,30,60]){let p={model,margin,cool};trials.push({p,val:compare(vb,sim(cut[0],cut[1],p))});}trials.sort((a,b)=>b.val.net-a.val.net||a.val.switches-b.val.switches);let best=trials[0],active=trials.filter(x=>x.val.switches>0),bestActive=active[0];
function scores(lo,hi,m){let n=0,hit=0,baseHit=0,log=0,baseLog=0,leadN=0,leadHit=0,k=0;for(let t=Math.ceil(lo);t<hi;t++){while(k<ev.length&&ev[k].t<=t)k++;let e=ev[k];if(!e||e.t>hi||e.t-t>30)continue;let p=grids[t][m],mass=1-p.surv,best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,0),fb=freq.reduce((b,x,c)=>x>freq[b]?c:b,0);n++;hit+=best===e.c;baseHit+=fb===e.c;log-=Math.log(p.prob[e.c]/mass);baseLog-=Math.log(freq[e.c]);if(e.t-t>=2){leadN++;leadHit+=best===e.c;}}return {n,hit,baseHit,logLoss:log/n,baselineLogLoss:baseLog/n,leadN,leadHit};}
function floors(lo,hi,m){let n=0,dist=0,base=0,exact=0;for(let e of ev){if(e.t<=lo||e.t>hi)continue;let g=grids[Math.floor(e.t)]?.[m];if(!g)continue;let f=e.f<=6?1:e.f<=12?2:e.f<=16?3:4,d=Math.abs(g.floorPred[e.c]-f);n++;dist+=d;base+=Math.abs(2-f);exact+=d===0;}return {n,dist,base,exact};}
return {raw:all.length,consolidated:ev.length,train,trainEnd:T,models,policyCount:trials.length,activeCount:active.length,selected:best,test:compare(tb,sim(cut[1],cut[2],best.p)),bestActive:bestActive?{...bestActive,test:compare(tb,sim(cut[1],cut[2],bestActive.p))}:null,scores:chosen.map((p,i)=>({p,validation:scores(cut[0],cut[1],i),test:scores(cut[1],cut[2],i),conditionalFloor:floors(cut[1],cut[2],i)})),checks:{baselineMatch:vb.lat===560.4429993629456&&tb.lat===196.87800192832947,probabilityMass:Object.values(grids).every(g=>Object.values(g).every(p=>Math.abs(sum(p.prob)+p.surv-1)<1e-8)),transitionNormalization:models.every(p=>build(p).links.every(l=>Math.abs(sum(l.map(x=>x[1]))-1)<1e-9)),emissionNormalization:models.every(p=>{let b=build(p);return b.lambda.every((v,k)=>Math.abs(sum(b.mark.map(m=>m[k]))-v)<1e-9);})},notes:"Factorized per-channel explicit-duration phase-expanded HSMM, no worker count/assignment constraint; negative binomial dwell durations; 1s Poisson marked bins, filter uses only completed bins. 12 grid fits selected by training likelihood; first-event channel allocation within one-second bins via proportional log survival decrement approximation. Training ends at full second (one half-second difference vs earlier methods). Same retrospective simulator and decision grid; no actual alert timing, eligibility, movement seconds. Conditional floor uses known target channel and instant mark distribution, not joint reach."};
}
if(require.main===module)console.log(JSON.stringify(experiment(require('node:fs').readFileSync(process.argv[2],'utf8')),null,2));
module.exports=experiment;
