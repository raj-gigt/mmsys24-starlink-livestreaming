"""Run a real recovery demonstration; optionally record the existing Chrome screen.

The demo is separate from the frozen final comparison and never alters its ledger.
Run policies sequentially. Watch http://localhost:7900 while this command runs.
"""
from argparse import ArgumentParser, Namespace
from contextlib import redirect_stdout
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from browser_trial import run, docker, WSL_ROOT
from rl.metrics import evaluate_samples
from rl.replay_validation import verify_replay

VIDEO = 'selenium/video@sha256:d3b1cbad721f444a39a8db2ff6d7bbd3a24feccb16f20c8128bf92e6ad5707fd'


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument('--policy',choices=['original','improved','conventional','leo'],default='improved')
    p.add_argument('--record',action='store_true',help='Record Chrome using the upstream Selenium video sidecar')
    args = p.parse_args()
    final = ROOT/'artifacts/final/evaluation/runs.json'
    if final.exists() and len(json.loads(final.read_text())) < 179:
        p.error('The shared Chrome is reserved for the unfinished frozen matrix. Finish that run first.')
    clock = ROOT/'artifacts/final/clock-control.json'
    if clock.exists() and json.loads(clock.read_text()).get('held'):
        p.error('Another experiment holds the clock guard. Do not run concurrent browser sessions.')
    folder = ROOT/'reports/final/demo';folder.mkdir(parents=True,exist_ok=True)
    tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    name = f'leo-demo-{args.policy}-{tag}'
    video_name = name+'.mp4'
    record_started = None
    container = None
    result = None
    subprocess.run([sys.executable,str(ROOT/'scripts/experiment_clock.py'),'hold'],check=True)
    try:
        if args.record:
            container = docker('run','-d','--name',name,'--network','dashjs',
                '-e','DISPLAY_CONTAINER_NAME=192.167.0.102','-e','FILE_NAME='+video_name,
                '-v',WSL_ROOT+'/reports/final/demo:/videos',VIDEO)
            record_started = datetime.now(timezone.utc).isoformat()
        policies = {'original':'abrCMAB','improved':'abrCMABImproved',
                    'conventional':'abrAnjanRL','leo':'abrAnjanRL'}
        manifest = ROOT/'configs/final/workloads/development.json'
        case = next(c for c in json.loads(manifest.read_text())['cases'] if c['family']=='post_handover_recovery')
        trial = Namespace(algorithm=policies[args.policy],variant='guard' if args.policy=='improved' else None,
            neural_variant=args.policy if args.policy in ['conventional','leo'] else None,
            seconds=case['seconds'],stages='',target=3,catchup='liveCatchupModeLoLP',fixed_kbps=-1,
            align_minute=True,local_clock=True,final_telemetry=True,scenario=str(manifest),
            case=case['id'],allow_test=False,allow_poor_playback=True)
        print('Running real '+args.policy+' recovery demo. Open http://localhost:7900 to watch.',flush=True)
        with (folder/(name+'.log')).open('w') as stream:
            with redirect_stdout(stream):summary = run(trial)
        raw = ROOT/'artifacts/runs'/summary['run_id']
        files = ['telemetry.json','summary.json','scenario.json','applied-profile.json','samples.json']
        payload = {n:json.loads((raw/n).read_text()) for n in files}
        telemetry = payload['telemetry.json']
        metrics = evaluate_samples(telemetry['samples'],horizon=case['seconds'])
        assert metrics['played_media_s'] > 5 and summary['completed_video_requests'] >= 3
        assert summary['mongo_documents']['metric'] > 0
        assert max(abs((s['epoch_ms']-telemetry['started_at_ms'])/1000-s['t_s']) for s in telemetry['samples'][1:]) < .1
        replay = verify_replay(payload)
        (folder/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(payload,separators=(',',':'),sort_keys=True).encode(),mtime=0))
        if (raw/'browser.png').exists():
            (folder/(name+'.png')).write_bytes((raw/'browser.png').read_bytes())
        if (raw/'run-timeline.svg').exists():
            (folder/(name+'-timeline.svg')).write_bytes((raw/'run-timeline.svg').read_bytes())
        result = {'status':'PASS','purpose':'real playback demonstration, excluded from final performance comparison',
            'policy':args.policy,'run_id':summary['run_id'],'case_id':case['id'],'metrics':metrics,
            'completed_video_requests':summary['completed_video_requests'],'mongo_documents':summary['mongo_documents'],
            'replay':replay,'record_started_utc':record_started,'video':video_name if args.record else None,
            'recorder_image':VIDEO if args.record else None,'raw_evidence':name+'.json.gz'}
    finally:
        try:
            if container:
                # Graceful stop finalizes MP4. Preserve video/logs on failure.
                try:
                    docker('stop','--time','30',container)
                    (folder/(name+'-recorder.log')).write_text(docker('logs',container),encoding='utf-8')
                finally:
                    docker('rm',container)
        finally:
            subprocess.run([sys.executable,str(ROOT/'scripts/experiment_clock.py'),'release'],check=True)
    if result:
        if args.record:
            video = folder/video_name
            assert video.exists() and video.stat().st_size > 10000,'No usable recording produced'
            result['video_bytes'] = video.stat().st_size
        (folder/(name+'.json')).write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
        subprocess.run([sys.executable,str(ROOT/'scripts/plot_demo_final.py')],check=True)


if __name__ == '__main__':
    main()
