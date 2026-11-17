"""Sequential, resumable paired browser development cases; never opens test data."""
import argparse
from argparse import Namespace
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import random
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser_trial import run, docker
from rl.metrics import evaluate_samples

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='memory-startup-v1')
    parser.add_argument('--variants', default='original,memory,startup,both')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--families', default='steady_bandwidth,bandwidth_variation,post_handover_recovery')
    args = parser.parse_args()
    manifest = ROOT/'configs/final/workloads/development.json'
    cases = [c for c in json.loads(manifest.read_text())['cases'] if c['family'] in args.families.split(',')]
    assert cases and all(c['role'] == 'development' for c in cases)
    sources = ['CMABAbrController.js', 'CMABImprovedController.js', 'CMABRule.js', 'CMABImprovedRule.js', 'CMABFeedback.js', 'CMABRuntime.js', '../NetworkObservations.js']
    base = ROOT/'dash.js/src/streaming/rules/abr/cmab'
    identity = {p: sha(base/p) for p in sources}
    # Verify the running image includes exactly the intended controller code.
    for path, expected in identity.items():
        actual = docker('exec', 'leo_abr_rl-dashjs-1', 'sha256sum', '/dash.js/src/streaming/rules/abr/cmab/'+path).split()[0]
        assert actual == expected, f'Rebuild player before measuring: {path}'
    fingerprint = hashlib.sha256(json.dumps({'sources': identity,'manifest':sha(manifest),'observer':sha(ROOT/'rl/web/telemetry.js'),'runner':sha(ROOT/'scripts/browser_trial.py')},sort_keys=True).encode()).hexdigest()
    out = ROOT/'artifacts/final/development'/args.name
    out.mkdir(parents=True, exist_ok=True)
    ledger = out/'runs.json'
    rows = json.loads(ledger.read_text()) if ledger.exists() else []
    for repeat in range(args.repeats):
        for case_index, case in enumerate(cases):
            variants = args.variants.split(',')
            random.Random(8000+repeat*100+case_index).shuffle(variants)
            for variant in variants:
                key = f'{fingerprint}:{case["id"]}:{variant}:{repeat}'
                if any(r['key']==key and r['status']=='complete' for r in rows):
                    continue
                trial = Namespace(algorithm='abrCMAB' if variant=='original' else 'abrCMABImproved',
                    variant=None if variant=='original' else variant,seconds=case['seconds'],stages='',target=3,
                    catchup='liveCatchupModeLoLP',align_minute=True,final_telemetry=True,
                    scenario=str(manifest),case=case['id'],allow_test=False,allow_poor_playback=True)
                output = io.StringIO()
                began = datetime.now(timezone.utc).isoformat()
                with contextlib.redirect_stdout(output):
                    summary = run(trial)
                (out/f'{case["id"]}-{variant}-{repeat}.log').write_text(output.getvalue(),encoding='utf-8')
                raw = ROOT/'artifacts/runs'/summary['run_id']
                telemetry = json.loads((raw/'telemetry.json').read_text())
                metrics = evaluate_samples(telemetry['samples'],horizon=case['seconds'])
                assert metrics['quality_attribution_fraction']>.99
                assert telemetry['cmab_decisions'], 'Controller never became active'
                if variant!='original':
                    assert {d['variant'] for d in telemetry['cmab_decisions']}=={variant}
                row = {'key':key,'status':'complete','case_id':case['id'],'family':case['family'],
                       'variant':variant,'repeat':repeat,'run_id':summary['run_id'],'source_identity':identity,
                       'began_utc':began,'completed_utc':datetime.now(timezone.utc).isoformat(),
                       'metrics':metrics,'decisions':len(telemetry['cmab_decisions']),
                       'outcome':'poor_playback' if summary['played_advance_s']<=5 else 'played',
                       'learned':sum(d.get('selection_source')=='LinTS' if 'selection_source' in d else not d['forced'] for d in telemetry['cmab_decisions'])}
                rows.append(row)
                ledger.write_text(json.dumps(rows,indent=2))
                print(json.dumps({k:row[k] for k in ['case_id','variant','run_id','decisions','learned']} |
                    {'qoe':metrics['qoe_per_wall_s'],'stall_s':metrics['stall_s'],'latency_s':metrics['mean_live_latency_s']}),flush=True)
    print('COMPLETE',len(rows),'verified development sessions',flush=True)


if __name__ == '__main__':
    main()
