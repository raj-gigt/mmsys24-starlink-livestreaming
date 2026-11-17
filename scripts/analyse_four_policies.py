"""Balanced four-policy synthesis of existing frozen trials; no new experiments."""
import itertools,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyse_final import ROOT,FAMILIES,METRICS,LABELS,COLORS,macro,paired_summary,csvwrite,save
from rl.evidence import load_run

def main():
    folder=ROOT/'artifacts/final/evaluation';allrows=json.loads((folder/'runs.json').read_text())
    policies=['original','improved','conventional','leo']
    rows=[r for r in allrows if r['policy'] in policies and r['family'] in FAMILIES and r['repeat']<2]
    assert len(rows)==80 and all(sum(r['policy']==p for r in rows)==20 for p in policies)
    for p in policies:
        assert {(r['case_id'],r['repeat']) for r in rows if r['policy']==p}=={(r['case_id'],r['repeat']) for r in rows if r['policy']=='original'}
    overall=[{'policy':p,'sessions':20,**{k:macro([r for r in rows if r['policy']==p],k) for k in METRICS}} for p in policies]
    pairs=[]
    for baseline,candidate in itertools.combinations(policies,2):
        mapped=[{**r,'policy':'original' if r['policy']==baseline else candidate} for r in rows if r['policy'] in [baseline,candidate]]
        pairs.append({'baseline':baseline,'candidate':candidate,**paired_summary(mapped,candidate)})
    families=[{'policy':p,'family':f,**{k:float(np.mean([r['metrics'][k] for r in rows if r['policy']==p and r['family']==f])) for k in METRICS}} for p in policies for f in FAMILIES]
    out={'status':'complete','sessions':80,'policies':policies,'overall':overall,'pairs':pairs,'families':families,
        'run_ids':[r['run_id'] for r in rows],'ledger_sha256':hashlib.sha256((folder/'runs.json').read_bytes()).hexdigest(),
        'scope':'Same two repeats of ten fixed cases; post-measurement reporting synthesis, not a new untouched test. All179 original results retained.',
        'uncertainty':'5000 paired-repeat bootstrap draws within each fixed case; conditional/descriptive95% intervals; individual comparisons, no family-wise multiplicity guarantee.'}
    (folder/'four-policy-analysis.json').write_text(json.dumps(out,indent=2))
    tables=ROOT/'reports/final/tables';figures=ROOT/'reports/final/figures'
    csvwrite(tables/'T4-four-policy.csv',overall)
    csvwrite(tables/'T4-four-policy-pairs.csv',[{k:v for k,v in p.items() if k!='cases'} for p in pairs])
    csvwrite(tables/'T4-four-policy-families.csv',families)
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(7.2,3.1))
    for i,p in enumerate(pairs[:3]):
        ax.scatter([i]*10,[v['difference'] for v in p['cases']],s=22,alpha=.55,color=COLORS[p['candidate']])
        ax.errorbar(i,p['mean_difference'],yerr=[[p['mean_difference']-p['ci95_low']],[p['ci95_high']-p['mean_difference']]],fmt='D',capsize=5,color=COLORS[p['candidate']])
    ax.axhline(0,color='black',lw=.8);ax.set(xticks=range(3),xticklabels=['Improved CMAB','Conventional A2C','LEO-aware A2C'],ylabel='Paired QoE difference / wall s')
    ax.grid(axis='y',alpha=.15);fig.tight_layout();save(fig,'F3-four-policy',figures)
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.0));x=np.arange(5);width=.23
    for j,p in enumerate(policies[1:]):
        for ax,key in zip(axes,['qoe_per_wall_s','stall_s']):
            vals=[next(r[key] for r in families if r['policy']==p and r['family']==f)-next(r[key] for r in families if r['policy']=='original' and r['family']==f) for f in FAMILIES]
            ax.bar(x+(j-1)*width,vals,width,color=COLORS[p],label=LABELS[p])
    for ax,y in zip(axes,['QoE difference / wall s','Stall difference (s)']):
        ax.axhline(0,lw=.7,color='black');ax.set(xticks=x,xticklabels=['Steady','Capacity','RTT','Outage','Recovery'],ylabel=y);plt.setp(ax.get_xticklabels(),rotation=30,ha='right');ax.grid(axis='y',alpha=.15)
    h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,loc='lower center',ncol=3,fontsize=8.5,frameon=False);fig.tight_layout(rect=(0,.12,1,1));save(fig,'F4-four-policy',figures)
    # Previously selected least-favourable CMAB case, repeat0, now all four policies.
    case='test-handover_interruption-6131';fig,axes=plt.subplots(3,1,figsize=(7.2,3.8),sharex=True)
    for p in policies:
        r=next(r for r in rows if r['policy']==p and r['case_id']==case and r['repeat']==0);d=load_run(r['run_id']);s=d['telemetry.json']['samples'];t=[v['t_s'] for v in s]
        if p=='original':
            stages=d['scenario.json']['stages'];axes[0].step([v['at_s'] for v in stages]+[120],[v['rate_mbit'] for v in stages]+[stages[-1]['rate_mbit']],where='post',color='black')
        for ax,k,scale in [(axes[1],'played_bitrate_bps',1e6),(axes[2],'latency_s',1)]:ax.plot(t,[v[k]/scale if v.get(k) is not None else np.nan for v in s],lw=1,color=COLORS[p],label=LABELS[p])
    for ax,y in zip(axes,['Capacity\n(Mbps)','Played rate\n(Mbps)','Live delay (s)']):ax.set_ylabel(y);ax.grid(alpha=.15)
    h,l=axes[1].get_legend_handles_labels();fig.legend(h,l,ncol=2,fontsize=8,loc='upper center',frameon=False)
    axes[2].set_xlabel('Wall time (s)');fig.tight_layout(rect=(0,0,1,.91));save(fig,'F5-four-policy-regression',figures)
    # Report-size learning curves from all ten completed main fits.
    fig,axes=plt.subplots(1,2,figsize=(7.2,2.5))
    for kind in ['conventional','leo']:
        curves=[json.loads((ROOT/f'artifacts/final/training/main/{kind}-{seed}/curve.json').read_text()) for seed in [47,71,101,131,167]]
        xs=np.array([r['steps'] for r in curves[0]])
        for ax,field in zip(axes,['validation_qoe','validation_stall_s']):
            v=np.array([np.interp(xs,[r['steps'] for r in c],[r[field] for r in c]) for c in curves]);ax.plot(xs/1e6,v.mean(0),color=COLORS[kind],label=LABELS[kind]);ax.fill_between(xs/1e6,v.min(0),v.max(0),color=COLORS[kind],alpha=.14)
    for ax,label in zip(axes,['Validation QoE / wall s','Validation stalls (s)']):ax.set(xlabel='Decisions (millions)',ylabel=label);ax.grid(alpha=.15)
    axes[0].legend(fontsize=8,frameon=False);fig.tight_layout();save(fig,'F7-report-training',figures)
    print(json.dumps({'sessions':80,'all_six_pairs':[{k:v for k,v in p.items() if k!='cases'} for p in pairs]},indent=2))

if __name__=='__main__':main()
