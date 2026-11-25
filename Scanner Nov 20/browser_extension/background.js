importScripts('screenshot_worker.js');
/* FM Rush v24.17: local deal bridge + Chrome alarm liveness check.
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
  // Trading records replace screenshot spam. Reset once on this workflow upgrade;
  // a later explicit opt-in is preserved across subsequent extension reloads.
  const saved=await chrome.storage.local.get('fmRushTextWorkflowV2417');
  if(!saved.fmRushTextWorkflowV2417){
    await chrome.storage.local.set({fmRushTextWorkflowV2417:true,fmRushScreenshotEnabled:false});
    await fmCaptureSetEnabled(false);
  }
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
  if (msg?.kind === 'fm-rush-capture-clicked') {
    fmCaptureClicked(msg.card,msg.deal,sender).then(respond).catch(err=>respond({ok:false,error:String(err)}));
    return true;
  }
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
  if (!msg || !['fm-rush-route-deal','fm-rush-visible-deals','fm-rush-select-deal','fm-rush-skip-deal','fm-rush-unlock-deal'].includes(msg.kind)) return false;
  const source = sender?.url || '';
  if (!/^https:\/\/(?:www\.)?henefm\.com\/flips\/deals(?:[/?#]|$)/.test(source)) {
    respond({ok:false,error:'Not an HeneFM Flips page',retryable:false});
    return false;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(),3500);
  const live=msg.kind==='fm-rush-visible-deals';
  fetch('http://127.0.0.1:18773/'+(live?'visible':msg.kind==='fm-rush-unlock-deal'?'unlock':msg.kind==='fm-rush-select-deal'?'select':msg.kind==='fm-rush-skip-deal'?'skip':'deal'), {
    method:'POST',
    headers:{'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view'},
    body:JSON.stringify(live?msg.snapshot:msg.deal),
    signal:controller.signal
  }).then(async response => {
    let body={};
    try {body=await response.json();}catch(_){}
    respond({ok:response.ok && body.ok,
      error:body.error||(!response.ok?'HTTP '+response.status:''),
      retryable:response.status>=500,
      focused_listing_id:body.focused_listing_id??null,
      chase_locked:body.chase_locked===true});
  }).catch(() => respond({ok:false,error:'FM Rush not connected. Start the FM Rush Windows app.',retryable:true}))
    .finally(() => clearTimeout(timeout));
  return true;
});

