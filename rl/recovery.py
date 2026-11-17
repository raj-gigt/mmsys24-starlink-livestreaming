"""Supplemental interruption recovery from actual playback; not online reward."""

def interruption_recovery(samples,stages,stable_window_s=2):
    outages=[];start=None
    for stage in stages:
        if stage['rate_mbit']==0 and start is None:start=stage['at_s']
        elif stage['rate_mbit']>0 and start is not None:
            outages.append((start,stage['at_s']));start=None
    results=[]
    for began,ended in outages:
        first=None;stable=None
        for i,a in enumerate(samples):
            if a['t_s']<ended:continue
            if first is None and not a.get('waiting',True) and not a.get('seeking',False) and not a.get('paused',False):first=a['t_s']
            j=i
            while j<len(samples) and samples[j]['t_s']<a['t_s']+stable_window_s:j+=1
            if j==len(samples):break
            window=samples[i:j+1];duration=window[-1]['t_s']-a['t_s']
            if any(s.get('paused') or s.get('seeking') or s.get('seek_epoch',0)!=a.get('seek_epoch',0) for s in window):continue
            waiting=sum(b['t_s']-x['t_s'] for x,b in zip(window,window[1:]) if x.get('waiting',True))
            advancement=window[-1]['media_s']-a['media_s']
            if waiting<=.1 and advancement>=.75*duration:
                stable=a['t_s'];break
        results.append({'outage_start_s':began,'outage_end_s':ended,
            'first_playing_after_end_s':None if first is None else first-ended,
            'sustained_playback_recovery_s':None if stable is None else stable-ended,
            'recovery_censored':stable is None,'stable_window_s':stable_window_s,
            'censor_horizon_after_end_s':samples[-1]['t_s']-ended})
    return results
