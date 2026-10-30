"""Short playback checks, not a matched-performance study."""
from argparse import Namespace
import json
from pathlib import Path
from browser_trial import run

rows = []
for algorithm, catchup in [('abrDynamic', 'liveCatchupModeDefault'),
                          ('abrL2A', 'liveCatchupModeDefault'),
                          ('abrLoLP', 'liveCatchupModeLoLP')]:
    rows.append(run(Namespace(algorithm=algorithm, catchup=catchup, seconds=45,
                              stages='', target=3)))
out = Path('artifacts/baselines')
out.mkdir(parents=True, exist_ok=True)
(out / 'smoke-summary.json').write_text(json.dumps(rows, indent=2))
