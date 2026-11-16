const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let cards=[],online=false,now=1000,routed=[],memory={};
function card(ign,{sold=false,metrics=true,room=true,hidden=false}={}){
 const link={href:'https://henefm.com/shops/'+ign,textContent:ign,getAttribute:()=>'/shops/'+ign,querySelectorAll:()=>[]};
 const item={lines:['Work Gloves',...(sold?['Sold']:[]),'Profit',metrics?'+1':'—',metrics?'1%':'—','Buy',metrics?'100':'—',ign,...(room?['CH 1 · FM 3']:[])],
  querySelectorAll:()=>[link],closest:()=>null,checkVisibility:()=>!hidden,matches:()=>false,
  getBoundingClientRect:()=>({left:0,top:0,width:400,height:180}),parentElement:null};
 link.parentElement=item;return item;
}
const document={readyState:'loading',addEventListener(){},querySelectorAll:()=>cards.map(c=>c.querySelectorAll()[0]),
 createTreeWalker(el){let i=0;const lines=el.lines||[el.textContent];return {nextNode(){return i<lines.length?{textContent:lines[i++],parentElement:{closest:()=>null}}:null}}}};
const window={postMessage(){}};
const context={window,document,URL,NodeFilter:{SHOW_TEXT:4},Date:{now:()=>now},console,
 location:{pathname:'/flips/deals',origin:'https://henefm.com'},setTimeout:()=>1,
 sessionStorage:{getItem:k=>memory[k]??null,setItem:(k,v)=>memory[k]=v},
 chrome:{runtime:{sendMessage(msg,cb){
  if(msg.kind!=='fm-rush-route-deal'){cb({ok:true});return;}
  if(online){routed.push(msg.deal);cb({ok:true});}else cb({ok:false,retryable:true});
 }}}};
const source=fs.readFileSync(__dirname+'/content.js','utf8').replace("  if (document.readyState === 'loading')",'  window.test={extract,scan};\n  if (document.readyState === \'loading\')');
vm.runInNewContext(source,context);
cards=[card('Mora'),card('Oral',{sold:true}),card('Missing',{metrics:false,room:false}),card('Hidden',{hidden:true})];
let results=window.test.extract();assert.equal(results.length,3);
assert.equal(results.find(d=>d.ign==='Oral').sold,true);
assert.equal(results.find(d=>d.ign==='Missing').profit_mesos,null);
assert.equal(results.find(d=>d.ign==='Missing').cc,null);
assert(results.every(d=>d.raw_text&&d.listing_id));
cards=[card('Twin'),card('Twin')];results=window.test.extract();
assert.equal(results.length,2);assert.equal(new Set(results.map(d=>d.listing_id)).size,2);
// More than the previous 30-listing queue; none may be evicted while offline.
cards=Array.from({length:40},(_,i)=>card('Seller'+i));window.test.scan();
assert.equal(JSON.parse(memory.fmRushPendingV2411).length,40);
// The page changes before reconnection: these observed listings must still arrive.
cards=[];online=true;
for(let i=0;i<45;i++){now+=2000;window.test.scan();}
assert.equal(routed.length,40);
assert.equal(new Set(routed.map(d=>d.ign)).size,40);
assert.equal(JSON.parse(memory.fmRushPendingV2411).length,0);
console.log('PASS: all visible/sold/missing-metric listings; 40 offline listings survive page changes and deliver');
