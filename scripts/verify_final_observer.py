"""Validate a real run's common collector and original-CMAB diagnostic trace."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rl.metrics import evaluate_samples

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('run_id')
    p.add_argument('--require-probes', action='store_true')
    args = p.parse_args()
    folder = ROOT / 'artifacts/runs' / args.run_id
    d = json.loads((folder/'telemetry.json').read_text())
    summary = json.loads((folder/'summary.json').read_text())
    metrics = evaluate_samples(d['samples'], horizon=summary['requested_seconds'])
    assert metrics['quality_attribution_fraction'] > .99, metrics
    assert metrics['played_media_s'] > 10
    assert len(d['requests']) > 4
    starts = [e for e in d['events'] if e['type'] == 'request-start']
    trace = d.get('cmab_decisions', [])
    if summary['algorithm'] == 'abrCMAB':
        assert trace and starts
        for decision in trace:
            assert decision['forced'] == (decision['slot_history_count'] <= 7)
        known = {t['id'] for t in trace}
        assert all(e['decision_id'] in known for e in starts if e['decision_id'])
    if args.require_probes:
        assert any(r['valid'] for r in d['probes']), 'No valid real RTT samples'
    report = {'status': 'PASS', 'run_id': args.run_id, 'metrics': metrics,
              'request_completions': len(d['requests']), 'request_starts': len(starts),
              'starts_with_decision_link': sum(e['decision_id'] is not None for e in starts),
              'ambiguous_candidate_links': sum(e['candidate_decision_count'] > 1 for e in starts),
              'cmab_callback_decisions': len(trace),
              'cmab_learned_decisions': sum(not t['forced'] for t in trace),
              'valid_probe_samples': sum(r['valid'] for r in d.get('probes', [])),
              'scope': 'Instrumentation verification only; not a policy comparison'}
    out = ROOT/'artifacts/final/observer-checks'
    out.mkdir(parents=True, exist_ok=True)
    (out/(args.run_id+'.json')).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
