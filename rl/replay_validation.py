"""Verify applied link state and phase without censoring poor player outcomes."""
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import csv,bisect

@lru_cache(maxsize=1)
def source_trace():
    path=Path(__file__).resolve().parents[1]/'runner/trace/isl-trace.csv'
    rows=list(csv.DictReader(path.open()));return [float(r['since']) for r in rows],[int(float(r['rtt'])) for r in rows]

def verify_replay(payload,tolerance=.5):
    scenario=payload['scenario.json'];summary=payload['summary.json'];applied=payload['applied-profile.json']
    assert applied['profile_id']==summary['run_id'],'Link profile identity mismatch'
    phase=datetime.fromisoformat(summary['load_wall_clock_utc']).timestamp()-summary['scheduled_start_unix_s']
    # Windows dispatch clock is diagnostic only. Player/source/shaper share the
    # guest clock and therefore determine actual experiment phase.
    actual_phase=payload['telemetry.json']['started_at_ms']/1000-summary['scheduled_start_unix_s']
    assert -.05<=actual_phase<=tolerance,('Player clock start phase',actual_phase)
    events=applied['applied'];assert events
    errors=[]
    if 'stages' in scenario:
        previous=None
        for i,stage in enumerate(scenario['stages']):
            value=(stage['rate_mbit'] if stage['rate_mbit']>0 else .05,stage['delay_ms'],
                stage.get('loss_percent',0) if stage['rate_mbit']>0 else 100)
            if value==previous:continue
            previous=value
            matching=[r for r in events if (r['rate_mbit'],r['delay_ms'],r['loss_percent'])==value
                and (r['relative_s']<=tolerance if i==0 else abs(r['relative_s']-stage['at_s'])<=tolerance)]
            assert matching,('Unverified applied stage',i,stage)
            if i:errors.append(min(abs(r['relative_s']-stage['at_s']) for r in matching))
    raw_checked=0
    if 'stages' not in scenario:
        times,delays=source_trace()
        for r in events:
            if 'source_trace_index' not in r:continue # Historical bounded PhaseA/Step10 evidence.
            at=r['source_trace_at_s'];idx=min(bisect.bisect_left(times,at),len(times)-1)
            if idx and abs(times[idx-1]-at)<=abs(times[idx]-at):idx-=1
            assert idx==r['source_trace_index']
            raw=delays[idx];assert (r['rate_mbit'],r['delay_ms'],r['loss_percent'])==(20,raw if raw>0 else 100,1 if raw>0 else 100)
            raw_checked+=1
        if any('source_trace_index' in r for r in events):
            assert raw_checked==len(events) and events[0]['relative_s']<=.5
            assert applied['captured_at_unix_s']-payload['telemetry.json']['started_at_ms']/1000>=scenario['seconds']-.5
    return {'status':'PASS','run_id':summary['run_id'],'start_phase_error_s':phase,'actual_player_start_phase_s':actual_phase,
        'verified_transitions':len(errors),'max_transition_error_s':max(errors,default=0),
        'raw_replay':'stages' not in scenario,'raw_source_rows_verified':raw_checked}
