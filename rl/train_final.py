"""Resumable, equal-budget conventional/LEO A2C research training.

Validation selects checkpoints; no sealed browser/test scenario is imported.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,time,random,pickle
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import A2C
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from .final_env import FinalLiveEnv,ROOT
from .warmstart import teacher_action

CONFIGS={
 'a':dict(learning_rate=3e-5,n_steps=32,ent_coef=.005),
 'b':dict(learning_rate=1e-4,n_steps=32,ent_coef=.005),
 'c':dict(learning_rate=3e-5,n_steps=64,ent_coef=.02),
 'd':dict(learning_rate=1e-4,n_steps=64,ent_coef=.02)}

def evaluate(model,leo=False):
    env=FinalLiveEnv('validation',leo=leo);rows=[];counts=Counter()
    for i,row in enumerate(env.rows):
        x,_=env.reset(seed=7100+i,options={'scenario_id':row['id']});done=False;ret=0
        while not done:
            action=int(model.predict(x,deterministic=True)[0]);counts[action]+=1
            x,r,_,done,info=env.step(action);ret+=r
        rows.append({'id':row['id'],'family':row['family'],'return':ret,
                     'qoe_per_wall_s':ret/env.wall,**env.totals})
    families=sorted({r['family'] for r in rows})
    return {'macro_qoe':float(np.mean([np.mean([r['qoe_per_wall_s'] for r in rows if r['family']==f]) for f in families])),
            'mean_stall_s':float(np.mean([r['stall_s'] for r in rows])),
            'mean_played_s':float(np.mean([r['played_s'] for r in rows])),
            'action_counts':dict(counts),'episodes':rows}

def warmstart(model,leo,seed,samples=8000):
    env=FinalLiveEnv('train',leo=leo);x,_=env.reset(seed=211)
    rng=np.random.default_rng(211);xs=[];ys=[]
    for _ in range(samples):
        a=teacher_action(x[:36]);xs.append(x);ys.append(a)
        x,_,_,done,_=env.step(a if rng.random()<.7 else int(rng.integers(8)))
        if done:x,_=env.reset()
    device=model.device;x=torch.as_tensor(np.array(xs),device=device);y=torch.as_tensor(ys,device=device)
    params=list(model.policy.mlp_extractor.policy_net.parameters())+list(model.policy.action_net.parameters())
    optimizer=torch.optim.Adam(params,lr=1e-3);losses=[]
    # Identical causal teacher samples and conventional information for both.
    for _ in range(10):
        order=rng.permutation(samples);loss_sum=0
        for i in range(0,samples,256):
            b=order[i:i+256];logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(x[b]))
            loss=torch.nn.functional.cross_entropy(logits,y[b]);optimizer.zero_grad();loss.backward();optimizer.step()
            loss_sum+=float(loss.detach().cpu())*len(b)
        losses.append(loss_sum/samples)
    return {'samples':samples,'epochs':10,'teacher':'causal throughput/buffer rule; training scenarios only',
            'teacher_labels':dict(Counter(ys)),'loss':losses}

class Progress(BaseCallback):
    def __init__(self,out,leo,every):
        super().__init__();self.out=out;self.leo=leo;self.every=every;self.next=every;self.rows=[];self.best=-float('inf');self.timer_start=time.perf_counter();self.previous_elapsed=0
    def record(self,steps):
        ev=evaluate(self.model,self.leo)
        row={'steps':steps,'validation_qoe':ev['macro_qoe'],'validation_stall_s':ev['mean_stall_s'],
             'validation_played_s':ev['mean_played_s'],'actions':ev['action_counts'],
             'training_return':float(np.mean([r['r'] for r in self.model.ep_info_buffer])) if self.model.ep_info_buffer else None}
        actor=list(self.model.policy.mlp_extractor.policy_net.parameters())+list(self.model.policy.action_net.parameters())
        flat=torch.cat([p.detach().flatten().cpu() for p in actor]).numpy()
        assert np.isfinite(flat).all(),'Nonfinite actor parameters'
        row.update(actor_parameter_sha256=hashlib.sha256(flat.tobytes()).hexdigest(),optimizer_updates=self.model._n_updates,
            gradient_l2=float(sum(float(p.grad.detach().square().sum()) for p in actor if p.grad is not None)**.5),
            elapsed_wall_s=self.previous_elapsed+time.perf_counter()-self.timer_start)
        self.rows.append(row)
        if ev['macro_qoe']>self.best:
            self.best=ev['macro_qoe'];self.model.save(self.out/'selected')
            (self.out/'selected-validation.json').write_text(json.dumps(ev,indent=2))
        (self.out/'curve.json').write_text(json.dumps(self.rows,indent=2));print(json.dumps(row),flush=True)
        self.model.save(self.out/'resume')
        # Includes simulator histories, episode clock, optimizer/model (in ZIP),
        # and Python/NumPy/Torch random state for interruption recovery.
        snapshot={'env':self.model.get_env(),'python_rng':random.getstate(),
            'numpy_rng':np.random.get_state(),'torch_rng':torch.get_rng_state(),
            'cuda_rng':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
            'last_obs':self.model._last_obs,'last_episode_starts':self.model._last_episode_starts}
        with (self.out/'resume-state.pkl').open('wb') as f:pickle.dump(snapshot,f)
    def _on_step(self):return True
    def _on_rollout_start(self):
        if self.num_timesteps>=self.next:self.record(self.num_timesteps);self.next+=self.every

def train(out,kind,config,seed,steps,device='cpu',eval_every=100000):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);manifest=out/'manifest.json'
    if manifest.exists():
        completed=json.loads(manifest.read_text())
        if completed['steps']>=steps:return completed
        manifest.replace(out/f'manifest-through-{completed["steps"]}.json')
        import shutil
        shutil.copy2(out/'last.zip',out/f'last-through-{completed["steps"]}.zip')
    torch.set_num_threads(1);leo=kind=='leo'
    env=DummyVecEnv([lambda:Monitor(FinalLiveEnv('train',leo=leo)) for _ in range(8)])
    model=A2C('MlpPolicy',env,**CONFIGS[config],gamma=.99,gae_lambda=1,vf_coef=.5,
        max_grad_norm=.5,normalize_advantage=True,seed=seed,device=device,verbose=0,
        policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64]),'activation_fn':torch.nn.ReLU})
    start=time.perf_counter();cb=Progress(out,leo,eval_every);cb.timer_start=start
    if (out/'resume-state.pkl').exists() and (out/'initialization.json').exists():
        with (out/'resume-state.pkl').open('rb') as f:snapshot=pickle.load(f)
        env.close();env=snapshot['env'];model=A2C.load(out/'resume.zip',env=env,device=device,force_reset=False)
        model._last_obs=snapshot['last_obs'];model._last_episode_starts=snapshot['last_episode_starts']
        random.setstate(snapshot['python_rng']);np.random.set_state(snapshot['numpy_rng']);torch.set_rng_state(snapshot['torch_rng'])
        if snapshot['cuda_rng'] is not None and torch.cuda.is_available():torch.cuda.set_rng_state_all(snapshot['cuda_rng'])
        init=json.loads((out/'initialization.json').read_text());cb.rows=json.loads((out/'curve.json').read_text())
        cb.previous_elapsed=cb.rows[-1].get('elapsed_wall_s',0)
        cb.best=max(r['validation_qoe'] for r in cb.rows);cb.next=(int(model.num_timesteps/eval_every)+1)*eval_every
        print('Resuming',str(out),'at',model.num_timesteps,flush=True)
    else:
        init=warmstart(model,leo,seed);(out/'initialization.json').write_text(json.dumps(init,indent=2))
        cb.init_callback(model);cb.record(0)
    model.learn(total_timesteps=max(0,steps-model.num_timesteps),callback=cb,reset_num_timesteps=False);model.save(out/'last')
    if cb.rows[-1]['steps']!=model.num_timesteps:cb.record(model.num_timesteps)
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'kind':kind,'config':config,'seed':seed,
        'hyperparameters':CONFIGS[config],'steps':model.num_timesteps,'requested_steps':steps,
        'wall_s':cb.previous_elapsed+time.perf_counter()-start,'device':str(model.device),'initialization':init,
        'input_count':64 if leo else 36,'architecture':[64 if leo else 36,64,64,8],
        'selected_step':max(cb.rows,key=lambda r:r['validation_qoe'])['steps'],
        'selected_validation_qoe':cb.best,'checkpoint_sha256':hashlib.sha256((out/'selected.zip').read_bytes()).hexdigest(),
        'selection':'Maximum equal-family mean validation QoE, checkpoints including warmstart; no test access',
        'scope':'Player-compatible A2C adaptation inspired by Pensieve/Gelato/Plume; not their published pretrained model',
        'environment_sha256':hashlib.sha256((ROOT/'rl/final_env.py').read_bytes()).hexdigest(),
        'simulator_config_sha256':hashlib.sha256((ROOT/'configs/final/simulator.json').read_bytes()).hexdigest(),
        'data_identity':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
            ['data/manifests/train.json','data/manifests/validation.json','data/manifests/media.json','rl/features.py','configs/final/neural-interface.json']}}
    manifest.write_text(json.dumps(record,indent=2));env.close();print(json.dumps(record),flush=True);return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['screen','main'],required=True)
    p.add_argument('--device',default='cpu');p.add_argument('--steps',type=int);args=p.parse_args()
    base=ROOT/'artifacts/final/training';records=[]
    if args.stage=='screen':
        for config in CONFIGS:
            for seed in [11,29]:
                for kind in ['conventional','leo']:
                    records.append(train(base/'screen'/f'{kind}-{config}-{seed}',kind,config,seed,args.steps or 250000,args.device,125000))
        # Same hyperparameters for both observations: maximize their joint validation mean.
        scores={c:float(np.mean([r['selected_validation_qoe'] for r in records if r['config']==c])) for c in CONFIGS}
        choice=max(scores,key=scores.get)
        (base/'screen-selection.json').write_text(json.dumps({'selected':choice,'scores':scores,'rule':'Joint mean across both observation types and two seeds; all have identical budgets'},indent=2))
    else:
        config=json.loads((base/'screen-selection.json').read_text())['selected']
        for seed in [47,71,101,131,167]:
            for kind in ['conventional','leo']:
                records.append(train(base/'main'/f'{kind}-{seed}',kind,config,seed,args.steps or 1000000,args.device))
        selected={}
        for kind in ['conventional','leo']:
            ranked=sorted([r for r in records if r['kind']==kind],key=lambda r:r['selected_validation_qoe'])
            selected[kind]=ranked[len(ranked)//2]
        (base/'main-selection.json').write_text(json.dumps({'rule':'Median validation seed per observation type, each seed uses its best validation checkpoint','selected':selected,'all_runs':records},indent=2))

if __name__=='__main__':main()
