'use strict';
const fs=require('node:fs');
const assert=require('node:assert/strict');
const core=require('../rl/web/policy_core.js');
const math=require('../rl/web/sync_actor.js');
const model=JSON.parse(fs.readFileSync('models/pilot/actor.json','utf8'));
const fixtures=JSON.parse(fs.readFileSync('artifacts/exports/pilot-fixtures.json','utf8'));
let error=0,preprocessing=0;
for(const fixture of fixtures){
    const input=core.features(fixture.observation);
    preprocessing=Math.max(preprocessing,...input.map((v,i)=>Math.abs(v-fixture.input[i])));
    const result=math.denseActor(model,input);
    error=Math.max(error,...result.logits.map((v,i)=>Math.abs(v-fixture.logits[i])));
    assert.equal(result.action,fixture.action);
    assert.equal(result instanceof Promise,false);
}
assert.ok(error<1e-4 && preprocessing<1e-6,{error,preprocessing});
assert.throws(()=>math.denseActor(model,[NaN]),/invalid-actor-input/);
assert.throws(()=>math.denseActor(model,Array(36).fill(Infinity)),/invalid-actor-input/);
const report={status:'PASS',fixtures:fixtures.length,recorded_player_fixtures:fixtures.filter(x=>x.kind.startsWith('recorded')).length,
    max_absolute_logit_error:error,max_preprocessing_error:preprocessing,action_agreement:1,
    return_type:'Completed synchronous object',invalid_input:'Rejected',
    scope:'Numerical and interface correctness; not proof of improved browser QoE'};
fs.writeFileSync('artifacts/exports/pilot-parity.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
