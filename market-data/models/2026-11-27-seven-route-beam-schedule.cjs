
function analyze(raw){
const base=Date.parse("2026-11-27T22:34:00+08:00"), route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],ix=Object.fromEntries(route.map((f,i)=>[f,i]));
const records=raw.map((l,i)=>{const m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {i:i+1,t:Date.parse(m[1]+"T"+m[2]+":"+m[3]+":"+m[4]+"."+m[5]+"+08:00")-base,c:+m[6],f:+m[7]};});
const seen=new Map(),ev=[],groups=[];for(const e of records){let k=e.c*100+e.f,p=seen.get(k);if(p!==undefined&&e.t-ev[p].t<2000){groups[p].push(e.i);continue;}seen.set(k,ev.length);ev.push(e);groups.push([e.i]);}
function run(cfg,keep=false){
const {d,cc,lag,mode,width}=cfg;const empty={a:-1,t:-1e12,id:0};let beam=[{w:Array.from({length:7},(_,i)=>({...empty,id:i})),cost:0,ccs:0,prev:null,action:null}];
let processed=0;
for(let j=0;j<ev.length;j++){const b=ev[j],pool=[];for(const s of beam){let usedEmpty=false;for(let z=0;z<7;z++){let p=s.w[z],a=ev[p.a],dt=a?b.t-a.t:0,k=a?(ix[b.f]-ix[a.f]+20)%20:0,sw=!!a&&a.c!==b.c;if(!a){if(usedEmpty)continue;usedEmpty=true;}
let min=0;if(a){if(sw){min=cc*1000;if(mode==="full")min+=d*1000*(19-ix[a.f]+ix[b.f]);}else min=d*1000*(mode==="both"?Math.min(k,20-k):k);}
let t=Math.max(b.t-lag*1000,p.t+min);if(t>b.t)continue;
let cost=s.cost;if(a){if(sw)cost+=25+Math.min(dt/1000,300)*.035+(19-ix[a.f]+ix[b.f])*.18;else cost+=Math.min(Math.abs(dt/1000-7*k),150)*.12+Math.max(0,k-1)*.4;}
let w=s.w.slice();w[z]={a:j,t,id:p.id};let node={w,cost,ccs:s.ccs+(sw?1:0),prev:keep?s:null,action:keep?{id:p.id,j,t}:null};pool.push(node);
}}
if(!pool.length)break;
pool.sort((a,b)=>a.cost-b.cost);let keys=new Set();beam=[];for(const p of pool){let key=p.w.map(w=>w.a+":"+w.t).sort().join("|");if(keys.has(key))continue;keys.add(key);beam.push(p);if(beam.length>=width)break;}processed=j+1;
}
let s=beam[0],summary={...cfg,processed,total:ev.length,ccs:s.ccs,cost:s.cost};if(!keep)return summary;let paths=Array.from({length:7},()=>[]);for(let p=s;p&&p.action;p=p.prev){let {id,j,t}=p.action,b=ev[j];paths[id].push({anchor:j+1,rawIndices:groups[j],c:b.c,f:b.f,observedMs:b.t,modeledMs:t});}paths.forEach(p=>p.reverse());return{summary,paths};
}
let tests=[];for(const mode of ["forward","both","full"])for(const d of [2,4,6])for(const lag of [1,2,4,8])tests.push(run({mode,d,cc:2,lag,width:32}));
let feasible=tests.filter(t=>t.processed===ev.length).sort((a,b)=>a.cost-b.cost);
let chosen=feasible[0];let best=chosen?run({...chosen,width:96},true):null;
if(best&&best.summary.processed!==ev.length)best=run(chosen,true);
return {raw:records.length,anchors:ev.length,tests,best};
}

module.exports=analyze;
