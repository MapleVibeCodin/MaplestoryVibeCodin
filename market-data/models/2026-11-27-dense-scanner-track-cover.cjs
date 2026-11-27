function tracking(raws){
 const route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],idx=[];route.forEach((v,i)=>idx[v]=i);
 const origin=Date.parse("2026-11-27T22:34:00+08:00")/1000,clock=t=>new Date((t+origin+28800)*1000).toISOString().slice(11,23),cut=Date.parse("2026-11-27T22:45:41.002+08:00")/1000-origin;
 const raw=[...new Set(raws.flatMap(x=>x.split(/\r?\n/).slice(1).filter(Boolean)))].sort().map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("bad record");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000-origin,c:+m[6],f:+m[7],i:idx[+m[7]]};});
 let seen=new Map(),ev=raw.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true;}).filter(e=>e.t>=0);
 const med=a=>{let b=a.slice().sort((a,b)=>a-b);return b.length?(b[Math.floor((b.length-1)/2)]+b[Math.floor(b.length/2)])/2:null;};
 function compatible(a,b,lo=4,hi=12){let k=(b.i-a.i+20)%20,dt=b.t-a.t;return k>=1&&k<=5&&dt/k>=lo&&dt/k<=hi;}
 let pairs=[],wraps=[],direct=[],stepTimes=Array.from({length:20},()=>[]),revisit=[],ep=[];
 for(let c=1;c<=40;c++){let s=ev.filter(e=>e.c===c),groups=[],prior={};for(let j=0;j<s.length;j++){let a=s[j-1],b=s[j];if(!a||b.t-a.t>60)groups.push([]);groups.at(-1).push(b);if(prior[b.f]!==undefined&&b.t-prior[b.f]>15)revisit.push(b.t-prior[b.f]);prior[b.f]=b.t;if(a&&a.f!==b.f&&b.t-a.t<=60){let k=(b.i-a.i+20)%20,dt=b.t-a.t,ok=compatible(a,b);pairs.push({c,k,dt,ok});if(ok&&b.i<a.i)wraps.push({c,from:a.f,to:b.f,start:clock(a.t),end:clock(b.t),k,dt});if(ok&&k===1){direct.push(dt);stepTimes[a.i].push(dt);}}}
 for(let g of groups){let s=g.filter((x,j)=>!j||g[j-1].f!==x.f),ok=s.slice(1).filter((x,j)=>compatible(s[j],x)).length;if(new Set(s.map(x=>x.f)).size>=4&&ok>=3&&ok/(s.length-1)>=.6)ep.push({c,start:s[0].t,end:s.at(-1).t,first:s[0].f,last:s.at(-1).f,rooms:s.map(x=>x.f),ok,total:s.length-1});}}
 ep.sort((a,b)=>a.start-b.start);const n=ep.length;
 // Minimum path cover of strong interval episodes. A link requires non-overlap and at least a chosen time gap.
 function cover(maxGap,minGap=0,same=false,seed=0,K=null){
  const N=2*n+2,S=2*n,T=S+1,G=Array.from({length:N},()=>[]);let rand=seed>>>0;function rng(){rand=(1664525*rand+1013904223)>>>0;return rand/4294967296;}
  function add(a,b,cap,cost,tag){let e={to:b,rev:G[b].length,cap,cost,tag};G[a].push(e);G[b].push({to:a,rev:G[a].length-1,cap:0,cost:-cost});}
  for(let i=0;i<n;i++){add(S,i,1,0);add(n+i,T,1,0);}
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){let gap=ep[j].start-ep[i].end;if(gap<minGap||gap>maxGap||(!same&&ep[i].c===ep[j].c))continue;let cost=gap+(seed?80*rng():0);add(i,n+j,1,cost,[i,j]);}
  let flow=0,total=0;while(K===null||flow<n-K){let dist=Array(N).fill(Infinity),pv=Array(N).fill(-1),pe=Array(N).fill(-1);dist[S]=0;for(let l=0;l<N-1;l++){let changed=false;for(let u=0;u<N;u++)if(isFinite(dist[u]))for(let k=0;k<G[u].length;k++){let e=G[u][k];if(e.cap&&dist[u]+e.cost<dist[e.to]-1e-8){dist[e.to]=dist[u]+e.cost;pv[e.to]=u;pe[e.to]=k;changed=true;}}if(!changed)break;}if(!isFinite(dist[T]))break;for(let v=T;v!==S;v=pv[v]){if(pv[v]<0)throw Error("path");let e=G[pv[v]][pe[v]];e.cap--;G[v][e.rev].cap++;}flow++;total+=dist[T];}
  let edges=[];for(let i=0;i<n;i++)for(let e of G[i])if(e.tag&&e.cap===0)edges.push(e.tag);
  let next=new Map(edges),incoming=new Set(edges.map(x=>x[1])),chains=[];for(let i=0;i<n;i++)if(!incoming.has(i)){let a=[],j=i;while(j!==undefined){a.push(j);j=next.get(j);}chains.push(a);}
  if(chains.flat().length!==n||new Set(chains.flat()).size!==n||chains.length!==n-flow)throw Error("path cover validation");
  return {count:n-flow,edges,chains,totalGap:edges.reduce((s,[i,j])=>s+ep[j].start-ep[i].end,0)};
 }
 let sensitivity=[];for(let max of [15,30,60,90,120,180,300,Infinity])for(let min of [0,2,5]){let v=cover(max,min);sensitivity.push({max:max===Infinity?"unbounded":max,min,count:v.count});}
 const choice=cover(Infinity,2);let gapList=choice.edges.map(([i,j])=>ep[j].start-ep[i].end),chains=choice.chains.map((a,i)=>({track:i+1,episodes:a.map(k=>({id:k,c:ep[k].c,start:clock(ep[k].start),end:clock(ep[k].end),rooms:ep[k].rooms})),gap:a.slice(1).map((v,j)=>ep[v].start-ep[a[j]].end)}));
 let frequencies={},valid=0;for(let seed=1;seed<=40;seed++){let v=cover(Infinity,2,false,seed,choice.count);if(v.count!==choice.count)continue;valid++;for(let [a,b] of v.edges){let key=a+"-"+b;frequencies[key]=(frequencies[key]??0)+1;}}
 const edgeStability=choice.edges.map(([a,b])=>({from:ep[a].c,to:ep[b].c,a,b,gap:ep[b].start-ep[a].end,frequency:(frequencies[a+"-"+b]??0)/valid}));let overlap=0;for(let e of ep)overlap=Math.max(overlap,ep.filter(a=>a.start<=e.start&&a.end>=e.start).length);
 // Count exact direct room edge vs reverse direction, conditioned only on observed gap 4..12, not route compatibility.
 let forward=0,reverse=0,other=0;for(let x of pairs){if(x.dt<4||x.dt>12)continue;if(x.k===1)forward++;else if(x.k===19)reverse++;else other++;}
 let revisitBins={short15to90:0,mid90to240:0,mid240to660:0,near855:0,other:0};for(let t of revisit){if(t<90)revisitBins.short15to90++;else if(t<240)revisitBins.mid90to240++;else if(t<660)revisitBins.mid240to660++;else if(Math.abs(t-855)<=120)revisitBins.near855++;else revisitBins.other++;}
 let fullCycle=stepTimes.reduce((s,x)=>s+med(x),0);
 return {n:ev.length,span:ev.at(-1).t,channels:new Set(ev.map(e=>e.c)).size,pairs:pairs.length,compatible:pairs.filter(x=>x.ok).length,direct:direct.length,directMedian:med(direct),fullCycle,steps:stepTimes.map((a,i)=>({from:route[i],to:route[(i+1)%20],n:a.length,median:med(a)})),wraps,forwardReverse:{forward,reverse,other},revisitN:revisit.length,revisitBins,episodes:ep.map((e,i)=>({...e,id:i,startClock:clock(e.start),endClock:clock(e.end)})),peakOverlap:overlap,meanOverlap:ep.reduce((s,e)=>s+e.end-e.start,0)/ev.at(-1).t,sensitivity,minCover:{count:choice.count,medianGap:med(gapList),maxGap:Math.max(...gapList),chains,edgeStability,perturbations:valid,stable:edgeStability.filter(e=>e.frequency>=.8).length,medianStability:med(edgeStability.map(e=>e.frequency))},notes:"Path cover on strong episode intervals is a combinatorial lower bound under one uninterrupted worker per strong envelope and assumed gap. Links are hypothetical, not identified worker transitions. Min cost based only on gaps; perturbations are robustness diagnostic, not posterior probability. Dense period from22:34 descriptive filter regime. No live prediction or user movement."};
}
if(require.main===module){const fs=require('node:fs');console.log(JSON.stringify(tracking(process.argv.slice(2).map(p=>fs.readFileSync(p,'utf8'))),null,2));}
module.exports=tracking;
