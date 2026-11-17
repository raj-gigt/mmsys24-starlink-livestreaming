"""Export validation-selected median-seed actors and native parity fixtures."""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import A2C
from .final_env import ROOT,FinalLiveEnv,final_features
from .export_layers import layer

def main():
    torch.set_num_threads(1)
    selection=json.loads((ROOT/'artifacts/final/training/main-selection.json').read_text());specs={};fixture_count=0
    for kind,record in selection['selected'].items():
        source=ROOT/'artifacts/final/training/main'/f'{kind}-{record["seed"]}'/'selected.zip'
        out=ROOT/'models/final'/kind;out.mkdir(parents=True,exist_ok=True);shutil.copy2(source,out/'checkpoint.zip')
        model=A2C.load(source,device='cpu');state=model.policy.state_dict()
        spec={'input_dim':record['input_count'],'layers':[layer(state,k) for k in ['mlp_extractor.policy_net.0','mlp_extractor.policy_net.2','action_net']],
            'action_bitrates':[300000,450000,900000,1200000,1500000,4900000,5100000,6000000],
            'identity':hashlib.sha256(source.read_bytes()).hexdigest(),'seed':record['seed'],
            'label':'Final player-compatible '+kind+' A2C; median validation seed'}
        specs[kind]=spec;(out/'actor.json').write_text(json.dumps(spec,separators=(',',':')))
        env=FinalLiveEnv('validation',leo=kind=='leo');x,_=env.reset(seed=7100);fixtures=[]
        def append(obs,label):
            obs=json.loads(json.dumps(obs,default=lambda value:value.item()))
            x=final_features(obs,kind=='leo')
            with torch.no_grad():logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(torch.as_tensor(x).unsqueeze(0))).flatten().tolist()
            fixtures.append({'kind':label,'observation':obs,'input':x.tolist(),'logits':logits,'action':int(np.argmax(logits))})
        for i in range(100):
            append(env.raw_obs(),'simulator')
            x,_,_,done,_=env.step(i%8)
            if done:x,_=env.reset()
        from .evidence import load_run
        calibration=json.loads((ROOT/'artifacts/final/calibration/runs.json').read_text())
        for run in calibration:
            if run['fixed_action'] is not None:continue
            data=load_run(run['run_id'])['telemetry.json']
            for decision in data['custom_decisions'][:60]:
                now=decision['at_ms']/1000;obs=dict(decision['observation'])
                history=[r for r in data['probes'] if isinstance(r.get('probe_at_s'),(int,float)) and r['probe_at_s']<=now][-8:]
                health=history[-1] if history else {};stamp=health.get('success_at_s')
                age=max(0,now-stamp) if isinstance(stamp,(int,float)) else 99
                obs.update(probes=[{'rtt_ms':r['rtt_ms'],'age_s':max(0,now-r['probe_at_s']),'ok':r['ok']} for r in history],
                    probe_success_age_s=age,probe_valid=bool(health.get('valid') and health.get('ok') and age<3))
                append(obs,'recorded Chrome input; only past logged probes')
        base=fixtures[0]['observation']
        append({**base,'history':[],'probes':[],'buffer_s':0,'probe_valid':False,'probe_success_age_s':99},'missing startup')
        append({**base,'history':[{'mbps':100,'download_s':30,'age_s':300}]*8,
            'probes':[{'rtt_ms':0,'ok':False,'age_s':30}]*8,'live_latency_s':24,'buffer_s':0,'probe_valid':False,'probe_success_age_s':99},'stale failure')
        append({**base,'buffer_s':12,'live_latency_s':24,'playback_rate':1.17,
            'probes':[{'rtt_ms':1000,'ok':True,'age_s':0}]*8,'probe_valid':True,'probe_success_age_s':0},'bounded extreme')
        (out/'fixtures.json').write_text(json.dumps(fixtures,separators=(',',':')))
        manifest={**record,'checkpoint_path':str((out/'checkpoint.zip').relative_to(ROOT)).replace(chr(92),'/'),
            'normalization':'rl/features.py conventional36; rl/final_env.py final_features appends28 causal LEO coordinates',
            'action_bitrates':spec['action_bitrates'],'inference':'Synchronous Float32 JavaScript, first-index argmax; no async bridge',
            'input_example':fixtures[10],'limitations':['Fluid approximate simulator; final claims require Chrome','Synthetic capacity/outages; RTT does not identify true handovers'],
            'selection_record':'artifacts/final/training/main-selection.json'}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
        fixture_count+=len(fixtures)
    (ROOT/'rl/web/final_models.js').write_text('window.LEO_FINAL_SPECS='+json.dumps(specs,separators=(',',':'))+';\n')
    print('Exported conventional and LEO median-seed actors with',fixture_count,'native fixtures')
if __name__=='__main__':main()
