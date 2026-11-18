const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let cards=[],messages=[],click;
function card(ign){
 const link={href:'https://henefm.com/shops/'+ign,textContent:ign,getAttribute:()=>'/shops/'+ign,querySelectorAll:()=>[]};
 const item={lines:['Work Gloves','Profit','+1','1%','Buy','100',ign,'CH 1 · FM 9'],dataset:{},style:{},
  querySelectorAll:()=>[link],closest:()=>null,checkVisibility:()=>true,matches:()=>false,
  getBoundingClientRect:()=>({left:0,top:0,width:400,height:180}),parentElement:null};
 link.parentElement=item;return item;
}
const document={readyState:'loading',addEventListener(kind,fn){if(kind==='click')click=fn;},
 querySelectorAll(sel){return sel.includes('data-fm-rush-selected')?cards.filter(c=>c.dataset.fmRushSelected):cards.map(c=>c.querySelectorAll()[0]);},
 createTreeWalker(el){let i=0;const lines=el.lines||[el.textContent];return {nextNode(){return i<lines.length?{textContent:lines[i++],parentElement:{closest:()=>null}}:null}}}};
const window={postMessage(){}};
const ctx={window,document,URL,NodeFilter:{SHOW_TEXT:4},console,Date,
 location:{pathname:'/flips/deals',origin:'https://henefm.com'},setTimeout:()=>1,
 sessionStorage:{getItem:()=>null,setItem(){}},
 chrome:{runtime:{sendMessage(msg,cb){messages.push(msg);cb({ok:true});}}}};
const src=fs.readFileSync(__dirname+'/content.js','utf8').replace("  if (document.readyState === 'loading')",'  window.test={scan,chooseDeal};\n  if (document.readyState === \'loading\')');
vm.runInNewContext(src,ctx);cards=[card('First'),card('Second')];window.test.scan();
assert(!messages.some(m=>m.kind==='fm-rush-select-deal'));
let prevented=false;click({button:0,target:cards[1],preventDefault(){prevented=true;}});
assert(prevented);let selection=messages.at(-1);assert.equal(selection.kind,'fm-rush-select-deal');assert.equal(selection.deal.ign,'Second');
assert.equal(cards[1].dataset.fmRushSelected,'true');
window.test.chooseDeal(cards[0],'skip');assert.equal(messages.at(-1).kind,'fm-rush-skip-deal');
assert.equal(cards[1].dataset.fmRushSelected,'true','skipping a different listing must keep selection');
assert(messages.at(-1).deal._choice_revision>selection.deal._choice_revision);
window.test.chooseDeal(cards[1],'skip');assert(!cards[1].dataset.fmRushSelected);
console.log('PASS: passive arrivals, card click selection, explicit skip and choice sequencing');
