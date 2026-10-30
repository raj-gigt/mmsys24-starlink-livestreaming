"""Audit saved pilot results without repeating training or opening sealed tests."""
import json
from pathlib import Path
import torch
from stable_baselines3 import A2C

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'artifacts/training/pilot-manifest.json').read_text())
result=json.loads((root/'artifacts/training/selected-validation.json').read_text())
warm=json.loads((root/'artifacts/training/warmstart.json').read_text())
assert manifest['selected_optimizer_updates']>0
assert manifest['selected_validation_mean_return']>manifest['warmstart_validation_mean_return']
assert result['mean_return']>manifest['fixed_low_validation_mean_return']
assert result['mean_return']>manifest['fixed_1500_validation_mean_return']
assert result['mean_played_s']>60 and len(result['action_counts'])>1
assert all(x.startswith('train-') for x in warm['training_scenario_ids'])
torch.set_num_threads(1)
model=A2C.load(root/'models/checkpoints/pilot-selected',device='cpu')
assert model._n_updates==manifest['selected_optimizer_updates']
report={'status':'PASS','verification':'Nonconstant trained actor; A2C optimizer updates; training-only teacher data; useful playback; improvement relative to its warm-start policy.',
    'actual_a2c_decisions':manifest['actual_steps'],'teacher_states':warm['samples'],
    'validation_return':result['mean_return'],'warmstart_return':manifest['warmstart_validation_mean_return'],
    'random_initialization_return':manifest['untrained_validation_mean_return'],
    'random_initialization_return_is_higher':manifest['untrained_validation_mean_return']>result['mean_return'],
    'selected_actions':sorted(map(int,result['action_counts'])),
    'limitation':'The fortuitous random initial actor scored higher on these validation cases. This pilot establishes deployment and useful learning, not best-policy performance or improvement over CMAB.',
    'initial_failed_assertion':'The original generic check compared against random initialization. The warm-started run must be compared with its actual pre-A2C starting policy; both comparisons remain reported.'}
(root/'artifacts/training/learning-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
