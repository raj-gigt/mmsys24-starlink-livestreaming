"""Pretraining fixed-policy browser comparison; no held-out performance access."""
from argparse import Namespace
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_trial import run
from rl.metrics import evaluate_samples
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'artifacts/final/calibration';out.mkdir(parents=True,exist_ok=True)
ledger=out/'runs.json';rows=json.loads(ledger.read_text()) if ledger.exists() else []
plans=[('steady_bandwidth',a) for a in [0,4,7,None]]+[('handover_interruption',a) for a in [0,None]]
cases=json.loads((ROOT/'configs/final/workloads/development.json').read_text())['cases']
for family,action in plans:
    key=f'{family}-{action}'
    if any(r['key']==key for r in rows):continue
    case=next(c for c in cases if c['family']==family)
    args=Namespace(algorithm='abrAnjanSimple',variant=None,seconds=case['seconds'],stages='',target=3,
        catchup='liveCatchupModeLoLP',align_minute=True,local_clock=True,final_telemetry=True,
        scenario=str(ROOT/'configs/final/workloads/development.json'),case=case['id'],allow_test=False,
        fixed_kbps=[300,450,900,1200,1500,4900,5100,6000][action] if action is not None else -1,
        allow_poor_playback=True)
    with (out/(key+'.log')).open('w') as log:
        with redirect_stdout(log):summary=run(args)
    t=json.loads((ROOT/'artifacts/runs'/summary['run_id']/'telemetry.json').read_text())
    assert summary['actual_abr_strategy']=='abrAnjanSimple'
    if action is not None:
        assert summary['auto_switch_video'] is False
        assert t['requests'] and {r['quality'] for r in t['requests']}=={action},'Fixed-rate calibration did not hold the requested representation'
    rows.append({'key':key,'run_id':summary['run_id'],'status':'complete','case_id':case['id'],
        'family':family,'fixed_action':action,'metrics':evaluate_samples(t['samples'],horizon=case['seconds'])})
    ledger.write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
print('COMPLETE: six browser calibration sessions')
