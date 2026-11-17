"""Check deployed CMAB input/action contracts and decision cost from real logs."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('ledger');args=p.parse_args()
rows=json.loads(Path(args.ledger).read_text());reports=[]
for row in rows:
    if row.get('status')!='complete':continue
    d=json.loads((ROOT/'artifacts/runs'/row['run_id']/'telemetry.json').read_text())
    trace=d['cmab_decisions'];variant=row.get('variant')
    physical=variant in ['scaled','buffer','context','seeded','guard','guard_only']
    dims=4 if variant=='scaled' else 6 if variant=='buffer' else 9
    for r in trace:
        assert isinstance(r['action'],int) and 0<=r['action']<8
        if 'duration_ms' in r:assert r['duration_ms']>=0 and math.isfinite(r['duration_ms'])
        if physical:
            x=r['model_input'];assert len(x)==dims and x[0]==1 and all(math.isfinite(v) for v in x)
            if dims==9:
                assert x[6] in [0,1] and 0<=x[7]<=1
                if not r['observation']['probe_valid']:assert x[3]==0 and x[6]==0
        if variant in ['guard','guard_only']:
            assert r['action']<=r['guard_maximum']
            if variant=='guard':assert r['action']==min(r['proposal'],r['guard_maximum'])
            else:assert r['selection_source']=='guard-only' and r['action']==r['guard_maximum']
    times=[r['duration_ms'] for r in trace if 'duration_ms' in r]
    reports.append({'run_id':row['run_id'],'variant':variant,'decisions':len(trace),
        'learned_calls':sum(r.get('selection_source')=='LinTS' if 'selection_source' in r else not r['forced'] for r in trace),
        'guard_overrides':sum(r.get('guard_override',False) for r in trace),
        'invalid_probe_calls':sum(not r['observation'].get('probe_valid',True) for r in trace) if variant!='original' else None,
        'median_ms':float(np.median(times)) if times else None,'p95_ms':float(np.percentile(times,95)) if times else None, 'max_ms':max(times) if times else None})
report={'status':'PASS','scope':'Contract and observed synchronous cost; not a hard timing guarantee','runs':reports}
output=Path(args.ledger).parent/'input-checks.json';output.write_text(json.dumps(report,indent=2))
print(json.dumps({'status':'PASS','verified_sessions':len(reports),'decisions':sum(r['decisions'] for r in reports)}))
