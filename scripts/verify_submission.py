"""Clean extraction, byte checks and exact evidence reproduction outside the project."""
import argparse,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--extract-dir',required=True,type=Path);args=p.parse_args()
 dest=args.extract_dir.resolve();assert not dest.is_relative_to(ROOT.resolve()),'Use an external extraction path'
 assert not dest.exists() or not any(dest.iterdir()),'Use a new or empty extraction directory'
 dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(args.archive) as archive:
  names=archive.namelist();assert len(names)==len(set(names)),'Duplicate ZIP names'
  for info in archive.infolist():assert (dest/info.filename).resolve().is_relative_to(dest),'Unsafe archive path'
  archive.extractall(dest)
 manifest=json.loads((dest/'release/manifest.json').read_text())
 for name,row in manifest['files'].items():
  data=(dest/name).read_bytes();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],name
 actual={p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
 assert actual==set(manifest['files'])|{'release/manifest.json'},'Missing or unexpected payload'
 assert not (dest/'.git').exists()
 for name in actual:
  path=Path(name);assert path.suffix.lower() not in ['.pptx','.mp4','.pyc'] and not any(p in ['.git','__pycache__','demo'] for p in path.parts),name
 index=json.loads((dest/'artifacts/final/evidence/index.json').read_text());assert len(index)==185
 assert {r['file'] for r in index.values()}=={n for n in actual if n.startswith('artifacts/final/evidence/') and n.endswith('.json.gz')}
 analyses=['analysis','four-policy-analysis','contrasts','deployment']
 before={n:json.loads((dest/f'artifacts/final/evaluation/{n}.json').read_text()) for n in analyses}
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MPLBACKEND':'Agg'}
 for name,extra in [('prepare_player.py',[]),('reproduce_final.py',['--saved-results'])]:
  subprocess.run([sys.executable,str(dest/'scripts'/name),*extra],cwd=dest,env=env,check=True)
 after={n:json.loads((dest/f'artifacts/final/evaluation/{n}.json').read_text()) for n in analyses}
 assert before==after,'Scientific analysis changed under saved-results reproduction'
 result={'status':'PASS','archive':str(args.archive.resolve()),'zip_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
  'verified_payload_files':len(actual),'portable_event_runs':len(index),'extracted_to':str(dest),
  'python':sys.executable,'scientific_reproduction':'Exact JSON agreement for full179-session analysis, balanced80-session/all6 contrasts, supporting contrasts and deployment summaries',
  'source_preparation':'Verified player source snapshot without Git/submodule metadata',
  'payload_checks':'Every file hash/size, exact inventory, no duplicate or unsafe paths, no presentation/video/cache files, exact portable event-index closure',
  'scope':'Saved evidence recomputation and source preparation, not a second179-session browser campaign'}
 (ROOT/'release/clean-extraction-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
