'use strict';
const fs = require('node:fs');
const assert = require('node:assert/strict');
const math = require('../rl/web/sync_actor.js');
const model = JSON.parse(fs.readFileSync('models/reference/maguro-actor.json','utf8'));
const fixtures = JSON.parse(fs.readFileSync('artifacts/exports/reference-fixtures.json','utf8'));
let error=0, intermediateError=0, preprocessingError=0, disagreements=0, minMargin=Infinity;
const difference=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
for (const fixture of fixtures) {
    const preprocessed=math.referenceInputs(fixture.raw);
    for (const k of Object.keys(preprocessed)) preprocessingError=Math.max(preprocessingError,
        difference(preprocessed[k].flat(Infinity),fixture.observation[k].flat(Infinity)));
    const result=math.referenceActor(model,preprocessed);
    error=Math.max(error,difference(result.logits,fixture.logits));
    intermediateError=Math.max(intermediateError,difference(result.latent,fixture.latent));
    for(const k of Object.keys(result.intermediates)) intermediateError=Math.max(intermediateError,
        difference(result.intermediates[k],fixture.intermediates[k]));
    if(result.action!==fixture.action)disagreements++;
    const ordered=fixture.logits.slice().sort((a,b)=>b-a);minMargin=Math.min(minMargin,ordered[0]-ordered[1]);
}
assert.ok(error<1e-4 && intermediateError<1e-4,{error,intermediateError});
assert.ok(preprocessingError<1e-10);
assert.equal(disagreements,0);
assert.equal(math.argmax([1,1,0]),0,'Exact ties choose first action, as PyTorch argmax');
assert.equal(math.argmax([1,1.00001,0]),1,'Small resolvable positive margin');
assert.throws(()=>math.referenceActor(model,{network_data:[NaN],video_sizes:[],ssim_dbs:[]}),/invalid-actor-input/);
const report={status:'PASS',fixtures:fixtures.length,max_absolute_logit_error:error,
    max_absolute_intermediate_error:intermediateError,max_preprocessing_error:preprocessingError,
    action_agreement:1,minimum_fixture_top_two_logit_gap:minMargin,
    tie_checks:'First-index exact tie and small positive margin passed',invalid_input:'Rejected',
    scope:'Faithful native-input reference export; not deployed in the eight-action player.'};
fs.writeFileSync('artifacts/exports/reference-parity.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
