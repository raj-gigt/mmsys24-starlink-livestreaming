"""Validation-only component/heuristic comparison, with mixed stress separate."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from select_cmab_final import FAMILIES
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',default='artifacts/final/validation/finalists-v2');args=p.parse_args()
    folder=ROOT/args.folder;rows=json.loads((folder/'runs.json').read_text());selection=json.loads((folder/'selection.json').read_text())
    assert len(rows)==24
    figures=ROOT/'reports/final/figures';figures.mkdir(parents=True,exist_ok=True)
    tables=ROOT/'reports/final/tables';tables.mkdir(parents=True,exist_ok=True)
    families=FAMILIES+['mixed_shifted'];positions=np.arange(len(families));width=.24
    fig,ax=plt.subplots(figsize=(9,3.8))
    palette={'context':'#4C78A8','guard':'#128C86','guard_only':'#C17A18'}
    labels={'context':'Context-only CMAB','guard':'Guarded CMAB','guard_only':'Guard-only heuristic'}
    for j,variant in enumerate(palette):
        values=[]
        for family in families:
            pool=[r for r in rows if r['family']==family]
            treatment=next(r for r in pool if r['variant']==variant);baseline=next(r for r in pool if r['variant']=='original')
            values.append(treatment['metrics']['qoe_per_wall_s']-baseline['metrics']['qoe_per_wall_s'])
        ax.bar(positions+(j-1)*width,values,width=width,label=labels[variant],color=palette[variant])
    ax.axvspan(4.5,5.5,color='#EFEFEF',zorder=-1)
    ax.axhline(0,lw=.9,color='#263B58');ax.grid(axis='y',alpha=.15)
    ax.set(xticks=positions,xticklabels=['Steady','Capacity\nvariation','RTT\nvariation','Interruption','Recovery','Mixed stress\n(separate)'],ylabel='QoE difference vs original / wall s')
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=3,frameon=False,fontsize=8)
    fig.suptitle('Validation: does the learned bandit add value beyond its guard?',fontsize=12,fontweight='bold')
    fig.text(.06,.025,'One session per case/policy; descriptive differences, no significance claim. Selection averages the first five families only.',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,.89))
    for ext in ['svg','png']:fig.savefig(figures/('F6-validation-components.'+ext),dpi=180)
    plt.close(fig)
    summary=[{'variant':variant,**metrics} for variant,metrics in selection['summary'].items()]
    with (tables/'T5-validation-summary.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    (figures/'F6-validation-source.json').write_text(json.dumps({'ledger_sha256':hashlib.sha256((folder/'runs.json').read_bytes()).hexdigest(),'selection':selection,'scope':'Validation only'},indent=2))
    print('Created validation figure F6 and table T5 from all24 frozen sessions')
if __name__=='__main__':main()
