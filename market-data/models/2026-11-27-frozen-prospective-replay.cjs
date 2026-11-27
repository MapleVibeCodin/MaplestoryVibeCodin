const frozen={
  "dataBlob": "68f456d30f5887421107fda32ffe29ad09ab5aca",
  "sourceBlobs": [
    "7617e75dba1f34742bbbb37acabb9f1332299ebb",
    "d288ad03d87ef4d2d83149ec99b72ac9f01e1ee1"
  ],
  "cutoff": "2026-11-27T21:19:37.057+08:00",
  "models": [
    {
      "name": "A HSMM",
      "h": 0,
      "hawkes": 0,
      "margin": 0.04
    },
    {
      "name": "B density HSMM",
      "h": 3,
      "hawkes": 0,
      "margin": 0.04
    },
    {
      "name": "C hybrid",
      "h": 1,
      "hawkes": 0.25,
      "margin": 0
    }
  ],
  "cooldown": 0,
  "channelChange": 2
};
function evaluate(raw,reference,sources,frozen,regression=false){
 const origin=Date.parse("2026-11-27T19:36:00+08:00")/1000,cutoff=Date.parse(frozen.cutoff)/1000-origin,prior=Date.parse("2026-11-27T21:02:59.731+08:00")/1000-origin;
 const lines=x=>x.split(/\r?\n/).slice(1).filter(Boolean);
 const ref=lines(reference),input=lines(raw);
 if(ref.length!==2558)throw Error("reference record count mismatch");
 if(input.length<ref.length||ref.some((l,i)=>input[i]!==l))throw Error("archived prefix mismatch; do not score missing/reordered/backfilled input");
 if(new Set(input).size!==input.length)throw Error("duplicate filenames");
 const stamp=l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m||+m[6]<1||+m[6]>40||+m[7]<1||+m[7]>20)throw Error("invalid filename");return Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin;};
 if(stamp(ref.at(-1))!==cutoff)throw Error("reference cutoff mismatch");
 let prev=cutoff;for(let l of input.slice(ref.length)){let t=stamp(l);if(t<=cutoff||t<prev)throw Error("new timestamps not strictly after freeze and sorted");prev=t;}
 const hi=stamp(input.at(-1)),lo=regression?prior:cutoff;
 if(!regression&&hi<=lo)return {status:"awaiting new records",newRaw:0,cutoff:frozen.cutoff};
 const cuts=[Date.parse("2026-11-27T20:35:05.774+08:00")/1000-origin,prior,hi];
 const parts=sources.map(s=>{let pos=s.indexOf("function sim(");if(pos<0)throw Error("forecast boundary missing");let prefix=s.slice(0,pos),old=prefix.match(/cut=\["20:35:05\.774","21:02:59\.731","21:19:37\.057"\]\.map\([^;\n]+\)/);if(!old)throw Error("unexpected source cutoff syntax");prefix=prefix.replace(old[0],"cut="+JSON.stringify(cuts));return new Function(prefix+"\nreturn {grids,ev,cut};\n}\nreturn experiment;")()(raw);});
 const {ev}=parts[0],sum=a=>a.reduce((s,v)=>s+v,0);
 if(JSON.stringify(ev)!==JSON.stringify(parts[1].ev))throw Error("event misalignment");
 const es=ev.filter(e=>e.t>lo&&e.t<=hi),grids=frozen.models.map(p=>{let g={};for(let t=Math.ceil(lo);t<=Math.floor(hi);t++){let h=parts[1].grids[t][p.h],k=parts[0].grids[t][0],prob=h.prob.map((v,c)=>v*(1-p.hawkes)+k.prob[c]*p.hawkes),surv=h.surv*(1-p.hawkes)+k.surv*p.hawkes,remaining=h.remaining*(1-p.hawkes)+k.remaining*p.hawkes;if(Math.abs(sum(prob)+surv-1)>1e-8)throw Error("mass error");g[t]={prob,remaining};}return g;});
 function sim(model){
 let current=ev.filter(e=>e.t<=lo).at(-1)?.c??0,target=current,done=-Infinity,arrived=lo,queued=null,sp=0,react=0,lat=0,early=0,rows=[],i=0,tick=Math.ceil(lo),clock=lo,trace=[];
 function move(c,t,spec){if(c===current)return;target=c;done=t+2;if(spec){sp++;trace.push({t,from:current+1,to:c+1});}else react++;}
 while(i<es.length||tick<=hi){let et=i<es.length?es[i].t:Infinity,tt=tick<=hi?tick:Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
 if(ft===t){current=target;arrived=t;done=-Infinity;if(queued!==null){let q=queued;queued=null;move(q,t,false);}}
 if(et===t){let e=es[i++],busy=done>t,cost=busy?done-t+(target===e.c?0:2):(current===e.c?0:2);lat+=cost;early+=!busy&&current===e.c&&t-arrived>=1?1:0;rows.push({t,c:e.c+1,f:e.f,delay:cost});if(busy)queued=e.c;else move(e.c,t,false);}
 if(tt===t){tick++;if(model!==null&&done<=t){let p=grids[model][t];if(p){let best=p.prob.reduce((b,x,c)=>x>p.prob[b]?c:b,0),gain=2*(p.prob[best]-p.prob[current])-p.remaining;if(best!==current&&gain>frozen.models[model].margin)move(best,t,true);}}}
 }
 return {n:es.length,lat,early,sp,react,rows,trace};
 }
 const base=sim(null),results=frozen.models.map((p,i)=>{let s=sim(i);return {name:p.name,lat:s.lat,net:base.lat-s.lat,early:s.early,switches:s.sp,reactive:s.react,gain:s.rows.filter((v,k)=>base.rows[k].delay-v.delay>=1-1e-8).length,loss:s.rows.filter((v,k)=>v.delay-base.rows[k].delay>=1-1e-8).length,trace:s.trace,perEvent:s.rows.map((v,k)=>({...v,baselineDelay:base.rows[k].delay,net:base.rows[k].delay-v.delay}))};});
 return {status:regression?"historical regression":"new temporal holdout",newRaw:input.length-ref.length,n:es.length,cutoff:frozen.cutoff,last:new Date((hi+origin)*1000).toISOString(),baseline:{lat:base.lat,early:base.early,reactive:base.react},results,notes:"Deterministically reconstruct fixed training fits from verified old prefix only; no new-data fitting or selection. Reset initial player channel to last observed channel at cutoff for comparability. Time is screenshot-download proxy, not verified announcement time. 2s assumed channel change, no room travel or eligibility data."};
}
const names=["2026-11-27-method02-hawkes.cjs","2026-11-27-method04-density-challenger.cjs"];
if(require.main===module){const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');const hash=b=>crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');const base=fs.readFileSync(path.join(__dirname,'../raw/2026-11-27/Pasted text(20261127-131959).txt')),src=names.map(n=>fs.readFileSync(path.join(__dirname,n)));if(hash(base)!==frozen.dataBlob||src.some((s,i)=>hash(s)!==frozen.sourceBlobs[i]))throw Error('Frozen source hash mismatch');if(!process.argv[2])throw Error('Usage: node evaluator.cjs NEW_EXPORT.txt');console.log(JSON.stringify(evaluate(fs.readFileSync(process.argv[2],'utf8'),base.toString('utf8'),src.map(s=>s.toString('utf8')),frozen),null,2));}
module.exports={evaluate,frozen};
