"""Faithfully export the pinned Maguro/Puffer actor linked from Plume.

Keep this native 10-action numerical reference separate from the dash.js actor.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import requests
import torch

ROOT=Path(__file__).resolve().parents[1]
PIN='b9c4069a947be0ba3a145ea65c7088e1a5402aea'
BASE=f'https://raw.githubusercontent.com/sagar-pa/abr_rl_test/{PIN}/'
REFERENCE=ROOT/'models/reference'

def layer(state,name):
    return {'shape':list(state[name+'.weight'].shape),
            'w':state[name+'.weight'].flatten().tolist(),'b':state[name+'.bias'].tolist()}

def native_inputs(raw):
    network=np.clip(np.array(raw['network_history'])/np.array([25,3,20,15,10]),0,1)
    reb=np.clip(np.array(raw['rebuffer_history']).reshape(10,3).sum(axis=1,keepdims=True)/3,0,1)
    ssims=np.array(raw['ssims'])
    db=np.where((ssims>0)&(ssims<1),-10*np.log10(np.clip(1-ssims,1e-12,1)),0)
    return {'network_data':np.concatenate([network,reb],axis=1).tolist(),
            'video_sizes':np.clip(np.array(raw['sizes'])/3,0,1).tolist(),
            'ssim_dbs':np.clip(db/25,0,1).tolist()}

def main():
    torch.set_num_threads(1);REFERENCE.mkdir(parents=True,exist_ok=True)
    source=ROOT/'rl/reference';source.mkdir(parents=True,exist_ok=True)
    for filename in ['maguro_model.py','maguro_env.py','utils.py','LICENSE']:
        response=requests.get(BASE+filename,timeout=30);response.raise_for_status()
        target=source/('LICENSE.abr_rl_test' if filename=='LICENSE' else filename)
        target.write_bytes(response.content)
    checkpoint=REFERENCE/'maguro_model.pt'
    if not checkpoint.exists():
        response=requests.get(BASE+'models/maguro_model.pt',timeout=30);response.raise_for_status();checkpoint.write_bytes(response.content)
    digest=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    assert digest=='ed28046faa624b247237b5700bb8e071b8b9000b0d423e785ab1d7aeb4556e09'
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    assert all(torch.isfinite(v).all() for v in state.values())
    spec=importlib.util.spec_from_file_location('pinned_maguro',source/'maguro_model.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    model=module.MaguroModel();model.load_state_dict(state);model.eval()
    exported={'convs':{name:[layer(state,name+'.0'),layer(state,name+'.2')] for name in ['network_net','video_size_net','ssim_net']},
              'policy':layer(state,'policy_net.0'),'action':layer(state,'action_net'),
              'action_count':10,'checkpoint_sha256':digest}
    (REFERENCE/'maguro-actor.json').write_text(json.dumps(exported,separators=(',',':')))
    rng=np.random.default_rng(1221);fixtures=[]
    for i in range(64):
        raw={'network_history':(rng.uniform(0,1,(10,5))*np.array([30,4,25,20,12])).tolist(),
             'rebuffer_history':rng.uniform(0,.4,30).tolist(),
             'sizes':rng.uniform(.01,4,(5,10)).tolist(),
             'ssims':rng.uniform(.5,.999,(5,10)).tolist()}
        if i==0:
            raw={k:np.zeros(np.array(v).shape).tolist() for k,v in raw.items()}
        obs=native_inputs(raw)
        tensors={k:torch.tensor(v,dtype=torch.float32).unsqueeze(0) for k,v in obs.items()}
        with torch.no_grad():
            parts={name:model._modules[name](tensors[key]) for name,key in [('network_net','network_data'),('video_size_net','video_sizes'),('ssim_net','ssim_dbs')]}
            latent=model.policy_net(torch.cat(list(parts.values()),dim=1))
            logits=model.action_net(latent).flatten().tolist()
            action=model(tensors)
        fixtures.append({'raw':raw,'observation':obs,'logits':logits,'action':action,
                         'intermediates':{k:v.flatten().tolist() for k,v in parts.items()},
                         'latent':latent.flatten().tolist()})
    out=ROOT/'artifacts/exports';out.mkdir(parents=True,exist_ok=True)
    (out/'reference-fixtures.json').write_text(json.dumps(fixtures,separators=(',',':')))
    manifest={'label':'Faithful released Maguro/Puffer 10-action forward-pass reference',
        'repository':'https://github.com/sagar-pa/abr_rl_test','commit':PIN,'checkpoint':'models/maguro_model.pt',
        'checkpoint_sha256':digest,'license':'MIT (Sagar Patel 2021); see rl/reference/LICENSE.abr_rl_test',
        'plume_reference_commit':'7dab8ce3961f8627a453bacd447b7b89052a4fa2',
        'provenance':'Plume README links abr_rl_test for Gelato models; exact training run/seed of this old Maguro checkpoint is not stated.',
        'architecture':'3 Conv1d branches -> 256 concatenated features -> Dense256 ReLU -> Dense10',
        'native_inputs':'10x6 normalized past history, 5x10 future segment sizes, 5x10 future SSIM dB',
        'clarification':'The chosen Maguro actor does not use TCP cwnd/RTT fields; other Puffer interfaces expose them. It still needs SSIM/future metadata absent from this player.',
        'deployed_in_player':False,'why':'Eight local representations versus ten native actions; native future SSIM/quality histories unavailable.',
        'fixture_scope':'Synthetic native-format fixtures for numerical correctness, not Puffer evaluation or invented browser observations.'}
    (REFERENCE/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'checkpoint_sha256':digest,'native_fixtures':len(fixtures),'exported_bytes':(REFERENCE/'maguro-actor.json').stat().st_size},indent=2))

if __name__=='__main__':main()
