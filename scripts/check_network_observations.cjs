const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
let calls=0,fail=false;const intervals=new Map(),window={};let id=0;
const box={window,module:{exports:{}},AbortController,
setTimeout:()=>100,clearTimeout(){},setInterval:fn=>{const key=++id;intervals.set(key,fn);return key;},clearInterval:key=>intervals.delete(key),
fetch:async()=>{calls++;if(fail)throw new Error('unavailable');return{ok:true,json:async()=>({valid:true,ok:true,probe_at_s:calls,success_at_s:calls,rtt_ms:40})};}};
const source=fs.readFileSync('dash.js/src/streaming/rules/abr/NetworkObservations.js','utf8').replace('export default function','function')+'\nmodule.exports=acquireNetworkObservations;';
vm.runInNewContext(source,box);const acquire=box.module.exports;
const first=acquire(),second=acquire();assert.equal(intervals.size,1);assert.equal(calls,1);assert.equal(window.LEO_SHARED_PROBE_ACTIVE,true);
const tick=async()=>{await new Promise(r=>setImmediate(r));};await tick();
assert.equal(window.LEO_PROBE.rtt_ms,40);
for(let i=0;i<12;i++){intervals.values().next().value();await tick();}
assert.equal(window.LEO_PROBE_HISTORY.length,8);
fail=true;intervals.values().next().value();await tick();assert.equal(window.LEO_PROBE.valid,false);
first();assert.equal(intervals.size,1);second();second();assert.equal(intervals.size,0);assert.equal(window.LEO_SHARED_PROBE_ACTIVE,false);
fail=false;const third=acquire();await tick();assert.equal(window.LEO_PROBE.valid,true);third();assert.equal(intervals.size,0);
console.log('PASS: shared production RTT poll, one timer, bounded causal history, explicit failure, idempotent release and restart');
})().catch(e=>{console.error(e);process.exitCode=1;});
