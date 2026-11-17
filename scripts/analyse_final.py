"""Reproduce held-out tables/figures exclusively from portable saved evidence."""
import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rl.evidence import load_run
from rl.metrics import evaluate_samples
from rl.recovery import interruption_recovery
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=['steady_bandwidth','bandwidth_variation','rtt_variation','handover_interruption','post_handover_recovery']
LABELS={'original':'Original CMAB','improved':'Guarded CMAB','guard_only':'Guard only','throughput':'Throughput','bola':'BOLA','conventional':'Conventional A2C','leo':'LEO A2C'}
COLORS={'original':'#7B8796','improved':'#128C86','guard_only':'#C17A18','throughput':'#8C6BB1','bola':'#A65F55','conventional':'#4C78A8','leo':'#1B566D'}
METRICS=['qoe_per_wall_s','stall_s','startup_s','played_bitrate_bps','switches','mean_live_latency_s','p95_live_latency_s','played_media_s','skipped_media_s','quality_utility','latency_area','variation']

def csvwrite(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def macro(rows,key):
    return float(np.mean([np.mean([r['metrics'][key] for r in rows if r['family']==f]) for f in FAMILIES]))

def paired_summary(rows,policy,key='qoe_per_wall_s'):
    lookup={(r['case_id'],r['repeat']):r for r in rows if r['policy']=='original'}
    groups=defaultdict(list)
    for r in rows:
        if r['policy']==policy:
            b=lookup[(r['case_id'],r['repeat'])]
            groups[(r['family'],r['case_id'])].append(r['metrics'][key]-b['metrics'][key])
    cases=[{'family':f,'case_id':c,'difference':float(np.mean(v)),'paired_repeats':len(v)} for (f,c),v in groups.items()]
    rng=np.random.default_rng(20261118);draws=[]
    # Keep the benchmark cases fixed. Related windows are not independent
    # recordings: resample paired browser repeats only, conditionally per case.
    for _ in range(5000):
        means=[]
        for f in FAMILIES:
            keys=[k for k in groups if k[0]==f];values=[]
            for k in keys:
                x=groups[k];values.append(np.mean(np.asarray(x)[rng.integers(len(x),size=len(x))]))
            means.append(np.mean(values))
        draws.append(np.mean(means))
    mean=float(np.mean([np.mean([r['difference'] for r in cases if r['family']==f]) for f in FAMILIES]))
    return {'mean_difference':mean,'ci95_low':float(np.percentile(draws,2.5)),'ci95_high':float(np.percentile(draws,97.5)),
        'positive_cases':sum(r['difference']>0 for r in cases),'cases':cases}

def save(fig,name,out):
    for ext in ['png','svg']:fig.savefig(out/(name+'.'+ext),dpi=180)
    plt.close(fig)

def main():
    folder=ROOT/'artifacts/final/evaluation';rows=json.loads((folder/'runs.json').read_text());freeze=json.loads((folder/'freeze.json').read_text())
    assert len(rows)==len(freeze['plan'])==179 and all(r['status']=='complete' for r in rows)
    controlled=[r for r in rows if r['family'] in FAMILIES];raw=[r for r in rows if r not in controlled]
    assert len(controlled)==170 and len(raw)==9
    figures=ROOT/'reports/final/figures';tables=ROOT/'reports/final/tables';tables.mkdir(parents=True,exist_ok=True)
    policies=list(LABELS);aggregates=[];paired={};familyrows=[];recovery=[]
    perrun=[]
    for r in rows:
        data=load_run(r['run_id']);computed=evaluate_samples(data['telemetry.json']['samples'],horizon=r['metrics']['duration_s'])
        for k in METRICS:assert abs(computed[k]-r['metrics'][k])<1e-8
        perrun.append({k:r[k] for k in ['policy','case_id','family','recording_id','repeat','run_id','outcome']}|r['metrics'])
        if r['family'] in ['handover_interruption','post_handover_recovery']:
            t0=data['telemetry.json']['started_at_ms']/1000;profile=data['applied-profile.json']
            stages=[{'at_s':x['at_unix_s']-t0,
                'rate_mbit':0 if x['loss_percent']==100 else x['rate_mbit']} for x in profile['applied']]
            recovery.extend({'policy':r['policy'],'case_id':r['case_id'],'repeat':r['repeat'],'run_id':r['run_id'],**x} for x in interruption_recovery(data['telemetry.json']['samples'],stages))
    for p in policies:
        pool=[r for r in controlled if r['policy']==p]
        aggregates.append({'policy':p,'sessions':len(pool),**{k:macro(pool,k) for k in METRICS}})
        if p!='original':paired[p]=paired_summary(controlled,p)
        for f in FAMILIES:
            group=[r for r in pool if r['family']==f]
            familyrows.append({'policy':p,'family':f,'sessions':len(group),**{k:float(np.mean([r['metrics'][k] for r in group])) for k in METRICS}})
    csvwrite(tables/'T3-per-run.csv',perrun);csvwrite(tables/'T4-overall.csv',aggregates);csvwrite(tables/'T4-families.csv',familyrows)
    csvwrite(tables/'T4-paired-effects.csv',[{'policy':p,**{k:v for k,v in d.items() if k!='cases'}} for p,d in paired.items()])
    if recovery:csvwrite(tables/'T4-recovery.csv',recovery)
    rawsummary=[{'policy':p,'sessions':sum(r['policy']==p for r in raw),**{k:float(np.mean([r['metrics'][k] for r in raw if r['policy']==p])) for k in METRICS}} for p in ['original','improved','guard_only']]
    csvwrite(tables/'T4-raw-replay.csv',rawsummary)
    # F3 paired case averages and conditional paired-repeat intervals.
    fig,ax=plt.subplots(figsize=(8.8,3.8));compare=[p for p in policies if p!='original']
    for i,p in enumerate(compare):
        d=paired[p];ax.scatter([i]*len(d['cases']),[r['difference'] for r in d['cases']],s=18,alpha=.5,color=COLORS[p])
        ax.errorbar(i,d['mean_difference'],yerr=[[max(0,d['mean_difference']-d['ci95_low'])],[max(0,d['ci95_high']-d['mean_difference'])]],fmt='D',color=COLORS[p],capsize=5,ms=6)
    ax.axhline(0,color='#263B58',lw=1);ax.set(xticks=range(len(compare)),xticklabels=[LABELS[p].replace(' ','\n',1) for p in compare],ylabel='Paired QoE difference / wall s')
    ax.grid(axis='y',alpha=.15);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Held-out browser comparison against original CMAB',fontsize=13)
    fig.text(.07,.015,'Points: 10 fixed-case means. Diamonds: equal-family means, 95% paired-repeat intervals conditional on these cases; not Starlink population intervals.',fontsize=7.2)
    fig.tight_layout(rect=(0,.06,1,.95));save(fig,'F3-overall-paired',figures)
    # F4 all required families, paired differences for each component.
    # Size for a full report column: avoid shrinking an11-inch figure until
    # the six-policy legend and scenario labels become illegible in the PDF.
    fig,axes=plt.subplots(1,3,figsize=(7.8,3.9));x=np.arange(5);width=.12
    for j,p in enumerate(compare):
        for ax,key in zip(axes,['qoe_per_wall_s','stall_s','mean_live_latency_s']):
            vals=[]
            for f in FAMILIES:
                a=next(r for r in familyrows if r['policy']==p and r['family']==f)
                b=next(r for r in familyrows if r['policy']=='original' and r['family']==f)
                vals.append(a[key]-b[key])
            ax.bar(x+(j-2.5)*width,vals,width,color=COLORS[p],label=LABELS[p])
    for ax,ylabel in zip(axes,['QoE difference / wall s','Stall difference (s)','Mean live-delay difference (s)']):
        ax.axhline(0,color='#263B58',lw=.8);ax.set(xticks=x,xticklabels=['Steady','Cap.','RTT','Outage','Recov.'],ylabel=ylabel);ax.tick_params(axis='x',labelsize=8.5);ax.grid(axis='y',alpha=.15)
    handles,names=axes[0].get_legend_handles_labels()
    for ax in axes:
        plt.setp(ax.get_xticklabels(),rotation=35,ha='right')
    fig.legend(handles,names,loc='lower center',ncol=3,frameon=False,fontsize=9)
    fig.suptitle('Scenario effects: higher QoE and lower stalls/delay are better',fontsize=11)
    fig.tight_layout(rect=(0,.16,1,.94));save(fig,'F4-family-effects',figures)
    # F5 fixed, predeclared trajectories, with the worst case explicitly added.
    for family in ['bandwidth_variation','post_handover_recovery']:
        case=next(r['case_id'] for r in controlled if r['family']==family and r['recording_id'].startswith('sey'))
        trajectory(controlled,case,figures,'F5-'+family)
    worst=min(paired['improved']['cases'],key=lambda r:r['difference']);trajectory(controlled,worst['case_id'],figures,'F5-worst-case')
    sensitivity=[]
    for name,field,base in [('stall','stall_s',4),('variation','variation',.3),('latency','latency_area',.1)]:
        for factor in [.5,2]:
            means={}
            for p in policies:
                pool=[r for r in controlled if r['policy']==p]
                values=[]
                for f in FAMILIES:
                    values.append(np.mean([r['metrics']['qoe_per_wall_s']-(factor-1)*base*r['metrics'][field]/r['metrics']['duration_s'] for r in pool if r['family']==f]))
                means[p]=float(np.mean(values))
            sensitivity.append({'coefficient':name,'factor':factor,'qoe':means,'differences':{p:means[p]-means['original'] for p in policies}})
    result={'status':'complete','sessions':len(rows),'controlled_sessions':170,'raw_replay_sessions':9,
        'overall':aggregates,'paired':paired,'families':familyrows,'raw_replay':rawsummary,'sensitivity':sensitivity,
        'worst_improved_case':worst,'uncertainty':freeze['uncertainty'],
        'ledger_sha256':hashlib.sha256((folder/'runs.json').read_bytes()).hexdigest(),
        'scope':'Common actually-played QoE on fixed synthetic-capacity/outage cases with two measured RTT recordings; raw repository replay reported separately'}
    (folder/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({'sessions':len(rows),'primary_effect':paired['improved']},indent=2))

def trajectory(rows,case,figures,name):
    fig,axes=plt.subplots(4,1,figsize=(9,7),sharex=True)
    selected=['original','improved','leo']
    for p in selected:
        row=next(r for r in rows if r['policy']==p and r['case_id']==case and r['repeat']==0)
        payload=load_run(row['run_id']);samples=payload['telemetry.json']['samples'];t=[r['t_s'] for r in samples]
        for ax,field,scale in zip(axes[1:],['played_bitrate_bps','buffer_s','latency_s'],[1e6,1,1]):
            ax.plot(t,[r[field]/scale if r.get(field) is not None else np.nan for r in samples],color=COLORS[p],label=LABELS[p],lw=1)
        if p=='original':
            stages=payload['scenario.json']['stages'];axes[0].step([r['at_s'] for r in stages]+[row['metrics']['duration_s']],[r['rate_mbit'] for r in stages]+[stages[-1]['rate_mbit']],where='post',color='#263B58',label='Capacity')
    for ax,label in zip(axes,['Capacity (Mbps)','Played nominal\nrate (Mbps)','Buffer (s)','Live delay (s)']):ax.set(ylabel=label);ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
    axes[1].legend(ncol=3,fontsize=8,frameon=False);axes[-1].set_xlabel('Wall time (s)');fig.suptitle(case.replace('test-','Held-out: '),fontsize=12);fig.tight_layout();save(fig,name,figures)

if __name__=='__main__':main()
