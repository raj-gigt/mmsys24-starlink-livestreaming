"""Execute the frozen held-out inventory, sequentially and resumably."""
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime,timezone
import hashlib,json,traceback,subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_trial import run
from freeze_final import identities
from rl.metrics import evaluate_samples
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'artifacts/final/evaluation';freeze_path=out/'freeze.json';freeze=json.loads(freeze_path.read_text())
    assert freeze['sources']==identities(),'Frozen source/config/model has changed; do not mix results'
    digest=hashlib.sha256(freeze_path.read_bytes()).hexdigest();ledger=out/'runs.json'
    rows=json.loads(ledger.read_text()) if ledger.exists() else []
    i=0;attempts={}
    while i<len(freeze['plan']):
        plan=freeze['plan'][i]
        key=f'{digest}:{plan["case_id"]}:{plan["policy"]}:{plan["repeat"]}'
        if any(r['key']==key and r['status']=='complete' for r in rows):i+=1;continue
        attempts[key]=attempts.get(key,0)+1
        manifest=ROOT/plan['workload'];case=next(c for c in json.loads(manifest.read_text())['cases'] if c['id']==plan['case_id'])
        args=Namespace(algorithm=plan['algorithm'],variant=plan.get('variant'),neural_variant=plan.get('neural_variant'),
            seconds=case['seconds'],stages='',target=3,catchup=plan['catchup'],fixed_kbps=-1,
            align_minute=True,local_clock=True,final_telemetry=True,scenario=str(manifest),
            case=case['id'],allow_test=True,allow_poor_playback=True)
        log=out/f'{i:03d}-{plan["policy"]}-attempt{attempts[key]}.log'
        try:
            with log.open('w') as f:
                with redirect_stdout(f):summary=run(args)
            raw=ROOT/'artifacts/runs'/summary['run_id'];t=json.loads((raw/'telemetry.json').read_text())
            assert abs((t['stopped_at_ms']-t['started_at_ms'])/1000-t['samples'][-1]['t_s'])<.1,'Observation clock integrity fault'
            assert max(abs((r['epoch_ms']-t['started_at_ms'])/1000-r['t_s']) for r in t['samples'][1:])<.1,'Within-session clock discontinuity'
            assert summary['actual_abr_strategy']==plan['algorithm'] and summary['auto_switch_video'] is True
            assert summary['clock_mode']=='host' and summary['utc_synchronization_enabled'] is False
            if plan.get('neural_variant'):assert summary['model']['kind']==plan['neural_variant']
            if plan.get('variant'):assert all(r['variant']==plan['variant'] for r in t['cmab_decisions'])
            metrics=evaluate_samples(t['samples'],horizon=case['seconds'])
            assert metrics['played_media_s']<1 or metrics['quality_attribution_fraction']>.99
            row={'key':key,'status':'complete','policy':plan['policy'],'variant':plan['policy'],
                'case_id':case['id'],'family':case['family'],'recording_id':case['recording_id'],
                'repeat':plan['repeat'],'run_id':summary['run_id'],'freeze_sha256':digest,
                'completed_utc':datetime.now(timezone.utc).isoformat(),'metrics':metrics,
                'outcome':'poor_playback' if metrics['played_media_s']<=5 else 'played'}
            rows.append(row);ledger.write_text(json.dumps(rows,indent=2))
            print(json.dumps({'progress':f'{len(rows)}/{len(freeze["plan"])}',**{k:row[k] for k in ['policy','case_id','repeat','run_id']},
                'qoe':metrics['qoe_per_wall_s'],'stalls':metrics['stall_s']}),flush=True)
            i+=1
        except Exception as exc:
            error={'key':key,'plan':plan,'run_id':getattr(args,'_run_id',None),'attempt':attempts[key],'error':traceback.format_exc()}
            (out/f'failure-{i:03d}-attempt{attempts[key]}.json').write_text(json.dumps(error,indent=2))
            # Only an explicit dual-clock inconsistency is automatically retried.
            # Slow inference, no playback and bad QoE are never erased this way.
            clock_fault=isinstance(exc,AssertionError) and str(exc) in ['Observation clock integrity fault','Within-session clock discontinuity']
            if clock_fault:
                invalid_path=out/'invalid-runs.json';invalid=json.loads(invalid_path.read_text()) if invalid_path.exists() else []
                invalid.append({**error,'status':'retained_unscored_retry_same_case','reason':'Measured epoch/monotonic clock inconsistency'})
                invalid_path.write_text(json.dumps(invalid,indent=2))
                if attempts[key]<3:
                    print('Retained clock-invalid recording; retry same frozen case:',error['run_id'],flush=True);continue
            raise
    assert len(rows)==len(freeze['plan']);print('COMPLETE:179 frozen browser trials',flush=True)
if __name__=='__main__':
    subprocess.run([sys.executable,str(ROOT/'scripts/experiment_clock.py'),'hold'],check=True)
    try:main()
    finally:subprocess.run([sys.executable,str(ROOT/'scripts/experiment_clock.py'),'release'],check=True)
