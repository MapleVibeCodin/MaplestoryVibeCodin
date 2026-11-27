
function analyze(raw){
const base=Date.parse("2026-11-27T22:34:00+08:00"), route=[1,7,17,18,19,20,16,15,14,13,8,9,10,11,12,6,5,4,3,2],ix=Object.fromEntries(route.map((f,i)=>[f,i]));
const records=raw.map((l,i)=>{const m=l.match(/^(\d{4}-\d\d-\d\d)_(\d\d)-(\d\d)-(\d\d)-(\d{3})_CH(\d+)-FM(\d+)_/);return {i:i+1,t:Date.parse(m[1]+"T"+m[2]+":"+m[3]+":"+m[4]+"."+m[5]+"+08:00")-base,c:+m[6],f:+m[7]};});
const seen=new Map(),ev=[],groups=[];for(const e of records){let k=e.c*100+e.f,p=seen.get(k);if(p!==undefined&&e.t-ev[p].t<2000){groups[p].push(e.i);continue;}seen.set(k,ev.length);ev.push(e);groups.push([e.i]);}
const validStart=Date.parse("2026-11-27T22:55:03.028+08:00")-base,testStart=Date.parse("2026-11-27T23:13:51.174+08:00")-base;
function run(cfg,keep=false){
const {count,d,lag,mode,width}=cfg;let beam=[{w:Array.from({length:count},(_,id)=>({a:-1,t:-1e12,id,streak:0})),cost:0,ccs:0,skips:0,rev:0,prev:null,action:null}];let snaps=[],score={val:{n:0,hit:0,top3:0,persist:0,rec15:0,assigned:0,ccs:0},test:{n:0,hit:0,top3:0,persist:0,rec15:0,assigned:0,ccs:0}},p=-1;
for(let j=0;j<ev.length;j++){const b=ev[j],origin=b.t-2000;while(p+1<j&&ev[p+1].t<origin)p++;let phase=b.t>testStart?"test":b.t>validStart?"val":null;
if(phase&&p>=0){let row=score[phase];row.n++;let w=snaps[p],sc=Array(41).fill(0),rec=Array(41).fill(0);
for(let z of w){if(z.a<0)continue;let e=ev[z.a],age=(origin-e.t)/1000;if(age>90)continue;let step=Math.max(1,Math.round((age+2)/7));let phaseWeight=Math.exp(-Math.pow(((age+2)-7*step)/4,2)/2);sc[e.c]+=Math.exp(-age/30)*(0.4+0.6*phaseWeight)*(1+Math.min(z.streak,5)*.18);}
for(let q=p;q>=0&&origin-ev[q].t<120000;q--)rec[ev[q].c]+=Math.exp(-(origin-ev[q].t)/15000);
let order=Array.from({length:40},(_,i)=>i+1).sort((a,b)=>sc[b]-sc[a]||rec[b]-rec[a]||a-b);let recbest=Array.from({length:40},(_,i)=>i+1).sort((a,b)=>rec[b]-rec[a]||a-b)[0];row.hit+=order[0]===b.c;row.top3+=order.slice(0,3).includes(b.c);row.persist+=ev[p].c===b.c;row.rec15+=recbest===b.c;}
let pool=[];for(const s of beam){let usedEmpty=false;for(let z=0;z<count;z++){let astate=s.w[z],a=ev[astate.a],dt=a?b.t-a.t:0,k=a?(ix[b.f]-ix[a.f]+20)%20:0,sw=!!a&&a.c!==b.c,rev=!sw&&mode==="both"&&k>10,steps=rev?20-k:k;if(!a){if(usedEmpty)continue;usedEmpty=true;}
let min=a?(sw?2000:d*1000*steps):0;let t=Math.max(b.t-lag*1000,astate.t+min);if(t>b.t)continue;
let c=s.cost;if(!a)c+=12;else if(sw)c+=30+Math.min(dt/1000,300)*.025+(19-ix[a.f]+ix[b.f])*.18;else c+=Math.min(Math.abs(dt/1000-7*steps),150)*.12+Math.max(0,steps-1)*.4+(rev?8:0);
let w=s.w.slice();w[z]={a:j,t,id:astate.id,streak:!a||sw?0:Math.min(9,astate.streak+1)};pool.push({w,cost:c,ccs:s.ccs+(sw?1:0),skips:s.skips,rev:s.rev+(rev?1:0),prev:keep?s:null,action:keep?{id:astate.id,j,t}:null});}
pool.push({w:s.w,cost:s.cost+90,ccs:s.ccs,skips:s.skips+1,rev:s.rev,prev:keep?s:null,action:keep?{id:-1,j,t:b.t}:null});}
pool.sort((a,b)=>a.cost-b.cost);let keys=new Set();beam=[];for(let s of pool){let k=s.w.map(w=>w.a+":"+w.t+":"+w.streak).sort().join("|");if(keys.has(k))continue;keys.add(k);beam.push(s);if(beam.length>=width)break;}snaps.push(beam[0].w);
}
let s=beam[0],used=s.w.filter(w=>w.a>=0).length,summary={...cfg,used,anchors:ev.length,assigned:ev.length-s.skips,skips:s.skips,ccs:s.ccs,reverse:s.rev,cost:s.cost,score};
if(!keep)return summary;
let paths=Array.from({length:count},()=>[]),unassigned=[];for(let p=s;p&&p.action;p=p.prev){let {id,j,t}=p.action,b=ev[j];let e={anchor:j+1,rawIndices:groups[j],c:b.c,f:b.f,observedMs:b.t,modeledMs:t};if(id>=0)paths[id].push(e);else unassigned.push(e);}paths.forEach(p=>p.reverse());unassigned.reverse();return {summary,paths,unassigned};
}
const tests=[];for(let count=5;count<=14;count++)for(const lag of [0,1,4])for(const mode of ["forward","both"])tests.push(run({count,d:2,lag,mode,width:24}));
const eligible=tests.filter(t=>t.assigned>=ev.length*.995&&t.used===t.count);
const ranked=eligible.sort((a,b)=>b.score.val.hit-a.score.val.hit||b.score.val.top3-a.score.val.top3||a.ccs-b.ccs||a.count-b.count);
const winner=ranked[0], challenger=eligible.slice().sort((a,b)=>a.ccs-b.ccs||a.count-b.count)[0];
return {raw:records.length,anchors:ev.length,validStart,testStart,tests,winner:winner?run(winner,true):null,lowSwitch:challenger?run(challenger,true):null};
}

module.exports=analyze;
