'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const operations=[];
const saved={};
let currentCard=null;
const chrome={
  storage:{local:{async get(keys){const kk=typeof keys==='string'?[keys]:Array.isArray(keys)?keys:Object.keys(keys);return Object.fromEntries(kk.map(k=>[k,saved[k]]));}, async set(values){Object.assign(saved,values);}}},
  tabs:{async sendMessage(tabId,message){assert.equal(message.kind,'fm-rush-locate-capture');return currentCard?{ok:true,card:currentCard}:{ok:false};},async get(tabId){return {id:tabId,url:'https://henefm.com/flips/deals?sort=fresh'};}},
  debugger:{async attach({tabId},v){operations.push('attach:'+tabId);assert.equal(v,'1.3');},
    async detach({tabId}){operations.push('detach:'+tabId);},
    async sendCommand({tabId},method,params){assert.equal(method,'Page.captureScreenshot');assert(params.captureBeyondViewport);assert.equal(params.clip.y,1500);operations.push('capture:'+tabId);return {data:'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y7PoXgAAAAASUVORK5CYII='.repeat(2)};}},
  downloads:{async download({url,filename,saveAs}){assert(url.startsWith('data:image/png;base64,'));assert(filename.includes('FM_Rush_Item_Screenshots/IGN_Hyperborean/'));assert(filename.endsWith('.png'));assert.equal(saveAs,false);operations.push('download:'+filename);return operations.length;}}
};
const context=vm.createContext({console,chrome,Date,Number,String,Object,Map,Set,Error,RegExp,setTimeout,Promise});
vm.runInContext(fs.readFileSync(__dirname+'/screenshot_worker.js','utf8'),context);
const run=expr=>vm.runInContext(expr,context);
(async()=>{
  const card={id:'abb12345aacc4321',item:'Blue Starlight',ign:'Hyperborean',cc:30,fm:5,
    buy_mesos:65000,sold:false,rect:{x:150,y:1400,width:430,height:300}};
  const sender={tab:{id:7},frameId:0,url:'https://henefm.com/flips/deals'};
  currentCard={...card,rect:{...card.rect,y:1500}};
  context.testCards=[card,card];context.sender=sender;
  let result=await run('fmCaptureEnqueue(testCards,sender)');
  assert.equal(result.ok,true);
  await run('(async()=>{while(fmCaptureRunning)await new Promise(r=>setTimeout(r,10));})()');
  assert.equal(operations.filter(x=>x.startsWith('download')).length,1,'one screenshot only');
  assert.equal(Object.keys(saved.fmRushScreenshotSeenByIGNV2).length,1,'ID persisted');
  await run('fmCaptureEnqueue(testCards,sender)');
  await run('(async()=>{while(fmCaptureRunning)await new Promise(r=>setTimeout(r,10));})()');
  assert.equal(operations.filter(x=>x.startsWith('download')).length,1,'no duplicate on 2nd scan');
  currentCard=null;context.testCards=[{...card,id:'aabbccddaabbccdd'}];
  await run('fmCaptureEnqueue(testCards,sender)');
  await run('(async()=>{while(fmCaptureRunning)await new Promise(r=>setTimeout(r,10));})()');
  assert.equal(operations.filter(x=>x.startsWith('download')).length,1,'A disappeared card must not be saved with another seller label');
  await run('fmCaptureSetEnabled(false)');
  const card2={...card,id:'aabbcccdaabbccdd'};
  context.testCards=[card2];
  await run('fmCaptureEnqueue(testCards,sender)');
  assert.equal(operations.filter(x=>x.startsWith('download')).length,1,'OFF toggle works');
  console.log('PASS: CDP offscreen clipping, actual PNG download, filenames, dedupe, persistence, toggle');
})().catch(err=>{console.error(err);process.exitCode=1;});
