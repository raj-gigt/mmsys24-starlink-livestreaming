(function () {
    'use strict';
    const spec = window.LEO_PILOT_SPEC;
    if (!spec || !window.LEO_SYNC_MATH || spec.input_dim !== 36 || spec.action_bitrates.length !== 8) {
        throw new Error('Pilot model or inference assets missing');
    }
    const warmupStarted = performance.now();
    for (let i = 0; i < 24; i++) window.LEO_SYNC_MATH.denseActor(spec, new Float32Array(36));
    Object.assign(window.LEO_ABR, {
        predict: input => window.LEO_SYNC_MATH.denseActor(spec, input),
        actionBitrates: spec.action_bitrates,
        modelIdentity: {sha256: spec.identity, label: spec.label},
        modelLoadMs: performance.now() - window.__anjanModelLoadStartedMs,
        warmupMs: performance.now() - warmupStarted,
        ready: true
    });
})();
