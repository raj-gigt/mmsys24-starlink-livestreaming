// Execute the actual controller with deterministic clock/runtime substitutes.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const path = 'dash.js/src/streaming/rules/abr/cmab/CMABImprovedController.js';
const source = fs.readFileSync(path, 'utf8').replace(/^import .*;\r?$/gm, '')
    .replace('export default FactoryMaker.getClassFactory(CMABImprovedController);', 'module.exports=CMABImprovedController;');
function run(variant, originalController=false) {
    let wall = Date.UTC(2026,10,17), fits=0;
    class Clock extends Date {constructor(...a) {super(...(a.length?a:[wall]));} static now(){return wall;}}
    const window = {location:{search:'?cmabVariant='+variant}};
    const context = {window, Date:Clock, Map, URLSearchParams, module:{exports:{}}, FactoryMaker:{},
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
        if (code.includes('mab.predict(test)')) {
            fits++;
            assert.equal(window.js_rewards.length,window.js_selected_arms.length);
            assert.equal(window.js_history.length,window.js_rewards.length+1);
            return 2;
        }
        return 4;
    }};
    for(let i=0;i<80;i++) {
        const ctx={buffer_s:.5,audio_bitrate:128,audio_codec:'mp4a',seg_duration:2,stream_id:0,
            video_codec:'avc1',target_latency:3};
        const a=c.getCMABNextQuality(runtime,ctx,ladder,arms,0,300,6000,3,1,8000,new Map(),1);
        assert.ok(Number.isInteger(a)&&a>=0&&a<8);
        wall+=2000;
    }
    const log=window.__LEO_CMAB_TRACE;
    if (variant==='memory'||variant==='both') assert.ok(Math.max(...log.map(r=>r.slot_history_count))<=31);
    return {fits, log};
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
