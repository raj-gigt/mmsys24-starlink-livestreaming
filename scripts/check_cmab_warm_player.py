"""Verify common prewarm and improved controller in real Chrome playback."""
from argparse import Namespace
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from browser_trial import run
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for algorithm,variant in [('abrCMAB',None),('abrCMABImproved','guard')]:
    args=Namespace(algorithm=algorithm,variant=variant,seconds=35,stages='0:8',target=3,
        catchup='liveCatchupModeLoLP',align_minute=False,final_telemetry=True,scenario=None,case=None,allow_test=False)
    s=run(args);folder=ROOT/'artifacts/runs'/s['run_id'];d=json.loads((folder/'telemetry.json').read_text())
    subprocess.run([sys.executable,'scripts/verify_final_observer.py',s['run_id'],'--require-probes'],check=True)
    loaded=datetime.fromisoformat(s['load_wall_clock_utc']).timestamp()*1000
    first=(d['cmab_decisions'][0]['at_ms']-loaded)/1000
    assert s['runtime_prewarm_ms'] is not None and first < 7,first
    if variant:
        subprocess.run([sys.executable,'scripts/verify_cmab_feedback.py',s['run_id']],check=True)
        assert all(r['action']<=r['guard_maximum'] for r in d['cmab_decisions'])
    rows.append({'status':'complete','run_id':s['run_id'],'algorithm':algorithm,'variant':variant,
        'runtime_prewarm_ms':s['runtime_prewarm_ms'],'first_choice_after_load_s':first})
(ROOT/'artifacts/final/warm-player-check.json').write_text(json.dumps({'status':'PASS','runs':rows},indent=2))
print('PASS: common warm initialization, original decision schedule and real guarded LinTS decisions')
