"""Versioned controlled workloads; preserve Phase A manifests and sealed roles."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ['steady_bandwidth', 'bandwidth_variation', 'rtt_variation',
            'handover_interruption', 'post_handover_recovery', 'mixed_shifted']


def stream_roundtrips(path):
    decoder = json.JSONDecoder()
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if '"round_trips": [' in line:
                break
        buffer = ''
        while True:
            buffer = buffer.lstrip(' \r\n\t,')
            if buffer.startswith(']'):
                return
            try:
                row, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk = f.read(65536)
                if not chunk:
                    raise ValueError('Incomplete RTT archive')
                buffer += chunk
                continue
            yield row
            buffer = buffer[end:]


def load_victoria():
    target = ROOT/'data/processed/final/victoria-1hz.npz'
    if target.exists():
        return dict(np.load(target))
    source = ROOT/'data/raw/lens/victoria-irtt-20251114-1900.json.gz'
    expected = json.loads((ROOT/'data/manifests/lens-reserve.json').read_text())['sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    bins = [[] for _ in range(3600)]
    first = None
    count = 0
    for row in stream_roundtrips(source):
        stamp = row['timestamps']['client']['send']['wall']
        if first is None:
            first = stamp
        index = int((stamp-first)/1e9)
        if 0 <= index < 3600:
            value = row.get('delay', {}).get('rtt', 0)/1e6
            if value > 0:
                bins[index].append(value)
        count += 1
    assert count > 300000
    carrier = 100.
    rtt, observed = [], []
    for values in bins:
        if values:
            carrier = float(np.median(values))
        rtt.append(carrier)
        observed.append(bool(values))
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, rtt_ms=rtt, rtt_observed=observed)
    return dict(np.load(target))


def make_case(role, family, source, lower, upper, seed, seconds):
    rng = np.random.default_rng(seed)
    offset = int(rng.integers(lower, upper-seconds+1))
    measured = source['rtt_ms'][offset:offset+seconds]
    observed = source['rtt_observed'][offset:offset+seconds]
    capacity = np.full(seconds, 8.)
    rtt = np.full(seconds, 40.)
    loss = np.zeros(seconds)
    event = 30 if seconds == 90 else int(rng.integers(35, 56))
    if family == 'steady_bandwidth':
        capacity[:] = float(rng.choice([1.5, 3., 8.]))
    if family in ['bandwidth_variation', 'mixed_shifted']:
        capacity[event:event+25] = float(rng.choice([.8, 1., 1.5]))
        capacity[event+25:] = 6.
    if family in ['rtt_variation', 'handover_interruption', 'post_handover_recovery', 'mixed_shifted']:
        rtt = measured.copy()
    if family == 'rtt_variation':
        rtt[event:event+20] += 120.
    if family in ['handover_interruption', 'post_handover_recovery', 'mixed_shifted']:
        outage = int(rng.integers(2, 5))
        capacity[event:event+outage] = 0.
        if family in ['post_handover_recovery', 'mixed_shifted']:
            end = event+outage
            capacity[end:end+20] = np.linspace(.5, 8., 20)
    stages = []
    last = None
    for t in range(seconds):
        values = (float(capacity[t]), round(float(rtt[t]), 1), float(loss[t]))
        if values != last:
            stages.append({'at_s': t, 'rate_mbit': values[0], 'delay_ms': values[1], 'loss_percent': values[2]})
            last = values
    return {'id': f'{role}-{family}-{seed}', 'role': role, 'family': family, 'seed': seed,
            'seconds': seconds, 'source_window_s': [offset, offset+seconds],
            'network_kind': 'synthetic capacity/outages; measured RTT window or declared constant/augmented delay',
            'probe_observed_fraction': float(np.mean(observed)),
            'policy_may_read_future_profile': False, 'stages': stages}


def main():
    sey = dict(np.load(ROOT/'data/processed/rtt-1hz.npz'))
    vic = load_victoria()
    roles = {'development': [], 'validation': [], 'test': [], 'reserve': []}
    for i, family in enumerate(FAMILIES):
        for role, lo, hi, seed in [('development', 0, 2088, 4100), ('validation', 2148, 2844, 5100)]:
            case = make_case(role, family, sey, lo, hi, seed+i, 90)
            case['recording_id'] = 'seychelles-20240130-0100'
            roles[role].append(case)
        if family == 'mixed_shifted':
            continue
        for role, limits, seed in [('test', [(2904, 3240), (0, 1500)], 6100),
                                   ('reserve', [(3300, 3600), (1800, 3600)], 7100)]:
            for source_index, (source, bounds) in enumerate(zip([sey, vic], limits)):
                case = make_case(role, family, source, *bounds, seed+i*10+source_index, 120)
                case['recording_id'] = ['seychelles-20240130-0100', 'victoria-20251114-1900'][source_index]
                roles[role].append(case)
    folder = ROOT/'configs/final/workloads'
    folder.mkdir(parents=True, exist_ok=True)
    for role, cases in roles.items():
        for case in cases:
            times = [r['at_s'] for r in case['stages']]
            assert times[0] == 0 and times == sorted(set(times))
            assert all(0 <= r['delay_ms'] <= 10000 for r in case['stages'])
        obj = {'version': 2, 'role': role, 'cases': cases,
               'independent_RTT_recordings': 2 if role in ['test', 'reserve'] else 1,
               'test_rule': 'No performance inspection until policies/selection protocol frozen',
               'limitation': 'Related windows and synthetic channels are not independent measured full-link sessions'}
        (folder/(role+'.json')).write_text(json.dumps(obj, indent=2), encoding='utf-8')
    print(json.dumps({role: len(cases) for role, cases in roles.items()}))


if __name__ == '__main__':
    main()
