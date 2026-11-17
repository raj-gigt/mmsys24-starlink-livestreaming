(function(){
    'use strict';
    const kind=new URLSearchParams(location.search).get('neuralVariant');
    if (!kind)return; // Preserve the historical Phase A pilot when explicitly used.
    if (!['conventional','leo'].includes(kind))throw new Error('Unknown neuralVariant');
    const spec=window.LEO_FINAL_SPECS[kind];
    if (!spec || spec.input_dim!==(kind==='leo'?64:36))throw new Error('Final model contract mismatch');
    const started=performance.now();
    for(let i=0;i<24;i++)window.LEO_SYNC_MATH.denseActor(spec,new Float32Array(spec.input_dim));
    Object.assign(window.LEO_ABR,{
        features:obs=>window.LEO_FINAL_FEATURES(obs,kind==='leo'),
        predict:input=>({...window.LEO_SYNC_MATH.denseActor(spec,input),reason:'final-a2c-'+kind}),
        actionBitrates:spec.action_bitrates,
        modelIdentity:{sha256:spec.identity,label:spec.label,kind,seed:spec.seed},
        modelLoadMs:performance.now()-window.__anjanModelLoadStartedMs,
        warmupMs:performance.now()-started,ready:true});
})();
