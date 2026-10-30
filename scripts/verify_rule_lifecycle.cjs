// Test the actual rule with a minimal dash.js context, not a second policy implementation.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const core = require('../rl/web/policy_core.js');
const source = fs.readFileSync('dash.js/src/streaming/rules/abr/anjan/AnjanRule.js', 'utf8')
    .replace(/^import .*;\r?$/gm, '')
    .replace('export default FactoryMaker.getClassFactory(AnjanRule);', 'module.exports = AnjanRule;');
const handlers = new Map();
const bus = {on:(event, fn)=>handlers.set(event, fn), off:event=>handlers.delete(event)};
const events = Object.fromEntries(['PLAYBACK_SEEKING','FRAGMENT_LOADING_STARTED','QUALITY_CHANGE_RENDERED'].map(k=>[k,k]));
const window = {LEO_ABR:{core}, app:{addEvent:()=>{}}};
const ctx = {module:{exports:{}}, window, Date, performance, console,
    FactoryMaker:{}, EventBus:()=>({getInstance:()=>bus}), MediaPlayerEvents:events,
    SwitchRequest:()=>({create:()=>({quality:-1})})};
vm.runInNewContext(source, ctx);
const bitrates = [300,450,900,1200,1500,4900,5100,6000].map(x=>x*1000);
const metrics = {getHttpRequests:()=>requests, getCurrentBufferLevel:()=>2};
let requests = [];
const rules = {getMediaType:()=>'video', getMediaInfo:()=>({bitrateList:bitrates.map((bandwidth,i)=>({bandwidth,id:'rep-'+i}))}),
    getStreamInfo:()=>({id:'stream'}), getAbrController:()=>({getQualityFor:()=>0}),
    getScheduleController:()=>({getPlaybackController:()=>({getLiveDelay:()=>3,getCurrentLiveLatency:()=>3,getPlaybackRate:()=>1}),setTimeToLoadDelay:()=>{}})};
const rule = ctx.module.exports.call({context:{}}, {dashMetrics:metrics,mode:'simple'});
assert.equal(rule.getMaxIndex(rules).quality, 0);
assert.equal(rule.getMaxIndex(rules).quality, 0);
assert.equal(window.__anjanDecisionLog.length, 1, 'Repeated startup callbacks must reuse a decision');
requests = [{type:'MediaSegment',responsecode:200,trequest:new Date(Date.now()-1000),
    _tfinish:new Date(Date.now()-10),trace:[{b:[100000]}],url:'/segment1'}];
assert.equal(rule.getMaxIndex(rules).quality, 1);
assert.equal(rule.getMaxIndex(rules).quality, 1);
assert.equal(window.__anjanDecisionLog.length, 2, 'One decision per completed request context');
handlers.get(events.FRAGMENT_LOADING_STARTED)({request:{type:'InitializationSegment',mediaType:'video'}});
assert.equal(window.__anjanDecisionLog[1].requests.length, 0);
handlers.get(events.FRAGMENT_LOADING_STARTED)({request:{type:'MediaSegment',mediaType:'video',quality:1,representationId:'rep-1',url:'/segment2'}});
assert.equal(window.__anjanDecisionLog[1].requests[0].representation_id, 'rep-1');
handlers.get(events.PLAYBACK_SEEKING)();
assert.equal(rule.getMaxIndex(rules).quality, 0, 'Seek must clear pre-seek throughput context');
assert.equal(window.__anjanDecisionLog[2].epoch, 1);
rule.reset();
assert.equal(handlers.size, 0, 'Reset must remove listeners');
window.LEO_ABR.actionBitrates = bitrates;
window.LEO_ABR.predict = ()=>Promise.resolve({action:7});
const neural = ctx.module.exports.call({context:{}}, {dashMetrics:metrics,mode:'rl'});
assert.equal(neural.getMaxIndex(rules).quality, 0, 'A Promise is not an action');
assert.equal(window.__anjanDecisionLog.at(-1).result.reason, 'invalid-model-action');
neural.reset();
console.log('Actual-rule startup deduplication, request association, init exclusion, seek/reset and asynchronous-result rejection: PASS');
