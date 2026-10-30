"""Bounded A2C fit for integration, using training/validation only (one seed)."""
from collections import Counter
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from torch import nn
from stable_baselines3 import A2C
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from .pilot_env import PilotLiveEnv

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/training'
MODELS=ROOT/'models/checkpoints'

def evaluate(model=None,fixed_action=None,stochastic=False):
    env=PilotLiveEnv('validation')
    rows=[];actions=Counter()
    for i,row in enumerate(env.rows):
        obs,_=env.reset(seed=7100+i,options={'scenario_id':row['id']})
        done=False;total=0
        while not done:
            action=int(model.predict(obs,deterministic=not stochastic)[0]) if model is not None else fixed_action
            obs,reward,_,done,info=env.step(action)
            total+=reward; actions[action]+=1
        rows.append({'scenario_id':row['id'],'family':row['family'],'return':total,**env.totals})
    return {'mean_return':float(np.mean([r['return'] for r in rows])),
            'mean_stall_s':float(np.mean([r['stall_s'] for r in rows])),
            'mean_played_s':float(np.mean([r['played_s'] for r in rows])),
            'action_counts':dict(actions),'episodes':rows}

class Progress(BaseCallback):
    def __init__(self,every=20000):
        super().__init__();self.every=every;self.next=every;self.rows=[];self.best=-float('inf')
    def _on_step(self):
        if self.num_timesteps>=self.next:
            evaluation=evaluate(self.model)
            self.rows.append({'steps':self.num_timesteps,'validation_return':evaluation['mean_return'],
                'validation_stall_s':evaluation['mean_stall_s'],
                'train_episode_return':float(np.mean([x['r'] for x in self.model.ep_info_buffer])) if self.model.ep_info_buffer else None,
                'action_counts':evaluation['action_counts']})
            if evaluation['mean_return']>self.best:
                self.best=evaluation['mean_return'];self.model.save(MODELS/'pilot-selected')
                (OUT/'selected-validation.json').write_text(json.dumps(evaluation,indent=2))
            (OUT/'learning-curve.json').write_text(json.dumps(self.rows,indent=2))
            print(json.dumps(self.rows[-1]),flush=True)
            self.next+=self.every
        return True

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--steps',type=int,default=50000)
    parser.add_argument('--eval-every',type=int,default=5000)
    parser.add_argument('--normalize-advantage',action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument('--warmstart',action=argparse.BooleanOptionalAction,default=True)
    args=parser.parse_args()
    torch.set_num_threads(1)
    OUT.mkdir(parents=True,exist_ok=True);MODELS.mkdir(parents=True,exist_ok=True)
    seed=42;budget=args.steps
    env=DummyVecEnv([lambda:Monitor(PilotLiveEnv('train')) for _ in range(8)])
    learning_rate=3e-5 if args.warmstart else 3e-4
    model=A2C('MlpPolicy',env,learning_rate=learning_rate,n_steps=32,gamma=.99,gae_lambda=1,
              ent_coef=.02,vf_coef=.5,max_grad_norm=.5,seed=seed,device='cpu',verbose=0,
              normalize_advantage=args.normalize_advantage,
              policy_kwargs={'net_arch':{'pi':[64,64],'vf':[64,64]},'activation_fn':nn.ReLU})
    initial=evaluate(model)
    warmstart_report=None;warmstart_evaluation=None
    if args.warmstart:
        from .warmstart import initialize_actor
        warmstart_report=initialize_actor(model)
        warmstart_evaluation=evaluate(model)
        print(json.dumps({'warmstart_teacher_agreement':warmstart_report['within_training_state_holdout_teacher_agreement'],
                          'warmstart_validation_return':warmstart_evaluation['mean_return']}),flush=True)
    low=evaluate(fixed_action=0);middle=evaluate(fixed_action=4)
    (OUT/'untrained-and-fixed-validation.json').write_text(json.dumps({'untrained':initial,'fixed_low':low,'fixed_1500kbps':middle},indent=2))
    start=time.perf_counter();callback=Progress(args.eval_every)
    model.learn(total_timesteps=budget,callback=callback)
    model.save(MODELS/'pilot-final')
    elapsed=time.perf_counter()-start
    selected=A2C.load(MODELS/'pilot-selected',device='cpu')
    result=evaluate(selected)
    checkpoint=MODELS/'pilot-selected.zip'
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'label':'pilot-trained player-compatible A2C adaptation',
        'algorithm':'Stable-Baselines3 A2C','seed':seed,'requested_steps':budget,'actual_steps':model.num_timesteps,
        'training_wall_s':elapsed,'steps_per_s':model.num_timesteps/elapsed,
        'actor':'36 -> 64 ReLU -> 64 ReLU -> 8 logits','actor_parameter_count':7048,
        'selection':f'Highest mean return on the fixed 18-scenario validation set at {args.eval_every}-decision intervals; no test evaluation.',
        'validation_interval_decisions':args.eval_every,
        'normalize_advantage':args.normalize_advantage,
        'learning_rate':learning_rate,
        'initialization':'Training-only imitation of causal throughput/buffer rule, then A2C' if args.warmstart else 'Random actor initialization',
        'warmstart_samples':warmstart_report['samples'] if warmstart_report else 0,
        'warmstart_validation_mean_return':warmstart_evaluation['mean_return'] if warmstart_evaluation else None,
        'selected_optimizer_updates':selected._n_updates,
        'selected_at_collected_decisions':max(callback.rows,key=lambda r:r['validation_return'])['steps'],
        'selected_checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'train_manifest_sha256':hashlib.sha256((ROOT/'data/manifests/train.json').read_bytes()).hexdigest(),
        'validation_manifest_sha256':hashlib.sha256((ROOT/'data/manifests/validation.json').read_bytes()).hexdigest(),
        'selected_validation_mean_return':result['mean_return'],'untrained_validation_mean_return':initial['mean_return'],
        'fixed_low_validation_mean_return':low['mean_return'],'fixed_1500_validation_mean_return':middle['mean_return'],
        'reward':{'quality':'Integral of log(nominal bitrate/300kbps) over actually played media seconds / 2',
                  'stall_coefficient_per_s':4,'startup_coefficient_per_s':1,'log_quality_variation_coefficient':.3,
                  'excess_live_latency_area_coefficient':.1,'excess_live_latency_target_s':3},
        'catchup':'Approximate LoL+ sigmoid, playback rate 0.83..1.17, buffer minimum 0.5s, drift seek at target+5s.',
        'status':'Integration pilot only; not calibrated or final LEO-aware policy; one seed; no performance claim over CMAB.',
        'not_observed_by_actor':['RTT','live_latency','future capacity/outage','handover state','trace identity'],
        'limitations':['Whole-segment model','Synthetic capacity and explicit interruptions','No TCP/congestion/loss dynamics',
                       'Approximate seek/catch-up lifecycle','Single-source chronological RTT split','One pilot seed']}
    (OUT/'pilot-manifest.json').write_text(json.dumps(record,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,3.5))
    axes[0].plot([r['steps'] for r in callback.rows],[r['train_episode_return'] for r in callback.rows],label='Training episodes (running mean)')
    axes[0].plot([r['steps'] for r in callback.rows],[r['validation_return'] for r in callback.rows],label='Fixed validation cases')
    axes[0].axhline(low['mean_return'],label='Fixed lowest quality (validation)',color='gray',linestyle='--')
    axes[0].set(xlabel='Training decisions',ylabel='Pilot simulator return');axes[0].legend(fontsize=7)
    axes[1].plot([r['steps'] for r in callback.rows],[r['validation_stall_s'] for r in callback.rows])
    axes[1].set(xlabel='Training decisions',ylabel='Mean validation stall duration (s)')
    fig.suptitle('One-seed integration pilot — simulator evidence only')
    fig.tight_layout();fig.savefig(OUT/'pilot-learning.png',dpi=150);plt.close(fig)
    print(json.dumps(record,indent=2),flush=True)
    assert result['mean_played_s']>60, 'Pilot has degenerate no-playback behaviour'
    reference=warmstart_evaluation if args.warmstart else initial
    assert result['mean_return']>reference['mean_return'], 'A2C did not improve its actual starting policy'
    assert len(result['action_counts'])>1, 'Pilot collapsed to a constant action'

if __name__=='__main__':main()
