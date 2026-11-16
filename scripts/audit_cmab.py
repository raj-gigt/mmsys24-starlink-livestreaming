"""Record the actual reference implementation, runtime and a completed control run."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile
import requests
from browser_trial import docker

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    run = ROOT / 'artifacts/runs' / args.run_id
    summary = json.loads((run / 'summary.json').read_text())
    assert summary['algorithm'] == 'abrCMAB'
    assert summary['played_advance_s'] > 20 and summary['completed_video_requests'] >= 8
    assert summary['mongo_documents']['metric'] > 0
    port = docker('compose', '-f', 'docker-compose-emulation.yaml', 'port', 'pyodide', '80').rsplit(':', 1)[1]
    response = requests.get(f'http://localhost:{port}/pyodide/mabwiser-2.7.0-py3-none-any.whl', timeout=20)
    response.raise_for_status()
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    mab = archive.read('mabwiser/mab.py').decode()
    constants = archive.read('mabwiser/utils.py').decode()
    default_seed = re.search(r'default_seed\s*=\s*(\d+)', constants)
    assert default_seed and 'seed: int = Constants.default_seed' in mab
    paths = ['dash.js/src/streaming/rules/abr/cmab/CMABAbrController.js',
             'dash.js/src/streaming/rules/abr/cmab/CMABRule.js', 'stats-server/app.py']
    controller = (ROOT / paths[0]).read_text()
    original = subprocess.check_output(['git', '-C', str(ROOT/'dash.js'), 'show',
        'f31314a7:src/streaming/rules/abr/cmab/CMABAbrController.js'], text=True)
    stripped = re.sub(r'^        // BEGIN LEO PASSIVE AUDIT\n.*?^        // END LEO PASSIVE AUDIT\n',
                      '', controller, flags=re.M | re.S)
    assert stripped == original, 'Reference decision logic has changed'
    assert 'LearningPolicy.LinTS(alpha=cmab_alpha)' in controller
    assert '_selectedArmsArray.length < cmabArms.length - 1' in controller
    report = {
        'status': 'PASS', 'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'reference_run': args.run_id, 'reference_summary': summary,
        'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'mabwiser_wheel_sha256': hashlib.sha256(response.content).hexdigest(),
        'mabwiser_version': '2.7.0', 'default_seed': int(default_seed.group(1)),
        'observations': ['throughput', 'playback_rate', 'network_latency'],
        'reset_second_boundaries': [12, 27, 42, 57],
        'forced_choices_after_reset': len(summary['ladder']) - 1,
        'feedback': 'Reward computed after selection and before new request completes',
        'rng_finding': 'MAB is constructed with its default seed on each fitted decision; investigate repeated draw initialization',
        'control_decision_logic_unchanged': True,
        'passive_hook_present': controller != stripped,
        'scope': 'Source/runtime audit and useful playback; no performance improvement claim',
    }
    out = ROOT / 'artifacts/final'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'reference-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['status', 'reference_run', 'default_seed', 'forced_choices_after_reset']}, indent=2))


if __name__ == '__main__':
    main()
