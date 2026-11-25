/* MetaScanner v24.57.0 — passive live HeneFM deal bridge and separate listing screenshot archive.
 * Reads only deal cards already rendered by the official HeneFM Flips page.
 * Adds Chase/Skip controls and selection feedback only; no automatic game inputs.
 * Does not request HeneFM endpoints or use the HeneFM Pricing API.
 */
(() => {
  'use strict';
  if (window.__fmRushPassiveBridgeInstalled) return;
  window.__fmRushPassiveBridgeInstalled = true;

  const isDealsPage = () => /^\/flips\/deals\/?$/.test(location.pathname);
  let cardDeals=new WeakMap();
  let cardCache=new WeakMap(),linkCache=new WeakMap(),dirtyCards=new WeakSet();
  let observer=null,lastFullParse=0,parseHits=0,parseMisses=0;
  let cachedDeals=[],needsExtract=true,quietScans=0;
  let selectionSerial=0;
  let activeListingId=null, lockedListingId=null, liveLocked=false;
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
  // Conservative until storage answers; click captures remain independent.
  let bulkCaptureEnabled = true;
  let lastScreenshotBatchAt = 0;
  let lastScreenshotBatchHash = '';
  const queued = [];
  const queuedIds = new Set();
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
  for (const deal of queued) queuedIds.add(deal.id);

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
      if (node.parentElement?.closest('script,style,noscript,template,[data-fm-rush-controls]')) continue;
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
    const all=lines.join(' ');
    const m=all.match(new RegExp('\\bBuy\\s*:?\\s*'+AMOUNT,'i'));
    if(!m)return {price:null,exact:false};
    const displayed=money(m[1]);
    // Only the tooltip immediately after the Buy amount is a unit buy price.
    // Never search the entire card: resale, total spend and profit also have tooltips.
    const tail=all.slice(m.index+m[0].length);
    const exact=tail.match(/^\s+((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+))\s+mesos\s+each\b/i);
    if(exact){
      const value=Number(exact[1].replace(/,/g,''));
      const compact=m[1].replace(/,/g,'').match(/^([0-9]+(?:\.[0-9]+)?)\s*([KMB])$/i);
      const step=compact?({'K':1000,'M':1e6,'B':1e9}[compact[2].toUpperCase()]/10**(compact[1].split('.')[1]?.length||0)):1;
      if(Number.isSafeInteger(value)&&value>=0&&value<=1e12&&displayed!==null&&Math.abs(value-displayed)<=step/2)
        return {price:value,exact:true};
    }
    return {price:displayed,exact:false};
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
  function readShopPosition(card) {
    const plot = card.querySelector('.deal-shop-map-plot');
    const image = plot?.querySelector('img[src]');
    const pin = plot?.querySelector('.deal-shop-pin');
    if (!image || !pin) return null;
    let path;
    try { path = new URL(image.getAttribute('src'), location.href).pathname; }
    catch (_) { return null; }
    const theme = path.match(/^\/api\/flips\/shop-map\/(grass|cave)$/)?.[1];
    const percent = value => /^\d+(?:\.\d+)?%$/.test(value) ? Number(value.slice(0, -1)) : NaN;
    const left = percent(pin.style.left);
    const top = percent(pin.style.top);
    return theme && left >= 0 && left <= 100 && top >= 0 && top <= 100
      ? {theme, left, top} : null;
  }
  function invalidate(records) {
    let relevant=false;
    for(const m of records){
      const el=m.target.nodeType===1?m.target:m.target.parentElement;
      if(!el || el.closest?.('[data-fm-rush-controls]'))continue;
      const nodes=[...m.addedNodes,...m.removedNodes];
      if(m.type==='childList' && nodes.length &&
         nodes.every(n=>n.nodeType===1 && n.matches?.('[data-fm-rush-controls]')))continue;
      if(m.type==='attributes' && m.attributeName==='style' &&
         !el.matches?.('.deal-shop-pin'))continue;
      relevant=true;
      for(let n=el;n&&n!==document.documentElement;n=n.parentElement)dirtyCards.add(n);
    }
    return relevant;
  }
  function parseCard(card,link) {
      const lines = linesOf(card);
      const sold = isSold(lines, card);
      const text = lines.join(' ');
      const position = text.match(/\b(?:CH|CC)\s*(\d{1,2})\s*[·•/|,\-]?\s*FM\s*(\d{1,2})\b/i);
      const cc=position?Number(position[1]):null, fm=position?Number(position[2]):null;
      if (position && (cc<1 || cc>40 || fm<1 || fm>20)) return null;
      const profit = readProfit(lines);
      const buyInfo = readBuy(lines);
      const buy = buyInfo.price;
      const label = (link.textContent || '').trim().replace(/\s+/g, ' ');
      let slug = '';
      try {slug = decodeURIComponent(new URL(link.href).pathname.split('/').filter(Boolean).pop());} catch (_) {}
      const ign = /^[A-Za-z0-9_]{3,24}$/.test(label) ? label : slug;
      if (!/^[A-Za-z0-9_]{3,24}$/.test(ign)) return null;
      const item = itemName(card, link, lines);
      if (!item) return null;
      const statWords=/\b(?:W\.DEF|M\.DEF|M\.ATT|ATT|STR|DEX|INT|LUK|ACC|AVOID|SPEED|JUMP|HP|MP|CDMG|CRIT)\s*[-+]?\d+(?:\s*[+-]\s*\d+)?|\b\d+\s+slots?(?:\s+\d+\s+used)?/gi;
      const stats=[...text.split(/\bBuy\b/i)[0].matchAll(statWords)].map(m=>m[0].replace(/\s+/g,' ')).join(' · ').slice(0,160);
      const unusuallyCheap = /Unusually\s+cheap\s*:\s*check\s+it\s+is\s+still\s+there/i.test(text);

      const itemAnchor = [...card.querySelectorAll('a[href]')]
        .find(a => a !== link && /\/items?\//i.test(a.getAttribute('href')||''));
      const baseKey=[card.getAttribute?.('data-listing-id')||'',link.href,itemAnchor?.href||'',cc,fm,
        item,stats,buy??''].join('|').toLowerCase();
      return {sold,cc,fm,profit,buy,ign,item,stats,unusuallyCheap,baseKey,shop_position:readShopPosition(card),raw_text:((buyInfo.exact ? `Buy exact: ${buy} mesos each\n` : '')+lines.join('\n')).slice(0,6000)};
  }
  function extract(forceCapture=false) {
    if(observer)invalidate(observer.takeRecords());
    if(Date.now()-lastFullParse>=10000){
      cardCache=new WeakMap();linkCache=new WeakMap();
      lastFullParse=Date.now();
    }
    cardDeals=new WeakMap();
    const results = [];
    const captureResults = [];
    const unique = new Set();
    const uniqueCaptured = new Set();
    const uniqueCards = new Set();
    const occurrences=new Map();
    const cardRows=[];
    const counts = {sellerLinks:0, cardsFound:0, soldCards:0, parsedCards:0, qualifyingDeals:0};
    const links = document.querySelectorAll(SELLER_LINKS);
    counts.sellerLinks = links.length;
    for (const link of links) {
      if (!/^https?:/.test(link.href)) continue;
      let card=linkCache.get(link);
      if(!card || !card.isConnected || !card.contains(link) || dirtyCards.has(card)){
        card=findCard(link);
        if(card)linkCache.set(link,card);
      }
      if (!card || uniqueCards.has(card)) continue;
      uniqueCards.add(card);
      counts.cardsFound++;
      // A card outside the viewport still has a DOM rect and can be captured
      // without scrolling; only truly hidden cards are excluded.
      if (card.closest('[hidden],[aria-hidden="true"]') ||
          (typeof card.checkVisibility === 'function' && !card.checkVisibility())) continue;
      let parsed=cardCache.get(card);
      if(!parsed || parsed.link!==link || dirtyCards.has(card)){
        parsed={link,value:parseCard(card,link)};cardCache.set(card,parsed);dirtyCards.delete(card);parseMisses++;
      }else parseHits++;
      if(!parsed.value)continue;
      const {sold,cc,fm,profit,buy,ign,item,stats,unusuallyCheap,baseKey,shop_position,raw_text}=parsed.value;
      if(sold)counts.soldCards++;
      const r=(bulkCaptureEnabled || forceCapture) ? card.getBoundingClientRect() : null;
      const occurrence=occurrences.get(baseKey)||0;occurrences.set(baseKey,occurrence+1);
      const captureKey=baseKey+'|'+occurrence;
      const captureId = fingerprint(captureKey) + fingerprint([...captureKey].reverse().join(''));
      if (r && !uniqueCaptured.has(captureId) && r.width >= 12 && r.height >= 24) {
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
        unusually_cheap:unusuallyCheap,shop_position,raw_text};
      deal.id=fingerprint([listing_id,sold,deal.profit_mesos,deal.profit_percent].join('|'));
      if (unique.has(deal.id)) continue;
      unique.add(deal.id);
      results.push(deal);
      cardDeals.set(card,deal);
      addChoiceControls(card);
      cardRows.push({card,deal});
    }
    // Live mode ALWAYS highlights the first rendered listing; a confirmed
    // CHASE/LOCK keeps its own card highlighted even if it is no longer #1.
    const focusId=liveLocked ? (lockedListingId || activeListingId)
      : (results[0]?.listing_id || null);
    for (const {card,deal} of cardRows) {
      const selected=deal.listing_id===focusId;
      card.classList.toggle('fm-rush-focus',selected);
      card.classList.toggle('fm-rush-locked',selected && liveLocked);
    }
    screenshotCandidates = captureResults;
    counts.qualifyingDeals = results.length;
    Object.assign(diagnostics, counts, {lastScanAt:Date.now(),parseHits,parseMisses});
    // Explicit click/capture extraction also refreshes the quiet heartbeat snapshot.
    cachedDeals=results;
    return results;
  }
  function choiceError(card,message){
    const status=card.querySelector?.('[data-fm-rush-status]');
    if(status)status.textContent=message;
  }
  function chooseDeal(card,action) {
    const deal=cardDeals.get(card);
    if(!deal)return;
    const serial=++selectionSerial;
    const {id,...payload}=deal;
    if (action === 'select') payload.shop_position = readShopPosition(card);
    choiceError(card,'');
    try { chrome.runtime.sendMessage({kind:action==='unlock'?'fm-rush-unlock-deal':action==='skip'?'fm-rush-skip-deal':'fm-rush-select-deal',deal:{...payload,_choice_session:liveSession,_choice_revision:serial}},response=>{
      if(serial!==selectionSerial)return;
      if(response?.ok && !chrome.runtime.lastError){
        if(action==='select'){
          lockedListingId=payload.listing_id;
          activeListingId=payload.listing_id;
          liveLocked=true;
        } else if(action==='unlock') {
          lockedListingId=null;activeListingId=null;
          liveLocked=false;
        } else if(lockedListingId===payload.listing_id){
          lockedListingId=null;activeListingId=null;
          liveLocked=false;
        }
        scheduleScan();
      }else {
        choiceError(card,response?.error || 'NOT SENT · start FM Rush and try again');
        console.warn('[FM Rush] Choice not delivered:',response?.error||chrome.runtime.lastError?.message);
      }
    }); }catch(error){choiceError(card,'NOT SENT · reload HeneFM');}
    if(action==='select')saveClicked(card, payload);
  }
  function saveClicked(card, payload) {
    // Snapshot the listing at click time, separately from selection acceptance.
    const r=card.getBoundingClientRect();
    const clicked={id:payload.listing_id,item:payload.item,ign:payload.ign,cc:payload.cc,fm:payload.fm,
      buy_mesos:payload.buy_mesos,sold:payload.sold,rect:{
        x:Math.max(0,Math.floor(r.left+window.scrollX-2)),
        y:Math.max(0,Math.floor(r.top+window.scrollY-2)),
        width:Math.ceil(r.width+4),height:Math.ceil(r.height+4)
      }};
    const status=card.querySelector?.('[data-fm-rush-save-status]');
    const note=text=>{if(status)status.textContent=text;};
    note('Saving click…');
    try {chrome.runtime.sendMessage({kind:'fm-rush-capture-clicked',card:clicked,deal:payload},response=>{
      const error=chrome.runtime.lastError?.message||response?.error;
      if(response?.ok)note('PNG saved');
      else if(response?.recordSaved)note('Listing saved · PNG unavailable');
      else note('Not saved · '+(error||'start FM Rush'));
      if(!response?.ok)console.warn('[FM Rush] Click screenshot:',error);
    });}catch(error){note('Not saved · reload HeneFM');}
  }
  function addChoiceControls(card){
    if(!card.querySelector || card.querySelector('[data-fm-rush-controls]') || !document.createElement)return;
    const controls=document.createElement('div');controls.dataset.fmRushControls='true';
    controls.style.cssText='display:flex;gap:6px;justify-content:flex-end;margin:4px 8px;';
    for(const [action,label] of [['select','CHASE'],['unlock','UNLOCK'],['skip','SKIP']]){
      const button=document.createElement('button');button.type='button';button.textContent=label;
      button.style.cssText='cursor:pointer;padding:4px 12px;border:1px solid #087962;border-radius:5px;background:#f0fffa;color:#075c49;font-weight:bold;';
      button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();chooseDeal(card,action);});
      controls.appendChild(button);
    }
    const status=document.createElement('span');status.dataset.fmRushStatus='true';
    status.setAttribute('role','status');status.style.cssText='color:#b71c1c;font-size:11px;align-self:center;';
    controls.appendChild(status);
    const saved=document.createElement('span');saved.dataset.fmRushSaveStatus='true';
    saved.setAttribute('role','status');saved.style.cssText='font-size:11px;color:#087962;align-self:center;';
    controls.appendChild(saved);card.appendChild(controls);
  }
  function captureListingClick(event){
    if(!isDealsPage() || !event.isTrusted || (event.button!==0 && event.button!==1))return;
    if(event.target?.closest?.('[data-fm-rush-controls]'))return;
    // Resolve against the current DOM, including a just-arrived live card.
    const chain=event.composedPath();
    if(observer && invalidate(observer.takeRecords()))needsExtract=true;
    // Clean known cards already have exact parsed identity. New/dirty cards
    // and periodic reconciliation still use the original full extraction.
    if(needsExtract || Date.now()-lastFullParse>=10000 || !chain.some(node=>cardDeals.has(node))){
      extract();needsExtract=false;
    }
    const card=chain.find(node=>cardDeals.has(node));
    if(!card)return;
    if(event.button!==0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey){
      const {id,...payload}=cardDeals.get(card);
      saveClicked(card,payload); // preserve native modified-click navigation
      return;
    }
    event.preventDefault();chooseDeal(card,'select');
  }
  document.addEventListener('click',captureListingClick,true);
  document.addEventListener('auxclick',captureListingClick,true);
  function archiveScreenshots() {
    if (!bulkCaptureEnabled || !isDealsPage() || !screenshotCandidates.length) return;
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
    if (queuedIds.has(deal.id)) return false;
    queued.push(deal);queuedIds.add(deal.id);
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
          queuedIds.delete(deal.id);
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
          queuedIds.delete(deal.id);
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
        if (queued.length) scheduleScan(false);
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
    if(liveSending)return;
    const hash=deals.map(d=>d.id+':'+JSON.stringify(d.shop_position)).join('|');
    if(hash===liveHash && Date.now()-liveSentAt<5000)return;
    liveSending=true;
    try {
      chrome.runtime.sendMessage({kind:'fm-rush-visible-deals',snapshot:{session:liveSession,
        revision:++liveRevision,observed_at_ms:Date.now(),deals:deals.map(({id,...deal})=>deal)}},response=>{
        liveSending=false;
        if(response?.ok && !chrome.runtime.lastError){
          const wasLocked=liveLocked;
          const previousFocus=activeListingId;
          liveLocked=response.chase_locked===true;
          activeListingId=response.focused_listing_id||null;
          lockedListingId=liveLocked ? activeListingId : null;
          liveHash=hash;liveSentAt=Date.now();
          if(wasLocked!==liveLocked || previousFocus!==activeListingId)scheduleScan();
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
    if (!isDealsPage()){needsExtract=true;cachedDeals=[];return;}
    if(observer && invalidate(observer.takeRecords()))needsExtract=true;
    if(needsExtract || Date.now()-lastFullParse>=10000){
      cachedDeals=extract();needsExtract=false;
    }else quietScans++;
    diagnostics.quietScans=quietScans;
    const deals=cachedDeals;
    syncLivePage(deals);
    // Include eligible cards on first load as well as newly appearing cards.
    let queueChanged=false;
    for (const deal of deals) if (!seen.has(deal.id)) queueChanged=enqueue(deal)||queueChanged;
    if(queueChanged)remember();
    // Keep unsent listings even after they leave the page; the archive must
    // not lose a seller while the local app is disconnected.
    sendNext();
    // Deal delivery is dispatched first; archiving follows independently.
    archiveScreenshots();
  }
  function scheduleScan(force=true) {
    if(force)needsExtract=true;
    if (scanTimer !== null) return;
    scanTimer = setTimeout(scan, 0);
  }
  function init() {
    // Highlight the ITEM NAME as well as the entire selected listing.
    // DOM class changes are excluded from the observer, so this doesn't
    // cause the scanner to repeatedly re-parse the same HeneFM page.
    if(!document.getElementById('fm-rush-focus-style')){
      const style=document.createElement('style');
      style.id='fm-rush-focus-style';
      style.textContent=`
        .fm-rush-focus { outline:3px solid #f5b72b !important;
          outline-offset:2px !important; border-radius:5px; }
        .fm-rush-focus a[href*="/items/"],
        .fm-rush-focus a[href*="/item/"] { background:#fff3a0 !important;
          color:#201300 !important; font-weight:900 !important;
          box-shadow:0 0 0 3px #ffdb40 !important; border-radius:3px; }
        .fm-rush-focus.fm-rush-locked { outline-color:#00c99a !important; }
        .fm-rush-focus.fm-rush-locked a[href*="/items/"],
        .fm-rush-focus.fm-rush-locked a[href*="/item/"] {
          box-shadow:0 0 0 3px #00c99a !important; }
      `;
      (document.head||document.documentElement).appendChild(style);
    }
    console.info('[FM Rush] Click a listing or CHASE to select one seller; SKIP never records a purchase.');
    // Listing controls are excluded from parser text; normal site data stays intact.
    observer = new MutationObserver(mutations => {
      if(invalidate(mutations))scheduleScan();
    });
    const setBulkCapture = enabled => {
      if(bulkCaptureEnabled===enabled)return;
      bulkCaptureEnabled=enabled;scheduleScan();
    };
    try {
      chrome.storage.local.get({fmRushScreenshotEnabled:false}, value=>{
        if(!chrome.runtime.lastError)setBulkCapture(value.fmRushScreenshotEnabled===true);
      });
      chrome.storage.onChanged.addListener((changes,area)=>{
        if(area==='local' && changes.fmRushScreenshotEnabled)setBulkCapture(changes.fmRushScreenshotEnabled.newValue===true);
      });
    } catch (_) { /* Preserve screenshot capture on storage failure. */ }
    observer.observe(document.documentElement, {subtree: true, childList: true,
      characterData: true, attributes: true, attributeFilter: ['data-sold', 'data-status', 'data-listing-id', 'href', 'src', 'hidden', 'aria-hidden', 'style']});
    document.addEventListener('visibilitychange', scheduleScan);
    window.addEventListener('pageshow', scheduleScan);
    window.addEventListener('popstate', scheduleScan);
    window.addEventListener('resize', scheduleScan);
    try {
      chrome.runtime.onMessage?.addListener((message,_sender,respond) => {
        if (message?.kind==='fm-rush-locate-capture') {
          extract(true);
          const card=screenshotCandidates.find(card=>card.id===message.id);
          respond(card?{ok:true,card}:{ok:false,error:'Listing no longer rendered'});
          return false;
        }
        if (message?.kind==='fm-rush-health-wake') {
          scheduleScan(false);
          respond({ok:true});
          return false;
        }
        if (message?.kind==='fm-rush-resend-current') {
          // Explicit opt-in to resend the current eligible page.
          seen.clear();
          liveHash=null;liveSentAt=-Infinity;
          remember();
          queued.length = 0;queuedIds.clear();
          remember();
          retryAfter = 0;
          retryFailures = 0;
          scheduleScan();
          respond({ok:true});
          return false;
        }
        if (message?.kind==='fm-rush-get-status') {
          respond({running:isDealsPage(),tabVisible:document.visibilityState==='visible',scanner:{...diagnostics,queued:queued.length,pending:sending,deliveredRemembered:seen.size}});
          return false;
        }
        return false;
      });
    } catch (_) {/* Extension lifecycle may be changing during page load. */}
    setInterval(()=>scheduleScan(false), 1200); // local DOM + bridge retry; NO network or page refresh
    scheduleScan();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();

