/* Causal final feature extension; conventional preprocessing is unchanged. */
(function(root){
    'use strict';
    const clip=(x,a,b)=>Math.max(a,Math.min(b,Number.isFinite(x)?x:a));
    function features(obs,leo){
        const base=Array.from(root.LEO_ABR.core.features(obs));
        if (!leo)return Float32Array.from(base);
        const h=(obs.probes||[]).slice(-8);
        for(let i=0;i<8;i++){
            const r=h[i-(8-h.length)];
            base.push(r&&r.ok?clip(r.rtt_ms/200,0,5):0,r?clip(r.age_s/4,0,1):1,r&&r.ok?1:0);
        }
        base.push(clip(obs.live_latency_s/3,0,8),clip((obs.probe_success_age_s??99)/3,0,1),
            obs.probe_valid?1:0,h.length?h.filter(r=>!r.ok).length/h.length:1);
        return Float32Array.from(base);
    }
    root.LEO_FINAL_FEATURES=features;
})(typeof window!=='undefined'?window:globalThis);
