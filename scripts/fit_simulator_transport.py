"""Fit two fluid-transport constants using fixed-policy development runs only."""
from datetime import datetime
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'artifacts/final/calibration/runs.json').read_text());assert len(rows)==6
x=[];y=[];rtts=[];sources=[]
workloads=json.loads((ROOT/'configs/final/workloads/development.json').read_text())['cases']
for r in rows:
    if r['fixed_action'] is None:continue
    d=json.loads((ROOT/'artifacts/runs'/r['run_id']/'samples.json').read_text())[-1]
    telemetry=json.loads((ROOT/'artifacts/runs'/r['run_id']/'telemetry.json').read_text())
    profile=next(c for c in workloads if c['id']==r['case_id'])['stages']
    for q in d['requests']:
        if q['type']!='MediaSegment' or q['code']!=200 or not q['finish'] or q['bytes']<=0:continue
        duration=(datetime.fromisoformat(q['finish'].replace('Z','+00:00'))-datetime.fromisoformat(q['start'].replace('Z','+00:00'))).total_seconds()
        start=datetime.fromisoformat(q['start'].replace('Z','+00:00')).timestamp()-telemetry['started_at_ms']/1000
        if r['family']=='handover_interruption' and 25<start<45:continue
        stage=next(s for s in reversed(profile) if s['at_s']<=start)
        if stage['rate_mbit']<=0:continue
        x.append(q['bytes']*8/(stage['rate_mbit']*1e6));y.append(duration);rtts.append(stage['delay_ms']/1000)
    sources.append(r['run_id'])
x=np.asarray(x);y=np.asarray(y);rtts=np.asarray(rtts);best=None
for multiplier in np.arange(1,8.01,.05):
    for inverse_efficiency in np.arange(1,1.501,.01):
        overhead=float(np.clip(np.median(y-multiplier*rtts-inverse_efficiency*x),0,.5))
        residual=y-(overhead+multiplier*rtts+inverse_efficiency*x)
        loss=float(np.mean(np.minimum(residual**2,.25)))
        if best is None or loss<best[0]:best=(loss,multiplier,inverse_efficiency,overhead)
record={'capacity_efficiency':float(1/best[2]),'rtt_multiplier':float(best[1]),
    'request_overhead_s':best[3],
    'method':'Bounded robust fit: transfer_s = effective_RTT_factor*RTT + overhead + payload_bits/(capacity*efficiency)',
    'fit_scope':'Four fixed-policy development runs; outage-adjacent requests excluded. Adaptive cases not used for fit. No validation/test outcomes.',
    'requests':len(x),'bounded_fit_loss':best[0],'source_runs':sources,
    'limitations':['Phenomenological transport constants do not model TCP retries/loss/RTO','Fitted transfer residuals are not independent validation','Exact browser seek/scheduler behavior remains approximate']}
(ROOT/'configs/final/simulator.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
