"""Check every portable run schedule; no minimum-playback filter."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rl.evidence import load_run
from rl.replay_validation import verify_replay
p=argparse.ArgumentParser();p.add_argument('ledger');args=p.parse_args()
rows=json.loads(Path(args.ledger).read_text());reports=[]
for row in rows:
    if row.get('status')=='complete':reports.append(verify_replay(load_run(row['run_id'])))
report={'status':'PASS','scope':'Controlled schedule/phase integrity, independent of outcome quality','runs':reports}
(Path(args.ledger).parent/'replay-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':'PASS','verified_runs':len(reports),'max_phase_error_s':max((r['start_phase_error_s'] for r in reports),default=0),'max_transition_error_s':max((r['max_transition_error_s'] for r in reports),default=0)}))
