/* Synchronous Float32 dense/Conv1d inference; no framework, Promise or network call. */
(function (root) {
    'use strict';
    const f = Math.fround;
    function validate(x, length) {
        if (!x || x.length !== length || !Array.from(x).every(Number.isFinite)) throw new Error('invalid-actor-input');
        return Float32Array.from(x);
    }
    function dense(x, layer, relu) {
        const [rows, cols] = layer.shape;
        x = validate(x, cols);
        const out = new Float32Array(rows);
        for (let i = 0; i < rows; i++) {
            let sum = f(layer.b[i]);
            for (let j = 0; j < cols; j++) sum = f(sum + f(layer.w[i * cols + j] * x[j]));
            out[i] = relu ? Math.max(0, sum) : sum;
        }
        return out;
    }
    function conv1d(x, length, layer) {
        const [outputs, channels, kernel] = layer.shape;
        x = validate(x, channels * length);
        const n = length - kernel + 1;
        if (n <= 0) throw new Error('invalid-convolution-shape');
        const out = new Float32Array(outputs * n);
        for (let o = 0; o < outputs; o++) {
            for (let t = 0; t < n; t++) {
                let sum = f(layer.b[o]);
                for (let c = 0; c < channels; c++) {
                    for (let k = 0; k < kernel; k++) {
                        sum = f(sum + f(layer.w[(o * channels + c) * kernel + k] * x[c * length + t + k]));
                    }
                }
                out[o * n + t] = Math.max(0, sum);
            }
        }
        return {values: out, length: n};
    }
    function argmax(x) {
        let best = 0;
        for (let i = 1; i < x.length; i++) if (x[i] > x[best]) best = i;
        return best;
    }
    function denseActor(spec, input) {
        let x = validate(input, spec.input_dim);
        spec.layers.forEach((layer, i) => { x = dense(x, layer, i < spec.layers.length - 1); });
        return {action: argmax(x), logits: Array.from(x), reason: 'pilot-a2c-argmax'};
    }
    function referenceActor(spec, observation) {
        const extracted = [];
        const intermediates = {};
        for (const [key, length] of [['network_net', 6], ['video_size_net', 10], ['ssim_net', 10]]) {
            const inputKey = {network_net:'network_data',video_size_net:'video_sizes',ssim_net:'ssim_dbs'}[key];
            let current = {values: Float32Array.from(observation[inputKey].flat(Infinity)), length};
            spec.convs[key].forEach(layer => { current = conv1d(current.values, current.length, layer); });
            intermediates[key] = Array.from(current.values);
            extracted.push(...current.values);
        }
        const latent = dense(Float32Array.from(extracted), spec.policy, true);
        const logits = dense(latent, spec.action, false);
        return {action: argmax(logits), logits: Array.from(logits), intermediates, latent: Array.from(latent)};
    }
    const clip01 = x => Math.max(0, Math.min(1, x));
    function referenceInputs(raw) {
        // maguro_env.py's native history/metadata transform (not the dash.js interface).
        const maximum = [25, 3, 20, 15, 10];
        const network = raw.network_history.map((row, i) => row.map((v, j) => clip01(v / maximum[j]))
            .concat([clip01(raw.rebuffer_history.slice(i * 3, i * 3 + 3).reduce((a, b) => a + b, 0) / 3)]));
        const sizes = raw.sizes.map(row => row.map(x => clip01(x / 3)));
        const quality = raw.ssims.map(row => row.map(x => clip01((x > 0 && x < 1 ? -10 * Math.log10(1 - x) : 0) / 25)));
        return {network_data: network, video_sizes: sizes, ssim_dbs: quality};
    }
    const api = {denseActor, referenceActor, referenceInputs, argmax};
    if (typeof module !== 'undefined') module.exports = api;
    if (root) root.LEO_SYNC_MATH = api;
})(typeof window !== 'undefined' ? window : null);
