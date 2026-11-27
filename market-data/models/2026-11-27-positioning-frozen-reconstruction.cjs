// Reconstructed frozen-rule evaluation; not original logistic model. Node.js usage: node thisfile.cjs latest.txt previous.txt
function analyze(latest,previous){
 const parse=s=>s.split(/\r?\n/).slice(1).map(l=>{const m=l.match(/^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})-(\d{3})_CH(\d+)-FM(\d+)_.*_([0-9a-f]+)\.png$/i);if(!m)throw Error("Malformed filename");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000,c:+m[6],f:+m[7],id:m[8]};}).sort((x,y)=>x.t-y.t);
 const all=parse(latest),old=parse(previous),cut=Date.parse("2026-11-27T20:29:52.486+08:00")/1000,start=Date.parse("2026-11-27T19:36:00+08:00")/1000;
 const raw=all.filter(x=>x.t>=start),fresh=all.filter(x=>x.t>cut);const prevMap=new Map(old.map(x=>[x.id,x]));const stable=old.every(x=>all.some(y=>y.id===x.id&&y.t===x.t&&y.c===x.c&&y.f===x.f));
 const seen=new Map(),obs=raw.filter(x=>{const k=x.c*100+x.f;if(x.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,x.t);return true;});
 const route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],floor=f=>f<=6?1:f<=12?2:f<=16?3:4;
 const freq=Array.from({length:41},()=>Array(21).fill(.5)),last=Array(41).fill(null),trans=Array.from({length:41},()=>Array(41).fill(1)),dec=Array(41).fill(0),pred=[];
 let lastRaw=null,j=0,clock=raw[0].t;
 for(let i=0;i<obs.length;i++){
  const d=obs[i];
  while(j<raw.length&&raw[j].t<=d.t){const x=raw[j++],w=Math.exp(-(x.t-clock)/15);for(let c=1;c<=40;c++)dec[c]*=w;clock=x.t;dec[x.c]++;if(lastRaw)trans[lastRaw.c][x.c]++;lastRaw=x;freq[x.c][x.f]++;last[x.c]=x;}
  const sd=dec.slice(1).reduce((a,b)=>a+b,0),st=trans[d.c].slice(1).reduce((a,b)=>a+b,0);
  const scores=Array.from({length:40},(_,k)=>({c:k+1,p:.75*dec[k+1]/sd+.25*trans[d.c][k+1]/st})).sort((a,b)=>b.p-a.p||a.c-b.c);
  const floors=Array(41).fill(2);
  for(let c=1;c<=40;c++){let s=freq[c].slice(1).reduce((a,b)=>a+b,0),v=last[c],age=v?d.t-v.t:Infinity,mix=Math.exp(-age/90),w=route.map((f,k)=>{if(!v)return 1;const center=route.indexOf(v.f)+age/7;const delta=((k-center)%20+30)%20-10;return Math.exp(-delta*delta/18);}),sw=w.reduce((a,b)=>a+b,0),pFloor=[0,0,0,0,0];route.forEach((f,k)=>pFloor[floor(f)]+=(1-mix)*freq[c][f]/s+mix*w[k]/sw);let p=0;for(let k=1;k<=4;k++){p+=pFloor[k];if(p>=.5){floors[c]=k;break;}}}
  pred.push({c:scores[0].c,top:scores.slice(0,5).map(x=>x.c),p:scores[0].p,floors});
 }
 const horizons=[0,5,10,15,30].map(h=>{let n=0,hit=0,base=0,top5=0;for(let i=0;i<obs.length-1;i++){if(obs[i].t<cut)continue;let k=i+1;while(k<obs.length&&obs[k].t<obs[i].t+h)k++;if(k===obs.length)continue;n++;hit+=pred[i].c===obs[k].c;base+=obs[i].c===obs[k].c;top5+=pred[i].top.includes(obs[k].c);}return {h,n,hit,base,top5};});
 const cases=[];let fsum=0,central=0,exact=0,within=0;
 for(let i=1;i<obs.length;i++){const x=obs[i],d=obs[i-1],p=pred[i-1];if(x.t<=cut)continue;const dist=Math.abs(p.floors[x.c]-floor(x.f));fsum+=dist;central+=Math.abs(2-floor(x.f));exact+=dist===0;within+=dist<=1;cases.push({gap:x.t-d.t,actual:x.c,prev:d.c,pred:p.c,confidence:p.p,predFloor:p.floors[p.c],actualFloor:floor(x.f)});}
 const sim=[1.5,2,3].map(cc=>{let reactive=0,predict=0,gain=0,loss=0,early=0,baseEarly=0,attempts=0;for(const x of cases){const base=x.prev===x.actual?0:cc,sw=x.prev!==x.pred;attempts+=sw;const rem=sw?Math.max(0,cc-x.gap):0;const cost=rem+(x.pred===x.actual?0:cc);reactive+=base;predict+=cost;gain+=base-cost>=1-1e-8;loss+=cost-base>=1-1e-8;early+=x.pred===x.actual&&x.gap>=(sw?cc:0)+1;baseEarly+=x.prev===x.actual&&x.gap>=1;}return {cc,n:cases.length,reactive,predict,net:reactive-predict,meanNet:(reactive-predict)/cases.length,gain,loss,early,baseEarly,attempts};});
 return {raw:all.length,old:old.length,fresh:fresh.length,allUnique:new Set(all.map(x=>x.id)).size,oldContained:stable,newIds:all.filter(x=>!prevMap.has(x.id)).length,evening:raw.length,consolidated:obs.length,pre:obs.filter(x=>x.t<=cut).length,newConsolidated:cases.length,horizons,conditionalFloor:{n:cases.length,fsum,central,exact,within},sim,cases,lastPrediction:{t:new Date(obs.at(-1).t*1000).toISOString(),c:pred.at(-1).c,confidence:pred.at(-1).p,floor:pred.at(-1).floors[pred.at(-1).c]}};
}
if (require.main === module) { const fs=require('node:fs'); console.log(JSON.stringify(analyze(fs.readFileSync(process.argv[2],'utf8'),fs.readFileSync(process.argv[3],'utf8')),null,2)); }
module.exports=analyze;
