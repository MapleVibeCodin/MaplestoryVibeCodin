const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let listener,requests=[];
const event={addListener(){}};
const context={importScripts(){},console,AbortController,AbortSignal,setTimeout,clearTimeout,
 chrome:{alarms:{get:async()=>({}),create:async()=>{},onAlarm:event},
 runtime:{onInstalled:event,onStartup:event,onMessage:{addListener(fn){listener=fn}}}},
 fetch:async(url,options)=>{requests.push({url,options});return {ok:true,status:200,json:async()=>({ok:true})}}};
vm.runInNewContext(fs.readFileSync(__dirname+'/background.js','utf8'),context);
(async()=>{
 const snapshot={session:'page',revision:1,deals:[{ign:'Hammy',listing_id:'a'.repeat(16)}]};
 const response=await new Promise(resolve=>listener({kind:'fm-rush-visible-deals',snapshot},{url:'https://henefm.com/flips/deals'},resolve));
 assert.equal(response.ok,true);
 assert.equal(requests[0].url,'http://127.0.0.1:18773/visible');
 assert.deepEqual(JSON.parse(requests[0].options.body),snapshot);
 assert.equal(requests[0].options.headers['X-FM-Rush-Bridge'],'v17-browser-view');
 const bad=await new Promise(resolve=>listener({kind:'fm-rush-visible-deals',snapshot},{url:'https://evil.example'},resolve));
 assert.equal(bad.ok,false);assert.equal(requests.length,1);
 console.log('PASS: live snapshot transport preserves complete payload and rejects other origins');
})().catch(err=>{console.error(err);process.exitCode=1});
