function analyze(raws){
 const lines=raws.map(s=>s.split(/\r?\n/).slice(1).filter(Boolean)),files=[...new Set(lines.flat())].sort(),raw=files.map(l=>{let m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("bad filename");return {t:Date.parse(`${m[1]}T${m[2]}:${m[3]}:${m[4]}.${m[5]}+08:00`)/1000,c:+m[6]-1,f:+m[7],day:m[1],id:l.match(/_([^_]+)\.png$/i)?.[1]};});
 const seen=new Map(),ev=raw.filter(e=>{let k=e.c*100+e.f;if(e.t-(seen.get(k)??-Infinity)<2)return false;seen.set(k,e.t);return true;});
 const start=Date.parse("2026-11-24T00:00:00+08:00")/1000,split=Date.parse("2026-11-27T00:00:00+08:00")/1000,lastCut=Date.parse("2026-11-27T21:19:37.057+08:00")/1000,end=ev.at(-1).t;
 const sum=a=>a.reduce((s,v)=>s+v,0),norm=a=>{let z=sum(a);return a.map(v=>v/z);},arg=a=>a.reduce((b,v,i)=>v>a[b]?i:b,0),floor=f=>f<=6?0:f<=12?1:f<=16?2:3;
 const median=a=>{let h=sum(a)/2,v=0;return a.findIndex(x=>(v+=x)>=h);};
 const route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],idx=[];route.forEach((f,i)=>idx[f]=i);
 const channel=Array(40).fill(1),cell=Array.from({length:40},()=>Array(20).fill(.25)),globalRoom=Array(20).fill(1),trans=Array.from({length:40},()=>Array(40).fill(0)),trTotal=Array(40).fill(0),last=Array(40).fill(null),onset=last.slice(),gapHistory=Array.from({length:6},()=>[0,0]),tau=[15,60,300],dec=tau.map(()=>Array(40).fill(0));let prev=null,clock=ev[0].t,j=0;
 const ticks=new Set(),actions=new Set(),origins=new Map();for(let e of ev){if(e.t>=start){let t=Math.floor(e.t-2);if(t>=start){ticks.add(t);if(!origins.has(t))origins.set(t,[]);origins.get(t).push(e);}}if(e.t>=start-45)for(let k of [0,2,5,10,20,40]){let t=Math.ceil(e.t)+k;if(t>=start&&t<=end){ticks.add(t);actions.add(t);}}}
 let times=[...ticks].sort((a,b)=>a-b),grids=new Map(),modelNames=["frequency","persistence","transition","recent15","recent60","recent300","route-recurrence","blend"];
 function decay(t){let dt=t-clock;if(dt<0)throw Error("clock backwards");for(let m=0;m<3;m++){let a=Math.exp(-dt/tau[m]);for(let c=0;c<40;c++)dec[m][c]*=a;}clock=t;}
 function observe(e){decay(e.t);channel[e.c]++;cell[e.c][e.f-1]++;globalRoom[e.f-1]++;for(let a of dec)a[e.c]++;if(prev&&e.t-prev.t<=60){trans[prev.c][e.c]++;trTotal[prev.c]++;}if(last[e.c]===null||e.t-last[e.c].t>60)onset[e.c]=e.t;last[e.c]=e;
 if(prev){let g=e.t-prev.t;for(let [k,a] of [0,2,5,10,20,40].entries())if(g>a){gapHistory[k][0]++;gapHistory[k][1]+=Math.max(0,2-(g-a));}}prev=e;}
 let recStats={compatible:0,total:0,step:[],perDay:{}};let previous=Array(40).fill(null);for(let e of ev){let p=previous[e.c];if(p&&p.f!==e.f&&e.t-p.t<=60){let k=(idx[e.f]-idx[p.f]+20)%20,d=(e.t-p.t)/k;recStats.total++;let s=recStats.perDay[e.day]??=[0,0];s[0]++;if(k>=1&&k<=5&&d>=4&&d<=12){recStats.compatible++;recStats.step.push(d);s[1]++;}}previous[e.c]=e;}
 let scoreSets={validation:[],day27:[],latest:[]};for(let k of Object.keys(scoreSets))scoreSets[k]=modelNames.map(name=>({name,n:0,hit:0,top5:0,loss:0,roomHit:0,floorDist:0,conditionalDist:0,conditionalExact:0,jointNear:0}));
 const floorModels=["fixed FM row1","fixed FM row2","fixed FM row3","fixed FM row4","historical marginal median","forecast marginal median","channel-conditioned median","route-conditioned median"],floorStats={validation:[],day27:[],latest:[]};for(let k of Object.keys(floorStats))floorStats[k]=floorModels.map(name=>({name,n:0,dist:0,exact:0,within1:0}));
 for(let t of times){while(j<ev.length&&ev[j].t<t){observe(ev[j++]);}decay(t);let freq=norm(channel),pc=prev?.c??0,age=prev?t-prev.t:1e6,transP=norm(trans[pc].map((v,c)=>v+30*freq[c])),pers=freq.map((v,c)=>.15*v+(c===pc?.85:0)),recs=dec.map(a=>norm(a.map((v,c)=>v+2*freq[c]))),routeWeight=last.map((e,c)=>{if(!e)return .5;let a=t-e.t,o=t-onset[c],remaining=Math.max(0,19-idx[e.f])*7,active=a<=Math.min(60,remaining+10)?Math.exp(-a/18):0,rec=o>427.5&&a>60?Math.exp(-Math.pow(o-855*Math.max(1,Math.round(o/855)),2)/(2*120*120)):0;return .25+5*active+rec;});let rp=norm(routeWeight.map((v,c)=>v*freq[c])),blend=norm(freq.map((v,c)=>.25*transP[c]+.35*recs[1][c]+.4*rp[c]));
 let ps=[freq,pers,transP,...recs,rp,blend],marginalRoom=norm(globalRoom),floorMass=a=>{let f=[0,0,0,0];a.forEach((v,i)=>f[floor(i+1)]+=v);return f;};
 let rooms=cell.map(a=>norm(a.map((v,i)=>v+15*marginalRoom[i]))),routeRooms=rooms.map((a,c)=>{let e=last[c];if(!e||t-e.t>60)return a;let age=t-e.t,center=idx[e.f]+age/7;if(center>21)return a;let w=.65*Math.exp(-age/90);let q=norm(a.map((v,i)=>Math.exp(-Math.pow(idx[i+1]-center,2)/18)+.03));return a.map((v,i)=>(1-w)*v+w*q[i]);});
 let floorConditional=rooms.map(a=>median(floorMass(a))),floorRoute=routeRooms.map(a=>median(floorMass(a))),globalFloor=median(floorMass(marginalRoom)), forecasts=ps.map(p=>{let c=arg(p),f=[0,0,0,0];for(let k=0;k<40;k++){let m=floorMass(routeRooms[k]);for(let a=0;a<4;a++)f[a]+=p[k]*m[a];}return {p,c,f:median(f),room:arg(routeRooms[c])+1};});
 let gapBin=age<2?0:age<5?1:age<10?2:age<20?3:age<40?4:5,gh=gapHistory[gapBin],risk=(gh[1]+5)/(gh[0]+10);
 grids.set(t,{forecasts:forecasts.map(x=>({c:x.c,p:x.p,f:x.f})),risk,globalFloor,conditional:floorConditional,route:floorRoute});
 if(origins.has(t))for(let e of origins.get(t)){let sets=e.t<split?["validation"]:e.t>lastCut?["day27","latest"]:["day27"];let actual=floor(e.f);for(let k of sets){for(let m=0;m<ps.length;m++){let s=scoreSets[k][m],p=ps[m],f=forecasts[m],rank=p.reduce((n,v,i)=>n+(v>p[e.c]||(v===p[e.c]&&i<e.c)?1:0),0);s.n++;s.hit+=f.c===e.c;s.top5+=rank<5;s.loss-=Math.log(Math.max(1e-12,p[e.c]));s.roomHit+=f.room===e.f&&f.c===e.c;s.floorDist+=Math.abs(f.f-actual);s.conditionalDist+=Math.abs(floorRoute[e.c]-actual);s.conditionalExact+=floorRoute[e.c]===actual;s.jointNear+=f.c===e.c&&Math.abs(f.f-actual)<=1;}
 let floors=[0,1,2,3,globalFloor,forecasts[7].f,floorConditional[e.c],floorRoute[e.c]];floors.forEach((f,i)=>{let s=floorStats[k][i],dist=Math.abs(f-actual);s.n++;s.dist+=dist;s.exact+=dist===0;s.within1+=dist<=1;});}}
 }
 
 function stand(lo,hi,policy){
  let es=ev.filter(e=>e.t>=lo&&e.t<=hi),ticks=times.filter(t=>actions.has(t)&&t>=lo&&t<=hi),hist=Array(40).fill(0);for(let e of ev)if(e.t<lo)hist[e.c]++;
  let cc=policy.fixed==="historical"?arg(hist):ev.filter(e=>e.t<lo).at(-1)?.c??0,target=cc,done=-Infinity,arrived=lo,clock=lo-1,i=0,j=0,lat=0,hits=0,early=0,sw=0,near=0,joint=0,either=0;
  while(i<es.length||j<ticks.length){
   let et=es[i]?.t??Infinity,tt=ticks[j]??Infinity,ft=done>clock?done:Infinity,t=Math.min(et,tt,ft);if(!isFinite(t)||t>hi)break;clock=t;
   if(ft===t){cc=target;arrived=t;done=-Infinity;}
   if(et===t){let e=es[i++],busy=done>t,hit=!busy&&cc===e.c,close=Math.abs(1-floor(e.f))<=1;hits+=hit;early+=hit&&t-arrived>=1;near+=close;joint+=hit&&close;either+=hit||close;lat+=busy?done-t+(target===e.c?0:2):hit?0:2;}
   if(tt===t){j++;if(policy.m!==undefined&&done<=t){let g=grids.get(t),x=g.forecasts[policy.m],adv=2*(x.p[x.c]-x.p[cc])-g.risk;if(x.c!==cc&&adv>policy.margin&&t-arrived>=policy.cool){target=x.c;done=t+2;sw++;}}}
  }
  return {n:es.length,hits,early,lat,sw,near,joint,either};
 }
 let choices=[{fixed:"historical"},{fixed:"last"}];for(let m=0;m<modelNames.length;m++)for(let margin of [-.25,0,.1,.25,.5])for(let cool of [0,5,15])choices.push({m,margin,cool});
 const trials=choices.map(p=>({p,val:stand(start,split-.001,p)}));const tie=(a,b)=>a.val.lat-b.val.lat||a.val.sw-b.val.sw;trials.sort(tie);
 const detail=x=>({...x,name:x.p.m===undefined?x.p.fixed:modelNames[x.p.m],test:stand(split,end,x.p),latest:stand(lastCut+.001,end,x.p)});
 let best=detail(trials[0]),byModel=modelNames.map((name,m)=>detail(trials.find(x=>x.p.m===m))),fixed=trials.filter(x=>x.p.fixed).map(detail);
 let hitBest=detail(trials.slice().sort((a,b)=>b.val.early-a.val.early||tie(a,b))[0]);
 return {policies:trials.length,selected:best,bestEarly:hitBest,byModel,fixed,notes:"Standby-only counterfactual: no forced chase on observation. Estimates hypothetical response time per event if pursued, but actual waiting trajectory assumes no events pursued. Cannot compare summed cost as actual game time. Action ticks from observed events only. Initial historical favorite uses only pre-split counts. Validation Nov24/26, Nov27 retrospective. Fixed floor2, same 2s switch."};
}

if(require.main===module){const fs=require('node:fs');console.log(JSON.stringify(analyze(process.argv.slice(2).map(p=>fs.readFileSync(p,'utf8'))),null,2));}
module.exports=analyze;
