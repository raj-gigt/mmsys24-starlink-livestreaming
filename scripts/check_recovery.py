"""Hand-computable recovery cases, including false progress from a seek."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rl.recovery import interruption_recovery
stages=[{'at_s':0,'rate_mbit':8},{'at_s':10,'rate_mbit':0},{'at_s':12,'rate_mbit':8}]
def samples(waiting_ranges=(),seek_at=None,horizon=22):
    rows=[];media=0
    for t in range(horizon+1):
        waiting=any(a<=t<b for a,b in waiting_ranges)
        if t and not any(a<=t-1<b for a,b in waiting_ranges):media+=1
        if t==seek_at:media+=100
        rows.append({'t_s':t,'media_s':media,'waiting':waiting,'seeking':t==seek_at,'seek_epoch':int(seek_at is not None and t>=seek_at)})
    return rows
assert interruption_recovery(samples(),stages)[0]['sustained_playback_recovery_s']==0
assert interruption_recovery(samples([(10,15)]),stages)[0]['sustained_playback_recovery_s']==3
r=interruption_recovery(samples([(10,13),(14,17)]),stages)[0]
assert r['first_playing_after_end_s']==1 and r['sustained_playback_recovery_s']==5
r=interruption_recovery(samples([(10,20)],horizon=20),stages)[0]
assert r['recovery_censored'] and r['sustained_playback_recovery_s'] is None
r=interruption_recovery(samples([(10,15)],seek_at=13),stages)[0]
assert r['sustained_playback_recovery_s']==3,'A clock jump must not count as sustained playback'
print('PASS: buffered outage, delayed recovery, transient false recovery, cutoff censoring and seek exclusion')
