/* FM Rush v24.3 — page-preserving refresh, real request telemetry and recovery.
 * This sends the same soft-refresh signal as before. It does NOT call any
 * private HeneFM API. The optional backup reload uses the CURRENT page URL
 * and is rate-limited to once per 45 seconds, only when no data request is
 * seen; it does not change the filters or sold status.
 */
(() => {
  'use strict';
  const VERSION='24.3.4';
  const KEY='__fmRushSoftRefreshV243';
  const KIND='FM_RUSH_REFRESH_V243';
  const DEFAULT_INTERVAL=1200, MIN_INTERVAL=800, MAX_INTERVAL=5000;
  const REQUEST_LEASE_MS=4500, BACKUP_IDLE_MS=45000;
  const BACKUP_KEY='fmRushV243LastBackupReload';
  const onDeals=()=>/^\/flips\/deals\/?$/.test(location.pathname);
  const time=()=>performance.now();
  const wall=()=>Date.now();
  const previous=window[KEY];
  try { previous?.stop?.(); } catch (_) {}
  try { window.__fmRushSoftRefreshV242?.stop?.(); } catch (_) {}
  if (window.heneFastRefresh!=null) {
    try {clearInterval(window.heneFastRefresh);} catch(_){}
    window.heneFastRefresh=null;
  }

  let intervalMs=DEFAULT_INTERVAL, fallbackEnabled=false, timer=null, stopped=false;
  let lastPulse=-Infinity, lastTick=time(), lastResourceAt=null, lastSiteAttemptAt=null;
  let lastDataChangeAt=null, lastBackupAt=null, lastResponseAt=null;
  let lastFocusEventAt=-Infinity, lastDomFingerprint=null, dealsOnPage=null;
  let resourceCompletions=0, fetchRequests=0, trackedCompleted=0, trackedFailed=0;
  let lastNetworkStarted=null, lastHttpErrorAt=null, requestId=0;
  const pending=new Map(), latencies=[];
  const metrics={pulses:0,busySkips:0,stalled:0,lateTicks:0,hiddenPulses:0,
    wakeups:0,focusSignals:0,backupReloads:0,dataChanges:0};
  try {lastBackupAt=Number(sessionStorage.getItem(BACKUP_KEY))||null;}catch(_){}

  const nativeFetch=window.fetch;
  function sameOriginURL(input){
    try {
      const raw=(typeof input==='string'||input instanceof URL)?input:input?.url;
      if(!raw)return false;
      return new URL(raw,location.href).origin===location.origin;
    }catch(_){return false;}
  }
  // Observe fetch start and completion without changing the response or body.
  const wrappedFetch=function(input,...args){
    const track=onDeals()&&sameOriginURL(input), id=track?++requestId:0;
    const started=time();
    if(track){
      fetchRequests++;lastSiteAttemptAt=wall();lastNetworkStarted=wall();
      pending.set(id,started);
    }
    let result;
    try{result=nativeFetch.apply(this,[input,...args]);}
    catch(err){if(track){pending.delete(id);trackedFailed++;}throw err;}
    if(!track)return result;
    return Promise.resolve(result).then(response=>{
      pending.delete(id);trackedCompleted++;lastResponseAt=wall();
      if(response?.status===429||response?.status>=500)lastHttpErrorAt=wall();
      latencies.push(time()-started);if(latencies.length>80)latencies.shift();
      return response;
    },err=>{pending.delete(id);trackedFailed++;throw err;});
  };
  window.fetch=wrappedFetch;

  // Observe *actual* browser ResourceTiming entries for page fetch and XHR.
  // These catch requests to /api, RSC, or other endpoints the older v24.2
  // /flips-only wrapper missed. They are not proof the deal list changed.
  let observer=null;
  const onResources=list=>{
    for(const e of list.getEntries()){
      if(!['fetch','xmlhttprequest'].includes(e.initiatorType))continue;
      if(!sameOriginURL(e.name))continue;
      resourceCompletions++;
      lastResourceAt=wall();
    }
  };
  try{
    performance.setResourceTimingBufferSize?.(1500);
    if(typeof PerformanceObserver==='function'){
      observer=new PerformanceObserver(onResources);
      observer.observe({type:'resource',buffered:false});
    }
  }catch(_){observer=null;}

  function expirePending(){
    for(const [id,start] of pending){
      if(time()-start>REQUEST_LEASE_MS){pending.delete(id);metrics.stalled++;}
    }
  }
  function plan(ms){
    if(timer!==null)clearTimeout(timer);
    if(!stopped)timer=setTimeout(()=>pulse('timer'),Math.max(40,Math.round(ms)));
  }
  function sendFocusFallback(){
    if(time()-lastFocusEventAt<10000)return;
    lastFocusEventAt=time();metrics.focusSignals++;
    try{window.dispatchEvent(new Event('focus'));}catch(_){}
  }
  function safeToReload(){
    if(!fallbackEnabled||!onDeals())return false;
    // Never lose in-progress filter edits or clicks on controls.
    const el=document.activeElement;
    if(document.hasFocus?.()&&el&&(
       /^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName)||el.isContentEditable))return false;
    if(lastHttpErrorAt&&wall()-lastHttpErrorAt<180000)return false;
    const activity=Math.max(lastSiteAttemptAt||0,lastResourceAt||0,lastDataChangeAt||0);
    if(activity&&wall()-activity<BACKUP_IDLE_MS)return false;
    if(wall()-startedAt<BACKUP_IDLE_MS)return false;
    if(lastBackupAt&&wall()-lastBackupAt<BACKUP_IDLE_MS)return false;
    return true;
  }
  const startedAt=wall();
  function pulse(reason){
    if(stopped)return;
    const t=time();
    if(reason==='timer'&&t-lastTick>intervalMs*1.8)metrics.lateTicks++;
    lastTick=t;
    if(!onDeals()){plan(intervalMs);return;}
    expirePending();
    if(safeToReload()){
      // One normal navigation reload, not a bulk scrape and not 1.2s reloads.
      lastBackupAt=wall();metrics.backupReloads++;
      try{sessionStorage.setItem(BACKUP_KEY,String(lastBackupAt));}catch(_){}
      location.reload();
      return;
    }
    if(pending.size){metrics.busySkips++;plan(Math.min(250,intervalMs/3));return;}
    const elapsed=t-lastPulse;
    if(reason!=='resume'&&elapsed<intervalMs-80){plan(Math.max(40,intervalMs-elapsed));return;}
    lastPulse=t;metrics.pulses++;
    if(document.visibilityState!=='visible')metrics.hiddenPulses++;
    try{document.dispatchEvent(new Event('visibilitychange'));}
    catch(err){console.warn('[FM Rush] Soft refresh event error',err);}
    // Some libraries listen to window focus rather than visibilitychange.
    // Try it sparingly (at most every 10 seconds), not on every 1.2s tick.
    if(time()-lastFocusEventAt>10000&&
       wall()-Math.max(lastResourceAt||0,lastSiteAttemptAt||0)>8000){
      sendFocusFallback();
    }
    plan(intervalMs);
  }
  function handleVisibility(e){if(e&&!e.isTrusted)return;if(document.visibilityState==='visible')pulse('resume');}
  function onPageShow(){pulse('resume');}
  function percentile(p){
    if(!latencies.length)return null;
    const sorted=[...latencies].sort((a,b)=>a-b);
    return Math.round(sorted[Math.ceil(p*sorted.length)-1]);
  }
  function status(){
    expirePending();
    return {version:VERSION,running:!stopped&&onDeals(),intervalMs,
      fallbackEnabled,tabVisible:document.visibilityState==='visible',
      // Legacy aliases are retained, but 'completed' means fetch calls
      // observed by this wrapper, NOT proven deal-list refreshes.
      attempts:metrics.pulses,completed:trackedCompleted,failed:trackedFailed,
      pending:pending.size,stalled:metrics.stalled,busySkips:metrics.busySkips,
      lateTicks:metrics.lateTicks,hiddenAttempts:metrics.hiddenPulses,
      wakeups:metrics.wakeups,focusSignals:metrics.focusSignals,
      requestsStarted:fetchRequests,resourceRequests:resourceCompletions,
      dataChanges:metrics.dataChanges,dealsOnPage,
      lastDataChangeAt,lastNetworkAt:lastResourceAt,lastSiteAttemptAt,
      lastResponseAt,lastBackupAt,backupReloads:metrics.backupReloads,
      p50Ms:percentile(.5),p95Ms:percentile(.95),
      lastAttemptAt:Number.isFinite(lastPulse)?wall()-Math.max(0,time()-lastPulse):null};
  }
  function onMessage(event){
    if(event.source!==window||event.origin!==location.origin||event.data?.kind!==KIND)return;
    const msg=event.data;
    if(msg.type==='set-settings'){
      const n=Number(msg.intervalMs);
      if(Number.isFinite(n))intervalMs=Math.max(MIN_INTERVAL,Math.min(MAX_INTERVAL,Math.round(n)));
      if(typeof msg.fallbackEnabled==='boolean')fallbackEnabled=msg.fallbackEnabled;
      plan(intervalMs);
    }else if(msg.type==='wake'){
      metrics.wakeups++;
      if(time()-lastPulse>intervalMs*1.5)pulse('wake');
    }else if(msg.type==='deal-snapshot'){
      dealsOnPage=Number(msg.count)||0;
      if(lastDomFingerprint!==null&&msg.fingerprint!==lastDomFingerprint){
        metrics.dataChanges++;lastDataChangeAt=wall();
      }
      lastDomFingerprint=msg.fingerprint;
    }else if(msg.type==='status'){
      window.postMessage({kind:KIND,type:'status-reply',requestId:msg.requestId,value:status()},location.origin);
    }
  }
  function stop(){
    stopped=true;
    if(timer!==null)clearTimeout(timer);
    document.removeEventListener('visibilitychange',handleVisibility);
    window.removeEventListener('pageshow',onPageShow);
    window.removeEventListener('message',onMessage);
    try{observer?.disconnect();}catch(_){}
    if(window.fetch===wrappedFetch)window.fetch=nativeFetch;
  }
  window[KEY]={stop,status};
  window.addEventListener('message',onMessage);
  document.addEventListener('visibilitychange',handleVisibility);
  window.addEventListener('pageshow',onPageShow);
  plan(intervalMs);
  console.info('[FM Rush v24.3.4] Default soft refresh 1200ms; backup reload OFF by default.');
})();
