"""Generate cross-seed neural evidence from saved validation curves."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'artifacts/final/training';selected=json.loads((base/'main-selection.json').read_text());rows=[]
fig,axes=plt.subplots(1,3,figsize=(10.4,3.3))
for kind,color,label in [('conventional','#4C78A8','Conventional A2C'),('leo','#128C86','LEO A2C')]:
    curves=[]
    for folder in sorted((base/'main').glob(kind+'-*')):
        manifest=json.loads((folder/'manifest.json').read_text());curve=json.loads((folder/'curve.json').read_text());curves.append(curve)
        rows.append({'kind':kind,'seed':manifest['seed'],'collected_steps':manifest['steps'],
            'selected_step':manifest['selected_step'],'validation_qoe':manifest['selected_validation_qoe'],
            'initial_validation_qoe':curve[0]['validation_qoe'],
            'gain_after_rl':manifest['selected_validation_qoe']-curve[0]['validation_qoe'],
            'wall_s':manifest['wall_s'],'representative':manifest['seed']==selected['selected'][kind]['seed']})
    xs=np.array([r['steps'] for r in curves[0]])
    for ax,field in [(axes[0],'validation_qoe'),(axes[1],'validation_stall_s')]:
        values=np.array([np.interp(xs,[r['steps'] for r in c],[r[field] for r in c]) for c in curves])
        ax.plot(xs/1e6,values.mean(0),color=color,label=label)
        ax.fill_between(xs/1e6,values.min(0),values.max(0),color=color,alpha=.13)
    relevant=[r for r in rows if r['kind']==kind];x=0 if kind=='conventional' else 1
    axes[2].scatter([x]*len(relevant),[r['validation_qoe'] for r in relevant],color=color,s=26)
    representative=next(r for r in relevant if r['representative'])
    axes[2].scatter([x],[representative['validation_qoe']],s=90,facecolors='none',edgecolors='#263B58',linewidth=1.5)
axes[0].set(xlabel='Collected decisions (millions)',ylabel='Validation QoE / wall s')
axes[1].set(xlabel='Collected decisions (millions)',ylabel='Validation stalls (s)')
axes[2].set(xticks=[0,1],xticklabels=['Conventional','LEO'],ylabel='Selected validation QoE / wall s')
axes[0].legend(fontsize=7,frameon=False)
for ax in axes:ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Five-seed training: validation means, ranges and selected seeds',fontsize=12)
fig.text(.04,.015,'Bands are seed min-max, not confidence intervals. Circles mark median-validation representatives. Step0 is teacher initialization.',fontsize=8)
fig.tight_layout(rect=(0,.06,1,.95));figures=ROOT/'reports/final/figures'
for ext in ['png','svg']:fig.savefig(figures/('F7-neural-training.'+ext),dpi=180)
plt.close(fig)
tables=ROOT/'reports/final/tables';tables.mkdir(parents=True,exist_ok=True)
with (tables/'T8-neural-training.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(base/'learning-checks.json').write_text(json.dumps({'scope':'Training/validation only; actual browser comparison required',
    'runs':rows,'all_five_seeds_per_kind':all(sum(r['kind']==k for r in rows)==5 for k in ['conventional','leo']),
    'note':'A selected step0 checkpoint is retained and explicitly counted; teacher fidelity is not ABR accuracy.'},indent=2))
print(json.dumps(rows,indent=2))
