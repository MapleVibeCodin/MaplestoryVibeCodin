const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let installed,saved={fmRushScreenshotEnabled:true};
const event={addListener(){}};
const context={console,Date,Number,String,Object,Map,Set,Error,RegExp,setTimeout,Promise,
 chrome:{storage:{local:{async get(keys){return Object.fromEntries((typeof keys==='string'?[keys]:keys).map(k=>[k,saved[k]]));},async set(values){Object.assign(saved,values);}}},
 alarms:{get:async()=>({}),onAlarm:event},runtime:{onStartup:event,onInstalled:{addListener(fn){installed=fn}},onMessage:event}},
 importScripts(name){vm.runInContext(fs.readFileSync(__dirname+'/'+name,'utf8'),ctx)}};
const ctx=vm.createContext(context);
vm.runInContext(fs.readFileSync(__dirname+'/background.js','utf8'),ctx);
(async()=>{
 await installed();assert.equal(saved.fmRushScreenshotEnabled,false,'workflow upgrade stops screenshot spam once');
 await vm.runInContext('fmCaptureSetEnabled(true)',ctx);
 await installed();assert.equal(saved.fmRushScreenshotEnabled,true,'explicit later opt-in survives reload');
 console.log('PASS: screenshot opt-out on workflow migration and later opt-in preserved');
})().catch(err=>{console.error(err);process.exitCode=1});
