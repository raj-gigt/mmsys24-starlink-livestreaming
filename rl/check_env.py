"""Hand-computable physics and reward checks before the bounded pilot fit."""
from collections import deque
import json
from pathlib import Path
import time
import numpy as np
from gymnasium.utils.env_checker import check_env
from .pilot_env import PilotLiveEnv, SIZES, UTILITY, catchup_rate

def fixed(capacity=8,rtt=100):
    env=PilotLiveEnv(allow_seek=False)
    env.reset(seed=11)
    env.trace={'t_s':np.arange(180),'capacity_mbps':np.full(180,float(capacity)),
               'rtt_ms':np.full(180,float(rtt))}
    env.origin=60;env.next_index=29;env.play_pos=58
    return env

def main():
    env=fixed()
    sent,complete,sought=env._transfer(1_000_000)
    assert complete and not sought and abs(env.wall-1)<1e-6 and abs(sent-1e6)<1e-6
    env=fixed(4);env.trace['capacity_mbps'][0]=8
    sent,complete,_=env._transfer(1_500_000)
    assert complete and abs(env.wall-2)<1e-6 and abs(sent-1.5e6)<1e-6
    env=fixed();env.trace['capacity_mbps'][:2]=0
    sent,complete,_=env._transfer(1_000_000)
    assert complete and abs(env.wall-3)<1e-6 and abs(env.totals['startup_s']-3)<1e-6
    env=fixed();env.next_index=31;env.play_pos=62
    expected=4+.1+float(SIZES[0,1])*8/8e6
    _,_,_,_,info=env.step(0)
    assert abs(info['wall_s']-expected)<1e-6, (info['wall_s'],expected)
    assert abs(env.history[-1]['download_s']-(expected-4))<1e-6, 'Source availability wait is not HTTP transfer time'
    assert env.totals['quality_utility']==0, 'Downloaded but unplayed media earns no quality credit'
    env=fixed();env.play_pos=57;env.queue=deque([[2.0,7]]);env.started=True
    env._advance(1)
    assert abs(env.totals['played_s']-1)<1e-6
    assert abs(env.totals['quality_utility']-float(UTILITY[7])/2)<1e-6
    assert env.totals['stall_s']==0 and abs(env.buffer-1)<1e-6
    assert catchup_rate(.1,3)<1 and catchup_rate(2,5)>1
    env=fixed();env.allow_seek=True;env.play_pos=57
    assert env._advance(10) and env.totals['seeks']==1 and env.totals['skipped_s']>0
    assert env.buffer==0 and env.latency<=env.target+5
    env=PilotLiveEnv();check_env(env,skip_render_check=True)
    started=time.perf_counter();steps=0;truncations=0
    env.reset(seed=9)
    for _ in range(1000):
        obs,reward,terminated,truncated,info=env.step(int(env.np_random.integers(8)))
        assert np.isfinite(obs).all() and np.isfinite(reward)
        assert not terminated
        steps+=1
        if truncated: truncations+=1;env.reset()
    elapsed=time.perf_counter()-started
    report={'status':'PASS','checks':['constant capacity','capacity boundary mid-transfer','zero-capacity outage and recovery',
            'full live-segment release time','played-only quality credit','LoL+ rate direction',
            'seek/reset','Gymnasium contract','finite random rollouts and truncation'],
            'benchmark_steps':steps,'benchmark_s':elapsed,'environment_steps_per_s':steps/elapsed,'truncations':truncations,
            'scope':'Minimal pilot physics checks; not full browser calibration'}
    out=Path('artifacts/training');out.mkdir(parents=True,exist_ok=True)
    (out/'environment-checks.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
