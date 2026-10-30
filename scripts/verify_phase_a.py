"""Final evidence audit. Reads completed outputs; does not rerun experiments/training."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def main():
    assert git('branch','--show-current')=='anjan'
    assert git('-C','dash.js','branch','--show-current')=='anjan'
    assert git('-C','dash.js','rev-parse','HEAD')==git('rev-parse','HEAD:dash.js')
    assert git('-C','livesim2','status','--porcelain')==''
    assert git('-C','paper-data','status','--porcelain')==''
    assert (ROOT/'artifacts/setup/net-admin.txt').stat().st_size>0
    reproduction=read('artifacts/reproduction/verification.json')
    assert reproduction['figure_count']==25
    for row in reproduction['figures']:
        with Image.open(ROOT/row['path']) as im:im.verify()
    baselines=read('artifacts/baselines/verified.json')['runs']
    assert {r['algorithm'] for r in baselines}=={'abrCMAB','abrDynamic','abrL2A','abrLoLP'}
    assert all(r['played_advance_s']>5 and r['mongo_documents']['metric']>0 for r in baselines)
    for row in baselines:
        assert len(list((ROOT/'figures/emulation/target-3s'/row['run_id']).glob('*.png')))==6
    link=read('artifacts/setup/link-verification.json')
    assert len(link['capacity_checks'])==2 and '100% packet loss' in link['outage_ping']
    data=read('artifacts/data/verification.json')
    assert data['status']=='PASS' and data['total_scenarios']==84 and data['deterministic_regeneration']=='PASS'
    assert len(read('data/manifests/media.json')['representations'])==8
    assert read('data/manifests/lens-reserve.json')['gzip_crc_check']=='PASS'
    reference=read('artifacts/exports/reference-parity.json')
    pilot=read('artifacts/exports/pilot-parity.json')
    browser=read('artifacts/exports/browser-parity-and-timing.json')
    assert all(x['status']=='PASS' and x['action_agreement']==1 for x in [reference,pilot,browser])
    assert browser['met_target_on_this_host']
    assert read('artifacts/training/learning-verification.json')['status']=='PASS'
    model=read('models/pilot/manifest.json')
    assert sha('models/pilot/checkpoint.zip')==model['checkpoint_sha256']
    assert sha('rl/web/pilot_model.js')==model['actor_js_sha256']
    patch=read('artifacts/setup/patch-reproducibility.json')
    assert patch['status']=='PASS' and patch['patch_sha256']==sha('patches/dashjs-anjan.patch')
    matched=read('artifacts/integration/matched-pilot-trials.json')['runs']
    assert len(matched)==3
    for row in matched:
        assert row['played_advance_s']>5
        assert datetime.fromisoformat(row['load_wall_clock_utc']).second<2
        assert row['catchup']=='liveCatchupModeLoLP' and row['target_latency_s']==3
        assert [x['rate_mbit'] for x in row['controlled_stages']]==[8,1,8]
        assert all(abs(row['controlled_stages'][i]['at_s']-t)<1 for i,t in [(1,25),(2,50)])
        assert row['build']=='anjan-phase-a-20261030-local-source-v1'
        assert not row['player_errors'],row['player_errors']
        if row['algorithm']=='abrCMAB':assert row['mongo_documents']['qoe']>0
        else:
            integration=read('artifacts/integration/'+row['run_id']+'.json')
            assert integration['fallbacks']==0 and integration['matched_completed_requests']>=5
        assert len(list((ROOT/'figures/emulation/target-3s'/row['run_id']).glob('*.png')))==6
    for folder in ['scripts','rl']:
        for source in (ROOT/folder).rglob('*.py'):compile(source.read_text(encoding='utf-8'),str(source),'exec')
    assert not (ROOT/'tmp').exists()
    for path in ['reports/phase-a/matched-playback.png','artifacts/training/pilot-learning.png','reports/phase-a/neural-player.png']:
        with Image.open(ROOT/path) as im:im.verify()
    report={'status':'PASS','completed_utc':datetime.now(timezone.utc).isoformat(),
        'steps':{str(i):'Complete' for i in range(1,7)},'branch':'anjan',
        'archived_figures':25,'existing_baseline_algorithms_checked':4,'matched_fresh_demo_runs':3,
        'native_reference_fixtures':reference['fixtures'],'pilot_fixtures':pilot['fixtures'],
        'real_chrome_decisions_verified':browser['actual_chrome_decisions'],
        'complete_decision_p99_ms':browser['complete_new_decision_p50_p95_p99_ms'][-1],
        'test_used_for_model_selection':False,'step7_executed':False,
        'limitations':['Integration pilot, not final LEO-aware model','No statistically supported CMAB improvement claim',
                       'Training capacity synthetic; one pilot seed; incomplete browser calibration','StarNet throughput not imported']}
    (ROOT/'artifacts/phase-a-completion.json').write_text(json.dumps(report,indent=2))
    index=read('reports/phase-a/evidence-index.json');index['phase_a_steps_1_to_6']='Complete; final evidence audit PASS';index['completion_record']='artifacts/phase-a-completion.json'
    (ROOT/'reports/phase-a/evidence-index.json').write_text(json.dumps(index,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
