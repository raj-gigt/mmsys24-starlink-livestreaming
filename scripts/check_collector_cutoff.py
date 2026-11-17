"""Ensure telemetry and decision records share the actual observation cutoff."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('ledger');args=p.parse_args()
root=Path(__file__).resolve().parents[1];rows=json.loads(Path(args.ledger).read_text())
for r in rows:
    d=json.loads((root/'artifacts/runs'/r['run_id']/'telemetry.json').read_text())
    assert d['version']==2
    duration=(d['stopped_at_ms']-d['started_at_ms'])/1000
    assert abs(duration-d['samples'][-1]['t_s'])<.1
    assert all(e['at_ms']<=d['stopped_at_ms'] for key in ['cmab_decisions','custom_decisions','feedback'] for e in d[key])
    assert all(e['t_s']<=duration+.02 for key in ['events','requests','samples'] for e in d[key])
print('PASS: shared cutoff and bounded event/decision horizon for',len(rows),'sessions')
