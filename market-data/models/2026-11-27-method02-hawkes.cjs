function experiment(raw){
const origin=Date.parse("2026-11-27T19:36:00+08:00")/1000,cut=["20:35:05.774","21:02:59.731","21:19:37.057"].map(x=>Date.parse("2026-11-27T"+x+"+08:00")/1000-origin);
const all=raw.split(/\r?\n/).slice(1).filter(Boolean).map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("invalid record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6]-1,f:+m[7]};}).filter(e=>e.t>=0).sort((a,b)=>a.t-b.t);
const seen=new Map(),ev=all.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true});
const train=ev.filter(e=>e.t<Math.floor(cut[0]*2)/2),T=Math.floor(cut[0]*2)/2,C=40,n=train.length,counts=Array(C).fill(10);for(let e of train)counts[e.c]++;const freq=counts.map(v=>v/(n+400));
const sum=a=>a.reduce((s,v)=>s+v,0);
function fit(ts,tc){
 let last=0,s=Array(C).fill(0),x=Array(C).fill(0),features=[],Is=0,Ic=0;
 for(let e of train){let d=e.t-last,ds=Math.exp(-d/ts),dc=Math.exp(-d/tc);for(let c=0;c<C;c++){s[c]*=ds;x[c]*=dc;}features.push([freq[e.c],s[e.c]/ts,(sum(x)-x[e.c])/(39*tc)]);s[e.c]++;x[e.c]++;last=e.t;Is+=-Math.expm1(-(T-e.t)/ts);Ic+=-Math.expm1(-(T-e.t)/tc);}
 let theta=[n/T*.5,.2,.3],integ=[T,Is,Ic],iterations=0;
 // EM for nonnegative additive intensities. Subcritical constrained M-step via scalar Lagrange multiplier.
 for(;iterations<1000;iterations++){let z=[0,0,0];for(let f of features){let v=f.map((a,k)=>a*theta[k]),den=sum(v);for(let k=0;k<3;k++)z[k]+=v[k]/den;}let next=z.map((v,k)=>v/integ[k]);if(next[1]+next[2]>.98){let lo=0,hi=1;while(z[1]/(Is+hi)+z[2]/(Ic+hi)>.98)hi*=2;for(let k=0;k<60;k++){let m=(lo+hi)/2;if(z[1]/(Is+m)+z[2]/(Ic+m)>.98)lo=m;else hi=m;}next[1]=z[1]/(Is+hi);next[2]=z[2]/(Ic+hi);}
 let diff=Math.max(...next.map((v,k)=>Math.abs(v-theta[k])));theta=next;if(diff<1e-9)break;}
 let ll=-sum(theta.map((v,k)=>v*integ[k]));for(let f of features)ll+=Math.log(sum(f.map((v,k)=>v*theta[k])));
 return {ts,tc,mu:theta[0],a:theta[1],b:theta[2],branch:theta[1]+theta[2],ll,iterations};
}
const models=[];for(let ts of [1,4,8,20,60])for(let tc of [.25,1,4,15,60])models.push(fit(ts,tc));models.sort((a,b)=>b.ll-a.ll);const chosen=models.slice(0,3);const grids={};
for(let m=0;m<chosen.length;m++){let {ts,tc,mu,a,b}=chosen[m],s=Array(C).fill(0),x=Array(C).fill(0),last=0,j=0;for(let t=0;t<=cut[2];t++){
 while(j<ev.length&&ev[j].t<t){let e=ev[j++],d=e.t-last,ds=Math.exp(-d/ts),dc=Math.exp(-d/tc);for(let c=0;c<C;c++){s[c]*=ds;x[c]*=dc;}s[e.c]++;x[e.c]++;last=e.t;}
 if(t<Math.ceil(cut[0]))continue;
 let ss=s.map(v=>v*Math.exp(-(t-last)/ts)),xx=x.map(v=>v*Math.exp(-(t-last)/tc)),S=sum(ss),X=sum(xx),prob=Array(C).fill(0),surv=1,remaining=0;
 const dt=.5;
 for(let u=0;u<30;u+=dt){let mid=u+dt/2,es=Math.exp(-mid/ts),ex=Math.exp(-mid/tc),integral=mu*dt+a*S*Math.exp(-u/ts)*(-Math.expm1(-dt/ts))+b*X*Math.exp(-u/tc)*(-Math.expm1(-dt/tc)),mass=surv*(-Math.expm1(-integral));let rates=ss.map((v,c)=>mu*freq[c]+a*v/ts*es+b*(X-xx[c])/(39*tc)*ex),total=sum(rates);for(let c=0;c<C;c++)prob[c]+=mass*rates[c]/total;remaining+=mass*Math.max(0,2-mid);surv-=mass;}
 (grids[t]??={})[m]={prob,surv,remaining};
}}
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
return {raw:all.length,consolidated:ev.length,train:n,trainEnd:T,models,policyCount:trials.length,selected:best,test:compare(tb,sim(cut[1],cut[2],best.p)),activeCount:active.length,bestActive:bestActive?{...bestActive,test:compare(tb,sim(cut[1],cut[2],bestActive.p))}:null,scores:chosen.map((m,i)=>({m,validation:scores(cut[0],cut[1],i),test:scores(cut[1],cut[2],i)})),top5:trials.slice(0,5),checks:{baseMatch:vb.lat===560.4429993629456&&tb.lat===196.87800192832947,subcritical:models.every(m=>m.branch<=.98000001),converged:models.every(m=>m.iterations<1000),probabilityMass: Object.values(grids).every(g=>Object.values(g).every(p=>Math.abs(sum(p.prob)+p.surv-1)<1e-9))},notes:"Retrospective same split and simulator as Method1; 25 kernel pairs trained with fixed smoothed frequency baseline, constrained EM; top3 by training likelihood only; exact survival integral, midpoint mark allocation and remaining delay approximation, horizon30s; no true announcement/eligibility or room travel. Conditional scores correlated. No live deployment."};
}
if(require.main===module)console.log(JSON.stringify(experiment(require('node:fs').readFileSync(process.argv[2],'utf8')),null,2));
module.exports=experiment;
