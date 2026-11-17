"""Check final native/Chrome actions, actual requests and observed callback cost."""
import argparse,hashlib,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from stable_baselines3 import A2C
from rl.final_env import final_features
ROOT=Path(__file__).resolve().parents[1]
def check(run_id):
    torch.set_num_threads(1);raw=ROOT/'artifacts/runs'/run_id;s=json.loads((raw/'summary.json').read_text())
    t=json.loads((raw/'telemetry.json').read_text());kind=s['neural_variant'];checkpoint=ROOT/f'models/final/{kind}/checkpoint.zip'
    model=A2C.load(checkpoint,device='cpu');assert s['model']['sha256']==hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    assert s['model']['kind']==kind and s['shared_probe_active'] is True
    decisions=t['custom_decisions'];assert len(decisions)>=3
    times=[];errors=[];links=0;valid=0
    for d in decisions:
        assert not d['result'].get('fallback'),d['result']
        x=final_features(d['observation'],kind=='leo');np.testing.assert_allclose(x,d['input'],atol=2e-6,rtol=0)
        with torch.no_grad():logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(torch.as_tensor(x).unsqueeze(0))).flatten().numpy()
        error=float(np.max(np.abs(logits-np.asarray(d['result']['logits']))));errors.append(error)
        np.testing.assert_allclose(logits,d['result']['logits'],atol=2e-4,rtol=2e-4)
        assert int(logits.argmax())==d['action'] and 0<=d['action']<8
        times.append(d['duration_ms']);valid+=bool(d['observation']['probe_valid'])
        links+=sum(q['at_ms']<=t['stopped_at_ms'] and q['quality']==d['quality'] and any(r['url']==q['url'] and r['quality']==q['quality'] for r in t['requests']) for q in d['requests'])
    assert links>=2 and valid>0,'No real matched downloads or production probe inputs'
    report={'status':'PASS','run_id':run_id,'kind':kind,'decisions':len(decisions),'matched_completed_request_links':links,
        'valid_probe_decisions':valid,'max_absolute_logit_error':max(errors),'action_agreement':1,
        'complete_decision_p50_p95_p99_ms':np.percentile(times,[50,95,99]).tolist(),'max_decision_ms':max(times),
        'model_assets_cold_load_ms':s['model_assets_cold_load_ms'],'timing_scope':'Observed Chrome114/WSL laptop CPU; no hard preemption or mobile guarantee'}
    out=ROOT/'artifacts/final/neural-browser-checks';out.mkdir(parents=True,exist_ok=True);(out/(run_id+'.json')).write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run_id');args=p.parse_args();print(json.dumps(check(args.run_id),indent=2))
