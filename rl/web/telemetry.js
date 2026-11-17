/* Passive, policy-independent playback collector injected before Load. */
(function () {
    'use strict';
    if (window.LEO_FINAL_COLLECTOR) return;
    const state = {version: 1, samples: [], events: [], requests: [], epoch: 0,
        waiting: true, played: false, quality: null, player: null, timer: null, probes: []};
    const event = (type, data) => state.events.push({type, t_s: (performance.now()-state.start)/1000, ...data});
    function sample() {
        const v = document.querySelector('video'), p = state.player;
        if (!p || !v || state.stopped) return;
        const ladder = p.getBitrateInfoListFor('video') || [];
        const rep = ladder.find(x => x.qualityIndex === state.quality);
        const latency = p.getCurrentLiveLatency();
        const row = {t_s: (performance.now()-state.start)/1000,
            media_s: v.currentTime, paused: state.played && v.paused,
            seeking: v.seeking, seek_epoch: state.epoch,
            waiting: state.waiting, ready_state: v.readyState,
            buffer_s: p.getDashMetrics().getCurrentBufferLevel('video') || 0,
            latency_s: Number.isFinite(latency) ? latency : null,
            rate: v.playbackRate, played_bitrate_bps: rep ? rep.bitrate : null,
            rendered_quality: state.quality,
            rtt: window.LEO_PROBE || null};
        const last = state.samples[state.samples.length-1];
        if (!last) row.t_s = 0;
        if (last && row.t_s === last.t_s) state.samples[state.samples.length-1] = row;
        else state.samples.push(row);
    }
    function bind(player) {
        state.player = player;
        const video = document.querySelector('video');
        ['playing', 'waiting', 'seeking', 'seeked', 'pause', 'loadedmetadata', 'error'].forEach(type => {
            video.addEventListener(type, () => {
                sample();
                if (type === 'playing') {state.waiting = false; state.played = true;}
                if (type === 'waiting') state.waiting = true;
                if (type === 'seeking') state.epoch++;
                event(type, {media_s: video.currentTime});
                sample();
            });
        });
        player.on('qualityChangeRendered', e => {
            if (e.mediaType !== 'video') return;
            sample(); state.quality = e.newQuality;
            event('rendered', {quality: e.newQuality}); sample();
        });
        player.on('fragmentLoadingCompleted', e => {
            const r = e.request;
            if (!r || r.mediaType !== 'video' || r.type !== 'MediaSegment') return;
            state.requests.push({t_s: (performance.now()-state.start)/1000,
                epoch: state.epoch, url: r.url, quality: r.quality,
                representation_id: r.representationId, media_start_s: r.startTime,
                duration_s: r.duration, index: r.index});
        });
        player.on('fragmentLoadingStarted', e => {
            const r = e.request;
            if (!r || r.mediaType !== 'video' || r.type !== 'MediaSegment') return;
            const log = window.__LEO_CMAB_TRACE || window.__anjanDecisionLog || [];
            const now = Date.now();
            const matching = log.filter(d => d.at_ms <= now && now-d.at_ms < 1000 &&
                (d.action === r.quality || d.quality === r.quality));
            event('request-start', {url: r.url, quality: r.quality,
                representation_id: r.representationId, media_start_s: r.startTime,
                decision_id: matching.length ? matching[matching.length-1].id : null,
                candidate_decision_count: matching.length, epoch: state.epoch});
        });
        state.timer = setInterval(sample, 100);
        function probe() {
            if (window.LEO_SHARED_PROBE_ACTIVE) {
                const row=window.LEO_PROBE;
                if (row && (!state.probes.length || row.probe_at_s !== state.probes[state.probes.length-1].probe_at_s)) state.probes.push(row);
                return;
            }
            const abort = new AbortController();
            const timeout = setTimeout(() => abort.abort(), 1000);
            fetch('http://stat-server:8000/ping/details', {signal: abort.signal})
                .then(r => {if (!r.ok) throw new Error('probe-health-http'); return r.json();})
                .then(r => {
                    window.LEO_PROBE = r;
                    if (!state.probes.length || r.probe_at_s !== state.probes[state.probes.length-1].probe_at_s) {
                        state.probes.push(r);
                        window.LEO_PROBE_HISTORY = state.probes.slice(-8);
                    }
                })
                .catch(() => {window.LEO_PROBE = {valid: false, ok: false, age_s: null, error: 'health-unavailable'};})
                .finally(() => clearTimeout(timeout));
        }
        state.probeTimer = setInterval(probe, 500);
        probe();
        sample();
    }
    const original = App.prototype._load;
    App.prototype._load = function () {
        state.start = performance.now(); state.stopped = false;
        const result = original.apply(this, arguments);
        bind(this.player);
        if (window.LEO_FINAL_DURATION_S) setTimeout(() => state.stop(), window.LEO_FINAL_DURATION_S*1000);
        return result;
    };
    state.stop = function () {sample(); state.stopped = true; clearInterval(state.timer); clearInterval(state.probeTimer);};
    window.LEO_FINAL_COLLECTOR = state;
})();
