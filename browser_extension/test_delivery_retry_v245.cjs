const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/content.js','utf8').replace(
  "  if (document.readyState === 'loading')", "  window.test={extract,scan,diagnostics};\n  if (document.readyState === 'loading')");
let persisted={};
const memory={getItem:k=>Object.prototype.hasOwnProperty.call(persisted,k)?persisted[k]:null,
  setItem:(k,v)=>{persisted[k]=v;}};
function boot(online){
 let calls=0, successful=0;
 const link={href:'https://henefm.com/shops/FantonRR',textContent:'FantonRR',getAttribute:()=>'/shops/FantonRR',querySelectorAll:()=>[],parentElement:null};
 const c={lines:['Work Gloves','Equipment · Gloves','CRIT 2','Profit','+233.2K','130%','Buy','180K','FantonRR','CH 10 · FM 14','Seen 20s ago'],
   querySelectorAll:()=>[link],closest:()=>null,checkVisibility:()=>true,matches:()=>false,getBoundingClientRect:()=>({left:0,top:0,width:400,height:180}),parentElement:null};
 link.parentElement=c;
 const document={readyState:'loading',addEventListener(){},querySelectorAll:()=>[link],createTreeWalker(el){let i=0;const a=el.lines||[el.textContent];return {nextNode(){return i<a.length?{textContent:a[i++],parentElement:{closest:()=>null}}:null}}}};
 const window={postMessage(){}};
 const chrome={runtime:{sendMessage(msg, cb){if(msg.kind!=='fm-rush-route-deal'){cb({ok:true});return;}calls++;if(online){successful++;cb({ok:true})}else cb({ok:false,retryable:true,error:'app offline'});}}};
 const ctx={window,document,URL,NodeFilter:{SHOW_TEXT:4},location:{pathname:'/flips/deals',origin:'https://henefm.com'},sessionStorage:memory,setTimeout:()=>1,console,chrome};
 vm.runInNewContext(src,ctx);
 window.test.scan();
 return {calls,successful,stats:window.test.diagnostics,storage:{...persisted}};
}
const offline=boot(false);
assert.equal(offline.calls,1,'offline app should be attempted');
assert.equal(JSON.parse(persisted.fmRushDeliveredV2411).length,0,'Unsent listings are not acknowledged');
assert.equal(JSON.parse(persisted.fmRushPendingV2411).length,1,'Unsent listing survives reload');
const online=boot(true);
assert.equal(online.successful,1,'new tab/reload must retry old unsent deal');
assert.equal(JSON.parse(persisted.fmRushDeliveredV2411).length,1,'persist only acknowledged delivery');
const reopened=boot(true);
assert.equal(reopened.calls,0,'acknowledged deals must not endlessly resend');
console.log('PASS: offline deals do not become seen; after restart they send; acknowledged deals dedupe');
