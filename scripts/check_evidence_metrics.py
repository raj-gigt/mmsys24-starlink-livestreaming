"""Recompute every reported run metric from hash-checked portable raw events."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rl.evidence import load_run
from rl.metrics import evaluate_samples
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('ledgers',nargs='+');args=p.parse_args()
checked=[]
for name in args.ledgers:
    path=Path(name);rows=json.loads(path.read_text());rows=rows['runs'] if isinstance(rows,dict) else rows
    for row in rows:
        if row.get('status')!='complete' or 'metrics' not in row:continue
        payload=load_run(row['run_id']);actual=evaluate_samples(payload['telemetry.json']['samples'],horizon=payload['summary.json']['requested_seconds'])
        for key,value in row['metrics'].items():
            if isinstance(value,(float,int)) and not isinstance(value,bool):
                assert math.isclose(actual[key],value,rel_tol=1e-10,abs_tol=1e-8),(row['run_id'],key,value,actual[key])
            else:assert actual[key]==value,(row['run_id'],key)
        checked.append(row['run_id'])
report={'status':'PASS','runs':checked,'count':len(checked),
    'metrics_source_sha256':hashlib.sha256((ROOT/'rl/metrics.py').read_bytes()).hexdigest(),
    'ledger_sha256':{name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in args.ledgers}}
(ROOT/'artifacts/final/evidence-metric-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':'PASS','recomputed_runs':len(checked)}))
