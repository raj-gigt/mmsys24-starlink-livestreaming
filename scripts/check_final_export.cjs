const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path'),root=path.resolve(__dirname,'..');
global.window=global;global.LEO_ABR={};
for(const file of ['policy_core.js','sync_actor.js','final_core.js','final_models.js'])
 vm.runInThisContext(fs.readFileSync(path.join(root,'rl/web',file),'utf8'));
let maximum=0,count=0;
for(const kind of ['conventional','leo']){
 const spec=LEO_FINAL_SPECS[kind];
 for(const fixture of JSON.parse(fs.readFileSync(path.join(root,'models/final',kind,'fixtures.json')))){
  const x=Array.from(LEO_FINAL_FEATURES(fixture.observation,kind==='leo'));
  assert(x.length===spec.input_dim);x.forEach((v,i)=>assert(Math.abs(v-fixture.input[i])<2e-6));
  const result=LEO_SYNC_MATH.denseActor(spec,x);
  assert(result.action===fixture.action,'Native/JS argmax mismatch');
  result.logits.forEach((v,i)=>{const err=Math.abs(v-fixture.logits[i]);maximum=Math.max(maximum,err);assert(err<2e-4*(1+Math.abs(fixture.logits[i])));});count++;
 }
 assert.throws(()=>LEO_SYNC_MATH.denseActor(spec,[]));
 assert.throws(()=>LEO_SYNC_MATH.denseActor(spec,new Array(spec.input_dim).fill(NaN)));
}
const report={status:'PASS',fixtures:count,max_absolute_logit_error:maximum,scope:'Native/JS preprocessing, logits, actions and invalid-input rejection'};
fs.writeFileSync(path.join(root,'artifacts/final/neural-export-check.json'),JSON.stringify(report,null,2));console.log(report);
