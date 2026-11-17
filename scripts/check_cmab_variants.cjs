// Execute the actual controller with deterministic clock/runtime substitutes.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const ledgerSource=fs.readFileSync('dash.js/src/streaming/rules/abr/cmab/CMABFeedback.js','utf8').replace('export default function','function')+'\nmodule.exports=CMABFeedback;';
const ledgerContext={module:{exports:{}}};vm.runInNewContext(ledgerSource,ledgerContext);
const Feedback=ledgerContext.module.exports;
const path = 'dash.js/src/streaming/rules/abr/cmab/CMABImprovedController.js';
const source = fs.readFileSync(path, 'utf8').replace(/^import .*;\r?$/gm, '')
    .replace('export default FactoryMaker.getClassFactory(CMABImprovedController);', 'module.exports=CMABImprovedController;');
function run(variant, originalController=false, freshProbe=false) {
    let wall = Date.UTC(2026,10,17), fits=0;
    class Clock extends Date {constructor(...a) {super(...(a.length?a:[wall]));} static now(){return wall;}}
    const window = {location:{search:'?cmabVariant='+variant}};
    const context = {window, Date:Clock, performance:{now:()=>wall}, Map, URLSearchParams, module:{exports:{}}, FactoryMaker:{}, CMABFeedback:Feedback,
        XMLHttpRequest:class {open(){} send(){this.status=200;this.responseText='40';}},
        fetch:()=>Promise.resolve({status:200,json:()=>Promise.resolve({})}), console:{log(){}}};
    const actualSource=originalController ? fs.readFileSync('dash.js/src/streaming/rules/abr/cmab/CMABAbrController.js','utf8')
        .replace(/CMABAbrController/g,'CMABImprovedController').replace(/^import .*;\r?$/gm,'')
        .replace('export default FactoryMaker.getClassFactory(CMABImprovedController);','module.exports=CMABImprovedController;') : source;
    vm.runInNewContext(actualSource,context);
    const c=context.module.exports.call({context:{}});
    const ladder=[300,450,900,1200,1500,4900,5100,6000].map(b=>({bandwidth:b*1000,width:1024,height:576}));
    const arms=ladder.map((_,i)=>i);
    const runtime={runPython(code){
        if ((code.includes('mab.predict(test)') || code.includes('mab.predict(contexts[-1:])'))) {
            fits++;
            assert.equal(window.js_rewards.length,window.js_selected_arms.length);
            assert.equal(window.js_history.length,window.js_rewards.length+1);
            if (code.includes('mab.predict(contexts[-1:])')) {
                const dim=variant==='scaled'?4:variant==='buffer'?6:9;
                assert.ok(window.js_physical_contexts.every(x=>x.length===dim && x[0]===1 && x.every(Number.isFinite)));
            }
            return variant==='guard' ? 7 : 2;
        }
        return 4;
    }};
    for(let i=0;i<80;i++) {
        if (freshProbe) window.LEO_PROBE={valid:true,ok:true,success_at_s:wall/1000,rtt_ms:40};
        const ctx={buffer_s:.5,audio_bitrate:128,audio_codec:'mp4a',seg_duration:2,stream_id:0,
            video_codec:'avc1',target_latency:3};
        const a=c.getCMABNextQuality(runtime,ctx,ladder,arms,0,300,6000,3,1,8000,new Map(),1);
        assert.ok(Number.isInteger(a)&&a>=0&&a<8);
        if (['delayed','outcome','scaled','buffer','context','seeded','guard','guard_only'].includes(variant)) {
            const request={mediaType:'video',type:'MediaSegment',quality:a,startTime:i*2,url:'segment-'+i};
            c.onRequestStart(request);
            wall+=1000;
            c.onRequestOutcome(request,'complete',3);
            c.onRequestOutcome(request,'complete',3); // duplicate must not create a second row
            if (i%20===0) c.onSeek();
            wall+=1000;
        } else wall+=2000;
    }
    const log=window.__LEO_CMAB_TRACE;
    if (variant==='memory'||variant==='both') assert.ok(Math.max(...log.map(r=>r.slot_history_count))<=31);
    return {fits, log, feedback:window.__LEO_FEEDBACK_TRACE||[], physical:window.js_physical_contexts};
}
const ref=run('reference'), memory=run('memory'), startup=run('startup'), both=run('both');
const actualOriginal=run('reference',true);
assert.deepEqual(Array.from(ref.log,x=>x.action),Array.from(actualOriginal.log,x=>x.action));
assert.equal(ref.fits,actualOriginal.fits,'Reference adapter preserves learned-call schedule');
assert.deepEqual(Array.from(memory.log,x=>x.forced),Array.from(ref.log,x=>x.forced), 'Memory-only retains forced-choice schedule');
assert.ok(startup.fits>ref.fits && both.fits>memory.fits);
assert.ok(memory.log.some(x=>x.slot>0 && x.slot_history_count>7));
assert.equal(startup.log[0].action,4,'Conservative startup chooses highest nominal rate below 8Mbps*0.45');
assert.equal(ref.log[0].action,7);
console.log('PASS: actual-controller history alignment/bounds, factorial isolation, startup and learned branch execution');

for(const variant of ['delayed','outcome']) {
    const result=run(variant);
    assert.ok(result.fits>50,variant+' must train on mature outcomes');
    assert.ok(result.log.every(x=>x.reward===null),'No immediate-choice reward is fed back');
    const accepted=result.feedback.filter(r=>r.accepted);
    const expected=variant==='delayed' ? 1 : Math.log(5)*.7-2;
    assert.ok(Math.abs(accepted[0].reward-expected)<1e-10,'Actual controller first completed reward matches hand calculation');
    assert.equal(new Set(accepted.map(r=>r.decision_id)).size,accepted.length);
}
let now=0;const outcomes=[];const book=Feedback(()=>now,row=>outcomes.push(row));
const request=()=>({mediaType:'video',type:'MediaSegment',quality:2,startTime:10,url:'same-url'});
book.offer({id:'known',action:2,observation:{throughput:1},bitrate:900,reward:(elapsed,latency)=>2-4*Math.max(0,elapsed-1)-.1*(latency-3)*elapsed});
const first=request();book.start(first);now=2000;book.finish(first,'complete',4);book.finish(first,'complete',4);
assert.equal(book.rows.length,1);assert.equal(book.rows[0].reward,-2.2);
book.offer({id:'censored',action:2,observation:{throughput:2},bitrate:900,reward:()=>100});
const second=request();book.start(second);book.seek();book.finish(second,'complete',3);
assert.equal(book.rows.length,1,'Seek/cancel must not invent played quality');
const unmatched=request();book.start(unmatched);book.finish(unmatched,'complete',3);
assert.equal(book.rows.length,1,'Unmatched request cannot borrow another action');
book.offer({id:'failed',action:2,observation:{throughput:3},bitrate:900,reward:()=>100});
const failed=request();book.start(failed);book.finish(failed,'error',3);assert.equal(book.rows.length,1);
for(let i=0;i<40;i++) {book.offer({id:'cap-'+i,action:2,observation:{throughput:i},bitrate:900,reward:()=>i});const r=request();book.start(r);book.finish(r,'complete',3);}
assert.equal(book.rows.length,30);assert.equal(book.rows[0].reward,10);
console.log('PASS: delayed/outcome actual controller and hand-calculated request ledger, duplicates, seek censoring, failures, unmatched identities and rolling cap');

for(const variant of ['scaled','buffer','context','seeded','guard','guard_only']) {
    const result=run(variant);
    if (variant==='guard_only') assert.equal(result.fits,0,'Guard-only never calls learned selection');
    else assert.ok(result.fits>50);
    if (variant==='guard' || variant==='guard_only') assert.ok(result.log.every(r=>r.action<=r.guard_maximum));
    if (variant==='guard') assert.ok(result.log.some(r=>r.guard_override));
    assert.ok(result.feedback.some(r=>r.accepted));
}
console.log('PASS: physical intercept/dimensions/finite features, model/guard isolation and logged action ceilings');

const freshContext=run('context',false,true),missingContext=run('context');
assert.ok(freshContext.physical.every(x=>x[3]===.2 && x[6]===1 && x[7]===0));
assert.ok(missingContext.physical.every(x=>x[3]===0 && x[6]===0 && x[7]===1));
console.log('PASS: valid RTT vs unavailable RTT/age is explicit and numerically distinct');
