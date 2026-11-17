"""Verify portable final evidence and reproduce the submitted results without Docker.

Run from the repository root: python scripts/reproduce_final.py --saved-results
Only Python/numpy/matplotlib are needed; MongoDB and original run folders are not.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rl.evidence import load_run
from rl.metrics import evaluate_samples
from rl.replay_validation import verify_replay
from rl.decision_validation import check_decisions


def canonical_hash(path):
    data = path.read_bytes()
    if path.suffix.lower() in {'.js','.cjs','.ts','.py','.html','.css','.json','.xml','.txt','.yaml','.yml','.md'} or path.name.startswith('Dockerfile'):
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def check_sources():
    freeze = json.loads((ROOT/'artifacts/final/evaluation/freeze.json').read_text())
    for name, expected in freeze['sources'].items():
        path = ROOT/name
        if not path.is_file() or canonical_hash(path) != expected:
            raise ValueError('Measured source identity differs: '+name)
    return len(freeze['sources'])


def check_models():
    source=(ROOT/'rl/web/final_models.js').read_text().strip()
    assert source.startswith('window.LEO_FINAL_SPECS=') and source.endswith(';')
    specs=json.loads(source.split('=',1)[1][:-1])
    ladder=[300000,450000,900000,1200000,1500000,4900000,5100000,6000000]
    for kind,dim in [('conventional',36),('leo',64)]:
        folder=ROOT/'models/final'/kind
        actor=json.loads((folder/'actor.json').read_text())
        manifest=json.loads((folder/'manifest.json').read_text())
        digest=hashlib.sha256((folder/'checkpoint.zip').read_bytes()).hexdigest()
        assert digest==manifest['checkpoint_sha256']==actor['identity']
        assert actor==specs[kind] and actor['input_dim']==dim and actor['action_bitrates']==ladder
        previous=dim
        for layer,output in zip(actor['layers'],[64,64,8],strict=True):
            assert layer['shape']==[output,previous]
            assert len(layer['w'])==output*previous and len(layer['b'])==output
            assert all(math.isfinite(x) for x in layer['w']+layer['b'])
            previous=output
    return 2


def check_evidence(require_complete=True):
    folder = ROOT/'artifacts/final/evaluation'
    rows = json.loads((folder/'runs.json').read_text())
    freeze_path = folder/'freeze.json'
    freeze = json.loads(freeze_path.read_text())
    digest = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    expected = {f'{digest}:{p["case_id"]}:{p["policy"]}:{p["repeat"]}' for p in freeze['plan']}
    plans={f'{digest}:{p["case_id"]}:{p["policy"]}:{p["repeat"]}':p for p in freeze['plan']}
    keys = [r['key'] for r in rows]
    assert len(keys) == len(set(keys)) and set(keys) <= expected
    if require_complete:
        assert set(keys) == expected and len(rows) == 179, 'Final inventory is incomplete'
    replay = [];decisions=[]
    for row in rows:
        assert row['status'] == 'complete' and row['freeze_sha256'] == digest
        payload = load_run(row['run_id'])  # Checks compressed file hash and run identity.
        telemetry = payload['telemetry.json']
        samples = telemetry['samples']
        duration = (telemetry['stopped_at_ms']-telemetry['started_at_ms'])/1000
        assert telemetry['version'] == 2 and abs(duration-samples[-1]['t_s']) < .1
        assert max(abs((s['epoch_ms']-telemetry['started_at_ms'])/1000-s['t_s']) for s in samples[1:]) < .1
        for name in ['cmab_decisions','custom_decisions','feedback']:
            assert all(e['at_ms'] <= telemetry['stopped_at_ms'] for e in telemetry[name])
        for name in ['events','requests','samples']:
            assert all(e['t_s'] <= duration+.02 for e in telemetry[name])
        actual = evaluate_samples(samples, horizon=payload['summary.json']['requested_seconds'])
        for key, value in row['metrics'].items():
            if isinstance(value, (int,float)) and not isinstance(value,bool):
                assert abs(actual[key]-value) <= 1e-8, (row['run_id'],key)
            else:
                assert actual[key] == value, (row['run_id'],key)
        replay.append(verify_replay(payload))
        decisions.append(check_decisions(payload,plans[row['key']]))
    report = {'status':'PASS', 'verified_sessions':len(rows),
              'inventory_complete':set(keys)==expected, 'freeze_sha256':digest,
              'checks':['exact inventory','compressed hashes','metric recomputation','shared cutoff','dual clock','actual applied schedule and source phase','actual policy/action/input and dense numerical replay','unique request-outcome attribution'],
              'replay_checks':replay,'decision_checks':decisions}
    (folder/'saved-results-check.json').write_text(json.dumps(report,indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-results',action='store_true',help='Require all179 runs, verify and regenerate final results')
    parser.add_argument('--verify-available',action='store_true',help='Verify currently archived complete runs without requiring the full inventory')
    args = parser.parse_args()
    if not (args.saved_results or args.verify_available):
        parser.error('Choose --saved-results or --verify-available')
    count = check_sources()
    models = check_models()
    report = check_evidence(require_complete=args.saved_results)
    print(json.dumps({'status':'PASS','frozen_source_files':count,'verified_models':models,'verified_sessions':report['verified_sessions']}),flush=True)
    if args.saved_results:
        subprocess.run([sys.executable,str(ROOT/'scripts/summarize_final_deployment.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/analyse_final.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/analyse_final_contrasts.py')],cwd=ROOT,check=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/analyse_four_policies.py')],cwd=ROOT,check=True)
        for name in ['plot_final_architecture.py','plot_cmab_ablation.py','plot_cmab_validation.py']:
            subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=ROOT,check=True)
        print('Reproduced full and balanced four-policy analyses, report figures and supporting tables. No Docker or MongoDB used.')


if __name__ == '__main__':
    main()
