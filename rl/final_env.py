"""Player-compatible research simulator; deliberately not a TCP emulator.

Full-segment release and encoded sizes are exact. Catch-up, browser startup,
retry and transport are approximations quantified against Chrome separately.
Only past completed transfers and past RTT probes reach either actor.
"""
from collections import deque
import json
from pathlib import Path
import numpy as np
from gymnasium import spaces
from .pilot_env import PilotLiveEnv, ROOT, SIZES
from .features import features


def final_features(obs, leo=False):
    base=features(obs)
    if not leo:return base
    history=obs.get('probes',[])[-8:];extra=[]
    for i in range(8):
        j=i-(8-len(history));r=history[j] if j>=0 else None
        extra.extend([np.clip(r['rtt_ms']/200,0,5) if r and r['ok'] else 0,
            np.clip(r['age_s']/4,0,1) if r else 1,1 if r and r['ok'] else 0])
    extra.extend([np.clip(obs['live_latency_s']/3,0,8),
        np.clip(obs.get('probe_success_age_s',99)/3,0,1),
        int(obs.get('probe_valid',False)),
        sum(not r['ok'] for r in history)/len(history) if history else 1])
    return np.concatenate([base,np.asarray(extra,dtype=np.float32)])


class FinalLiveEnv(PilotLiveEnv):
    def __init__(self,split='train',leo=False,controlled=None,initial_action=None,record=False):
        super().__init__(split)
        path=ROOT/'configs/final/simulator.json'
        self.transport=json.loads(path.read_text()) if path.exists() else {'capacity_efficiency':1.0,'request_overhead_s':0.0}
        self.leo=leo;self.initial_action=initial_action;self.record=record
        self.observation_space=spaces.Box(-1,10,(64 if leo else 36,),dtype=np.float32)
        if controlled:
            spec=json.loads(Path(controlled).read_text());self.rows=spec['cases'];self.traces={}
            assert all(r['role'] in ['development','validation'] for r in self.rows)
            for r in self.rows:
                n=r['seconds'];cap=np.empty(n);rtt=np.empty(n);observed=np.ones(n,dtype=bool)
                for i,s in enumerate(r['stages']):
                    end=int(r['stages'][i+1]['at_s']) if i+1<len(r['stages']) else n
                    start=int(s['at_s']);cap[start:end]=s['rate_mbit'];rtt[start:end]=s['delay_ms']
                    observed[start:end]=s['loss_percent']<100 and s['rate_mbit']>0
                self.traces[r['id']]={'t_s':np.arange(n),'capacity_mbps':cap,'rtt_ms':rtt,'rtt_observed':observed}

    def reset(self,*,seed=None,options=None):
        self.samples=[]
        super().reset(seed=seed,options=options)
        phase=float((options or {}).get('source_phase_s',self.np_random.uniform(0,60)))
        self.origin=120+phase
        rtt=float(self.trace['rtt_ms'][0])/1000
        self.initial_manifest_s=.05+5*rtt
        self.initial_video_setup_s=.01+3*rtt
        self.play_pos=self.origin+self.initial_manifest_s-self.target
        self.next_index=int(self.play_pos//2)
        self.first=True;self.previous=2 if self.initial_action is None else self.initial_action
        # ResourceTiming shows about5 RTTs for manifest establishment and3 for
        # init retrieval on this supplied HTTPS testbed. Actor decides after MPD.
        self._advance(self.initial_manifest_s)
        return self._obs(),{'scenario_id':self.row['id']}

    def raw_obs(self):
        obs=super().raw_obs();probes=[];success=None
        # Fixed 0.5-second polling. Only probes whose response could have arrived
        # are exposed. A failed measurement never becomes a zero-millisecond RTT.
        for t in np.arange(max(0,np.floor(self.wall*2)/2-6),self.wall+.001,.5):
            idx=min(int(t),len(self.trace['rtt_ms'])-1)
            # rtt_observed is provenance of the original recording, not loss in
            # our generated emulated path. Positive-capacity configured links
            # respond to the production sidecar even at a carried-forward RTT.
            rtt=float(self.trace['rtt_ms'][idx]);ok=self.trace['capacity_mbps'][idx]>0
            finished=t+(rtt/1000 if ok else 1)
            if finished<=self.wall:
                probes.append({'rtt_ms':rtt if ok else 0,'ok':ok,'age_s':self.wall-finished})
                if ok:success=finished
        obs.update(probes=probes[-8:],probe_success_age_s=self.wall-success if success is not None else 99,
            probe_valid=bool(probes and probes[-1]['ok'] and success is not None and self.wall-success<3))
        return obs

    def _obs(self):return final_features(self.raw_obs(),getattr(self,'leo',False))

    def _advance(self,duration):
        # Chromium does not begin at a tiny tail fragment (<stallThreshold0.3s).
        # Preserve that partial buffer while startup waits for the next response.
        held=self.queue if not self.started and self.buffer<.3 else None
        if held is not None:self.queue=deque()
        result=super()._advance(duration)
        if held is not None and not result:self.queue=held
        if result:
            # Catch-up seeks to the target inside its segment, not its start.
            position=self.origin+self.wall-self.target
            self.totals['skipped_s']+=max(0,position-self.play_pos)
            self.play_pos=position
        if getattr(self,'record',False):self.samples.append({'t_s':self.wall,'buffer_s':self.buffer,'latency_s':self.latency,'stall_s':self.totals['stall_s']})
        return result

    def _transfer(self,byte_count):
        if self._advance(self.transport['request_overhead_s']):return 0.,False,True
        remaining=float(byte_count);transferred=0.;started=self.wall
        while remaining>1e-6 and self.wall<self.horizon-1e-8 and self.wall-started<20-1e-8:
            if abs(self.wall-round(self.wall))<1e-8:self.wall=float(round(self.wall))
            index=min(int(self.wall),len(self.trace['capacity_mbps'])-1)
            cap=float(self.trace['capacity_mbps'][index])*1e6/8*self.transport['capacity_efficiency']
            dt=min(1-(self.wall%1),20-(self.wall-started),self.horizon-self.wall)
            if cap>0:dt=min(dt,remaining/cap)
            before=self.wall;sought=self._advance(dt)
            sent=min(remaining,cap*(self.wall-before));remaining-=sent;transferred+=sent
            if sought:return transferred,False,True
        return transferred,remaining<=1e-6,False

    def step(self,action):
        action=int(action);assert self.action_space.contains(action)
        first=self.first;action=self.initial_action if first and self.initial_action is not None else action
        before=self.totals.copy();began=self.wall
        if first:self._advance(self.initial_video_setup_s)
        requested=self.next_index
        release=max(0,(requested+1)*2-self.origin-self.wall)
        # ScheduleController retries unavailable full segments at its500ms
        # default timeout. This wait occurs before HTTP timing starts.
        wait=float(np.ceil(release/.5)*.5) if release>1e-8 else 0
        sought=self._advance(wait) if wait else False
        http_started=self.wall;sent=0.;complete=False
        if not sought and self.wall<self.horizon:
            i=min(int(self.wall),len(self.trace['rtt_ms'])-1)
            sought=self._advance(float(self.trace['rtt_ms'][i])/1000*self.transport.get('rtt_multiplier',1))
            if not sought:sent,complete,sought=self._transfer(int(SIZES[action,requested%30]))
        self.totals['downloaded_bytes']+=sent
        http_elapsed=self.wall-http_started
        if complete and not sought:
            prefix=max(0,self.play_pos-requested*2)
            self.queue.append([max(0,2-prefix),action]);self.next_index=requested+1
            self.history.append({'mbps':sent*8/max(http_elapsed,1e-6)/1e6,'download_s':http_elapsed,
                'finished_s':self.wall,'bytes':sent})
        else:self.totals['discarded_bytes']+=sent
        self.previous=action;self.first=False
        delta={k:self.totals[k]-before[k] for k in self.totals}
        reward=delta['quality_utility']-4*delta['stall_s']-delta['startup_s']-.3*delta['variation']-.1*delta['latency_area']
        if first:reward-=self.initial_manifest_s
        done=self.wall>=self.horizon-1e-6
        info={'scenario_id':self.row['id'],'family':self.row['family'],'wall_s':self.wall,
            'buffer_s':self.buffer,'latency_s':self.latency,'elapsed_s':self.wall-began,
            'source_wait_s':wait,'http_elapsed_s':http_elapsed,'completed':complete and not sought,'totals':self.totals.copy()}
        if self.record:self.samples.append({'t_s':self.wall,'buffer_s':self.buffer,'latency_s':self.latency,'stall_s':self.totals['stall_s']})
        assert np.isfinite(reward) and self.buffer>=0
        return self._obs(),float(reward),False,done,info
