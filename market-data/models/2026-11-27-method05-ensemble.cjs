function ensemble(raw,sources){
const parts=sources.map(s=>{let pos=s.indexOf("function sim(");if(pos<0)throw Error("forecast boundary absent");return new Function(s.slice(0,pos)+"\nreturn {grids,ev,cut};\n}\nreturn experiment;")()(raw);});
const {ev,cut}=parts[0],start=Math.ceil(cut[0]),end=Math.floor(cut[2]),sum=a=>a.reduce((s,v)=>s+v,0);
if(!parts.every(p=>JSON.stringify(p.ev)===JSON.stringify(ev)&&JSON.stringify(p.cut)===JSON.stringify(cut)))throw Error("event alignment failed");
const weights=[];for(let a=0;a<=4;a++)for(let b=0;b<=4-a;b++)for(let c=0;c<=4-a-b;c++){let d=4-a-b-c;for(let h=0;h<(d?4:1);h++)weights.push({w:[a/4,b/4,c/4,d/4],h});}
const grids=weights.map(({w,h})=>{let g=[];for(let t=start;t<=end;t++){let ps=[parts[0].grids[t][30],parts[1].grids[t][0],parts[2].grids[t][1],parts[3].grids[t][h]],p=Array(40).fill(0),remaining=0,surv=0;for(let m=0;m<4;m++){for(let c=0;c<40;c++)p[c]+=w[m]*ps[m].prob[c];remaining+=w[m]*ps[m].remaining;surv+=w[m]*ps[m].surv;}let best=p.reduce((b,x,c)=>x>p[b]?c:b,0);g[t]={p,remaining,surv,best};}return g;});
function sim(lo,hi,policy){
 let es=ev.filter(e=>e.t>lo&&e.t<=hi),current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,prevSpec=-Infinity,sp=0,react=0,lat=0,early=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo;
 function move(c,t,spec){if(c===current)return;target=c;done=t+2;if(spec){sp++;prevSpec=t}else react++;}
 while(i<es.length||tick<=hi){let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
 if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
 if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push(cost);if(busy)queued=e.c;else move(e.c,t,false);}
 if(tt===t){tick++;if(policy&&done<=t&&t-prevSpec>=policy.cool){let p=grids[policy.model][t];if(p){let gain=2*(p.p[p.best]-p.p[current])-p.remaining;if(p.best!==current&&gain>policy.margin)move(p.best,t,true);}}}
 }
 return {n:es.length,lat,early,sp,react,rows};
}
const vb=sim(cut[0],cut[1],null),tb=sim(cut[1],cut[2],null);
function compare(b,p){return {n:b.n,baseline:b.lat,policy:p.lat,net:b.lat-p.lat,earlyBase:b.early,early:p.early,switches:p.sp,reactive:p.react,baselineReactive:b.react,gain:p.rows.filter((v,i)=>b.rows[i]-v>=1-1e-8).length,loss:p.rows.filter((v,i)=>v-b.rows[i]>=1-1e-8).length};}
let trials=[{p:null,val:compare(vb,vb)}];for(let model=0;model<weights.length;model++)for(let margin of [0,.005,.01,.02,.04,.08,.15])for(let cool of [0,5,15,30,60]){let p={model,margin,cool};trials.push({p,val:compare(vb,sim(cut[0],cut[1],p))});}trials.sort((a,b)=>b.val.net-a.val.net||a.val.switches-b.val.switches);
function scores(lo,hi,m){let n=0,hit=0,log=0,k=0,leadN=0,leadHit=0;for(let t=Math.ceil(lo);t<hi;t++){while(k<ev.length&&ev[k].t<=t)k++;let e=ev[k];if(!e||e.t>hi||e.t-t>30)continue;let p=grids[m][t];n++;hit+=p.best===e.c;log-=Math.log(p.p[e.c]/(1-p.surv));if(e.t-t>=2){leadN++;leadHit+=p.best===e.c;}}return {n,hit,logLoss:log/n,leadN,leadHit};}
function summarize(x){return {...x,weights:x.p?weights[x.p.model]:null,test:compare(tb,sim(cut[1],cut[2],x.p)),validationScore:x.p?scores(cut[0],cut[1],x.p.model):null,testScore:x.p?scores(cut[1],cut[2],x.p.model):null};}
const best=trials[0],blend=trials.find(x=>x.p&&weights[x.p.model].w.filter(v=>v>0).length>=2),allfour=trials.find(x=>x.p&&weights[x.p.model].w.every(v=>v>0)),density=trials.find(x=>x.p&&weights[x.p.model].w[3]>0&&weights[x.p.model].h>0),individual=weights.map((w,m)=>({w,m})).filter(x=>x.w.w.includes(1)).map(x=>summarize(trials.find(t=>t.p?.model===x.m)));
const mass=grids.every(g=>g.slice(start).every(p=>Math.abs(sum(p.p)+p.surv-1)<1e-8));
return {weightsCount:weights.length,policyCount:trials.length,activeCount:trials.filter(x=>x.val.switches>0).length,selected:summarize(best),bestBlend:summarize(blend),bestAllFour:summarize(allfour),bestDensity:summarize(density),individual,top:trials.slice(0,10).map(x=>({...x,weights:x.p?weights[x.p.model]:null})),checks:{eventAlignment:true,probabilityMass:mass,baselineMatch:vb.lat===560.4429993629456&&tb.lat===196.87800192832947,method1Replay:individual.some(x=>x.weights.w[0]===1&&Math.abs(x.test.net+3.31000018119812)<1e-8),hsmmReplay:individual.some(x=>x.weights.w[3]===1&&x.weights.h===0&&Math.abs(x.val.net-3.0759997367858887)<1e-8)},notes:"Fixed component grids extracted from exact archived sources, TPP shrink30, Hawkes top training fit, renewal60s (validation log loss), HSMM nominal855 with four density variants. Mixture of unconditional first-event mark mass and remaining travel penalty; weights 0.25 lattice, select validation net then fewer switches. Retrospective reused test, no live alert timestamps or actual travel. No prospective confirmation. Method4 floor not optimized in this channel benchmark."};
}
const names=["2026-11-27-method01-marked-point-process.cjs","2026-11-27-method02-hawkes.cjs","2026-11-27-method03-renewal.cjs","2026-11-27-method04-density-challenger.cjs"];
if(require.main===module){const fs=require('node:fs'),path=require('node:path');console.log(JSON.stringify(ensemble(fs.readFileSync(process.argv[2],'utf8'),names.map(n=>fs.readFileSync(path.join(__dirname,n),'utf8'))),null,2));}
module.exports=ensemble;
