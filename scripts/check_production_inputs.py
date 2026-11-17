"""Prove inference/RTT work without the injected observer; verify real fallback."""
from argparse import Namespace
from contextlib import redirect_stdout
import json
from pathlib import Path
from browser_trial import run
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'artifacts/final/neural-production';out.mkdir(parents=True,exist_ok=True);reports=[]
for fail in [False,True]:
    args=Namespace(algorithm='abrAnjanRL',neural_variant='leo',variant=None,seconds=18,target=3,stages='0:8',
        catchup='liveCatchupModeLoLP',fixed_kbps=-1,align_minute=False,local_clock=True,final_telemetry=False,
        scenario=None,case=None,allow_test=False,allow_poor_playback=False,simulate_model_failure=fail)
    with (out/('fallback.log' if fail else 'observer-free.log')).open('w') as log:
        with redirect_stdout(log):s=run(args)
    raw=ROOT/'artifacts/runs'/s['run_id'];d=json.loads((raw/'samples.json').read_text())[-1]['decisions']
    assert s['shared_probe_active'] is True and not (raw/'telemetry.json').exists()
    assert d and all(len(r['input'])==64 for r in d)
    if fail:assert all(r['action']==0 and r['result'].get('fallback') and r['result']['reason']=='diagnostic-missing-model' for r in d)
    else:assert any(r['observation']['probe_valid'] for r in d) and not any(r['result'].get('fallback') for r in d)
    reports.append({'run_id':s['run_id'],'status':'PASS','diagnostic_failure_injected':fail,
        'injected_observer':False,'decisions':len(d),'played_advance_s':s['played_advance_s'],
        'completed_video_requests':s['completed_video_requests'],'mongo_metrics':s['mongo_documents']['metric']})
(out/'checks.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports,indent=2))
