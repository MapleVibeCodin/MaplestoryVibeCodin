function spatial(raws){
 const files=[...new Set(raws.flatMap(s=>s.split(/\r?\n/).slice(1).filter(Boolean)))].sort(),raw=files.map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000,c:+m[6]-1,f:+m[7],id:l.match(/_([^_]+)\.png$/i)?.[1]};}),seen=new Map(),ev=raw.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true;});
 const start=Date.parse("2026-11-24T00:00:00+08:00")/1000,split=Date.parse("2026-11-27T00:00:00+08:00")/1000,last=Date.parse("2026-11-27T21:19:37.057+08:00")/1000,end=ev.at(-1).t;
 const route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],idx=[];route.forEach((v,i)=>idx[v]=i);
 const floor=f=>f<=6?0:f<=12?1:f<=16?2:3,sum=a=>a.reduce((s,x)=>s+x,0),norm=a=>{let z=sum(a);return a.map(x=>x/z)},med=a=>{let q=sum(a)/2,s=0;return a.findIndex(x=>(s+=x)>=q)},cost=(p,x)=>sum(p.map((v,i)=>v*Math.abs(x-i)));
 const rowMass=p=>{let a=[0,0,0,0];p.forEach((v,i)=>a[floor(i+1)]+=v);return a;};
 const room=Array(20).fill(1),cells=Array.from({length:40},()=>Array(20).fill(.25)),prev=Array(40).fill(null);
 const ticks=new Set();for(let e of ev)for(let k of [0,2,5,10,20,40]){let t=Math.ceil(e.t)+k;if(t>=start&&t<=end)ticks.add(t);}
 const times=[...ticks].sort((a,b)=>a-b),grids=new Map();let i=0;
 for(let t of times){while(i<ev.length&&ev[i].t<t){let e=ev[i++];room[e.f-1]++;cells[e.c][e.f-1]++;prev[e.c]=e;}
 let base=norm(room),global=rowMass(base),conditional=cells.map((a,c)=>{let p=norm(a.map((v,j)=>v+15*base[j])),e=prev[c];if(!e||t-e.t>60)return rowMass(p);let age=t-e.t,center=idx[e.f]+age/7;if(center>21)return rowMass(p);let w=.65*Math.exp(-age/90),q=norm(p.map((v,j)=>Math.exp(-Math.pow(idx[j+1]-center,2)/18)+.03));return rowMass(p.map((v,j)=>(1-w)*v+w*q[j]));});
 grids.set(t,{global,conditional});}
 function replay(lo,hi,p){
  let es=ev.filter(e=>e.t>=lo&&e.t<=hi),ts=times.filter(t=>t>=lo&&t<=hi),i=0,j=0,cc=ev.filter(e=>e.t<lo).at(-1)?.c??0,target=cc,done=-Infinity,queued=null,clock=lo-1,position=1,walkTarget=1,moving=false,totalWalk=0,changes=0,stats={n:es.length,dist:0,near:0,exact:0,channelHit:0,joint:0,either:0,correctChannelDistance:0,correctChannelNear:0,wrongChannelDistance:0,wrongChannelNear:0,lat:0};
  function advance(t){if(moving){let d=Math.min(Math.abs(walkTarget-position),Math.max(0,t-clock)/p.sec);let dir=Math.sign(walkTarget-position);position+=d*dir;totalWalk+=d;if(Math.abs(position-walkTarget)<1e-9)moving=false;}clock=t;}
  function change(c,t){if(c===cc)return;target=c;done=t+2;moving=false;walkTarget=position;}
  while(i<es.length||j<ts.length){let et=es[i]?.t??Infinity,tt=ts[j]??Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;advance(t);
   if(t===ft){cc=target;done=-Infinity;if(queued!==null){let q=queued;queued=null;change(q,t);}}
   if(t===et){let e=es[i++],busy=done>t,hit=!busy&&cc===e.c,d=Math.abs(position-floor(e.f)),near=d<=1+1e-9;stats.dist+=d;stats.near+=near;stats.exact+=d<1e-9;stats.channelHit+=hit;stats.joint+=hit&&near;stats.either+=hit||near;stats.lat+=busy?done-t+(target===e.c?0:2):hit?0:2;if(hit){stats.correctChannelDistance+=d;stats.correctChannelNear+=near;}else{stats.wrongChannelDistance+=d;stats.wrongChannelNear+=near;}
    if(busy)queued=e.c;else change(e.c,t);
   }
   if(t===tt){j++;if(p.weight>0&&done<=t){let g=grids.get(t),q=g.global.map((v,k)=>(1-p.weight)*v+p.weight*g.conditional[cc][k]),b=med(q),gain=cost(q,position)-cost(q,b);if(gain>p.margin&&Math.abs(b-walkTarget)>1e-9){walkTarget=b;moving=true;changes++;}}}
  }
  return {...stats,totalWalk,changes};
 }
 let base={weight:0,sec:1,margin:0},val=replay(start,split-.001,base),test=replay(split,end,base),tail=replay(last+.001,end,base),candidates=[];
 for(let sec of [.5,1,2,4])for(let weight of [0,.25,.5,.75,1])for(let margin of [0,.05,.15,.3]){if(weight===0&&margin!==0)continue;let p={sec,weight,margin};candidates.push({p,val:replay(start,split-.001,p)});}
 const selections=[];for(let sec of [.5,1,2,4]){let list=candidates.filter(x=>x.p.sec===sec).sort((a,b)=>a.val.dist-b.val.dist||a.val.totalWalk-b.val.totalWalk);let a=list[0];let other=candidates.filter(x=>x.p.sec===sec).sort((a,b)=>b.val.either-a.val.either||a.val.dist-b.val.dist||a.val.totalWalk-b.val.totalWalk)[0];for(let [objective,x] of [["distance",a],["either",other]])selections.push({objective,...x,test:replay(split,end,x.p),latest:replay(last+.001,end,x.p)});}
 // Static room geometry sensitivity: hypothetical equal-width and centered rows, ordinal distance only.
 function coords(f){let rr=floor(f),first=[1,7,13,17][rr],width=[6,6,4,4][rr];return {x:f-first+(6-width)/2,y:rr};}
 let staticResults=[];for(let vertical of [1,2,3,4]){let costs=Array.from({length:20},(_,j)=>{let a=coords(j+1),s=0,n=0;for(let e of ev){if(e.t>=start&&e.t<split){let b=coords(e.f);s+=Math.abs(a.x-b.x)+vertical*Math.abs(a.y-b.y);n++;}}return s/n;});let min=Math.min(...costs),best=costs.indexOf(min)+1;let testCosts=Array.from({length:20},(_,j)=>{let a=coords(j+1),s=0,n=0;for(let e of ev){if(e.t>=split){let b=coords(e.f);s+=Math.abs(a.x-b.x)+vertical*Math.abs(a.y-b.y);n++;}}return s/n;});staticResults.push({vertical,best,validation:min,test:testCosts[best-1],testBest:testCosts.indexOf(Math.min(...testCosts))+1,FM9:testCosts[8],FM10:testCosts[9]});}
 // Dedup sensitivity: first observation per listing ID, then same-room consolidation.
 let ids=new Set(),rs=new Map(),unique=raw.filter(e=>{if(ids.has(e.id))return false;ids.add(e.id);return true;}).filter(e=>{let k=e.c*100+e.f;if(e.t-(rs.get(k)??-Infinity)<2)return false;rs.set(k,e.t);return true;}),rows=[0,0,0,0];unique.forEach(e=>rows[floor(e.f)]++);
 return {baseline:{validation:val,day27:test,latest:tail},candidates:candidates.length,selections,staticResults,idDedup:{n:unique.length,rows,bestRow:med(rows)+1,near:(rows[0]+rows[1]+rows[2])/unique.length},notes:"Reactive channel pursuit identical for each variant; floor-only speculative movement when not changing channels; position preserved across channel change; no post-alert shop movement, horizontal movement or travel measurement. Linear continuous walking in row units, hypothetical .5/1/2/4 seconds per row. Predictions use only events strictly before action ticks scheduled from earlier events. Selection on Nov24/26 only, Nov27 retrospective comparison. Either=correct channel OR within one row conditional on position transfer; not actual physical proximity."};
}
if(require.main===module){const fs=require('node:fs');console.log(JSON.stringify(spatial(process.argv.slice(2).map(p=>fs.readFileSync(p,'utf8'))),null,2));}
module.exports=spatial;
