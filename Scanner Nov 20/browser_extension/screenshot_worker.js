/* FM Rush screenshot archiver (MV3 service worker helper).
 * Only receives positions and labels of deal cards visible in the HeneFM DOM.
 * CDP captures one actual PNG per unique rendered listing without scrolling,
 * changing filters, refreshing the page or delaying the deal bridge.
 */
const FM_CAPTURE_SEEN_KEY = 'fmRushScreenshotSeenByIGNV2';
const FM_CAPTURE_ENABLED_KEY = 'fmRushScreenshotEnabled';
const FM_CAPTURE_FOLDER = 'FM_Rush_Item_Screenshots';
const FM_CAPTURE_RETENTION_MS = 48 * 60 * 60 * 1000;
const FM_CAPTURE_QUEUE_LIMIT = 800;
const FM_CAPTURE_RETRY_MS = 20000;
const fmCaptureQueue = [];
const fmClickedQueue = [];
const fmCapturePending = new Set();
const fmCaptureFailures = new Map();
const fmCaptureSaved = new Map();
let fmCaptureReady = null;
let fmCaptureRunning = false;
let fmCaptureEnabled = false;
let fmCaptureSavedInSession = 0;
let fmCaptureLastSavedAt = 0;
let fmCaptureLastError = '';
let fmCaptureFailedInSession = 0;

function fmCaptureSanitize(input, maxLength=52) {
  return String(input ?? '').normalize('NFKC')
    .replace(/[\\/:*?"<>|\x00-\x1F]/g, '_')
    .replace(/\s+/g, ' ').trim().replace(/[. ]+$/g, '').slice(0,maxLength) || 'unknown';
}
function fmCaptureTimestamp(now) {
  const pad=(n,width=2)=>String(n).padStart(width,'0');
  return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}-${pad(now.getMilliseconds(),3)}`;
}
function fmCaptureFileName(card) {
  const now=new Date();
  const date=fmCaptureTimestamp(now);
  const day=date.slice(0,10);
  const location=`CH${String(card.cc??'--').padStart(2,'0')}-FM${String(card.fm??'--').padStart(2,'0')}`;
  const price=Number.isSafeInteger(card.buy_mesos)?`${card.buy_mesos}mesos`:'price_unknown';
  const sold=card.sold?'_SOLD':'';
  return `${FM_CAPTURE_FOLDER}/IGN_${fmCaptureSanitize(card.ign,24)}/${day}/${date}_${location}_${fmCaptureSanitize(card.item)}_${fmCaptureSanitize(card.ign,24)}_${price}${sold}_${card.id}.png`;
}
function fmCaptureValidCard(card) {
  const r=card?.rect;
  return /^[a-f0-9]{8,24}$/.test(String(card?.id||'')) &&
    typeof card.item==='string' && card.item.length>0 && card.item.length<=150 &&
    typeof card.ign==='string' && card.ign.length<=40 &&
    (card.cc==null || (Number.isInteger(card.cc) && card.cc>=1 && card.cc<=40)) &&
    (card.fm==null || (Number.isInteger(card.fm) && card.fm>=1 && card.fm<=20)) &&
    r && ['x','y','width','height'].every(k=>Number.isFinite(r[k])) &&
    r.x>=0 && r.y>=0 && r.x<300000 && r.y<1000000 &&
    r.width>=12 && r.width<=3000 && r.height>=24 && r.height<=3000;
}
async function fmCaptureInit() {
  if (fmCaptureReady) return fmCaptureReady;
  fmCaptureReady = (async()=>{
    const state=await chrome.storage.local.get([FM_CAPTURE_SEEN_KEY, FM_CAPTURE_ENABLED_KEY]);
    fmCaptureEnabled=state[FM_CAPTURE_ENABLED_KEY] === true;
    const previous=state[FM_CAPTURE_SEEN_KEY] || {};
    const cutoff=Date.now()-FM_CAPTURE_RETENTION_MS;
    for(const [key,when] of Object.entries(previous)){
      if(/^[a-f0-9]{8,24}$/.test(key) && Number.isFinite(when) && when>cutoff){
        fmCaptureSaved.set(key,when);
      }
    }
  })().catch(err=>{fmCaptureReady=null;throw err;});
  return fmCaptureReady;
}
function fmCaptureStatus() {
  return {enabled:fmCaptureEnabled,queued:fmCaptureQueue.length,running:fmCaptureRunning,
    savedThisSession:fmCaptureSavedInSession,remembered:fmCaptureSaved.size,
    failedThisSession:fmCaptureFailedInSession,lastSavedAt:fmCaptureLastSavedAt,
    lastError:fmCaptureLastError,folder:FM_CAPTURE_FOLDER};
}
async function fmCapturePersist() {
  const cutoff=Date.now()-FM_CAPTURE_RETENTION_MS;
  for (const [id,at] of fmCaptureSaved){if(at<cutoff)fmCaptureSaved.delete(id);}
  // Bound local storage and preserve most recent items only.
  const tail=[...fmCaptureSaved.entries()].slice(-6000);
  await chrome.storage.local.set({[FM_CAPTURE_SEEN_KEY]:Object.fromEntries(tail)});
}
async function fmCaptureEnqueue(cards, sender) {
  await fmCaptureInit();
  if (!fmCaptureEnabled) return fmCaptureStatus();
  const tabId=sender?.tab?.id;
  if (!Number.isInteger(tabId) || sender.frameId !== 0 ||
      !/^https:\/\/(?:www\.)?henefm\.com\/flips\/deals(?:[/?#]|$)/.test(sender.url||'')) {
    return {ok:false,error:'Invalid sender for screenshot capture'};
  }
  const now=Date.now();
  for(const card of Array.isArray(cards)?cards.slice(0,1000):[]){
    if (!fmCaptureValidCard(card) || fmCaptureSaved.has(card.id) || fmCapturePending.has(card.id))continue;
    if(now-(fmCaptureFailures.get(card.id)||0)<FM_CAPTURE_RETRY_MS)continue;
    if(fmCaptureQueue.length>=FM_CAPTURE_QUEUE_LIMIT)break;
    fmCaptureQueue.push({tabId,card});
    fmCapturePending.add(card.id);
  }
  if(!fmCaptureRunning) void fmCaptureDrain();
  return {ok:true,...fmCaptureStatus()};
}
async function fmCaptureClicked(card, deal, sender) {
  const tabId=sender?.tab?.id;
  if (!Number.isInteger(tabId) || sender.frameId !== 0 ||
      !/^https:\/\/(?:www\.)?henefm\.com\/flips\/deals(?:[/?#]|$)/.test(sender.url||'') ||
      !fmCaptureValidCard(card) || deal?.listing_id!==card.id) {
    return {ok:false,error:'Invalid clicked listing'};
  }
  if(fmClickedQueue.length>=24)return {ok:false,error:'Screenshot queue busy'};
  return new Promise(resolve=>{
    fmClickedQueue.push({tabId,card,deal,resolve,clicked:true});
    if(!fmCaptureRunning)void fmCaptureDrain();
  });
}
async function fmCaptureSaveClicked(card,deal,png) {
  const response=await fetch('http://127.0.0.1:18773/listing-screenshot',{
    method:'POST',headers:{'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view'},
    body:JSON.stringify({deal,png}),signal:AbortSignal.timeout(8000)
  });
  const result=await response.json();
  if(!response.ok || !result.ok)throw Error(result.error||'Screenshot save failed');
  return result;
}
async function fmCaptureDrain() {
  if(fmCaptureRunning)return;
  fmCaptureRunning=true;
  let attachedTabId=null;
  try {
    while(fmClickedQueue.length || (fmCaptureQueue.length && fmCaptureEnabled)){
      const task=fmClickedQueue.length?fmClickedQueue.shift():fmCaptureQueue.shift();
      let {tabId,card}=task;
      try {
        const tab=await chrome.tabs.get(tabId);
        if(!/^https:\/\/(?:www\.)?henefm\.com\/flips\/deals(?:[/?#]|$)/.test(tab.url||'')) {
          throw Error('HeneFM Deals tab navigated away');
        }
        if(attachedTabId!==tabId){
          if(attachedTabId!==null){await chrome.debugger.detach({tabId:attachedTabId});attachedTabId=null;}
          await chrome.debugger.attach({tabId},'1.3');
          attachedTabId=tabId;
        }
        const current=await chrome.tabs.sendMessage(tabId,{kind:'fm-rush-locate-capture',id:card.id});
        if(!current?.ok || !fmCaptureValidCard(current.card) || current.card.id!==card.id) {
          throw Error('Listing no longer rendered; skipped stale screenshot');
        }
        card=current.card;
        const result=await chrome.debugger.sendCommand({tabId},'Page.captureScreenshot',{
          format:'png', fromSurface:true, captureBeyondViewport:true, optimizeForSpeed:true,
          clip:{x:card.rect.x,y:card.rect.y,width:card.rect.width,
            height:card.rect.height,scale:1}
        });
        if(!result?.data || result.data.length<100)throw Error('Empty screenshot from browser');
        if(task.clicked){
          // Do not label a neighboring card as the clicked one after a refresh.
          const after=await chrome.tabs.sendMessage(tabId,{kind:'fm-rush-locate-capture',id:card.id});
          if(!after?.ok || !fmCaptureValidCard(after.card) ||
              after.card.id!==card.id || ['x','y','width','height'].some(k=>Math.abs(after.card.rect[k]-card.rect[k])>2))
            throw Error('Listing moved during capture; click again');
          const saved=await fmCaptureSaveClicked(card,task.deal,result.data);
          task.resolve(saved);
          continue;
        }
        const downloadId=await chrome.downloads.download({
          url:`data:image/png;base64,${result.data}`,
          filename:fmCaptureFileName(card),
          conflictAction:'uniquify', saveAs:false
        });
        if(!Number.isInteger(downloadId))throw Error('Browser refused screenshot download');
        fmCaptureSaved.set(card.id,Date.now());
        fmCaptureSavedInSession++;
        fmCaptureLastSavedAt=Date.now();
        fmCaptureLastError='';
        // Persist once per file so a reload will not duplicate saved screenshots.
        await fmCapturePersist();
      } catch (err) {
        if(task.clicked)task.resolve({ok:false,error:String(err?.message||err)});
        fmCaptureFailedInSession++;
        fmCaptureLastError=String(err?.message||err);
        fmCaptureFailures.set(card.id,Date.now());
        if(fmCaptureFailedInSession<=3 || fmCaptureFailedInSession%20===0) {
          console.warn('[FM Rush] Could not save listing screenshot:',fmCaptureLastError);
        }
        // CDP can be stolen by an opened DevTools window; retry after backoff.
        if(attachedTabId===tabId && /debugger|attached|detached|target closed|DevTools/i.test(fmCaptureLastError)){
          attachedTabId=null;
        }
      } finally {if(!task.clicked)fmCapturePending.delete(card.id);}
    }
  } finally {
    if(attachedTabId!==null){try{await chrome.debugger.detach({tabId:attachedTabId});}catch(_){}}
    fmCaptureRunning=false;
    if(fmClickedQueue.length || (fmCaptureEnabled && fmCaptureQueue.length))void fmCaptureDrain();
  }
}
async function fmCaptureSetEnabled(enabled){
  await fmCaptureInit();
  fmCaptureEnabled=enabled;
  await chrome.storage.local.set({[FM_CAPTURE_ENABLED_KEY]:enabled});
  if(!enabled){
    for(const task of fmCaptureQueue)fmCapturePending.delete(task.card.id);
    fmCaptureQueue.length=0;
  }
  return fmCaptureStatus();
}
