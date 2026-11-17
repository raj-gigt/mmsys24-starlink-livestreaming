"""Allowlist the verified source, portable evidence and deliverables into a ZIP.

The ZIP includes the required dash.js source snapshot; a parent GitHub ZIP alone
cannot include its Git submodules. It excludes environments and resume caches.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_paths():
    paths=set()
    roots=['scripts','rl','configs','models/final','models/reference','data/manifests',
           'data/processed','artifacts/final','reports/final','reports/phase-a','stats-server','shaper',
           'etc','patches','dash.js/src','dash.js/samples/starlink/testplayer']
    for name in roots:
        for path in (ROOT/name).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or '.git' in path.parts:
                continue
            if path.name in ['resume.zip','resume-state.pkl'] or path.suffix=='.pyc':
                continue
            paths.add(path)
    for pattern in ['Dockerfile*','docker-compose*.yaml','requirements*.txt']:
        paths.update(ROOT.glob(pattern))
    paths.update((ROOT/'runner').glob('*.py'))
    paths.update((ROOT/'experiments').glob('batch-*.json'))
    paths.update((ROOT/'assets').glob('*'))
    for name in ['README.md','roadmap.md','deliverables.md','starter.md','LICENSE',
                 '.gitmodules','.gitattributes','.dockerignore','pyproject.toml','poetry.lock',
                 'dash.js/LICENSE.md','dash.js/package.json','dash.js/package-lock.json',
                 'runner/trace/isl-trace.csv',
                 'runner/trace/irtt/seychelles-irtt-10ms-1h-2024-01-30-01-00-00.csv']:
        path=ROOT/name
        if path.is_file():paths.add(path)
    return sorted((p for p in paths if p.is_file()),key=lambda p:p.relative_to(ROOT).as_posix())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='release/Group4-submission.zip')
    args=p.parse_args()
    required=['reports/final/Group4-final-report.pdf','reports/final/Group4-final-presentation.pptx',
              'reports/final/reproduction.md','reports/final/presentation-guide.md',
              'artifacts/final/evaluation/analysis.json','artifacts/final/evaluation/saved-results-check.json']
    for name in required:assert (ROOT/name).is_file(),name
    analysis=json.loads((ROOT/'artifacts/final/evaluation/analysis.json').read_text())
    check=json.loads((ROOT/'artifacts/final/evaluation/saved-results-check.json').read_text())
    assert analysis['sessions']==179 and check['status']=='PASS' and check['inventory_complete']
    assert list((ROOT/'reports/final/demo').glob('*.mp4')),'Real recorded fallback is required'
    paths=payload_paths()
    for path in paths:
        assert path.resolve().is_relative_to(ROOT.resolve())
        assert path.name not in ['.env','credentials.json','token.json']
    files={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
    publication=json.loads((ROOT/'artifacts/final/evaluation/publication.json').read_text())
    manifest={'format':'group4-source-evidence-release-v1',
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'repository':'https://github.com/raj-gigt/mmsys24-starlink-livestreaming/tree/anjan',
        'assembly_parent_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'measured_source_publication':publication,
        'freeze_sha256':sha(ROOT/'artifacts/final/evaluation/freeze.json'),
        'files':files,'payload_bytes':sum(r['bytes'] for r in files.values()),
        'scope':'Required local player source included; pinned images supply unchanged upstream dependencies/media. Full upstream submodules can be obtained recursively from GitHub.',
        'omitted':'Git internals, environments, caches, training resume state, original large Victoria archive (source URL/hash and derived arrays included).',
        'human_outstanding':['Fill actual contribution statements in the intentional template','Portal upload','Team rehearsal']}
    release=ROOT/'release';release.mkdir(exist_ok=True)
    manifest_path=release/'manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True))
    target=Path(args.output);target=target if target.is_absolute() else ROOT/target
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in paths:archive.write(path,path.relative_to(ROOT).as_posix())
        archive.write(manifest_path,'release/manifest.json')
    checksum=sha(target)
    (release/'SHA256SUMS').write_text(checksum+'  '+target.name+'\n')
    print(json.dumps({'zip':str(target),'sha256':checksum,'zip_bytes':target.stat().st_size,'files':len(files)+1}))


if __name__=='__main__':main()
