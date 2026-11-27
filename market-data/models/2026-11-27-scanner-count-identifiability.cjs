function identify(raws){
const origin=Date.parse("2026-11-27T22:34:00+08:00")/1000,route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],idx=[];route.forEach((v,i)=>idx[v]=i);
const clock=t=>new Date((t+origin+28800)*1000).toISOString().slice(11,23);
let raw=[...new Set(raws.flatMap(x=>x.split(/\r?\n/).slice(1).filter(Boolean)))].sort().map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6],f:+m[7],i:idx[+m[7]]};});
let last=new Map(),ev=raw.filter(e=>{let k=e.c*100+e.f;if(e.t-(last.get(k)??-Infinity)<2)return false;last.set(k,e.t);return true;}).filter(e=>e.t>=0);raw=raw.filter(e=>e.t>=0);
const med=a=>{let b=a.slice().sort((a,b)=>a-b);return b.length?(b[Math.floor((b.length-1)/2)]+b[Math.floor(b.length/2)])/2:null;};
function window(a,seconds){let best={n:0},j=0,counts=new Map();for(let i=0;i<a.length;i++){while(j<a.length&&a[j].t-a[i].t<seconds){counts.set(a[j].c,(counts.get(a[j].c)??0)+1);j++;}if(counts.size>best.n)best={n:counts.size,t:clock(a[i].t),channels:[...counts.keys()].sort((a,b)=>a-b),records:j-i};let c=a[i].c;counts.set(c,counts.get(c)-1);if(!counts.get(c))counts.delete(c);}return best;}
let intervals=[];for(let c=1;c<=40;c++){let a=ev.filter(e=>e.c===c);for(let j=1;j<a.length;j++){let p=a[j-1],q=a[j],k=(q.i-p.i+20)%20,dt=q.t-p.t;if(k>=1&&k<=5&&dt/k>=4&&dt/k<=12)intervals.push({c,a:p.t,b:q.t,from:p.f,to:q.f,k,dt});}}
function overlap(kmax,maxgap,trim){let ints=intervals.filter(x=>x.k<=kmax&&x.dt<=maxgap&&x.dt>2*trim).map(x=>({...x,a:x.a+trim,b:x.b-trim}));let best={n:0};for(let e of ints){let a=ints.filter(x=>x.a<=e.a&&x.b>e.a),cs=new Set(a.map(x=>x.c));if(cs.size>best.n)best={n:cs.size,t:clock(e.a),tracks:a.map(x=>({c:x.c,from:x.from,to:x.to,start:clock(x.a),end:clock(x.b),dt:x.dt}))};}return best;}
const shortOverlap=[];for(let k of [1,2,5])for(let maxgap of [12,24,60])for(let trim of [0,1,2])shortOverlap.push({k,maxgap,trim,...overlap(k,maxgap,trim)});
 // Exact minimum path cover of individual observed marks under explicit transition constraints.
 // Same room allowed any gap; different same-channel rooms may be observed in forward order with min dwell per skipped step;
 // long gaps can reset route. Different channel transitions constrained by assumed minimum time, with optional preservation of phase.
 function cover(minCC,minStep,phase,reset=60){
 const n=ev.length,adj=Array.from({length:n},()=>[]);for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){let a=ev[i],b=ev[j],dt=b.t-a.t,k=(b.i-a.i+20)%20;if(dt>=reset||(a.c===b.c?(k===0||dt>=minStep*k):(dt>=minCC&&(!phase||dt>=minCC+minStep*Math.min(k,20-k)))))adj[i].push(j);}
 let l=Array(n).fill(-1),rr=Array(n).fill(-1),dist=Array(n).fill(-1),flow=0;
 function bfs(){let q=[];for(let i=0;i<n;i++){dist[i]=l[i]<0?0:-1;if(l[i]<0)q.push(i);}let found=false;for(let i of q)for(let j of adj[i]){let u=rr[j];if(u<0)found=true;else if(dist[u]<0){dist[u]=dist[i]+1;q.push(u);}}return found;}
 function dfs(i){for(let j of adj[i]){let u=rr[j];if(u<0||(dist[u]===dist[i]+1&&dfs(u))){l[i]=j;rr[j]=i;return true;}}dist[i]=-1;return false;}
 while(bfs())for(let i=0;i<n;i++)if(l[i]<0&&dfs(i))flow++;
 let chains=[];for(let i=0;i<n;i++)if(rr[i]<0){let a=[],j=i;while(j>=0){a.push(j);j=l[j];}chains.push(a);}if(chains.flat().length!==n||new Set(chains.flat()).size!==n||chains.length!==n-flow)throw Error("cover mismatch");
 return {count:n-flow,chainLengths:chains.map(x=>x.length).sort((a,b)=>b-a)};
 }
 let covers=[];for(let cc of [1,2,3,4,5,6,7,8,10])for(let step of [0,2,4])for(let phase of [false,true]){if(step===0&&phase)continue;covers.push({cc,step,phase,...cover(cc,step,phase)});}
 const rawGaps=raw.slice(1).map((e,i)=>e.t-raw[i].t);
 return {raw:raw.length,consolidated:ev.length,span:ev.at(-1).t,rawGapMedian:med(rawGaps),rawUnderHalf:rawGaps.filter(x=>x<.5).length,windows:[.5,1,2,3,5,7,10].map(s=>({seconds:s,raw:window(raw,s),consolidated:window(ev,s)})),shortOverlap,covers,notes:"All filename times are download/observation proxies. Windows bound concurrent workers only if timestamps are exact scan times and workers cannot change channels within window. Short interval overlaps assume continuous same-channel occupancy between marks. Individual mark cover permits unobserved jumps after60s; conditional minimum only, not estimate of actual physical worker count. Phase preservation is hypothetical; actual scanner CC timing unknown. More workers can always split a feasible track."};
}
if(require.main===module){const fs=require('node:fs');console.log(JSON.stringify(identify(process.argv.slice(2).map(p=>fs.readFileSync(p,'utf8'))),null,2));}
module.exports=identify;
