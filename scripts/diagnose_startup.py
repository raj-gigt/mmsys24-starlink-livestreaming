"""Keep all startup stages, including uncontrolled external time requests."""
from argparse import Namespace,ArgumentParser
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_trial import run
from rl.metrics import evaluate_samples
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'artifacts/final/startup-diagnosis';out.mkdir(parents=True,exist_ok=True)
parser=ArgumentParser();parser.add_argument('--align',action='store_true');parser.add_argument('--local-clock',action='store_true');cli=parser.parse_args()
mode=('host' if cli.local_clock else 'external')+('-aligned' if cli.align else '')
rows=[]
for algorithm,variant in [('abrCMABImproved','guard'),('abrCMAB',None)]:
    args=Namespace(algorithm=algorithm,variant=variant,seconds=18,stages='0:8',target=3,
        catchup='liveCatchupModeLoLP',align_minute=cli.align,local_clock=cli.local_clock,final_telemetry=True,scenario=None,case=None,
        allow_test=False,allow_poor_playback=True)
    with (out/(algorithm+'-'+mode+'-clock.log')).open('w') as log:
        with redirect_stdout(log):summary=run(args)
    data=json.loads((ROOT/'artifacts/runs'/summary['run_id']/'telemetry.json').read_text())
    metrics=evaluate_samples(data['samples'],horizon=18)
    first_request=next((e['t_s'] for e in data['events'] if e['type']=='request-start'),None)
    timing=[{**r,'relative_start_s':(r['start_ms']-data['start_performance_ms'])/1000}
        for r in data['resource_timings'] if any(v in r['name'] for v in ['akamai','stream.mpd'])]
    rows.append({'run_id':summary['run_id'],'algorithm':algorithm,'clock_mode':summary['clock_mode'],'utc_synchronization_enabled':summary['utc_synchronization_enabled'],'startup_s':metrics['startup_s'],
        'first_request_s':first_request,'startup_events':[r for r in data['events'] if r['type'] in ['manifestLoaded','streamInitialized','loadedmetadata','playing']][:5],
        'resources':timing})
    print(json.dumps(rows[-1]),flush=True)
(out/(mode+'-clock.json')).write_text(json.dumps(rows,indent=2))
