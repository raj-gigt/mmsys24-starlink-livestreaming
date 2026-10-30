"""Fixed, causal pilot preprocessing. Must agree with rl/web/policy_core.js."""
import numpy as np

def features(obs):
    history=obs.get('history',[])[-8:]
    x=[]
    for i in range(8):
        j=i-(8-len(history))
        h=history[j] if j>=0 else None
        x.extend([np.clip(h['mbps']/10,0,3) if h else 0,
                  np.clip(h['download_s']/2,0,10) if h else 0,
                  np.clip(h['age_s']/30,0,1) if h else 1,1 if h else 0])
    ladder=obs['ladder']
    previous=next((r for r in ladder if r['quality']==obs['previous_quality']),None)
    maximum=max(r['bandwidth'] for r in ladder)
    x.extend([np.clip(obs['buffer_s']/obs['target_s'],0,4),
              previous['bandwidth']/maximum if previous else 0,
              np.clip((obs['playback_rate']-1)/.17,-1,1),np.clip(obs['target_s']/6,0,2)])
    return np.array(x,dtype=np.float32)
