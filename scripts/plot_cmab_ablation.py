"""Local mechanism effects, with cold/warm scopes kept explicitly separate."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
STUDIES=[('memory-startup-v1','Cold startup/history','original',[('H1','memory','original'),('H2','startup','original'),('H1xH2','both','original')]),
 ('feedback-v1','Cold feedback/attribution','both',[('H3 timing','delayed','both'),('H3 reward','outcome','delayed')]),
 ('context-guard-v2','Warm context/guard','outcome',[('H5 scaling+bias','scaled','outcome'),('H4 buffer+delay','buffer','scaled'),('H4 RTT health/history','context','buffer'),('H5 refit seed','seeded','context'),('H6 guard','guard','context'),('H6 guard-only','guard_only','guard')])]
def main():
    folder=ROOT/'reports/final/tables';folder.mkdir(parents=True,exist_ok=True)
    figures=ROOT/'reports/final/figures';figures.mkdir(parents=True,exist_ok=True)
    detailed=[];summaries=[]
    fig,axes=plt.subplots(1,3,figsize=(10,4.6),gridspec_kw={'width_ratios':[1,1,1.5]})
    for ax,(name,label,plot_base,treatments) in zip(axes,STUDIES):
        rows=json.loads((ROOT/'artifacts/final/development'/name/'runs.json').read_text())
        lookup={(r['case_id'],r['variant'],r['repeat']):r for r in rows}
        effects=[];labels=[]
        for hypothesis,variant,baseline in treatments:
            local=[]
            for row in rows:
                if row['variant']!=variant:continue
                control=lookup[(row['case_id'],baseline,row['repeat'])]
                record={'study':name,'initialization':'warm' if name=='context-guard-v2' else 'cold',
                    'hypothesis':hypothesis,'treatment':variant,'baseline':baseline,'case_id':row['case_id'],
                    'treatment_run_id':row['run_id'],'baseline_run_id':control['run_id'],
                    'qoe_difference':row['metrics']['qoe_per_wall_s']-control['metrics']['qoe_per_wall_s'],
                    'stall_difference_s':row['metrics']['stall_s']-control['metrics']['stall_s']}
                detailed.append(record);local.append(record)
            assert len(local)==3
            summary={'study':name,'hypothesis':hypothesis,'treatment':variant,'baseline':baseline,
                'cases':3,'repeats_per_case':1,'positive_qoe_cases':sum(r['qoe_difference']>0 for r in local),
                'mean_paired_qoe_difference':sum(r['qoe_difference'] for r in local)/3,
                'mean_paired_stall_difference_s':sum(r['stall_difference_s'] for r in local)/3}
            summaries.append(summary);effects.append(summary['mean_paired_qoe_difference']);labels.append(hypothesis)
        ax.barh(range(len(effects)),effects,color=['#128C86' if v>0 else '#C17A18' for v in effects],height=.6)
        ax.set(yticks=range(len(labels)),yticklabels=labels,title=label,xlabel='Paired QoE difference / wall s')
        ax.invert_yaxis();ax.axvline(0,color='#263B58',lw=.8);ax.grid(axis='x',alpha=.15)
        ax.spines[['top','right']].set_visible(False);ax.tick_params(labelsize=8)
    fig.suptitle('Development ablations: effects are local to each named comparison',fontsize=12,fontweight='bold')
    fig.text(.04,.025,'Exploratory: external UTC enabled, one run/case; startup/source-phase variability can affect these differences.\nCold/warm use different families and local baselines; bars are not additive contributions to the final controller.',fontsize=8)
    fig.tight_layout(rect=(0,.13,1,.93))
    for ext in ['svg','png']:fig.savefig(figures/('F6-development-ablation.'+ext),dpi=180)
    plt.close(fig)
    for filename,records in [('T5-development-effects.csv',detailed),('T5-hypothesis-summary.csv',summaries)]:
        with (folder/filename).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    (figures/'F6-development-source.json').write_text(json.dumps({'studies':[r[0] for r in STUDIES],'scope':'Development only; no final test scores','records':summaries},indent=2))
    print('Created local-effect table T5 and development figure F6 from42 completed research sessions')
if __name__=='__main__':main()
