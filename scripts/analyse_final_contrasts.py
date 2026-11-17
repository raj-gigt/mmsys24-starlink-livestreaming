"""Direct component comparisons and score-component diagnosis; no test tuning."""
import json
from pathlib import Path
from analyse_final import FAMILIES,paired_summary,csvwrite
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'artifacts/final/evaluation';tables=ROOT/'reports/final/tables'
rows=[r for r in json.loads((folder/'runs.json').read_text()) if r['family'] in FAMILIES]
comparisons={}
for base,candidate,label in [('guard_only','improved','bandit_restart_package_vs_guard_only'),('conventional','leo','leo_vs_conventional')]:
    matched=[{**r,'policy':'original' if r['policy']==base else candidate} for r in rows if r['policy'] in [base,candidate]]
    comparisons[label]={'baseline':base,'candidate':candidate,**paired_summary(matched,candidate)}
csvwrite(tables/'T4-direct-contrasts.csv',[{'comparison':k,**{a:b for a,b in v.items() if a!='cases'}} for k,v in comparisons.items()])
diagnosis=[]
for case in sorted({r['case_id'] for r in rows}):
    pools={p:[r for r in rows if r['case_id']==case and r['policy']==p] for p in ['original','improved']}
    means={}
    for p,pool in pools.items():
        means[p]={name:sum(coef*r['metrics'][metric]/r['metrics']['duration_s'] for r in pool)/len(pool)
            for name,metric,coef in [('quality','quality_utility',1),('stall','stall_s',-4),('startup','startup_s',-1),('variation','variation',-.3),('latency','latency_area',-.1)]}
    parts={k:means['improved'][k]-means['original'][k] for k in means['original']}
    effect=sum(parts.values())
    direct=sum(r['metrics']['qoe_per_wall_s'] for r in pools['improved'])/3-sum(r['metrics']['qoe_per_wall_s'] for r in pools['original'])/3
    assert abs(effect-direct)<1e-10
    diagnosis.append({'case_id':case,'qoe_difference':effect,**{k+'_contribution':v for k,v in parts.items()},'regression':effect<0})
csvwrite(tables/'T4-score-components.csv',diagnosis)
result={'status':'PASS','direct_contrasts':comparisons,'score_components':diagnosis,
    'qualification':'Conditional paired-repeat intervals on fixed cases only. Guard-only also changes restart choices, so the first comparison is not pure removal of learning. No controller or score coefficient changes.'}
(folder/'contrasts.json').write_text(json.dumps(result,indent=2))
print(json.dumps(comparisons,indent=2))
