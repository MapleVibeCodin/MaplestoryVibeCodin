importScripts('screenshot_worker.js');
/* FM Rush v24.5: local deal bridge + Chrome alarm liveness check.
 * Does not fetch HeneFM URLs, use HeneFM APIs, or edit the website.
 */
const HEALTH_ALARM = 'fm-rush-health-v243';
async function ensureHealthAlarm() {
  try {
    const alarm = await chrome.alarms.get(HEALTH_ALARM);
    if (!alarm) await chrome.alarms.create(HEALTH_ALARM, {periodInMinutes:0.5});
  } catch (err) { console.warn('[FM Rush] Could not schedule health check',err); }
}
chrome.runtime.onInstalled.addListener(async () => {
  await chrome.storage.local.set({fmRushIntervalMs:1200,fmRushBackupReload:false});
  // Screenshot archiver defaults ON; a saved OFF preference is preserved.
  const saved = await chrome.storage.local.get('fmRushScreenshotEnabled');
  if(saved.fmRushScreenshotEnabled===undefined)await chrome.storage.local.set({fmRushScreenshotEnabled:true});
  await ensureHealthAlarm();
});
chrome.runtime.onStartup.addListener(ensureHealthAlarm);
chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name !== HEALTH_ALARM) return;
  try {
    const tabs = await chrome.tabs.query({url:[
      'https://henefm.com/flips/deals*',
      'https://www.henefm.com/flips/deals*'
    ]});
    for (const tab of tabs) {
      if (!tab.id) continue;
      chrome.tabs.sendMessage(tab.id, {kind:'fm-rush-health-wake'}).catch(()=>{});
    }
  } catch (_) { /* A tab might be closing, suspended or discarded. */ }
});
ensureHealthAlarm();

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (msg?.kind === 'fm-rush-capture-cards') {
    fmCaptureEnqueue(msg.cards, sender).then(respond).catch(err=>respond({ok:false,error:String(err)}));
    return true;
  }
  if (msg?.kind === 'fm-rush-capture-status') {
    fmCaptureInit().then(()=>respond({ok:true,...fmCaptureStatus()}))
      .catch(err=>respond({ok:false,error:String(err)}));
    return true;
  }
  if (msg?.kind === 'fm-rush-capture-toggle') {
    fmCaptureSetEnabled(msg.enabled===true).then(res=>respond({ok:true,...res}))
      .catch(err=>respond({ok:false,error:String(err)}));
    return true;
  }
  if (msg?.kind === 'fm-rush-local-health') {
    fetch('http://127.0.0.1:18773/health', {cache:'no-store', signal:AbortSignal.timeout(1250)})
      .then(async r=>{let body={};try{body=await r.json()}catch(_){}respond({ok:r.ok&&body.ok===true});})
      .catch(()=>respond({ok:false}));
    return true;
  }
  if (!msg || msg.kind !== 'fm-rush-route-deal') return false;
  const source = sender?.url || '';
  if (!/^https:\/\/(?:www\.)?henefm\.com\/flips\/deals(?:[/?#]|$)/.test(source)) {
    respond({ok:false,error:'Not an HeneFM Flips page',retryable:false});
    return false;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(),3500);
  fetch('http://127.0.0.1:18773/deal', {
    method:'POST',
    headers:{'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view'},
    body:JSON.stringify(msg.deal),
    signal:controller.signal
  }).then(async response => {
    let body={};
    try {body=await response.json();}catch(_){}
    respond({ok:response.ok && body.ok,
      error:body.error||(!response.ok?'HTTP '+response.status:''),
      retryable:response.status>=500});
  }).catch(() => respond({ok:false,error:'FM Rush not connected. Start the FM Rush Windows app.',retryable:true}))
    .finally(() => clearTimeout(timeout));
  return true;
});
