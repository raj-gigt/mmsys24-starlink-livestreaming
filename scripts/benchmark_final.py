"""Measure the actual eight-environment A2C pipeline on CPU or CUDA."""
import argparse,json,time,platform,subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from stable_baselines3 import A2C
from stable_baselines3.common.vec_env import DummyVecEnv
from rl.final_env import FinalLiveEnv,ROOT
p=argparse.ArgumentParser();p.add_argument('--device',default='cpu');p.add_argument('--steps',type=int,default=16384);args=p.parse_args()
torch.set_num_threads(1)
if args.device=='cuda':assert torch.cuda.is_available(),'CUDA installation unavailable'
records=[]
for leo in [False,True]:
    for repeat in range(2):
        env=DummyVecEnv([lambda:FinalLiveEnv('train',leo=leo) for _ in range(8)])
        model=A2C('MlpPolicy',env,n_steps=32,seed=11,device=args.device,verbose=0,
            policy_kwargs={'net_arch':dict(pi=[64,64],vf=[64,64]),'activation_fn':torch.nn.ReLU})
        if args.device=='cuda':torch.cuda.synchronize()
        start=time.perf_counter();model.learn(total_timesteps=args.steps)
        if args.device=='cuda':torch.cuda.synchronize()
        elapsed=time.perf_counter()-start
        records.append({'leo':leo,'repeat':repeat,'steps':model.num_timesteps,'wall_s':elapsed,'steps_per_s':model.num_timesteps/elapsed})
        env.close();print(json.dumps(records[-1]),flush=True)
result={'device':args.device,'torch':torch.__version__,'cuda_runtime':torch.version.cuda,
    'cuda_device':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    'platform':platform.platform(),'threads':1,'parallel_envs':8,'runs':records}
out=ROOT/'artifacts/final/calibration';out.mkdir(parents=True,exist_ok=True)
(out/('benchmark-'+args.device+'.json')).write_text(json.dumps(result,indent=2))
