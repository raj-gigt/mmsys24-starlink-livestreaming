"""Rescore existing events' components, never train or choose test coefficients."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
from select_cmab_final import summarize
ROOT=Path(__file__).resolve().parents[1]
def score(m,stall=4,variation=.3,latency=.1):
    return (m['quality_utility']-stall*m['stall_s']-m['startup_s']-variation*m['variation']-latency*m['latency_area'])/m['duration_s']
def main():
    p=argparse.ArgumentParser();p.add_argument('ledger');args=p.parse_args();path=Path(args.ledger);rows=json.loads(path.read_text())
    for r in rows:assert math.isclose(score(r['metrics']),r['metrics']['qoe_per_wall_s'],abs_tol=1e-8)
    scenarios=[('base',{})]+[(name+'_'+str(factor),{name:base*factor}) for name,base in [('stall',4),('variation',.3),('latency',.1)] for factor in [.5,2]]
    results=[]
    for label,parameters in scenarios:
        changed=deepcopy(rows)
        for r in changed:r['metrics']['qoe_per_wall_s']=score(r['metrics'],**parameters)
        summary=summarize(changed)
        results.append({'setting':label,'parameters':parameters,
            'qoe_per_wall_s':{v:m['qoe_per_wall_s'] for v,m in summary.items()},
            'paired_difference_vs_original':{v:m['qoe_per_wall_s']-summary['original']['qoe_per_wall_s'] for v,m in summary.items()}})
    report={'scope':'One-at-a-time0.5x/2x offline rescore; coefficients never selected from these results','rows':results}
    (path.parent/'score-sensitivity.json').write_text(json.dumps(report,indent=2));print('Rescored7 fixed settings from saved components')
if __name__=='__main__':main()
