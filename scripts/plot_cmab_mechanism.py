"""Source-backed CMAB mechanism figures from portable development evidence."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rl.evidence import load_run
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/final/figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
ledger=ROOT/'artifacts/final/development/memory-startup-v1/runs.json'
rows=json.loads(ledger.read_text());case='development-steady_bandwidth-4100'
pair={r['variant']:r for r in rows if r['case_id']==case and r['variant'] in ['original','startup']}
fig,axes=plt.subplots(3,1,figsize=(8.6,7.2),sharex=True,gridspec_kw={'height_ratios':[1.3,1,1]})
colors={'original':'#263B58','startup':'#128C86'}
for variant,offset in [('original',0),('startup',0)]:
    row=pair[variant];payload=load_run(row['run_id']);d=payload['telemetry.json'];s=payload['summary.json']
    origin=datetime.fromisoformat(s['load_wall_clock_utc']).timestamp()*1000
    trace=d['cmab_decisions'];x=[(r['at_ms']-origin)/1000 for r in trace]
    y=[r['bitrate_bps']/1e6+offset for r in trace]
    axes[0].step(x,y,where='post',lw=1,color=colors[variant],alpha=.55)
    for forced,marker in [(True,'x'),(False,'o')]:
        chosen=[(t,z) for t,z,r in zip(x,y,trace) if r['forced']==forced]
        if chosen:axes[0].scatter(*zip(*chosen),s=22,marker=marker,color=colors[variant],label=variant+' / '+('forced' if forced else 'learned callback'))
    samples=d['samples']
    axes[1].plot([r['t_s'] for r in samples],[r['buffer_s'] for r in samples],color=colors[variant],lw=1.2,label=variant)
    axes[2].plot([r['t_s'] for r in samples],[r['latency_s'] for r in samples],color=colors[variant],lw=1.2,label=variant)
axes[0].axhline(1.5,color='#C17A18',ls='--',lw=1,label='configured link capacity')
axes[0].set(ylabel='Selected nominal rate (Mb/s)',ylim=(0,6.6))
axes[1].set(ylabel='Video buffer (s)',ylim=(0,None))
axes[2].set(ylabel='Live delay (s)',xlabel='Time since Load (s)',ylim=(0,25),xlim=(0,90))
for ax in axes:ax.grid(alpha=.15)
axes[0].legend(loc='lower left',bbox_to_anchor=(0,1.02),fontsize=7,ncol=2,frameon=False)
fig.suptitle('Repeated forced high-rate choices can prevent learned decisions',x=.08,ha='left',fontsize=12,fontweight='bold')
fig.text(.08,.925,'Matched 90 s development case, 1.5 Mb/s. Decision calls are not distinct downloads.',fontsize=9)
fig.text(.08,.035,'Cold initialization / external UTC; one session per policy. Startup treatment changes forced duration and initial rate.\nBoth policies still stall substantially; this is mechanism evidence, not final performance.',fontsize=8,color='#444444')
fig.subplots_adjust(left=.1,right=.98,top=.81,bottom=.13,hspace=.16)
for ext in ['svg','png']:fig.savefig(OUT/('F2-cmab-timeline.'+ext),dpi=180)
plt.close(fig)
fixture=json.loads((ROOT/'artifacts/final/runtime-check.json').read_text())['fixture']
fig,ax=plt.subplots(figsize=(5.4,2.8));positions=[0,1]
ax.bar([x-.18 for x in positions],list(fixture['zero_centered_scores'].values()),width=.34,label='Centered context = zero',color='#263B58')
ax.bar([x+.18 for x in positions],list(fixture['post_scaling_intercept_scores'].values()),width=.34,label='Explicit intercept added',color='#128C86')
ax.set(xticks=positions,xticklabels=['Arm 0 (reward 1)','Arm 1 (reward 2)'],ylabel='Predicted score',title='Pinned-runtime constant-context fixture')
ax.legend(fontsize=7);ax.grid(axis='y',alpha=.15);fig.tight_layout()
for ext in ['svg','png']:fig.savefig(OUT/('F2b-intercept-fixture.'+ext),dpi=180)
plt.close(fig)
metadata={'scope':'Development mechanism and conditional estimator fixture; not held-out effects',
    'run_ids':[r['run_id'] for r in pair.values()],
    'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),
    'metric_version':'played-ledger-v2','script':'scripts/plot_cmab_mechanism.py'}
(OUT/'F2-source.json').write_text(json.dumps(metadata,indent=2))
print('Created F2 mechanism and F2b estimator figures from verified portable evidence')
