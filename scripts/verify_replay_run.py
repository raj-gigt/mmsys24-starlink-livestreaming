"""Verify actual applied schedule, playback horizon and derived plot compatibility."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rl.metrics import evaluate_samples
from plot_run_timeline import plot_run

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('run_id')
    p.add_argument('--repair-plot-summary', action='store_true')
    args = p.parse_args()
    folder = ROOT/'artifacts/runs'/args.run_id
    scenario = json.loads((folder/'scenario.json').read_text())
    applied = json.loads((folder/'applied-profile.json').read_text())['applied']
    summary = json.loads((folder/'summary.json').read_text())
    if args.repair_plot_summary and isinstance(summary['controlled_stages'], dict):
        (folder/'summary.before-plot-fix.json').write_bytes((folder/'summary.json').read_bytes())
        summary['controlled_stages'] = [{'at_s': r.get('relative_s', 0),
            'rate_mbit': r['rate_mbit'], 'delay_ms': r['delay_ms'], 'loss_percent': r['loss_percent']}
            for r in applied]
        summary['diagnostic_plot_fix'] = 'Converted saved applied-profile envelope to timeline stage rows; original preserved'
        (folder/'summary.json').write_text(json.dumps(summary, indent=2))
    errors = []
    for stage in scenario['stages'][1:]:
        rate = stage['rate_mbit'] if stage['rate_mbit'] > 0 else .05
        loss = stage['loss_percent'] if stage['rate_mbit'] > 0 else 100.
        matches = [r for r in applied if r['rate_mbit'] == rate and r['delay_ms'] == stage['delay_ms']
                   and r['loss_percent'] == loss and abs(r['relative_s']-stage['at_s']) < .5]
        assert matches, stage
        errors.append(min(abs(r['relative_s']-stage['at_s']) for r in matches))
    telemetry = json.loads((folder/'telemetry.json').read_text())
    metrics = evaluate_samples(telemetry['samples'], horizon=scenario['seconds'])
    assert summary['played_advance_s'] > 5 and len(telemetry['requests']) >= 3
    assert metrics['quality_attribution_fraction'] > .99
    plot_run(folder)
    report = {'status': 'PASS', 'run_id': args.run_id, 'scenario_id': scenario['id'],
              'verified_transitions': len(errors), 'max_transition_error_s': max(errors, default=0),
              'metrics': metrics, 'plot_generated': True,
              'runner_plot_envelope_repair': 'diagnostic_plot_fix' in summary,
              'scope': 'Development replay verification; no test performance used'}
    (ROOT/'artifacts/final/replay-verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
