"""Use the authors' original plotting code on a selected experiment's MongoDB data."""
from pathlib import Path
import json
import sys
from browser_trial import docker, WSL_ROOT

for run_id in sys.argv[1:]:
    summary_path=Path('artifacts/runs')/run_id/'summary.json'
    seconds=json.loads(summary_path.read_text())['requested_seconds'] if summary_path.exists() else 60
    code = 'from plot import generate_plots; import sys; generate_plots(sys.argv[1],int(sys.argv[2]),3,-1,True)'
    print(docker('run', '--rm', '--network', 'dashjs', '-v', WSL_ROOT + '/figures:/figures',
                 '--entrypoint', 'poetry', 'clarkzjw/dashjs-runner:master', 'run', 'python',
                 '-c', code, run_id, str(seconds)))
    files = list((Path('figures/emulation/target-3s') / run_id).glob('*.png'))
    assert len(files) == 6, (run_id, len(files))
    print(run_id, ': six original-code plots exported')
