"""Check real request/outcome identity and duplicate/censoring accounting."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('run_id');args=p.parse_args()
d=json.loads((ROOT/'artifacts/runs'/args.run_id/'telemetry.json').read_text())
f=d['feedback'];starts={r['request_id']:r for r in f if r['type']=='request-start'}
ends=[r for r in f if r['type']=='request-outcome'];accepted=[r for r in ends if r['accepted']]
assert starts and accepted, 'No linked real completed outcomes'
assert len({r['request_id'] for r in ends})==len(ends), 'Duplicate request updates'
assert len({r['decision_id'] for r in accepted})==len(accepted), 'A choice trained twice'
known={r['id']:r for r in d['cmab_decisions']}
for r in accepted:
    s=starts[r['request_id']];choice=known[r['decision_id']]
    assert r['outcome']=='complete' and r['epoch']==s['epoch']
    assert choice['action']==s['quality'] and choice['at_ms']<=s['start_ms']<=r['at_ms']
    assert math.isfinite(r['reward']) and r['elapsed_s']>=0
    assert any(q['url']==s['url'] and q['quality']==s['quality'] for q in d['requests'])
assert all(r['reward'] is None for r in ends if not r['accepted'])
report={'status':'PASS','run_id':args.run_id,'starts':len(starts),'settled':len(ends),
    'accepted':len(accepted),'linked_start_fraction':sum(s['decision_id'] is not None for s in starts.values())/len(starts),
    'outcomes':dict(Counter(r['outcome'] for r in ends)),
    'limitation':'Censored/unmatched transfers are not trained. Reward is a request-completion proxy, not played quality or causal segment-level stall attribution.'}
out=ROOT/'artifacts/final/feedback-checks';out.mkdir(parents=True,exist_ok=True)
(out/(args.run_id+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
