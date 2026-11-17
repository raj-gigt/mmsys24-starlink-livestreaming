"""Verify five fresh seeds, native assets and honest validation-based selection."""
import hashlib,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'artifacts/final/training';selection=json.loads((base/'main-selection.json').read_text())
expected={(k,s) for k in ['conventional','leo'] for s in [47,71,101,131,167]};records=[]
for p in sorted((base/'main').glob('*/manifest.json')):
    r=json.loads(p.read_text());curve=json.loads((p.parent/'curve.json').read_text());best=max(curve,key=lambda x:x['validation_qoe'])
    assert r['steps']>=r['requested_steps']>=1000000 and r['config']=='d'
    assert r['environment_sha256']==hashlib.sha256((ROOT/'rl/final_env.py').read_bytes()).hexdigest()
    assert r['simulator_config_sha256']==hashlib.sha256((ROOT/'configs/final/simulator.json').read_bytes()).hexdigest()
    assert r['selected_step']==best['steps'] and r['selected_validation_qoe']==best['validation_qoe']
    assert r['checkpoint_sha256']==hashlib.sha256((p.parent/'selected.zip').read_bytes()).hexdigest()
    assert all(math.isfinite(x['gradient_l2']) and math.isfinite(x['validation_qoe']) for x in curve)
    assert curve[0]['actor_parameter_sha256']!=curve[-1]['actor_parameter_sha256'] and curve[-1]['optimizer_updates']>0
    ev=json.loads((p.parent/'selected-validation.json').read_text());assert ev['mean_played_s']>90 and len(ev['action_counts'])>1
    records.append({'kind':r['kind'],'seed':r['seed'],'steps':r['steps'],'selected_step':r['selected_step'],
        'initial_qoe':curve[0]['validation_qoe'],'selected_qoe':r['selected_validation_qoe'],'final_qoe':curve[-1]['validation_qoe'],
        'last3_mean_qoe':float(np.mean([x['validation_qoe'] for x in curve[-3:]])),
        'preceding3_mean_qoe':float(np.mean([x['validation_qoe'] for x in curve[-6:-3]])),
        'wall_s':r['wall_s']})
assert {(r['kind'],r['seed']) for r in records}==expected
for kind in ['conventional','leo']:
    ranked=sorted([r for r in records if r['kind']==kind],key=lambda r:r['selected_qoe'])
    assert selection['selected'][kind]['seed']==ranked[2]['seed']
trend={k:float(np.mean([r['last3_mean_qoe']-r['preceding3_mean_qoe'] for r in records if r['kind']==k])) for k in ['conventional','leo']}
report={'status':'PASS','runs':10,'interactions':sum(r['steps'] for r in records),'total_wall_s':sum(r['wall_s'] for r in records),
    'fresh_seeds':[47,71,101,131,167],'selected_seeds':{k:r['seed'] for k,r in selection['selected'].items()},
    'late_validation_trend':trend,'all_improve_initialization':all(r['selected_qoe']>r['initial_qoe'] for r in records),
    'extension_signal':any(v>.01 for v in trend.values()),'records':records}
(base/'main-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
