/* FM Rush v24.17 — PASSIVE HeneFM deal bridge and separate listing screenshot archive.
 * Reads only deal cards already rendered by the official HeneFM Flips page.
 * Does not insert, remove, style, sort, hide, click or modify ANY page element.
 * Does not request HeneFM endpoints or use the HeneFM Pricing API.
 */
(() => {
  'use strict';
  if (window.__fmRushPassiveBridgeInstalled) return;
  window.__fmRushPassiveBridgeInstalled = true;

  const isDealsPage = () => /^\/flips\/deals\/?$/.test(location.pathname);
  const SELLER_LINKS = 'a[href*="/shops/"],a[href*="/shop/"]';
  const SEEN_KEY = 'fmRushDeliveredV2411';
  const QUEUE_KEY = 'fmRushPendingV2411';
  const AMOUNT = '([0-9][0-9,]*(?:\\.[0-9]+)?(?:\\s*[KMB](?=mesos?\\b|\\b))?)';

  let seen = new Set();
  let scanTimer = null;
  let sending = false;
  let retryAfter = 0;
  let retryFailures = 0;
  let screenshotCandidates = [];
  let lastScreenshotBatchAt = 0;
  let lastScreenshotBatchHash = '';
  const queued = [];
  const liveSession=Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
  let liveRevision=0,liveSending=false,liveHash=null,liveSentAt=-Infinity;
  const diagnostics = {lastScanAt:0, sellerLinks:0, cardsFound:0, soldCards:0, parsedCards:0, qualifyingDeals:0, sent:0, rejected:0, lastSentAt:0, lastError:'', lastRejectAt:0};

  try {
    const saved = sessionStorage.getItem(SEEN_KEY);
    if (saved !== null) {
      seen = new Set(JSON.parse(saved));
    }
    const pending=JSON.parse(sessionStorage.getItem(QUEUE_KEY)||'[]');
    if(Array.isArray(pending))queued.push(...pending);
  } catch (_) { /* Fallback to tab-local state. */ }

  function remember() {
    try {
      sessionStorage.setItem(SEEN_KEY, JSON.stringify([...seen].slice(-1200)));
      sessionStorage.setItem(QUEUE_KEY, JSON.stringify(queued));
    }
    catch (_) { diagnostics.lastError='Pending listings are in memory; browser storage failed. Keep this tab open until delivery.'; }
  }
  function money(text) {
    const m = String(text ?? '').replace(/,/g, '').match(/([0-9]+(?:\.[0-9]+)?)\s*([KMB]?)(?![A-Za-z])/i);
    if (!m) return null;
    const n = Number(m[1]) * ({'': 1, K: 1000, M: 1e6, B: 1e9}[m[2].toUpperCase()]);
    return Number.isFinite(n) && n >= 0 ? Math.round(n) : null;
  }
  function fingerprint(value) {
    let h = 2166136261;
    for (let i = 0; i < value.length; i++) {
      h ^= value.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0).toString(16);
  }
  function linesOf(element) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const result = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement?.closest('script,style,noscript,template')) continue;
      const text = node.textContent.replace(/\u00a0/g, ' ').trim();
      if (text) result.push(text);
    }
    return result;
  }
  function findCard(sellerLink) {
    let element = sellerLink;
    for (let i = 0; element && i < 14; i++, element = element.parentElement) {
      if (element === document.body || element === document.documentElement) break;
      const sellers = new Set([...element.querySelectorAll(SELLER_LINKS)]
        .map(a => a.getAttribute('href')));
      // Never join two different listings when walking toward the page root.
      if (sellers.size > 1) break;
      const text = linesOf(element).join(' ');
      if (text.length > 9000) break;
      if (/\bProfit\b/i.test(text) && /\bBuy(?=\s|[:+0-9])/i.test(text)) {
        return element;
      }
    }
    return null;
  }
  function readProfit(lines) {
    const all = lines.join(' ');
    const block=all.split(/\bProfit\b/i)[1]?.split(/\b(?:Buy|Resell at|Average sale|Time to resell)\b/i)[0];
    if (!block) return null;
    // Single item: "Profit +22.3K 34%".
    // Multi-item:  "Profit · all 3 +47.7K +15.9K each 1026%".
    const gain = block.match(new RegExp('([+-])\\s*' + AMOUNT, 'i'));
    const percentages = [...block.matchAll(/(-?[0-9][0-9,]*(?:\.[0-9]+)?)\s*%/g)];
    if (!gain || !percentages.length) return null;
    return { gain: (gain[1]==='-'?-1:1)*money(gain[2]), pct: Number(percentages.at(-1)[1].replace(/,/g, '')) };
  }
  function readBuy(lines) {
    const all = lines.join(' ');
    const m = all.match(new RegExp('\\bBuy\\s*:?\\s*' + AMOUNT, 'i'));
    return m ? money(m[1]) : null;
  }
  function itemName(card, sellerLink, lines) {
    const anchor = [...card.querySelectorAll('a[href]')]
      .find(a => a !== sellerLink && /\/items?\//i.test(a.getAttribute('href') || ''));
    if (anchor) {
      const title = (anchor.textContent || '').replace(/\s+/g, ' ').trim();
      if (title && title.length <= 100) return title;
    }
    const prior = lines.slice(0, Math.max(0, lines.findIndex(s => /^Profit\b/i.test(s))));
    return prior.find(s => s.length > 2 && s.length <= 100 &&
      s !== sellerLink.textContent?.trim() &&
      !/^(Sold\b|Equipment\b|Cash item\b|Use\b|Consumable\b|Seen\b|CH\s*\d+)/i.test(s)) || '';
  }
  function isSold(lines, card) {
    // Do not mistake "84 sold a day" (sales-volume estimate) for listing status.
    if (card.matches('[data-sold="true"], [data-status="sold"]')) return true;
    return lines.some(line =>
      /^Sold(?:$|\s+(?:\d+\s*(?:s|sec|m|min|h|hr|d|day)\b|just\b|out\b|Equipment\b|Use\b|Cash\b)|\s*[·•:])/i.test(line));
  }
  function extract() {
    const results = [];
    const captureResults = [];
    const unique = new Set();
    const uniqueCaptured = new Set();
    const uniqueCards = new Set();
    const occurrences=new Map();
    const counts = {sellerLinks:0, cardsFound:0, soldCards:0, parsedCards:0, qualifyingDeals:0};
    const links = document.querySelectorAll(SELLER_LINKS);
    counts.sellerLinks = links.length;
    for (const link of links) {
      if (!/^https?:/.test(link.href)) continue;
      const card = findCard(link);
      if (!card || uniqueCards.has(card)) continue;
      uniqueCards.add(card);
      counts.cardsFound++;
      // A card outside the viewport still has a DOM rect and can be captured
      // without scrolling; only truly hidden cards are excluded.
      if (card.closest('[hidden],[aria-hidden="true"]') ||
          (typeof card.checkVisibility === 'function' && !card.checkVisibility())) continue;
      const lines = linesOf(card);
      const sold = isSold(lines, card);
      if (sold) counts.soldCards++;
      const text = lines.join(' ');
      const position = text.match(/\b(?:CH|CC)\s*(\d{1,2})\s*[·•/|,\-]?\s*FM\s*(\d{1,2})\b/i);
      const cc=position?Number(position[1]):null, fm=position?Number(position[2]):null;
      if (position && (cc<1 || cc>40 || fm<1 || fm>20)) continue;
      const profit = readProfit(lines);
      const buy = readBuy(lines);
      const label = (link.textContent || '').trim().replace(/\s+/g, ' ');
      let slug = '';
      try {slug = decodeURIComponent(new URL(link.href).pathname.split('/').filter(Boolean).pop());} catch (_) {}
      const ign = /^[A-Za-z0-9_]{3,24}$/.test(label) ? label : slug;
      if (!/^[A-Za-z0-9_]{3,24}$/.test(ign)) continue;
      const item = itemName(card, link, lines);
      if (!item) continue;
      const statWords=/\b(?:W\.DEF|M\.DEF|M\.ATT|ATT|STR|DEX|INT|LUK|ACC|AVOID|SPEED|JUMP|HP|MP|CDMG|CRIT)\s*[-+]?\d+(?:\s*[+-]\s*\d+)?|\b\d+\s+slots?(?:\s+\d+\s+used)?/gi;
      const stats=[...text.split(/\bBuy\b/i)[0].matchAll(statWords)].map(m=>m[0].replace(/\s+/g,' ')).join(' · ').slice(0,160);
      const unusuallyCheap = /Unusually\s+cheap\s*:\s*check\s+it\s+is\s+still\s+there/i.test(text);

      // Screenshots are a separate feature and include every rendered item on
      // the user's current Deals view (even low profit and sold entries).
      // Listing delivery and screenshots both include the current page contents.
      const r = card.getBoundingClientRect();
      const itemAnchor = [...card.querySelectorAll('a[href]')]
        .find(a => a !== link && /\/items?\//i.test(a.getAttribute('href')||''));
      const baseKey=[card.getAttribute?.('data-listing-id')||'',link.href,itemAnchor?.href||'',cc,fm,
        item,stats,buy??''].join('|').toLowerCase();
      const occurrence=occurrences.get(baseKey)||0;occurrences.set(baseKey,occurrence+1);
      const captureKey=baseKey+'|'+occurrence;
      const captureId = fingerprint(captureKey) + fingerprint([...captureKey].reverse().join(''));
      if (!uniqueCaptured.has(captureId) && r.width >= 12 && r.height >= 24) {
        uniqueCaptured.add(captureId);
        captureResults.push({id:captureId,item:item.slice(0,150),ign,cc,fm,
          buy_mesos:buy,sold,rect:{
            x:Math.max(0,Math.floor(r.left + window.scrollX - 2)),
            y:Math.max(0,Math.floor(r.top + window.scrollY - 2)),
            width:Math.ceil(r.width + 4),height:Math.ceil(r.height + 4)
          }});
      }

      // Mirror rendered listings exactly; profit and sold state are metadata.
      counts.parsedCards++;
      const listing_id=captureId;
      const deal = {cc,fm,ign,item,stats:stats.slice(0,160),listing_id,sold,
        buy_mesos:buy,profit_mesos:profit?.gain??null,profit_percent:profit?.pct??null,
        unusually_cheap:unusuallyCheap,raw_text:lines.join('\n').slice(0,6000)};
      deal.id=fingerprint([listing_id,sold,deal.profit_mesos,deal.profit_percent].join('|'));
      if (unique.has(deal.id)) continue;
      unique.add(deal.id);
      results.push(deal);
    }
    screenshotCandidates = captureResults;
    counts.qualifyingDeals = results.length;
    Object.assign(diagnostics, counts, {lastScanAt:Date.now()});
    return results;
  }
  function archiveScreenshots() {
    if (!isDealsPage() || !screenshotCandidates.length) return;
    const now=Date.now();
    const digest=fingerprint(screenshotCandidates.map(c=>c.id).sort().join(','));
    if (digest===lastScreenshotBatchHash && now-lastScreenshotBatchAt<5000) return;
    lastScreenshotBatchHash=digest;
    lastScreenshotBatchAt=now;
    // A completely separate message: never await screenshots before routing
    // deals, and never change the HeneFM page.
    try {
      chrome.runtime.sendMessage({kind:'fm-rush-capture-cards',cards:screenshotCandidates},()=>{
        void chrome.runtime.lastError; // Popup reports any capture failures.
      });
    } catch (_) { /* Extension may be reloading. */ }
  }
  function enqueue(deal) {
    if (queued.some(d => d.id === deal.id)) return false;
    queued.push(deal);
    return true;
  }
  function sendNext() {
    if (sending || Date.now() < retryAfter || !isDealsPage()) return;
    const deal = queued[0];
    if (!deal) return;
    sending = true;
    const {id, ...payload} = deal;
    try {
      chrome.runtime.sendMessage({kind: 'fm-rush-route-deal', deal: payload}, response => {
        sending = false;
        const error = chrome.runtime.lastError?.message || response?.error;
        if (response?.ok && !chrome.runtime.lastError) {
          const index=queued.findIndex(d=>d.id===deal.id);
          if(index>=0)queued.splice(index,1);
          // Only remember a deal AFTER FM Rush actually acknowledges it.
          // Previously a reload while the app was disconnected permanently
          // suppressed unsent deals for the rest of the tab session.
          seen.add(deal.id);
          remember();
          diagnostics.sent++;
          diagnostics.lastSentAt = Date.now();
          diagnostics.lastError = '';
          retryFailures = 0;
          retryAfter = 0;
          console.info('[FM Rush] Routed', deal.ign, 'CH' + deal.cc, 'FM' + deal.fm);
        } else if (response?.retryable === false) {
          const index=queued.findIndex(d=>d.id===deal.id);
          if(index>=0)queued.splice(index,1);
          remember(); // Invalid data is reported instead of retrying forever.
          diagnostics.rejected++;
          diagnostics.lastRejectAt = Date.now();
          diagnostics.lastError = String(error || 'invalid deal');
          console.warn('[FM Rush] Deal rejected:', diagnostics.lastError);
        } else {
          retryFailures++;
          diagnostics.lastError = String(error || 'app disconnected');
          retryAfter = Date.now() + Math.min(15000, 1200 * 2 ** Math.min(retryFailures - 1, 4));
          if (retryFailures === 1) console.info('[FM Rush] App disconnected; retrying while the deal remains visible.');
        }
        if (queued.length) scheduleScan();
      });
    } catch (_) {
      sending = false;
      retryFailures++;
      diagnostics.lastError = 'Extension context invalidated: reload HeneFM';
      retryAfter = Date.now() + 3000;
      console.warn('[FM Rush] Extension context invalidated; reload the HeneFM tab.');
    }
  }
  function syncLivePage(deals) {
    const hash=deals.map(d=>d.id).sort().join('|');
    if(liveSending || (hash===liveHash && Date.now()-liveSentAt<5000))return;
    liveSending=true;
    try {
      chrome.runtime.sendMessage({kind:'fm-rush-visible-deals',snapshot:{session:liveSession,
        revision:++liveRevision,observed_at_ms:Date.now(),deals:deals.map(({id,...deal})=>deal)}},response=>{
        liveSending=false;
        if(response?.ok && !chrome.runtime.lastError){
          liveHash=hash;liveSentAt=Date.now();
          diagnostics.liveListings=deals.length;diagnostics.liveSentAt=liveSentAt;
          diagnostics.liveError='';
        } else {
          diagnostics.liveError=chrome.runtime.lastError?.message || response?.error || 'Live page not connected';
        }
      });
    } catch(err) {
      liveSending=false;diagnostics.liveError=String(err);
    }
  }
  function scan() {
    scanTimer = null;
    if (!isDealsPage()) return;
    const deals = extract();
    syncLivePage(deals);
    // Include eligible cards on first load as well as newly appearing cards.
    let queueChanged=false;
    for (const deal of deals) if (!seen.has(deal.id)) queueChanged=enqueue(deal)||queueChanged;
    if(queueChanged)remember();
    // Keep unsent listings even after they leave the page; the archive must
    // not lose a seller while the local app is disconnected.
    // A compact fingerprint, not seller names, is passed to the refresh telemetry.
    // A changed fingerprint shows rendered deal data changed, not necessarily
    // that the server itself just generated a new list.
    try {
      const fingerprintKey = deals.map(d => d.id).sort().join(',');
      window.postMessage({kind:'FM_RUSH_REFRESH_V243',type:'deal-snapshot',
        count:deals.length,fingerprint:fingerprint(fingerprintKey)},location.origin);
    } catch (_) {}
    sendNext();
    // Deal delivery is dispatched first; archiving follows independently.
    archiveScreenshots();
  }
  function scheduleScan() {
    if (scanTimer !== null) return;
    scanTimer = setTimeout(scan, 80);
  }
  function init() {
    console.info('[FM Rush] Passive bridge active. Original HeneFM page is unchanged.');
    // The observer and listeners do not alter the page or intercept its controls.
    const observer = new MutationObserver(mutations => {
      if (mutations.some(m => m.type === 'childList' || m.type === 'characterData' ||
          (m.type === 'attributes' && m.target.matches?.('[data-sold],[data-status],[hidden]')))) {
        scheduleScan();
      }
    });
    observer.observe(document.documentElement, {subtree: true, childList: true,
      characterData: true, attributes: true, attributeFilter: ['data-sold', 'data-status', 'hidden']});
    document.addEventListener('visibilitychange', scheduleScan);
    window.addEventListener('pageshow', scheduleScan);
    window.addEventListener('popstate', scheduleScan);
    // MAIN-world refresh script cannot read extension storage directly.
    // Transfer only the local interval setting; never touch HeneFM controls.
    const REFRESH_KIND = 'FM_RUSH_REFRESH_V243';
    const signalRefresh = (type, extra={}) => {
      window.postMessage({kind:REFRESH_KIND, type, ...extra},location.origin);
    };
    try {
      chrome.storage?.local?.get({fmRushIntervalMs:1200,fmRushBackupReload:false}, result => {
        signalRefresh('set-settings',{intervalMs:result?.fmRushIntervalMs ?? 1200,
          fallbackEnabled:result?.fmRushBackupReload === true});
      });
      chrome.storage?.onChanged?.addListener((changes,area) => {
        if (area==='local' && (changes.fmRushIntervalMs || changes.fmRushBackupReload)) {
          chrome.storage.local.get({fmRushIntervalMs:1200,fmRushBackupReload:false},result=> {
            signalRefresh('set-settings',{intervalMs:result.fmRushIntervalMs,
              fallbackEnabled:result.fmRushBackupReload === true});
          });
        }
      });
      chrome.runtime.onMessage?.addListener((message,_sender,respond) => {
        if (message?.kind==='fm-rush-locate-capture') {
          extract();
          const card=screenshotCandidates.find(card=>card.id===message.id);
          respond(card?{ok:true,card}:{ok:false,error:'Listing no longer rendered'});
          return false;
        }
        if (message?.kind==='fm-rush-health-wake') {
          scheduleScan();
          signalRefresh('wake');
          respond({ok:true});
          return false;
        }
        if (message?.kind==='fm-rush-resend-current') {
          // Explicit opt-in to resend the current eligible page.
          seen.clear();
          liveHash=null;liveSentAt=-Infinity;
          remember();
          queued.length = 0;
          remember();
          retryAfter = 0;
          retryFailures = 0;
          scheduleScan();
          respond({ok:true});
          return false;
        }
        if (message?.kind==='fm-rush-get-status') {
          const requestId='status-'+Date.now()+'-'+Math.random().toString(36).slice(2);
          let done=false;
          const complete=value => {
            if (done) return;
            done=true;
            window.removeEventListener('message',reply);
            respond({...value, scanner:{...diagnostics,queued:queued.length,pending:sending, deliveredRemembered:seen.size}});
          };
          const reply=event => {
            if (event.source===window && event.origin===location.origin &&
                event.data?.kind===REFRESH_KIND && event.data?.type==='status-reply' &&
                event.data.requestId===requestId) complete(event.data.value);
          };
          window.addEventListener('message',reply);
          signalRefresh('status',{requestId});
          setTimeout(()=>complete({running:false}),750);
          return true;
        }
        return false;
      });
    } catch (_) {/* Extension lifecycle may be changing during page load. */}
    setInterval(scheduleScan, 1200); // local DOM + bridge retry; NO network or page refresh
    scheduleScan();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
