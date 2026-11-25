/* Exact finite-slot renewal optimization. Monetary values are in any consistent unit. */
(function(root){
'use strict';
function validate(o){
 const n=Number(o.slots), b=Number(o.base), t=Number(o.target), salvage=Number(o.salvage||0);
 if(!Number.isInteger(n)||n<1||n>20||!Number.isFinite(b)||b<=0||!Number.isInteger(t)||t<1||t>400||!Number.isFinite(salvage)||salvage<0||salvage>=b)throw Error('Use 1–20 slots, a positive base price, a whole-number target (1–400), and discard recovery at least zero and below base price.');
 const a=o.scrolls.filter(s=>s.enabled!==false).map((s,i)=>({name:String(s.name||'Scroll '+(i+1)),c:Number(s.cost),p:Number(s.success)/100,d:Number(s.destroy||0)/100,g:Number(s.gain)}));
 if(!a.length||a.length>12||a.some(s=>!Number.isFinite(s.c)||s.c<0||!Number.isFinite(s.p)||!Number.isFinite(s.d)||s.p<0||s.d<0||s.p+s.d>1+1e-10||!Number.isInteger(s.g)||s.g<1||s.g>20))throw Error('Enable 1–12 scrolls; prices must be nonnegative, gains whole numbers 1–20, and success + destruction must not exceed 100%.');
 return {n,b,t,salvage,a,full:!!o.full,mode:o.mode==='point'?'point':'item'};
}
function solve(o){
 const v=validate(o), {n,b,t,salvage,a,full,mode}=v, maxG=Math.max(...a.filter(s=>s.p>0).map(s=>s.g),0);
 if(t>n*maxG)return null;
 // One fresh-base attempt is a renewal cycle. Optimize E[cost]-lambda*E[reward].
 const reward=(g)=>mode==='point'?g:1;
 function run(lambda){
  const mem=new Map();
  function dp(r,g){
   const key=r+','+g;if(mem.has(key))return mem.get(key);
   let best={z:-salvage,c:-salvage,p:0,h:0,act:'discard'};
   function consider(x){if(x.z<best.z-1e-10*Math.max(1,Math.abs(x.z),Math.abs(best.z))||(Math.abs(x.z-best.z)<=1e-10*Math.max(1,Math.abs(x.z),Math.abs(best.z))&&x.p>best.p))best=x;}
   if(g>=t&&(!full||r===0))consider({z:-lambda*reward(g),c:0,p:1,h:g,act:'keep'});
   if(r>0&&(g+r*maxG>=t))for(let j=0;j<a.length;j++){
    const s=a[j],f=Math.max(0,1-s.p-s.d),w=s.p?dp(r-1,g+s.g):null,l=f?dp(r-1,g):null;
    const c=s.c+(w?s.p*w.c:0)+(l?f*l.c:0),p=(w?s.p*w.p:0)+(l?f*l.p:0),h=(w?s.p*w.h:0)+(l?f*l.h:0);
    consider({z:c-lambda*(mode==='point'?h:p),c,p,h,act:j});
   }
   mem.set(key,best);return best;
  }
  return {root:dp(n,0),mem,dp};
 }
 let lo=0,hi=Math.max(1,b),test=run(hi);let step=0;
 while(b+test.root.z>0&&step++<100){hi*=2;test=run(hi);}
 if(b+test.root.z>1e-7||!Number.isFinite(hi))return null;
 for(let k=0;k<66;k++){const m=(lo+hi)/2;if(b+run(m).root.z>0)lo=m;else hi=m;}
 const policy=run(hi+Math.max(1e-8,hi*1e-8));
 if(!policy.root.p)return null;
 const evaluated=evaluate(v,(r,g)=>policy.dp(r,g).act);
 return {...evaluated,states:policy.mem,action:(r,g)=>policy.dp(r,g).act,config:v,objective:mode==='point'?evaluated.perPoint:evaluated.perItem};
}
function evaluate(v,choose){
 const {n,b,t,salvage,a,full}=v;let cost=b,accepted=0,points=0,discarded=0,destroyed=0;const dist={}, reached={},usage=a.map(()=>0);
 let layer=new Map([[0,1]]);
 for(let r=n;r>=0;r--){const next=new Map();for(const [g,mass] of layer){if(mass<=0)continue;let j=choose(r,g);reached[r+','+g]={r,g,mass,action:j};
  if(j==='keep'&&g>=t&&(!full||r===0)){accepted+=mass;points+=mass*g;dist[g]=(dist[g]||0)+mass;continue;}
  if(j==='discard'||r===0||!a[j]){discarded+=mass;cost-=mass*salvage;continue;}
  const s=a[j];cost+=mass*s.c;usage[j]+=mass;destroyed+=mass*s.d;
  const put=(k,p)=>{if(p>0)next.set(k,(next.get(k)||0)+p);};put(g+s.g,mass*s.p);put(g,mass*Math.max(0,1-s.p-s.d));
 }layer=next;}
 return {cost,accepted,points,discarded,destroyed,dist,reached,usage,perItem:accepted?cost/accepted:Infinity,perPoint:points?cost/points:Infinity,mean:accepted?points/accepted:0,bases:accepted?1/accepted:Infinity};
}
// Fixed full-length schedules; discard failed final pieces, no early reset.
function fixed(v,seq){return evaluate(v,(r,g)=>r?seq[v.n-r]:g>=v.t?'keep':'discard');}
// Reset on any failure of first scroll; retry opener on same base until first success.
function opener(v,head,tail,retry){
 return evaluate(v,(r,g)=>{if(r===0)return g>=v.t?'keep':'discard';if(g===0){if(r===v.n||retry)return head;return 'discard';}return tail;});
}
function compare(o){const v=validate(o), rows=[], key=v.mode==='point'?'perPoint':'perItem';
 const add=(name,x)=>rows.push({name,...x});const opt=solve(o);if(opt)add('Optimal adaptive (all methods)',opt);
 v.a.forEach((s,i)=>add('All '+s.name,fixed(v,Array(v.n).fill(i))));
 v.a.forEach((s,i)=>v.a.forEach((q,j)=>{add('Reset '+s.name+' opener → '+q.name,opener(v,i,j,false));add('Retry '+s.name+' on same base → '+q.name,opener(v,i,j,true));}));
 // Enumerate all nonadaptive full schedules when tractable, including permutations.
 const total=v.a.length**v.n;let best=null,bestSeq=null;
 if(total<=100000){const rec=(seq)=>{if(seq.length===v.n){const x=fixed(v,seq);if(!best||x[key]<best[key]){best=x;bestSeq=seq.slice();}return;}for(let j=0;j<v.a.length;j++)rec([...seq,j]);};rec([]);if(best&&Number.isFinite(best[key]))add('Best fixed: '+bestSeq.map(i=>v.a[i].name).join(' → '),best);}
 rows.sort((x,y)=>x[key]-y[key]);return {rows,enumerated:total<=100000?total:0};}
const api={validate,solve,evaluate,fixed,opener,compare};if(typeof module!=='undefined')module.exports=api;else root.ScrollEV=api;
})(typeof globalThis!=='undefined'?globalThis:this);
