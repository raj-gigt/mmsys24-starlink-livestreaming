const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
(async()=>{
for(const name of ['CMABRule','CMABImprovedRule']) {
 const handlers=new Map();let released=0;
 const events={BUFFER_LOADED:'loaded',BUFFER_EMPTY:'empty',FRAGMENT_LOADING_STARTED:'start',
 FRAGMENT_LOADING_COMPLETED:'complete',FRAGMENT_LOADING_ABANDONED:'abandoned',PLAYBACK_SEEKING:'seek'};
 const factory=()=>({create:()=>({getCMABNextQuality:()=>0,onRequestStart(){},onRequestOutcome(){},onSeek(){}})});
 const sandbox={module:{exports:{}},console:{log(){}},dashjs:{FactoryMaker:{getClassFactoryByName:()=>()=>({create:()=>({})})}},
 FactoryMaker:{},Constants:{},MetricsConstants:{},MediaPlayerEvents:events,
 EventBus:()=>({getInstance:()=>({on:(e,f)=>handlers.set(e,f),off:e=>handlers.delete(e)})}),
 Settings:()=>({getInstance:()=>({get:()=>({streaming:{abr:{cmab:{alpha:1}}}})})}),
 prepareCMABRuntime:()=>Promise.resolve({runPython(){}}),acquireNetworkObservations:()=>()=>released++,
 CMABAbrController:factory,CMABImprovedController:factory};
 let source=fs.readFileSync('dash.js/src/streaming/rules/abr/cmab/'+name+'.js','utf8').replace(/^import .*;\r?$/gm,'')
 .replace('export default FactoryMaker.getClassFactory('+name+');','module.exports='+name+';');
 vm.runInNewContext(source,sandbox);const rule=sandbox.module.exports.call({context:{}},{dashMetrics:{}});
 await Promise.resolve();await Promise.resolve();
 assert.doesNotThrow(()=>{handlers.get('empty')({mediaType:'video'});handlers.get('loaded')({mediaType:'video'});},'Initial buffer must not index an unknown bitrate');
 rule.reset();assert.equal(handlers.size,0);if(name==='CMABImprovedRule')assert.equal(released,1);
}
console.log('PASS: both actual CMAB rules handle initial buffer before first decision and clean up listeners');
})().catch(e=>{console.error(e);process.exitCode=1;});
