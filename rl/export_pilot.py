"""Export only the trained actor and fixed preprocessing/action contract."""
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import torch
from stable_baselines3 import A2C
from .features import features
from .export_reference import layer

ROOT=Path(__file__).resolve().parents[1]

def main():
    torch.set_num_threads(1)
    checkpoint=ROOT/'models/checkpoints/pilot-selected.zip'
    model=A2C.load(checkpoint,device='cpu')
    state=model.policy.state_dict()
    identity=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    spec={'input_dim':36,'layers':[layer(state,k) for k in
        ['mlp_extractor.policy_net.0','mlp_extractor.policy_net.2','action_net']],
        'action_bitrates':[300000,450000,900000,1200000,1500000,4900000,5100000,6000000],
        'identity':identity,'label':'imitation-initialized, A2C-updated integration pilot; one seed'}
    out=ROOT/'rl/web/pilot_model.js'
    out.write_text('window.LEO_PILOT_SPEC='+json.dumps(spec,separators=(',',':'))+';\n')
    (ROOT/'models/pilot').mkdir(parents=True,exist_ok=True)
    shutil.copy2(checkpoint,ROOT/'models/pilot/checkpoint.zip')
    (ROOT/'models/pilot/actor.json').write_text(json.dumps(spec,separators=(',',':')))
    fixtures=[]
    for run in sorted((ROOT/'artifacts/runs').glob('phasea-abrAnjanSimple*/samples.json')):
        decisions=json.loads(run.read_text())[-1]['decisions']
        for decision in decisions:
            obs=decision['observation'];x=features(obs)
            with torch.no_grad():
                tensor=torch.from_numpy(x).unsqueeze(0)
                latent=model.policy.mlp_extractor.forward_actor(tensor)
                logits=model.policy.action_net(latent).flatten().tolist()
            fixtures.append({'observation':obs,'input':x.tolist(),'logits':logits,
                             'action':int(np.argmax(logits)),'kind':'recorded real-player input'})
    base=fixtures[0]['observation']
    for history,buffer in [([],0),([],6),([{'mbps':0,'download_s':30,'age_s':90}],0),
                           ([{'mbps':100,'download_s':.001,'age_s':0}]*8,12)]:
        obs={**base,'history':history,'buffer_s':buffer};x=features(obs)
        with torch.no_grad():logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(torch.from_numpy(x).unsqueeze(0))).flatten().tolist()
        fixtures.append({'observation':obs,'input':x.tolist(),'logits':logits,
                         'action':int(np.argmax(logits)),'kind':'startup/stale/extreme fixture'})
    (ROOT/'artifacts/exports/pilot-fixtures.json').write_text(json.dumps(fixtures,separators=(',',':')))
    training=json.loads((ROOT/'artifacts/training/pilot-manifest.json').read_text())
    manifest={'label':spec['label'],'checkpoint_sha256':identity,'checkpoint_path':'models/pilot/checkpoint.zip','actor_js_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'actor_js_bytes':out.stat().st_size,'input_count':36,'actions':spec['action_bitrates'],
        'architecture':'36 -> 64 ReLU -> 64 ReLU -> 8 logits, deterministic first-index argmax',
        'normalization':'8 chronological rows [throughput_Mbps/10 clipped0..3, download_s/2 clipped0..10, age_s/30 clipped0..1, present]; left-pad [0,0,1,0]; scalars [buffer/target clipped0..4, previous_nominal_bitrate/max_nominal_bitrate, (rate-1)/.17 clipped-1..1, target/6 clipped0..2]',
        'training_status':'Pilot-trained in the minimal live environment; validation selected; sealed test untouched',
        'initialization':{'method':training['initialization'],'teacher_states':training['warmstart_samples'],'a2c_decisions':training['actual_steps']},
        'native_reference':'models/reference/manifest.json; its ten-action checkpoint is not used here',
        'main_thread_budget':{'target_complete_decision_p99_ms':2,'hard_preemption':False,'reason':'A synchronous JS call cannot be interrupted by a timer on the same thread.'},
        'example':fixtures[min(4,len(fixtures)-1)],'fixtures':len(fixtures),
        'inference':'window.LEO_ABR.predict(Array.from(window.LEO_ABR.core.features(observation)))'}
    (ROOT/'models/pilot/manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'identity':identity,'javascript_bytes':out.stat().st_size,'fixtures':len(fixtures)},indent=2))

if __name__=='__main__':main()
