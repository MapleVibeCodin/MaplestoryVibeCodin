const vm=require('node:vm'), fs=require('node:fs'), assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/refresh_2s.js','utf8');
function setup(){
  let ms=0, nextId=0, reloaded=0;
  const tasks=new Map(), listeners=new Map(), documentListeners=new Map(), store=new Map();
  let resourceHandler=null;
  const add=(where,type,fn)=>{if(!where.has(type))where.set(type,new Set());where.get(type).add(fn)};
  const del=(where,type,fn)=>where.get(type)?.delete(fn);
  const call=(where,type,e={})=>{for(const fn of where.get(type)||[])fn(e);};
  const window={fetch:()=>Promise.resolve({status:200}),addEventListener:(t,f)=>add(listeners,t,f),
   removeEventListener:(t,f)=>del(listeners,t,f), dispatchEvent:e=>call(listeners,e.type,e),
   postMessage:data=>call(listeners,'message',{source:window,origin:'https://henefm.com',data})};
  const document={visibilityState:'visible',activeElement:null,hasFocus:()=>false,
    addEventListener:(t,f)=>add(documentListeners,t,f),removeEventListener:(t,f)=>del(documentListeners,t,f),
    dispatchEvent:e=>call(documentListeners,e.type,e)};
  const location={pathname:'/flips/deals',origin:'https://henefm.com',href:'https://henefm.com/flips/deals?min_pct=15',reload:()=>{reloaded++}};
  class PerformanceObserver{constructor(cb){resourceHandler=cb}observe(){}disconnect(){}}
  const context={window,document,location,URL,Promise,console:{info(){},warn(){}},
    Date:{now:()=>1790000000000+ms},performance:{now:()=>ms,setResourceTimingBufferSize(){}},PerformanceObserver,
    Event:class{constructor(type){this.type=type;this.isTrusted=false}},
    sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)},
    setTimeout(fn,delay){const id=++nextId;tasks.set(id,{at:ms+delay,fn});return id},
    clearTimeout(id){tasks.delete(id)},clearInterval(id){tasks.delete(id)} };
  function advance(delta){const end=ms+delta;for(let n=0;n<1000;n++){
    const candidates=[...tasks.entries()].filter(x=>x[1].at<=end).sort((a,b)=>a[1].at-b[1].at);
    if(!candidates.length)break;const [id,task]=candidates[0];tasks.delete(id);ms=task.at;task.fn();
  }ms=end;}
  function status(){return window.__fmRushSoftRefreshV243.status()}
  function message(type,extra={}){window.postMessage({kind:'FM_RUSH_REFRESH_V243',type,...extra})}
  function resource(url='https://henefm.com/api/flips/deals'){
    resourceHandler?.({getEntries:()=>[{name:url,initiatorType:'xmlhttprequest'}]})
  }
  vm.runInNewContext(src,context);
  return {window,document,location,context,advance,status,message,resource,get reloaded(){return reloaded},get tasks(){return tasks.size}};
}
(async()=>{
  const a=setup();
  assert.equal(a.status().intervalMs,1200);
  assert.equal(a.status().lastNetworkAt,null,'no bogus Unix-zero timestamp');
  a.advance(12000);
  assert.equal(a.status().attempts,10,'10 signals in 12 seconds');
  assert.equal(a.status().resourceRequests,0,'no fabricated fetches');
  assert.equal(a.status().focusSignals,2,'10-second sparse focus recovery');
  assert.equal(a.status().dataChanges,0);
  a.message('deal-snapshot',{fingerprint:'aa',count:6});
  a.message('deal-snapshot',{fingerprint:'ab',count:7});
  assert.equal(a.status().dataChanges,1);
  assert.equal(a.status().dealsOnPage,7);
  a.resource();
  assert.equal(a.status().resourceRequests,1,'real resource request detected');
  assert(a.status().lastNetworkAt>0,'proper timestamp');
  a.advance(32000);
  assert.equal(a.reloaded,0,'no reload during recently observed activity');
  a.advance(15000);
  assert.equal(a.reloaded,0,'backup reload off by default after idle');
  a.advance(60000);
  assert.equal(a.reloaded,0,'backup stays off after extended idle');
  const b=setup();
  b.message('set-settings',{intervalMs:1000,fallbackEnabled:false});
  b.advance(130000);
  assert.equal(b.reloaded,0,'fallback can be disabled');
  assert.equal(b.status().intervalMs,1000);
  // Fetch-based site requests count properly even outside /flips.
  const c=setup();
  const response=await c.window.fetch('/api/v2/deal-flips');
  assert.equal(response.status,200);
  assert.equal(c.status().requestsStarted,1);
  assert.equal(c.status().completed,1);
  // Re-installing the page script restores the original fetch without duplication.
  vm.runInNewContext(src,c.context);
  assert.equal(c.tasks,1,'one timer after reinjection');
  console.log('PASS v24.3.4: 1200ms cadence, backup disabled through extended idle, telemetry, settings and reinjection');
})().catch(e=>{console.error(e);process.exitCode=1});
