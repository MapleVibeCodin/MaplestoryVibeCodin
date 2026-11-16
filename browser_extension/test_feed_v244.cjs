const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
let cards=[],routes=[];
function card(lines){
 const pos=lines.findIndex(l=>/^CH \d+/.test(l)),ign=lines[pos-1];
 const link={href:'https://henefm.com/shops/'+ign,textContent:ign,getAttribute:()=>'/shops/'+ign,querySelectorAll:()=>[],parentElement:null};
 const c={lines,querySelectorAll:()=>[link],closest:()=>null,checkVisibility:()=>true,matches:()=>false,getBoundingClientRect:()=>({left:0,top:0,width:400,height:180}),parentElement:null};link.parentElement=c;return c;
}
const document={readyState:'loading',addEventListener(){},querySelectorAll:()=>cards.map(c=>c.querySelectorAll()[0]),createTreeWalker(el){let i=0;const a=el.lines||[el.textContent];return {nextNode(){return i<a.length?{textContent:a[i++],parentElement:{closest:()=>null}}:null}}}};
const window={postMessage(){}};
const ctx={window,document,URL,NodeFilter:{SHOW_TEXT:4},location:{pathname:'/flips/deals',origin:'https://henefm.com'},sessionStorage:{getItem:()=>null,setItem(){}},setTimeout:()=>1,console,chrome:{runtime:{sendMessage(msg,cb){if(msg.kind==='fm-rush-route-deal')routes.push(msg.deal);cb({ok:true})}}}};
let src=fs.readFileSync(__dirname+'/content.js','utf8').replace("  if (document.readyState === 'loading')",'  window.test={extract,scan};\n  if (document.readyState === \'loading\')');vm.runInNewContext(src,ctx);
function offer(gain,pct,flag=false,sold=false){return card(['Test Item','Equipment · Top',...(flag?['***Unusually cheap: check it is still there***']:[]),...(sold?['Sold']:[]),'Profit','+'+gain+'mesos',pct+'%','Buy','1Kmesos','2pro','CH 21 · FM 6','Seen 1s ago']);}
for(const [gain,pct,flag,sold,yes] of [[15000,15,false,false,true],[14999,15,false,false,true],[15000,14.99,false,false,true],[8600,819,true,false,true],[100,1,true,false,true],[8600,819,true,true,true]]){
 cards=[offer(gain,pct,flag,sold)];assert.equal(window.test.extract().length,yes?1:0,JSON.stringify([gain,pct,flag,sold]));
}
if(process.argv[2]){
 const text=fs.readFileSync(process.argv[2],'utf8').replace(/\r/g,'');
 cards=text.split(/\n\s*\n/).filter(b=>/\bProfit\b/.test(b)&&/CH \d+ · FM/.test(b)).map(b=>card(b.trim().split('\n')));
 const matches=window.test.extract();assert.equal(matches.length,cards.length);assert(matches.some(d=>d.item==='Black Steal'&&d.profit_mesos===8600&&d.unusually_cheap));assert(matches.some(d=>d.item==='Iron Ingot'&&d.profit_mesos===53100));
 window.test.scan();for(let i=0;i<cards.length+2;i++)window.test.scan();assert.equal(routes.length,matches.length,'initial matches delivered once');
 if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(routes));
 console.log(matches.map(d=>`${d.item}: ${d.ign}, ${d.profit_mesos}, ${d.profit_percent}%`).join('\n'));
}
console.log('PASS: all visible listings, below-threshold and sold entries, numeric seller names and dedupe');
