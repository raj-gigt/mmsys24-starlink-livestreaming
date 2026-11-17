"""Produce T7 definitions and T8 observed deployment cost from portable events.

Timing spans differ between the CMAB controller and neural outer rule. These
descriptive host timings are not a runtime benchmark or hard latency guarantee.
"""
import csv
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from rl.evidence import load_run


def write(path,rows):
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def stats(values,p):
    return float(np.percentile(values,p)) if values else None


def main():
    rows=json.loads((ROOT/'artifacts/final/evaluation/runs.json').read_text())
    assert len(rows)==179 and all(r['status']=='complete' for r in rows)
    reports=[]
    for policy in ['original','improved','guard_only','throughput','bola','conventional','leo']:
        pool=[r for r in rows if r['policy']==policy]
        durations=[];pages=[];prewarms=[];assets=[];fallbacks=[];player_errors=0;count=0;cached=0;overrides=0
        for row in pool:
            data=load_run(row['run_id']);t=data['telemetry.json'];s=data['summary.json']
            trace=t['custom_decisions'] if policy in ['conventional','leo'] else t['cmab_decisions']
            count+=len(trace);durations.extend(d['duration_ms'] for d in trace if 'duration_ms' in d)
            if policy in ['conventional','leo']:
                fallbacks.extend(d for d in trace if d['result'].get('fallback'))
                final=data.get('samples.json',[])
                callbacks=final[-1].get('callbacks',[]) if final else []
                cached+=sum(d['cached'] for d in callbacks if d['at_ms']<=t['stopped_at_ms'])
            overrides+=sum(bool(d.get('guard_override')) for d in trace)
            player_errors+=len(s['player_errors'])
            for target,name in [(pages,'page_load_to_ready_ms'),(prewarms,'runtime_prewarm_ms'),(assets,'model_assets_cold_load_ms')]:
                value=s.get(name)
                if value is not None:target.append(value)
        neural=policy in ['conventional','leo']
        actor=json.loads((ROOT/f'models/final/{policy}/actor.json').read_text()) if neural else None
        reports.append({'policy':policy,'sessions':len(pool),'fresh_decisions':count if policy not in ['throughput','bola'] else None,
            'timed_fresh_decisions':len(durations) if neural or policy in ['improved','guard_only'] else None,'fresh_p50_ms':stats(durations,50),
            'fresh_p95_ms':stats(durations,95),'fresh_p99_ms':stats(durations,99),
            'fresh_max_ms':max(durations) if durations else None,
            'page_to_ready_p50_ms':stats(pages,50),'separate_pyodide_prewarm_p50_ms':stats(prewarms,50),
            'model_assets_load_p50_ms':stats(assets,50),'neural_fallbacks':len(fallbacks) if neural else None,
            'cached_callbacks':cached if neural else None,'guard_overrides':overrides if policy=='improved' else None,
            'player_errors':player_errors,'actor_parameters':sum(len(x['w'])+len(x['b']) for x in actor['layers']) if neural else None,
            'actor_json_bytes':(ROOT/f'models/final/{policy}/actor.json').stat().st_size if neural else None,
            'combined_served_weights_js_bytes':(ROOT/'rl/web/final_models.js').stat().st_size if neural else None,
            'runtime':'Synchronous Float32 JS, Chrome main-thread CPU' if neural else 'JS guard in the Pyodide-initialized CMAB wrapper' if policy=='guard_only' else 'Synchronous existing Pyodide/WASM' if policy in ['original','improved'] else 'Native dash.js JS',
            'timing_scope':'Fresh neural outer-rule instrumented span; cache hits excluded' if neural else 'CMAB controller selection span; outer rule/feedback update excluded' if durations else 'No dedicated decision timing instrumentation',
            'host':'Chrome114, Linux/WSL on the measured laptop; no mobile/hard-deadline claim'})
    tables=ROOT/'reports/final/tables';tables.mkdir(parents=True,exist_ok=True)
    write(tables/'T8-deployment.csv',reports)
    definitions=[
        ('Q','Sum log(nominal_bps/300000)*actually_played_media_s/2','utility','Nominal quality proxy; skipped or unknown-quality media not credited'),
        ('B','Waiting idle wall time after playback starts, with idle>0.02s','seconds','Includes automatic catch-up seek wait; excludes deliberate user interactions'),
        ('S','Idle wall time before first actual playback','seconds','Initial live positioning is startup, not skipped epoch-sized media'),
        ('V','Sum abs(log(new_played_bitrate/previous_played_bitrate))','log-ratio','Only changes in actually attributed played quality'),
        ('A','Integral max(0,live_delay_s-3)*wall_dt','seconds squared','Excess over3s target; time weighted'),
        ('QoE/T','(Q-4B-S-0.3V-0.1A)/actual_observation_wall_s','utility per wall second','Same independent outcome definition for every policy; negative values are valid'),
        ('Mean live delay','Wall-time-weighted mean of finite observed delay','seconds','Case/family tables average session means'),
        ('p95 live delay','Weighted95th percentile within each session','seconds','Macro table averages session percentiles; not a pooled percentile'),
        ('Played bitrate','Nominal bitrate weighted by attributed played media seconds','bit/s','Actual encoded bytes separately drive network/training dynamics'),
        ('Skipped media','Positive media-time jumps after playback started','media seconds','Not credited as watched video; startup positioning excluded'),
        ('Sampling','Passive100ms browser samples plus event boundaries','seconds','Shared stop cutoff; actual elapsed and dual clocks verified'),
        ('Aggregation','Equal five-family weights; equal two-case weights within family','case/repeat','Raw repository replay is separate'),
        ('Uncertainty','Resample paired browser repeats within each fixed case','repeatability','Only2/3 repeats; related windows are not independent Starlink recordings'),
        ('CMAB update surrogate','log(b/300k)*segment_s/2-4max(0,transfer_s-buffer_at_choice)-0.3abs(log(b/previous_b))-0.1max(0,outcome_delay-target)*transfer_s','request proxy','Completed matched requests only; not the final actually-played score')]
    write(tables/'T7-metric-definitions.csv',[{'symbol':s,'definition':d,'units':u,'qualification':q} for s,d,u,q in definitions])
    out={'status':'PASS','scope':'179 final sessions, controlled and raw deployment costs pooled descriptively; no QoE selection',
        'runs':reports,'limitations':['CMAB and neural timing spans differ; no speedup ratio claimed','Original CMAB/native baseline decision cost not independently instrumented','Missing instrumentation is null, not zero cost or zero fallbacks']}
    (ROOT/'artifacts/final/evaluation/deployment.json').write_text(json.dumps(out,indent=2))
    print('Created T7 metric definitions and T8 deployment feasibility from179 portable browser sessions')


if __name__=='__main__':main()
