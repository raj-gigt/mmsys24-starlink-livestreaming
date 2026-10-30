"""Minimal whole-segment live environment for the Phase A integration pilot.

This is NOT a calibrated replacement for the browser. Full TCP/loss, chunk-level
delivery, HTTP retries and browser seek timing still require Phase B calibration.
"""
from collections import deque
import json
from pathlib import Path
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .features import features

ROOT=Path(__file__).resolve().parents[1]
MEDIA=json.loads((ROOT/'data/manifests/media.json').read_text())
LADDER=[{'quality':r['action'],'bandwidth':r['nominal_bps'],'id':r['representation_id']} for r in MEDIA['representations']]
SIZES=np.array([[s['bytes'] for s in r['segments']] for r in MEDIA['representations']])
UTILITY=np.log(np.array([r['bandwidth'] for r in LADDER])/LADDER[0]['bandwidth'])

def catchup_rate(buffer_s,latency_s,target_s=3):
    delta=buffer_s-.5 if buffer_s<.5 else latency_s-target_s
    if buffer_s>=.5 and abs(delta)<=.02*target_s: return 1.0
    return .83+.34/(1+np.exp(-np.clip(delta*5,-60,60)))

class PilotLiveEnv(gym.Env):
    metadata={}
    def __init__(self,split='train',scenario_ids=None,allow_seek=True):
        assert split in ['train','validation'], 'Pilot trainer/evaluator cannot open sealed test data'
        manifest=json.loads((ROOT/f'data/manifests/{split}.json').read_text())
        self.rows=[r for r in manifest['scenarios'] if scenario_ids is None or r['id'] in scenario_ids]
        assert self.rows
        self.traces={r['id']:{k:v for k,v in np.load(ROOT/r['path']).items()} for r in self.rows}
        self.action_space=spaces.Discrete(8)
        self.observation_space=spaces.Box(-1,10,(36,),dtype=np.float32)
        self.allow_seek=allow_seek

    @property
    def buffer(self): return sum(s[0] for s in self.queue)
    @property
    def latency(self): return max(0,self.origin+self.wall-self.play_pos)

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        wanted=(options or {}).get('scenario_id')
        self.row=next(r for r in self.rows if r['id']==wanted) if wanted else self.rows[int(self.np_random.integers(len(self.rows)))]
        self.trace=self.traces[self.row['id']]
        self.wall=0.0; self.target=3.0
        self.origin=60+int(self.np_random.integers(30))*2
        self.next_index=int((self.origin-self.target)//2)
        self.play_pos=self.next_index*2.0
        self.queue=deque(); self.history=deque(maxlen=8)
        self.previous=0; self.played_action=None; self.started=False; self.rate=1.0
        self.horizon=float(len(self.trace['t_s']))
        self.totals={k:0.0 for k in ['quality_utility','stall_s','startup_s','variation','latency_area',
                                   'played_s','skipped_s','seeks','downloaded_bytes','discarded_bytes']}
        return self._obs(),{'scenario_id':self.row['id']}

    def raw_obs(self):
        return {'history':[{**h,'age_s':max(0,self.wall-h['finished_s'])} for h in self.history],
                'buffer_s':self.buffer,'target_s':self.target,'live_latency_s':self.latency,
                'playback_rate':self.rate,'previous_quality':self.previous,'ladder':LADDER}

    def _obs(self): return features(self.raw_obs())

    def _advance(self,duration):
        """Advance clocks and played-quality ledger; return whether catch-up sought."""
        left=min(duration,self.horizon-self.wall)
        if 0 < left <= 1e-8:
            self.wall+=left
            return False
        while left>1e-8:
            dt=min(.25,left)
            self.rate=catchup_rate(self.buffer,self.latency,self.target) if self.started else 1.0
            self.totals['latency_area']+=max(0,self.latency-self.target)*dt
            remaining=dt
            while self.queue and remaining>1e-9:
                segment=self.queue[0]
                if not self.started: self.started=True
                if self.played_action is not None and self.played_action!=segment[1]:
                    self.totals['variation']+=abs(float(UTILITY[segment[1]]-UTILITY[self.played_action]))
                self.played_action=segment[1]
                real=min(remaining,segment[0]/self.rate)
                media=real*self.rate
                segment[0]-=media; self.play_pos+=media; remaining-=real
                self.totals['played_s']+=media
                self.totals['quality_utility']+=float(UTILITY[segment[1]])*media/2
                if segment[0]<1e-8: self.queue.popleft()
            self.totals['stall_s' if self.started else 'startup_s']+=max(0,remaining)
            self.wall+=dt; left-=dt
            if self.allow_seek and self.wall>2 and self.latency>self.target+5:
                fresh=int((self.origin+self.wall-self.target)//2)
                self.totals['skipped_s']+=max(0,fresh*2-self.play_pos)
                self.totals['seeks']+=1
                self.play_pos=fresh*2.0; self.next_index=fresh
                self.queue.clear(); self.history.clear()
                return True
        return False

    def _transfer(self,byte_count):
        """Integrate payload across capacity changes without charging RTT twice."""
        remaining=float(byte_count); transferred=0.0; started=self.wall
        while remaining>1e-6 and self.wall<self.horizon-1e-8 and self.wall-started<20-1e-8:
            if abs(self.wall-round(self.wall))<1e-8: self.wall=float(round(self.wall))
            index=min(int(self.wall),len(self.trace['capacity_mbps'])-1)
            capacity=float(self.trace['capacity_mbps'][index])*1e6/8
            dt=min(1-(self.wall%1),20-(self.wall-started),self.horizon-self.wall)
            if capacity>0: dt=min(dt,remaining/capacity)
            before=self.wall
            sought=self._advance(dt)
            sent=min(remaining,capacity*(self.wall-before))
            remaining-=sent; transferred+=sent
            if sought: return transferred,False,True
        return transferred,remaining<=1e-6,False

    def step(self,action):
        action=int(action); assert self.action_space.contains(action)
        before=self.totals.copy(); began=self.wall
        requested=self.next_index
        # Full-segment availability follows the actual runtime MPD, not VOD.
        release=max(0,(requested+1)*2-self.origin-self.wall)
        sought=self._advance(release) if release else False
        http_started=self.wall
        sent=0.0; complete=False
        if not sought and self.wall<self.horizon:
            i=min(int(self.wall),len(self.trace['rtt_ms'])-1)
            sought=self._advance(float(self.trace['rtt_ms'][i])/1000)
            if not sought:
                sent,complete,sought=self._transfer(int(SIZES[action,requested%30]))
        self.totals['downloaded_bytes']+=sent
        elapsed=self.wall-began
        http_elapsed=self.wall-http_started
        if complete and not sought:
            self.queue.append([2.0,action])
            self.next_index=requested+1
            self.history.append({'mbps':sent*8/max(http_elapsed,1e-6)/1e6,'download_s':http_elapsed,
                                 'finished_s':self.wall,'bytes':sent})
        else:
            self.totals['discarded_bytes']+=sent
        self.previous=action
        delta={k:self.totals[k]-before[k] for k in self.totals}
        # Q - lambda*B - mu*V - eta*L, with separate startup accounting.
        reward=delta['quality_utility']-4*delta['stall_s']-delta['startup_s']-.3*delta['variation']-.1*delta['latency_area']
        truncated=self.wall>=self.horizon-1e-6
        info={'scenario_id':self.row['id'],'family':self.row['family'],'wall_s':self.wall,
              'buffer_s':self.buffer,'latency_s':self.latency,'elapsed_s':elapsed,
              'source_wait_s':release,'http_elapsed_s':http_elapsed,
              'completed':complete and not sought,'totals':self.totals.copy()}
        assert self.buffer>=-1e-7 and np.isfinite(reward)
        return self._obs(),float(reward),False,truncated,info
