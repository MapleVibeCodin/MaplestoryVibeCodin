const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let cards=[],online=true,now=1000,snapshots=[],memory={};
function card(ign){
 const link={href:'https://henefm.com/shops/'+ign,textContent:ign,getAttribute:()=>'/shops/'+ign,querySelectorAll:()=>[]};
 const item={lines:['Work Gloves','Profit','+1','1%','Buy','100',ign,'CH 1 · FM 9'],
  querySelectorAll:()=>[link],closest:()=>null,checkVisibility:()=>true,matches:()=>false,
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
  if(msg.kind==='fm-rush-visible-deals'){
   snapshots.push(JSON.parse(JSON.stringify(msg.snapshot)));cb({ok:online});
  }else cb({ok:true});
 }}}};
const source=fs.readFileSync(__dirname+'/content.js','utf8').replace("  if (document.readyState === 'loading')",'  window.test={scan};\n  if (document.readyState === \'loading\')');
vm.runInNewContext(source,context);
cards=[card('languiwhisp'),card('Hammy')];window.test.scan();
assert.deepEqual(snapshots.at(-1).deals.map(d=>d.ign),['languiwhisp','Hammy']);
const session=snapshots[0].session;assert(session);
now+=1200;window.test.scan();assert.equal(snapshots.length,1,'unchanged page throttled');
now+=5000;window.test.scan();assert.equal(snapshots.length,2,'heartbeat independent of archive delivery dedupe');
cards=[card('NextSeller')];window.test.scan();
assert.deepEqual(snapshots.at(-1).deals.map(d=>d.ign),['NextSeller'],'snapshot replaces rather than appends');
assert(snapshots.at(-1).revision>snapshots[0].revision);
cards=[];window.test.scan();assert.equal(snapshots.at(-1).deals.length,0,'empty page clears scanner');
online=false;cards=[card('OfflineOld')];window.test.scan();
cards=[card('FreshLive')];online=true;window.test.scan();
assert.deepEqual(snapshots.at(-1).deals.map(d=>d.ign),['FreshLive'],'reconnect sends latest page, not old snapshot');
assert.equal(snapshots.at(-1).session,session);
console.log('PASS: exact live two, rotation, heartbeat, empty page and latest-only reconnect');
