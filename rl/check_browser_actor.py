"""Compare real Chrome decisions with the native checkpoint and audit timing."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import torch
from stable_baselines3 import A2C

root=Path(__file__).resolve().parents[1]
run=Path(sys.argv[1]) if len(sys.argv)>1 else sorted((root/'artifacts/runs').glob('phasea-abrAnjanRL*'))[-1]
summary=json.loads((run/'summary.json').read_text())
final=json.loads((run/'samples.json').read_text())[-1]
torch.set_num_threads(1)
checkpoint=root/'models/pilot/checkpoint.zip'
model=A2C.load(checkpoint,device='cpu')
identity=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
assert summary['model']['sha256']==identity
maximum=0;actions=set()
for decision in final['decisions']:
    assert not decision['result'].get('fallback')
    x=torch.tensor(decision['input'],dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(x)).flatten().numpy()
    maximum=max(maximum,float(np.abs(logits-np.array(decision['result']['logits'])).max()))
    assert int(logits.argmax())==decision['action']
    actions.add(decision['action'])
assert maximum<1e-4 and len(actions)>1
new_times=[d['duration_ms'] for d in final['decisions']]
callback_times=[r['ms'] for r in final['callbacks']]
percentiles=np.percentile(new_times,[50,95,99]).tolist()
report={'status':'PASS','run_id':summary['run_id'],'actual_chrome_decisions':len(new_times),
    'max_absolute_logit_error':maximum,'action_agreement':1,'selected_actions':sorted(actions),
    'complete_new_decision_p50_p95_p99_ms':percentiles,'all_callback_p50_p95_p99_ms':np.percentile(callback_times,[50,95,99]).tolist(),
    'model_cold_assets_and_warmup_ms':summary['model_assets_cold_load_ms'],
    'page_load_to_ready_ms':summary['page_load_to_ready_ms'],
    'target_complete_p99_ms':2,'met_target_on_this_host':percentiles[-1]<2,
    'host':'Chrome 114 inside Selenium container, WSL2, laptop CPU; no mobile-device inference test',
    'scope':'Small playback sample. Timing is preliminary; no hard timer preemption or final-runtime conclusion.'}
(root/'artifacts/exports/browser-parity-and-timing.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
