function reconstruct(raw, opts={}){
const route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2], H=3600, D=7, L=140, offset=140, end=H+offset, base=Date.parse("2026-11-27T22:13:51.434+08:00")/1000,clock=t=>new Date(Math.round((base+t+28800)*1000)).toISOString().slice(11,23);
const events=[],seen=new Map();for(const l of raw.split(/\r?\n/).slice(1).filter(Boolean)){const m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);if(!m)throw Error("bad record");const t=Date.parse(m[1]+"T"+m[2]+":"+m[3]+":"+m[4]+"."+m[5]+"+08:00")/1000-base,c=+m[6]-1,f=route.indexOf(+m[7]),k=c*20+f;if(t-(seen.get(k)??-Infinity)<2)continue;seen.set(k,t);if(t>=0&&t<H&&!(opts.blocked??[]).some(v=>v.c===c+1&&v.f===route[f]&&v.start<=t&&t<v.end))events.push({t,c,f});}
const n=end+L+2, mask=Array.from({length:800},()=>new Uint8Array(n));for(const e of events){const b=Math.floor(e.t)+offset;for(let s=Math.max(0,b-D+1);s<=b;s++)mask[e.c*20+e.f][s]=1;}
const score=new Float64Array((end+1)*40).fill(-1e9),pstart=new Int32Array(score.length).fill(-1),pc=new Int8Array(score.length).fill(-1),phase=new Int8Array(score.length),hits=new Uint8Array(score.length);
const best1=new Int8Array(end+1).fill(-1),best2=new Int8Array(end+1).fill(-1);const at=(s,c)=>s*40+c;let last={v:-1e9,s:-1,c:-1};
for(let s=0;s<end;s++){
 for(let c=0;c<40;c++){
  let best=-1e9,ps=-1,pch=-1;
  if(s<=offset&&s+L>offset)best=0;
  for(let g=2;g<=12;g++){let t=s-L-g;if(t<0)continue;let a=best1[t]===c?best2[t]:best1[t];if(a<0)continue;let v=score[at(t,a)]-.035*(g-2);if(v>best){best=v;ps=t;pch=a;}}
  if(best<-1e8)continue;
  let b=-1,p=0;for(let k=0;k<20;k++){if(opts.onlyFM1&&k!==0)continue;let z=0;for(let j=0;j<20;j++)z+=mask[c*20+(k+j)%20][s+j*D];if(z>b){b=z;p=k;}}
  if(opts.separateChannels&&(opts.blocked??[]).some(v=>v.c===c+1&&v.start<s-offset+L&&v.end>s-offset))continue;
  if(opts.exclude&&s-offset<=opts.exclude.t&&s-offset+L>opts.exclude.t&&c+1===opts.exclude.c)continue;
  const i=at(s,c);score[i]=best+b;phase[i]=p;hits[i]=b;pstart[i]=ps;pc[i]=pch;
  if(best1[s]<0||score[i]>score[at(s,best1[s])]){best2[s]=best1[s];best1[s]=c;}else if(best2[s]<0||score[i]>score[at(s,best2[s])])best2[s]=c;
  if(s+L>=end&&score[i]>last.v)last={v:score[i],s,c};
 }
}
if(last.s<0)throw Error("no path");let sweeps=[];for(let s=last.s,c=last.c;s>=0;){let i=at(s,c);sweeps.push({start:s-offset,end:s-offset+L,c:c+1,phase:phase[i],hits:hits[i]});let old=pstart[i];c=pc[i];s=old;}sweeps.reverse();
const visits=[],switches=[];let hitMarks=0;for(let i=0;i<sweeps.length;i++){let a=sweeps[i];for(let j=0;j<20;j++){let t=a.start+j*D,f=(a.phase+j)%20;if(t+D<=0||t>=H)continue;let es=events.filter(e=>e.c===a.c-1&&e.f===f&&e.t>=t&&e.t<t+D);hitMarks+=es.length;visits.push({c:a.c,f:route[f],start:Math.max(0,t),end:Math.min(H,t+D),observed:es.map(e=>clock(e.t))});}if(i>0){let b=sweeps[i-1];switches.push({from:b.c,to:a.c,start:b.end,end:a.start,gap:a.start-b.end});}}
function pos(t){let v=visits.find(v=>v.start<=t&&t<v.end);if(v)return {channel:v.c,room:v.f,observed:v.observed};let g=switches.find(x=>x.start<=t&&t<x.end);return g?{switch:[g.from,g.to]}:{unknown:true};}
const minutes=[];for(let t=0;t<H;t+=60)minutes.push({time:clock(t),...pos(t),observedRooms:visits.filter(v=>v.start<t+60&&v.end>t&&v.observed.length).length});
const minuteClock=[];for(let t=60-51.434;t<H;t+=60)minuteClock.push({time:clock(t),...pos(t),observedRooms:visits.filter(v=>v.start<t+60&&v.end>t&&v.observed.length).length});
const supported=visits.filter(v=>v.observed.length).length,scanning=visits.reduce((s,v)=>s+v.end-v.start,0),switchTime=switches.reduce((s,v)=>s+Math.min(H,v.end)-Math.max(0,v.start),0);
return {start:clock(0),end:clock(H),events:events.length,sweeps:sweeps.map(x=>({...x,startClock:clock(Math.max(0,x.start)),endClock:clock(Math.min(H,x.end)),first:route[x.phase]})),visits:visits.map(v=>({...v,startClock:clock(v.start),endClock:clock(v.end)})),switches:switches.map(v=>({...v,startClock:clock(v.start),endClock:clock(v.end)})),minutes,minuteClock,objective:last.v,supported,hitMarks,scanning,switchTime,cutoffPosition:pos(H-.001),unobserved:visits.length-supported,visitCount:visits.length,options:{separateChannels:!!opts.separateChannels,exclude:opts.exclude??null,blockedVisits:opts.blocked?.length??0},notes:"One maximum-score synthetic one-worker trajectory, not a recovered identity. 7s room windows, 20 rooms per sweep, arbitrary start phase, distinct channel changes with modeled gaps 2–12s, same nominal room times whether alert present or not. Reward 1 per room-window with >=1 consolidated observation, small gap penalty .035/sec over2s. Screenshot download time proxy. No credit for multiple alerts in a room. Missing marks do not distinguish empty room from no profitable deal. Whole hour retrospective optimization, not predictive validation."};
}




if(require.main===module){const fs=require('node:fs');const raw=fs.readFileSync(process.argv[2],'utf8'),p=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));console.log(JSON.stringify(reconstruct(raw,{blocked:[...p.scanner1.visits,...p.scanner2.visits,...p.scanner3.visits,...p.scanner4.visits]}),null,2));}
module.exports=reconstruct;
