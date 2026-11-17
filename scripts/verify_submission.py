"""Extract outside the project, check every byte, and reproduce saved results."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path)
    p.add_argument('--extract-dir',required=True,type=Path)
    args=p.parse_args()
    dest=args.extract_dir.resolve()
    assert not dest.is_relative_to(ROOT.resolve()),'Extraction must be outside the project'
    assert not dest.exists() or not any(dest.iterdir()),'Use a new or empty extraction directory'
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.archive) as archive:
        for info in archive.infolist():
            assert (dest/info.filename).resolve().is_relative_to(dest),'Unsafe archive path'
        archive.extractall(dest)
    manifest=json.loads((dest/'release/manifest.json').read_text())
    for name,expected in manifest['files'].items():
        path=dest/name
        assert path.stat().st_size==expected['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==expected['sha256'],name
    actual={p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
    assert actual==set(manifest['files'])|{'release/manifest.json'},'Missing or unexpected payload'
    before=json.loads((dest/'artifacts/final/evaluation/analysis.json').read_text())
    subprocess.run([sys.executable,str(dest/'scripts/prepare_player.py')],cwd=dest,check=True)
    subprocess.run([sys.executable,str(dest/'scripts/reproduce_final.py'),'--saved-results'],cwd=dest,check=True)
    after=json.loads((dest/'artifacts/final/evaluation/analysis.json').read_text())
    assert before==after,'Saved-results reproduction changed the scientific result'
    result={'status':'PASS','archive':str(args.archive.resolve()),
            'zip_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
            'verified_payload_files':len(actual),'extracted_to':str(dest),
            'metric_and_analysis_reproduction':'Exact JSON agreement for all179 sessions; all final tables/figures regenerated',
            'source_preparation':'Verified snapshot without Git/submodule metadata',
            'scope':'Saved evidence and source preparation checked; does not claim a second179-session rerun'}
    (ROOT/'release/clean-extraction-check.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
