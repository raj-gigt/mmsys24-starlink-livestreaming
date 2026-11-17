"""Quantify simulator mismatch on development fixed/adaptive browser policies."""
import json,re
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rl.final_env import FinalLiveEnv
from rl.warmstart import teacher_action
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'artifacts/final/calibration';ledger=json.loads((folder/'runs.json').read_text())
results=[];transfers=[];trajectories=[]
for row in ledger:
    raw=ROOT/'artifacts/runs'/row['run_id'];d=json.loads((raw/'telemetry.json').read_text())
    s=json.loads((raw/'summary.json').read_text());last=json.loads((raw/'samples.json').read_text())[-1]
    phase=d['started_at_ms']/1000%60
    action=row['fixed_action'];env=FinalLiveEnv('train',controlled=ROOT/'configs/final/workloads/development.json',
        initial_action=action,record=True)
    x,_=env.reset(seed=1,options={'scenario_id':row['case_id'],'source_phase_s':phase})
    done=False;ret=0
    while not done:
        x,r,_,done,info=env.step(action if action is not None else teacher_action(x[:36]));ret+=r
    for request in last['requests']:
        if request['type']!='MediaSegment' or request['code']!=200 or not request['finish']:continue
        from datetime import datetime
        begin=datetime.fromisoformat(request['start'].replace('Z','+00:00')).timestamp()-d['started_at_ms']/1000
        end=datetime.fromisoformat(request['finish'].replace('Z','+00:00')).timestamp()-d['started_at_ms']/1000
        if begin<0 or end>row['metrics']['duration_s'] or request['bytes']<=0:continue
        i=min(max(0,int(begin)),len(env.trace['rtt_ms'])-1);t=begin+float(env.trace['rtt_ms'][i])/1000*env.transport.get('rtt_multiplier',1)+env.transport['request_overhead_s'];remaining=request['bytes']
        while remaining>0 and t<env.horizon:
            idx=min(int(t),len(env.trace['capacity_mbps'])-1);cap=float(env.trace['capacity_mbps'][idx])*1e6/8*env.transport['capacity_efficiency']
            dt=min(1-(t%1),remaining/cap if cap>0 else 1)
            remaining-=cap*dt;t+=max(dt,1e-8)
        prediction=t-begin
        transfers.append({'run_id':row['run_id'],'key':row['key'],'actual_s':end-begin,'predicted_s':prediction,
                          'start_s':begin,'url':request['url']})
    actual=[r for r in d['samples'] if r['latency_s'] is not None and r['t_s']>.5]
    ts=np.array([r['t_s'] for r in env.samples]);
    errors={}
    for field in ['buffer_s','latency_s']:
        pred=np.interp([r['t_s'] for r in actual],ts,[r[field] for r in env.samples])
        errors[field+'_mae']=float(np.mean(np.abs(pred-np.array([r[field] for r in actual]))))
    results.append({'key':row['key'],'run_id':row['run_id'],'browser':row['metrics'],'simulator':env.totals,
        'simulator_qoe_per_wall_s':ret/env.wall,**errors})
    trajectories.append((row['key'],actual,env.samples))
relative=[abs(r['actual_s']-r['predicted_s'])/r['actual_s'] for r in transfers if r['actual_s']>=.05]
report={'scope':'Development calibration; no TCP/loss/retransmission or exact browser scheduling model',
    'transport_fit':env.transport,
    'status':'quantified','median_transfer_relative_error':float(np.median(relative)),
    'per_case_transfer_median_relative_error':{r['key']:float(np.median([abs(t['actual_s']-t['predicted_s'])/t['actual_s'] for t in transfers if t['key']==r['key'] and t['actual_s']>=.05])) for r in results},
    'buffer_mae_s':float(np.mean([r['buffer_s_mae'] for r in results])),
    'latency_mae_s':float(np.mean([r['latency_s_mae'] for r in results])),
    'playable_cases_latency_mae_s':float(np.mean([r['latency_s_mae'] for r in results if r['browser']['played_media_s']>0])),
    'playable_cases_qualification':'Diagnostic subset only; overloaded no-playback case remains in overall errors and final results',
    'targets':{'transfer_relative_error':.2,'buffer_mae_s':1,'latency_mae_s':1},
    'runs':results,'transfers':transfers}
report['targets_met']=report['median_transfer_relative_error']<=.2 and report['buffer_mae_s']<=1 and report['latency_mae_s']<=1
(folder/'comparison.json').write_text(json.dumps(report,indent=2))
fig,axes=plt.subplots(1,3,figsize=(10,3.1))
axes[0].scatter([r['actual_s'] for r in transfers],[r['predicted_s'] for r in transfers],s=8,alpha=.55)
maximum=max(max(r['actual_s'],r['predicted_s']) for r in transfers);axes[0].plot([0,maximum],[0,maximum],color='gray',ls='--')
axes[0].set(xlabel='Chrome transfer (s)',ylabel='Fluid prediction (s)')
key,a,b=next(t for t in trajectories if t[0]=='handover_interruption-None')
for ax,field,label in [(axes[1],'buffer_s','Buffer (s)'),(axes[2],'latency_s','Live latency (s)')]:
    ax.plot([r['t_s'] for r in a],[r[field] for r in a],label='Chrome',lw=1)
    ax.plot([r['t_s'] for r in b],[r[field] for r in b],label='Simulator',lw=1)
    ax.set(xlabel='Wall time (s)',ylabel=label);ax.grid(alpha=.15)
axes[2].legend(fontsize=7)
fig.suptitle('Development calibration: measured simulator-to-browser gap',fontsize=12)
fig.tight_layout();target=ROOT/'reports/final/figures';target.mkdir(parents=True,exist_ok=True)
for ext in ['png','svg']:fig.savefig(target/('F8-calibration.'+ext),dpi=180)
plt.close(fig)
print(json.dumps({k:v for k,v in report.items() if k not in ['runs','transfers']},indent=2))
