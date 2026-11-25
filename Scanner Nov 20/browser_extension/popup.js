'use strict';
const $=id=>document.getElementById(id);
function ago(t){if(!t)return 'Not observed';const age=Math.max(0,Math.round((Date.now()-t)/1000));return age<2?'just now':age+'s ago';}
function statusText(message,warn){$('status').textContent=message;$('status').className='status'+(warn?' warn':'');}
async function readStatus(){
  try{
    const tabs=await chrome.tabs.query({url:['https://henefm.com/flips/deals*','https://www.henefm.com/flips/deals*']});
    const tab=tabs.find(t=>t.active)||tabs[0];
    if(!tab?.id){statusText('Open an HeneFM Deals tab',true);return;}
    const info=await chrome.tabs.sendMessage(tab.id,{kind:'fm-rush-get-status'});
    const scannerActive=Number(info?.scanner?.lastScanAt)>0;
    if(!scannerActive){statusText('Reload HeneFM after installing',true);return;}
    statusText(info.tabVisible?'Live scanner · no forced refresh':'Live scanner · tab backgrounded',!info.tabVisible);
    const sc=info.scanner||{};
    const fmt=x=>x?.n?`${x.p50_ms} / ${x.p95_ms} ms (n=${x.n})`:'Not measured';
    $('pro-batch').textContent=sc.pro?.batches?`${sc.pro.p50_ms} / ${sc.pro.p95_ms} ms`:'Not measured';
    $('pro-on').textContent=fmt(sc.scanTiming?.on);
    $('pro-off').textContent=fmt(sc.scanTiming?.off);
    $('links').textContent=sc.sellerLinks??'—';
    $('cards').textContent=sc.cardsFound??'—';
    $('sold').textContent=sc.soldCards??'—';
    $('parsed').textContent=sc.parsedCards??'—';
    $('qualified').textContent=sc.qualifyingDeals??'—';
    $('sent').textContent=sc.sent??'—';
    $('live-time').textContent=ago(sc.liveSentAt);
    $('queued').textContent=sc.queued??'—';
    $('scanner-time').textContent=ago(sc.lastScanAt);
    $('scanner-error').textContent=sc.liveError||sc.lastError||'None';
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
  const captureSettings=await chrome.storage.local.get({fmRushScreenshotEnabled:false,fmRushProEnabled:true,fmRushProProfile:'normal'});
  $('pro-enabled').checked=captureSettings.fmRushProEnabled===true;
  $('pro-profile').value=captureSettings.fmRushProProfile;
  $('pro-enabled').addEventListener('change',()=>chrome.storage.local.set({fmRushProEnabled:$('pro-enabled').checked}));
  $('pro-profile').addEventListener('change',()=>chrome.storage.local.set({fmRushProProfile:$('pro-profile').value}));
  $('capture').checked=captureSettings.fmRushScreenshotEnabled===true;
  $('capture').addEventListener('change',async()=>{
    await chrome.runtime.sendMessage({kind:'fm-rush-capture-toggle',enabled:$('capture').checked});
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
