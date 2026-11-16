'use strict';
const $=id=>document.getElementById(id);
const intervals=new Set([800,1000,1200,1500,2000,3000]);
function ago(t){if(!t)return 'Not observed';const age=Math.max(0,Math.round((Date.now()-t)/1000));return age<2?'just now':age+'s ago';}
function statusText(message,warn){$('status').textContent=message;$('status').className='status'+(warn?' warn':'');}
async function readStatus(){
  try{
    const tabs=await chrome.tabs.query({url:['https://henefm.com/flips/deals*','https://www.henefm.com/flips/deals*']});
    const tab=tabs.find(t=>t.active)||tabs[0];
    if(!tab?.id){statusText('Open an HeneFM Deals tab',true);return;}
    const info=await chrome.tabs.sendMessage(tab.id,{kind:'fm-rush-get-status'});
    const scannerActive=Number(info?.scanner?.lastScanAt)>0;
    if(!info?.running && !scannerActive){statusText('Reload HeneFM after installing',true);return;}
    if(!info?.running){statusText('Scanner active · soft refresh not detected',true);}
    else statusText(info.tabVisible?'Monitoring · tab visible':'Monitoring · tab backgrounded',!info.tabVisible);
    $('attempts').textContent=info.attempts??'—';
    $('started').textContent=info.requestsStarted??'—';
    $('resources').textContent=info.resourceRequests??'—';
    $('changes').textContent=info.dataChanges??'—';
    $('deals').textContent=info.dealsOnPage??'—';
    $('last').textContent=ago(Math.max(info.lastNetworkAt||0,info.lastSiteAttemptAt||0));
    $('reloaded').textContent=info.backupReloads??'—';
    $('busy').textContent=(info.busySkips??0)+' / '+(info.stalled??0);
    const sc=info.scanner||{};
    $('links').textContent=sc.sellerLinks??'—';
    $('cards').textContent=sc.cardsFound??'—';
    $('sold').textContent=sc.soldCards??'—';
    $('parsed').textContent=sc.parsedCards??'—';
    $('qualified').textContent=sc.qualifyingDeals??'—';
    $('sent').textContent=sc.sent??'—';
    $('queued').textContent=sc.queued??'—';
    $('scanner-time').textContent=ago(sc.lastScanAt);
    $('scanner-error').textContent=sc.lastError||'None';
    const captureStatus=await chrome.runtime.sendMessage({kind:'fm-rush-capture-status'});
    if (captureStatus?.ok) {
      $('capture').checked=captureStatus.enabled;
      $('shots').textContent=captureStatus.savedThisSession??'—';
      $('shots-queued').textContent=captureStatus.queued??'—';
      $('shots-failed').textContent=captureStatus.failedThisSession??'—';
      $('capture-error').textContent=captureStatus.lastError||'None';
    } else $('capture-error').textContent=captureStatus?.error||'Status unavailable';
    const health=await chrome.runtime.sendMessage({kind:'fm-rush-local-health'});
    $('local').textContent=health?.ok?'Connected':'Not connected (start FM Rush app)';
    $('local').style.color=health?.ok?'#a5e3b8':'#f3cb80';
  }catch(_){statusText('Reload HeneFM once',true);}
}
async function init(){
  const saved=await chrome.storage.local.get({fmRushIntervalMs:1200,fmRushBackupReload:false});
  $('speed').value=String(intervals.has(saved.fmRushIntervalMs)?saved.fmRushIntervalMs:1200);
  $('backup').checked=saved.fmRushBackupReload===true;
  const captureSettings=await chrome.storage.local.get({fmRushScreenshotEnabled:true});
  $('capture').checked=captureSettings.fmRushScreenshotEnabled!==false;
  $('capture').addEventListener('change',async()=>{
    await chrome.runtime.sendMessage({kind:'fm-rush-capture-toggle',enabled:$('capture').checked});
    readStatus();
  });
  $('speed').addEventListener('change',async()=>{
    const ms=Number($('speed').value);
    if(intervals.has(ms))await chrome.storage.local.set({fmRushIntervalMs:ms});
    readStatus();
  });
  $('backup').addEventListener('change',async()=>{
    await chrome.storage.local.set({fmRushBackupReload:$('backup').checked});
    readStatus();
  });
  $('open-deals').addEventListener('click',()=>chrome.tabs.create({url:'https://henefm.com/flips/deals'}));
  $('recheck').addEventListener('click',readStatus);
  $('resend').addEventListener('click',async()=>{
    const tabs=await chrome.tabs.query({url:['https://henefm.com/flips/deals*','https://www.henefm.com/flips/deals*']});
    const tab=tabs.find(t=>t.active)||tabs[0];
    if(tab?.id) await chrome.tabs.sendMessage(tab.id,{kind:'fm-rush-resend-current'});
    setTimeout(readStatus,300);
  });
  await readStatus();
}
init();
