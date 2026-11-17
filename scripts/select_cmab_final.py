"""Frozen validation-only bandit selection, with physical/useful-playback gates."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=['steady_bandwidth','bandwidth_variation','rtt_variation','handover_interruption','post_handover_recovery']
METRICS=['qoe_per_wall_s','stall_s','startup_s','p95_live_latency_s','mean_live_latency_s',
    'played_bitrate_bps','switches','played_media_s','skipped_media_s']

def summarize(rows):
    variants=sorted({r['variant'] for r in rows});result={}
    for variant in variants:
        pool=[r for r in rows if r['variant']==variant]
        families={family:[r for r in pool if r['family']==family] for family in FAMILIES}
        assert all(families.values()),'Missing mandatory family'
        means={key:sum(sum(r['metrics'][key] for r in group)/len(group) for group in families.values())/len(FAMILIES) for key in METRICS}
        assert all(math.isfinite(v) for v in means.values())
        means['minimum_played_fraction']=min(r['metrics']['played_media_s']/r['metrics']['duration_s'] for r in pool)
        means['mixed_stress_qoe']=sum(r['metrics']['qoe_per_wall_s'] for r in pool if r['family']=='mixed_shifted')/max(1,sum(r['family']=='mixed_shifted' for r in pool))
        result[variant]=means
    return result

def choose(rows,rule,protocol):
    summary=summarize(rows);baseline=summary['original'];selection=protocol['selection'];eligible=[];gates={}
    horizon=sum(r['metrics']['duration_s'] for r in rows)/len(rows)
    for variant in rule['candidate_bandits']:
        m=summary[variant]
        tests={'useful_playback':m['minimum_played_fraction']>=rule['minimum_candidate_played_fraction_each_case'],
            'stalls':m['stall_s']-baseline['stall_s']<=max(selection['max_extra_mean_stall_s']*horizon/120,selection['max_extra_mean_stall_fraction']*baseline['stall_s']),
            'tail_delay':m['p95_live_latency_s']-baseline['p95_live_latency_s']<=selection['max_extra_p95_latency_s'],
            'startup':m['startup_s']-baseline['startup_s']<=selection['max_extra_startup_s']}
        gates[variant]=tests
        if all(tests.values()):eligible.append(variant)
    chosen=max(eligible,key=lambda v:summary[v]['qoe_per_wall_s']) if eligible else None
    return {'selected':chosen,'eligibility':gates,'summary':summary,'status':'selected' if chosen else 'no_eligible_bandit'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--ledger',default='artifacts/final/validation/finalists-v1/runs.json');args=p.parse_args()
    rule=json.loads((ROOT/'configs/final/validation-selection.json').read_text());protocol=json.loads((ROOT/'configs/final/protocol.json').read_text())
    path=ROOT/args.ledger;rows=json.loads(path.read_text());cases=json.loads((ROOT/'configs/final/workloads/validation.json').read_text())['cases']
    expected={(c['id'],v,rep) for c in cases for v in rule['candidate_bandits']+rule['controls'] for rep in range(rule['repetitions'])}
    assert len(rows)==len(expected) and {(r['case_id'],r['variant'],r['repeat']) for r in rows}==expected,'Validation matrix incomplete or duplicated'
    assert all(r['status']=='complete' and r['metrics']['metric_version']==protocol['metrics']['version'] for r in rows)
    assert len({json.dumps(r['source_identity'],sort_keys=True) for r in rows})==1
    assert len({json.dumps(r['measurement_identity'],sort_keys=True) for r in rows})==1
    result=choose(rows,rule,protocol)
    result.update(ledger=args.ledger,scope='Validation selection; no final-test scores inspected',
        limitations='One session per case/policy; descriptive component ablations, not statistical proof')
    if result['selected']:
        selected=result['summary'][result['selected']]
        result['qoe_delta_vs_original']=selected['qoe_per_wall_s']-result['summary']['original']['qoe_per_wall_s']
        result['qoe_delta_vs_guard_only']=selected['qoe_per_wall_s']-result['summary']['guard_only']['qoe_per_wall_s']
        manifest={'label':'Validation-selected CMAB refinement','algorithm':'abrCMABImproved','variant':result['selected'],
            'type':'Online contextual bandit with optional action ceiling; not RL',
            'runtime':'Synchronous Pyodide0.23.4 / MABWiser2.7.0',
            'fit_scope':'Within each session, only unique linked completed-request outcomes; fresh state each session',
            'offline_pretrained_weights':False,'history_rows':30,'alpha':1,'default_seed':123456,
            'source_revision':subprocess.check_output(['git','-C',str(ROOT/'dash.js'),'rev-parse','HEAD'],text=True).strip(),
            'source_sha256':rows[0]['source_identity'],'measurement_identity':rows[0]['measurement_identity'],
            'configuration':'configs/final/cmab_variants.json','selection':'artifacts/final/validation/finalists-v1/selection.json',
            'reward_qualification':'Download-outcome surrogate, not actual played quality; cancellations/unmatched requests are censored'}
        folder=ROOT/'models/final/cmab';folder.mkdir(parents=True,exist_ok=True)
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (path.parent/'selection.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if not result['selected']:raise SystemExit(2)
if __name__=='__main__':main()
