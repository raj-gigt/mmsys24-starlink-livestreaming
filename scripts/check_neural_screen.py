"""Verify all equal-budget screening runs and their checkpoint selection."""
import csv,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'artifacts/final/training';records=[]
expected={(k,c,s) for k in ['conventional','leo'] for c in ['a','b','c','d'] for s in [11,29]}
for p in sorted((base/'screen').glob('*/manifest.json')):
    r=json.loads(p.read_text());curve=json.loads((p.parent/'curve.json').read_text());ev=json.loads((p.parent/'selected-validation.json').read_text())
    assert r['steps']>=250000 and r['requested_steps']==250000
    assert all(math.isfinite(x['validation_qoe']) and math.isfinite(x['gradient_l2']) for x in curve)
    assert curve[-1]['optimizer_updates']>0 and curve[0]['actor_parameter_sha256']!=curve[-1]['actor_parameter_sha256']
    best=max(curve,key=lambda x:x['validation_qoe']);assert best['steps']==r['selected_step'] and best['validation_qoe']==r['selected_validation_qoe']
    assert hashlib.sha256((p.parent/'selected.zip').read_bytes()).hexdigest()==r['checkpoint_sha256']
    assert ev['mean_played_s']>90 and len(ev['action_counts'])>1
    records.append({'kind':r['kind'],'config':r['config'],'seed':r['seed'],'steps':r['steps'],
        'initial_qoe':curve[0]['validation_qoe'],'selected_qoe':r['selected_validation_qoe'],
        'rl_gain':r['selected_validation_qoe']-curve[0]['validation_qoe'],'selected_step':r['selected_step'],'wall_s':r['wall_s']})
assert {(r['kind'],r['config'],r['seed']) for r in records}==expected
selection=json.loads((base/'screen-selection.json').read_text());scores={c:sum(r['selected_qoe'] for r in records if r['config']==c)/4 for c in ['a','b','c','d']}
assert selection['selected']==max(scores,key=scores.get)
report={'status':'PASS','runs':16,'interactions':sum(r['steps'] for r in records),'selected_common_recipe':selection['selected'],
    'joint_scores':scores,'all_improve_own_initialization':all(r['rl_gain']>0 for r in records),'records':records}
(base/'screen-checks.json').write_text(json.dumps(report,indent=2))
out=ROOT/'reports/final/tables'
with (out/'T8-neural-screen.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
