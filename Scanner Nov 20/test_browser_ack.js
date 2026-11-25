/* Offline regression for the actual production acknowledgement helper.
 * Run: node test_browser_ack.js (optional; no third-party packages).
 */
'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict'), vm=require('node:vm');
const base=path.join(__dirname,'browser_extension');
const source=fs.readFileSync(path.join(base,'content.js'),'utf8');
new vm.Script(source);
new vm.Script(fs.readFileSync(path.join(base,'background.js'),'utf8'));
const start=source.indexOf('  function acknowledgeVisible('),end=source.indexOf('  function sendNext()',start);
assert.ok(start>=0 && end>start);
const acknowledgeVisible=new Function(source.slice(start,end)+'return acknowledgeVisible;')();
const q=[{id:'old'},{id:'a'},{id:'b'},{id:'later'}],p=new Set(q.map(x=>x.id)),s=new Set(['a']);
assert.deepEqual(acknowledgeVisible(new Set(['a','b','new']),q,p,s),{newlyDelivered:2,changed:true});
assert.deepEqual(q.map(x=>x.id),['old','later']);
assert.deepEqual([...p],['old','later']);
assert.ok(s.has('new'));
assert.deepEqual(acknowledgeVisible(new Set(['a','b','new']),q,p,s),{newlyDelivered:0,changed:false});
assert.deepEqual(acknowledgeVisible(new Set(),q,p,s),{newlyDelivered:0,changed:false});
assert.deepEqual(q.map(x=>x.id),['old','later']);
console.log('Browser syntax and three acknowledgement cases passed.');
