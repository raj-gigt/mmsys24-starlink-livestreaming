"""Short real-browser deployment validation; never opens final test cases."""
from argparse import Namespace
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_trial import run
from check_final_browser import check
from rl.metrics import evaluate_samples
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'artifacts/final/validation/neural-v1';out.mkdir(parents=True,exist_ok=True)
ledger=out/'runs.json';rows=json.loads(ledger.read_text()) if ledger.exists() else []
manifest=ROOT/'configs/final/workloads/validation.json';cases=json.loads(manifest.read_text())['cases']
for family in ['steady_bandwidth','rtt_variation','post_handover_recovery']:
    case=next(c for c in cases if c['family']==family)
    for kind in ['conventional','leo']:
        key=family+':'+kind
        if any(r['key']==key for r in rows):continue
        args=Namespace(algorithm='abrAnjanRL',neural_variant=kind,variant=None,seconds=case['seconds'],target=3,
            stages='',catchup='liveCatchupModeLoLP',fixed_kbps=-1,align_minute=True,local_clock=True,
            final_telemetry=True,scenario=str(manifest),case=case['id'],allow_test=False,allow_poor_playback=True)
        with (out/(family+'-'+kind+'.log')).open('w') as log:
            with redirect_stdout(log):s=run(args)
        check(s['run_id']);d=json.loads((ROOT/'artifacts/runs'/s['run_id']/'telemetry.json').read_text())
        assert abs((d['stopped_at_ms']-d['started_at_ms'])/1000-d['samples'][-1]['t_s'])<.1,'Observation clock integrity fault'
        assert max(abs((r['epoch_ms']-d['started_at_ms'])/1000-r['t_s']) for r in d['samples'][1:])<.1,'Within-session clock discontinuity'
        row={'key':key,'status':'complete','variant':kind,'case_id':case['id'],'family':family,'run_id':s['run_id'],'metrics':evaluate_samples(d['samples'],horizon=case['seconds'])}
        rows.append(row);ledger.write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
print('COMPLETE: six real neural deployment checks')
