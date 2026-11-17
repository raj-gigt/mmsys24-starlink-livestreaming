"""Verify applied link state and phase without censoring poor player outcomes."""
from datetime import datetime

def verify_replay(payload,tolerance=.5):
    scenario=payload['scenario.json'];summary=payload['summary.json'];applied=payload['applied-profile.json']
    assert applied['profile_id']==summary['run_id'],'Link profile identity mismatch'
    phase=datetime.fromisoformat(summary['load_wall_clock_utc']).timestamp()-summary['scheduled_start_unix_s']
    assert -.05<=phase<=tolerance,('Start phase',phase)
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
    return {'status':'PASS','run_id':summary['run_id'],'start_phase_error_s':phase,
        'verified_transitions':len(errors),'max_transition_error_s':max(errors,default=0),
        'raw_replay':'stages' not in scenario}
