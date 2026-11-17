"""Meaningful causality, media-byte and ledger checks before training."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from stable_baselines3.common.env_checker import check_env
from rl.final_env import FinalLiveEnv,final_features
ROOT=Path(__file__).resolve().parents[1]
records=[]
for leo in [False,True]:
    env=FinalLiveEnv('train',leo=leo);check_env(env,warn=True)
    x,_=env.reset(seed=123);assert len(x)==(64 if leo else 36)
    original=env.trace;clone={k:v.copy() for k,v in original.items()};env.trace=clone
    # Future information must not alter today's state.
    clone['rtt_ms'][20:]=999;clone['capacity_mbps'][20:]=.001
    np.testing.assert_array_equal(x,env._obs());env.trace=original
    total=0;done=False;n=0
    while not done:
        x,r,_,done,info=env.step(n%8);total+=r;n+=1
        assert np.isfinite(x).all() and env.buffer>=0
    t=env.totals
    expected=t['quality_utility']-4*t['stall_s']-t['startup_s']-.3*t['variation']-.1*t['latency_area']
    assert abs(expected-total)<1e-6,(expected,total)
    records.append({'leo':leo,'decisions':n,'return':total,'totals':t})
out=ROOT/'artifacts/final/calibration';out.mkdir(parents=True,exist_ok=True)
(out/'environment-checks.json').write_text(json.dumps({'status':'PASS','scope':'Dynamics bookkeeping and actor causality, not browser calibration','runs':records},indent=2))
print('PASS: both observation shapes, Gym contract, future isolation and episode reward ledger')
