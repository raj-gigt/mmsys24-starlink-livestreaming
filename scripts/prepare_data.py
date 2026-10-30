"""Inventory supplied measurements and create a reproducible development-only package.

Run with the external Python environment. Do not use playback actions as labels.
Test manifests are produced and audited, but no trainer loads them by default.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ['steady_bandwidth', 'bandwidth_variation', 'rtt_variation',
            'handover_interruption', 'post_handover_recovery', 'mixed_shifted']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')

def main():
    manifest = ROOT / 'data/manifests'
    processed = ROOT / 'data/processed'
    processed.mkdir(parents=True, exist_ok=True)
    raw = ROOT / 'runner/trace/irtt/seychelles-irtt-10ms-1h-2024-01-30-01-00-00.csv'
    derived = ROOT / 'runner/trace/isl-trace.csv'
    original = np.genfromtxt(raw, delimiter=',', names=True)
    replay = np.genfromtxt(derived, delimiter=',', names=True)
    times = (original['timestamp'] - original['timestamp'][0]) / 1e9
    valid = original['rtt'] > 0
    assert len(original) == len(replay) and np.allclose(original['rtt'], replay['rtt'])
    assert np.max(np.abs(times - replay['since'])) < 0.002
    n = int(np.floor(times[-1])) + 1
    bins = np.minimum(times.astype(int), n-1)
    rtt = np.full(n, np.nan)
    loss = np.ones(n)
    for second in range(n):
        ix = bins == second
        present = ix & valid
        if present.any():
            rtt[second] = np.median(original['rtt'][present])
        if ix.any():
            loss[second] = 1 - valid[ix].mean()
    observed = np.isfinite(rtt)
    # Causal last-known carrier value, with explicit observed mask. No zero RTT.
    carrier = rtt.copy()
    last = 100.0  # fixed missing-start default, never fitted using later validation/test values
    for i in range(n):
        if observed[i]: last = carrier[i]
        else: carrier[i] = last
    np.savez_compressed(processed/'rtt-1hz.npz', t_s=np.arange(n), rtt_ms=carrier,
                        rtt_observed=observed, probe_loss_fraction=loss)
    inventory = {'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope':'Local measured RTT plus explicitly synthetic link scenarios; not independent real-session generalization.',
        'sources':[{'path':str(raw.relative_to(ROOT)), 'sha256':sha(raw), 'kind':'measured_probe_RTT',
            'recording_id':'seychelles-20240130-0100', 'timestamp_unit':'ns UTC epoch', 'rtt_unit':'ms',
            'start_utc':datetime.fromtimestamp(original['timestamp'][0]/1e9,timezone.utc).isoformat(),
            'duration_s':float(times[-1]), 'rows':len(original), 'invalid_rtt_rows':int((~valid).sum()),
            'rtt_positive_p5_p50_p95_ms':np.percentile(original['rtt'][valid],[5,50,95]).tolist(),
            'max_sampling_gap_s':float(np.diff(times).max()),
            'license':'Bundled in the upstream GPL-3.0 code repository; original LENS dataset distribution states CC-BY-SA-4.0. Preserve original data attribution.'},
            {'path':str(derived.relative_to(ROOT)), 'sha256':sha(derived), 'kind':'derived_alias',
             'recording_id':'seychelles-20240130-0100', 'not_independent':True,
             'warning':'Original shaper maps non-positive RTT to 100% link loss; this is an emulation convention, not proof of a real outage.'}],
        'throughput_examples':[], 'playback_logs':[],
        'archive':{'path':'paper-data/data', 'kind':'policy-dependent archived outcomes',
                   'git_commit':subprocess.check_output(['git','-C','paper-data','rev-parse','HEAD'],text=True).strip(),
                   'file_count':sum(p.is_file() for p in (ROOT/'paper-data/data').rglob('*'))},
        'semantics':{'probe_loss':'Unanswered probe, never automatically converted into full data-path outage.',
                     'capacity':'Generated link capacity; measured goodput examples remain separate to avoid double-counting RTT/loss.',
                     'actions':'MongoDB decisions are observations of a policy, not supervised optimal-action labels.'}}
    for path in sorted((ROOT/'paper-data/src/throughput/downlink').glob('*iperf*.json')):
        obj = json.loads(path.read_text())
        intervals = [s.get('sum', {}) for s in obj['intervals']]
        rates = np.array([s['bits_per_second']/1e6 for s in intervals])
        record = {'path':str(path.relative_to(ROOT)), 'sha256':sha(path), 'rows':len(intervals),
            'duration_s':float(intervals[-1]['end']), 'value_unit':'Mbit/s',
            'kind':'measured_downlink_goodput_example_not_training_trace',
            'mbps_p5_p50_p95':np.percentile(rates,[5,50,95]).tolist(),
            'reason':'Two short same-day examples retained for diagnostics; no defensible three-way group split.'}
        inventory['throughput_examples'].append(record)
    for path in sorted((ROOT/'paper-data/src/throughput/downlink').glob('*irtt*.json')):
        obj = json.loads(path.read_text())
        inventory['sources'].append({'path':str(path.relative_to(ROOT)), 'sha256':sha(path),
            'kind':'measured_probe_RTT_companion_to_short_iperf_example',
            'probe_count':len(obj.get('round_trips',[])), 'delay_unit':'ns',
            'use':'Diagnostic only; audit exact timestamp overlap before combining channels.'})
    for path in sorted((ROOT/'artifacts/runs').glob('*/summary.json')):
        obj = json.loads(path.read_text())
        inventory['playback_logs'].append({'run_id':obj['run_id'],'algorithm':obj['algorithm'],
            'summary_sha256':sha(path),'kind':'policy-dependent real player measurements',
            'use':'calibration/export parity only; not final sealed evaluation'})
    write(manifest/'sources.json', inventory)
    # Split a single recording chronologically, with two 60s guards, before cropping.
    usable = n-120
    a = int(usable*.6)
    b = a + 60 + int(usable*.2)
    blocks = {'train':(0,a),'validation':(a+60,b),'test':(b+60,n)}
    spec = {'recording_id':'seychelles-20240130-0100','strategy':'chronological blocks with 60-second guards',
            'guard_s':60,'blocks':blocks,'families':FAMILIES,
            'limitation':'All RTT blocks share one recording; separated windows do not create independent locations/days.',
            'test_rule':'Test manifests sealed from training, hyperparameter choice and pilot result selection.'}
    write(manifest/'split-policy.json', spec)
    for split, (lo,hi) in blocks.items():
        rows = []
        count, base = {'train':(8,1000),'validation':(3,2000),'test':(3,3000)}[split]
        for fno,family in enumerate(FAMILIES):
            for rep in range(count):
                seed = base + fno*100 + rep
                rng = np.random.default_rng(seed)
                length = 180
                offset = int(rng.integers(lo, hi-length))
                measured = carrier[offset:offset+length].copy()
                cap = np.full(length, float(rng.choice([0.8,1.5,3,6,10])))
                rtt_values = np.full(length, float(np.median(measured)))
                disruption = np.zeros(length, dtype=bool)
                parameters = {'base_mbps':float(cap[0])}
                if family in ['bandwidth_variation','mixed_shifted']:
                    for j in range(0,length,20):
                        cap[j:j+20] = float(rng.uniform(0.55,11))
                if family in ['rtt_variation','handover_interruption','post_handover_recovery','mixed_shifted']:
                    rtt_values = measured.copy()
                if family in ['handover_interruption','post_handover_recovery','mixed_shifted']:
                    at = int(rng.integers(35,105))
                    duration = int(rng.integers(1,6))
                    cap[at:at+duration] = 0
                    disruption[at:at+duration] = True
                    parameters.update(outage_start_s=at, outage_duration_s=duration)
                    if family in ['post_handover_recovery','mixed_shifted']:
                        recovery = int(rng.integers(10,26))
                        end = at+duration
                        cap[end:end+recovery] *= np.linspace(.15,1,recovery)
                        parameters['recovery_s'] = recovery
                if family == 'mixed_shifted':
                    rtt_values[90:110] += 250
                    parameters['synthetic_extra_rtt_ms'] = 250
                name = f'{split}-{family}-{seed}'
                path = processed/'scenarios'/split/(name+'.npz')
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(path,t_s=np.arange(length),capacity_mbps=cap,rtt_ms=rtt_values,
                    probe_valid=observed[offset:offset+length],
                    probe_loss_fraction=loss[offset:offset+length],synthetic_outage=disruption)
                rows.append({'id':name,'path':str(path.relative_to(ROOT)).replace('\\','/'),
                    'sha256':sha(path),'family':family,'seed':seed,'source_window_s':[offset,offset+length],
                    'recording_id':spec['recording_id'],'split':split,
                    'network_kind':'synthetic_capacity_and_explicit_interruptions_with_measured_RTT_or_its_window_median',
                    'causal_inputs_only':True,'parameters':parameters})
        write(manifest/(split+'.json'), {'split':split,'scenarios':rows,'source_sha256':sha(raw)})
    print(json.dumps({'sources':len(inventory['sources']),'blocks':blocks,
                      'scenario_counts':{'train':48,'validation':18,'test':18},'seconds':n},indent=2))

if __name__ == '__main__': main()
