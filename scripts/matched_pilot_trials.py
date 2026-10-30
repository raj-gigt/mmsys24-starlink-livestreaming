"""Three matched short demonstrations, not a statistically powered evaluation."""
from argparse import Namespace
import json
from pathlib import Path
from browser_trial import run

rows=[]
out=Path('artifacts/integration/matched-pilot-trials.json')
out.parent.mkdir(parents=True,exist_ok=True)
for algorithm in ['abrAnjanRL','abrCMAB','abrAnjanSimple']:
    summary=run(Namespace(algorithm=algorithm,catchup='liveCatchupModeLoLP',target=3,
                          seconds=75,stages='0:8,25:1,50:8',align_minute=True))
    rows.append(summary)
    out.write_text(json.dumps({'scope':'Single matched short integration demonstrations; no CMAB improvement claim.',
        'matching':'Common custom build, source phase at minute boundary, target3s, LoL+ catch-up, 8/1/8Mbps,40ms,zero configured loss',
        'runs':rows},indent=2))
    print('VERIFIED PLAYBACK:',algorithm,summary['run_id'],flush=True)
