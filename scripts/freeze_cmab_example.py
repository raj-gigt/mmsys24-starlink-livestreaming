"""Export a real linked decision including its online training state."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rl.evidence import load_run
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--ledger',default='artifacts/final/validation/finalists-v2/runs.json');args=p.parse_args()
    manifest=json.loads((ROOT/'models/final/cmab/manifest.json').read_text());variant=manifest['variant']
    rows=json.loads((ROOT/args.ledger).read_text());example=None
    for row in rows:
        if row['variant']!=variant:continue
        payload=load_run(row['run_id']);d=payload['telemetry.json'];decisions={r['id']:r for r in d['cmab_decisions']}
        accepted=[r for r in d['feedback'] if r.get('accepted')]
        starts={r['request_id']:r for r in d['feedback'] if r['type']=='request-start'}
        for decision in d['cmab_decisions']:
            if decision['selection_source']!='LinTS':continue
            outcome=next((r for r in accepted if r['decision_id']==decision['id']),None)
            prior=[r for r in accepted if r['at_ms']<decision['at_ms']][-30:]
            if outcome is None or len(prior)<8:continue
            request=starts[outcome['request_id']]
            example={'run_id':row['run_id'],'decision_id':decision['id'],'variant':variant,
                'action_bitrates':[300000,450000,900000,1200000,1500000,4900000,5100000,6000000],
                'contexts':[decisions[r['decision_id']]['model_input'] for r in prior],
                'actions':[decisions[r['decision_id']]['action'] for r in prior],
                'rewards':[r['reward'] for r in prior],'input':decision['model_input'],
                'seed':123456,'alpha':1,'expected_proposal':decision['proposal'],
                'guard_maximum':decision['guard_maximum'],'expected_action':decision['action'],
                'actual_completed_request':request['url'],'duration_ms':decision['duration_ms'],
                'qualification':'Online state matters: the9-vector alone is not a stateless classifier input. Rewards are completed-download surrogates, not played QoE.'}
            break
        if example:break
    assert example and len(example['contexts'])==len(example['actions'])==len(example['rewards'])
    path=ROOT/'models/final/cmab/example-state.json';path.write_text(json.dumps(example,indent=2))
    print('Exported real',len(example['actions']),'row online history and linked input/action from',example['run_id'])
if __name__=='__main__':main()
