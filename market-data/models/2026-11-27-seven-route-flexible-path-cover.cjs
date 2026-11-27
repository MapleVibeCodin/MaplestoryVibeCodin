
function analyze(raw){
const base=Date.parse("2026-11-27T22:34:00+08:00")/1000,route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],ix=Object.fromEntries(route.map((f,i)=>[f,i]));
const records=raw.map((l,i)=>{const m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {i:i+1,t:Date.parse(m[1]+"T"+m[2]+":"+m[3]+":"+m[4]+"."+m[5]+"+08:00")/1000-base,c:+m[6],f:+m[7]};});
const seen=new Map(),ev=[],groups=[];for(const e of records){let k=e.c*100+e.f,p=seen.get(k);if(p!==undefined&&e.t-ev[p].t<2){groups[p].push(e.i);continue;}seen.set(k,ev.length);ev.push(e);groups.push([e.i]);}
const n=ev.length;function solve(cfg,keep=false){
const {d,cc,lag,mode,maxGap}=cfg;
function travel(a,b){if(a.c!==b.c){if(mode==="full")return cc+d*((19-ix[a.f])+ix[b.f]);return cc;}let k=(ix[b.f]-ix[a.f]+20)%20;if(mode==="bidirectional")k=Math.min(k,20-k);if(mode==="free")k=Math.min(k,1);return d*k;}
function cost(a,b,dt){let k=(ix[b.f]-ix[a.f]+20)%20;if(a.c===b.c){if(mode==="bidirectional")k=Math.min(k,20-k);return Math.abs(dt-7*k)*.14+Math.max(0,k-1)*.7;}return 25+Math.min(dt,300)*.04+((19-ix[a.f])+ix[b.f])*.25;}
let adj=Array.from({length:n},()=>[]);for(let i=0;i<n;i++){let a=ev[i];for(let j=i+1;j<n;j++){let b=ev[j],dt=b.t-a.t;if(dt>maxGap)break;let min=travel(a,b);if(min<=dt+lag+1e-7)adj[i].push({j,c:cost(a,b,dt)});}adj[i].sort((a,b)=>a.c-b.c||a.j-b.j);}
let L=new Int32Array(n).fill(-1),R=new Int32Array(n).fill(-1),dist=new Int32Array(n),matched=0;
function bfs(){let q=[];for(let i=0;i<n;i++){dist[i]=L[i]<0?0:-1;if(L[i]<0)q.push(i);}let found=false;for(let h=0;h<q.length;h++){let i=q[h];for(const {j} of adj[i]){let k=R[j];if(k<0)found=true;else if(dist[k]<0){dist[k]=dist[i]+1;q.push(k)}}}return found;}
function dfs(i){for(const {j} of adj[i]){let k=R[j];if(k<0||(dist[k]===dist[i]+1&&dfs(k))){L[i]=j;R[j]=i;return true}}dist[i]=-1;return false}
while(bfs()){for(let i=0;i<n;i++)if(L[i]<0&&dfs(i))matched++;}
let minTracks=n-matched;
if(minTracks<7){let edges=Array.from(L).map((j,i)=>({i,j})).filter(x=>x.j>=0).sort((a,b)=>cost(ev[b.i],ev[b.j],ev[b.j].t-ev[b.i].t)-cost(ev[a.i],ev[a.j],ev[a.j].t-ev[a.i].t));for(let k=0;k<7-minTracks;k++){let {i,j}=edges[k];L[i]=-1;R[j]=-1;}}
let paths=[];for(let i=0;i<n;i++)if(R[i]<0){let p=[];for(let j=i;j>=0;j=L[j])p.push(j);paths.push(p)}
let violation=0,maxLate=0,ccs=0,forward=0,same=0,reverse=0,shortCC=0,lagNeeded=0,totalCost=0,delayCount=0;
let out=paths.map(p=>{let t=ev[p[0]].t-lag;return p.map((j,i)=>{let b=ev[j];if(i){let a=ev[p[i-1]],dt=b.t-a.t,min=travel(a,b);t=Math.max(b.t-lag,t+min);totalCost+=cost(a,b,dt);if(a.c!==b.c){ccs++;if(dt<2)shortCC++;}else{same++;let k=(ix[b.f]-ix[a.f]+20)%20;if(k===1)forward++;if(k===19)reverse++;}}let late=Math.max(0,t-b.t);if(late>1e-6)violation++;maxLate=Math.max(maxLate,late);lagNeeded=Math.max(lagNeeded,b.t-t+late);if(b.t-t>1e-6)delayCount++;return {anchor:j+1,rawIndices:groups[j],c:b.c,f:b.f,observed:b.t,modeled:t};})});
let summary={...cfg,minTracks,tracks:paths.length,violations:violation,maxLate,ccs,same,forward,reverse,shortCC,totalCost,delayCount,covered:paths.reduce((a,p)=>a+p.length,0),rawCovered:groups.reduce((a,g)=>a+g.length,0),lengths:paths.map(p=>p.length)};
return keep?{summary,paths:out}:summary;
}
let tests=[];for(const mode of ["full","forward","bidirectional","free"])for(const d of [2,4,6])for(const lag of [0,1,2,4])tests.push(solve({mode,d,cc:2,lag,maxGap:180}));
let candidates=tests.filter(x=>x.tracks===7&&x.violations===0).sort((a,b)=>a.lag-b.lag|| (a.mode==="forward"?0:a.mode==="full"?0:1)-(b.mode==="forward"?0:b.mode==="full"?0:1)||b.d-a.d||a.ccs-b.ccs);
let chosen=candidates[0];return {raw:records.length,anchors:n,tests,chosen:chosen?solve(chosen,true):null};
}

module.exports=analyze;
