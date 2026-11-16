"""Maintain resumable final-project progress and the existing roadmap tracker."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def update(step, status, evidence):
    folder = ROOT / 'artifacts/final'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'state.json'
    state = json.loads(path.read_text()) if path.exists() else {
        'submission_deadline': '2026-11-18T08:00:00+05:30',
        'presentation': '2026-11-20T11:00:00+05:30',
        'authorization': {'autonomous_execution': True, 'commit_push': True,
                          'basis': 'User: you can commit/push whenever you need to'},
        'steps': {},
    }
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    state['steps'][str(step)] = {'status': status, 'evidence': evidence,
                                 'updated_utc': state['updated_utc']}
    state['current_step'] = step
    path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    roadmap = ROOT / 'roadmap.md'
    text = roadmap.read_text(encoding='utf-8')
    text = re.sub(rf'(^\| {step} \| )[^|]+(\| )[^\n]+',
                  lambda m: m[1] + status + ' ' + m[2] + evidence + ' |', text, flags=re.M)
    text = re.sub(rf'(### Step {step} -[^\n]*\n\*\*Status:\*\* )[^.\n]+',
                  lambda m: m[1] + status, text)
    roadmap.write_text(text, encoding='utf-8')
    print(json.dumps(state['steps'][str(step)]))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('step', type=int)
    p.add_argument('status')
    p.add_argument('evidence')
    args = p.parse_args()
    update(args.step, args.status, args.evidence)
