/* Causal preprocessing shared by the browser policy and Python parity fixtures. */
(function (root) {
    'use strict';
    const clip = (v, lo, hi) => Math.max(lo, Math.min(hi, Number.isFinite(v) ? v : lo));
    function features(obs) {
        const history = (obs.history || []).slice(-8);
        const x = [];
        for (let i = 0; i < 8; i++) {
            const h = history[i - (8 - history.length)];
            x.push(h ? clip(h.mbps / 10, 0, 3) : 0,
                h ? clip(h.download_s / 2, 0, 10) : 0,
                h ? clip(h.age_s / 30, 0, 1) : 1, h ? 1 : 0);
        }
        const ladder = obs.ladder;
        const max = Math.max(...ladder.map(r => r.bandwidth));
        const previous = ladder.find(r => r.quality === obs.previous_quality);
        x.push(clip(obs.buffer_s / obs.target_s, 0, 4),
            previous ? previous.bandwidth / max : 0,
            clip((obs.playback_rate - 1) / 0.17, -1, 1),
            clip(obs.target_s / 6, 0, 2));
        return Float32Array.from(x);
    }
    function simple(obs) {
        const fresh = (obs.history || []).slice(-4).filter(h => h.age_s < 15 && h.mbps > 0);
        if (!fresh.length) return {action: 0, reason: 'startup-or-stale'};
        const harmonic = fresh.length / fresh.reduce((n, h) => n + 1 / h.mbps, 0);
        const safe = harmonic * (obs.buffer_s < 1 ? 0.45 : 0.78) * 1e6;
        let action = 0;
        obs.ladder.forEach((r, i) => { if (r.bandwidth <= safe) action = i; });
        if (obs.buffer_s < 0.35) action = Math.max(0, action - 1);
        return {action, reason: 'measured-throughput-buffer', safe_bps: safe};
    }
    const core = {features, simple, featureCount: 36, version: 'phase-a-v1'};
    if (typeof module !== 'undefined') module.exports = core;
    if (root) root.LEO_ABR = Object.assign(root.LEO_ABR || {}, {core, ready: true});
})(typeof window !== 'undefined' ? window : null);
