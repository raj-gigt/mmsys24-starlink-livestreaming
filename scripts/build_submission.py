"""Build the submission-only ZIP from explicit dependencies and selected evidence."""
import argparse
from datetime import datetime,timezone
import hashlib,json,subprocess,zipfile
from pathlib import Path
from submission_inventory import inventory
ROOT=Path(__file__).resolve().parents[1]

def digest(data):return hashlib.sha256(data).hexdigest()
def encoded(obj):return (json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='release/Group4-submission.zip');args=p.parse_args()
 required=['README.md','reports/final/Group4-final-report.pdf','reports/final/reproduction.md',
   'artifacts/final/evaluation/four-policy-analysis.json','artifacts/final/evaluation/saved-results-check.json']
 for name in required:assert (ROOT/name).is_file(),name
 check=json.loads((ROOT/required[-1]).read_text());assert check['status']=='PASS' and check['verified_sessions']==179 and check['inventory_complete']
 plan=inventory();assert not plan['missing_required'],plan['missing_required']
 release=ROOT/'release';release.mkdir(exist_ok=True)
 invpath=release/'submission-files.json';invpath.write_bytes(encoded(plan))
 payload={}
 for name in plan['files']:
  path=ROOT/name
  assert path.resolve().is_relative_to(ROOT.resolve()) and path.name not in ['.env','credentials.json','token.json'],name
  assert not any(part in ['__pycache__','.git','demo'] for part in path.relative_to(ROOT).parts),name
  assert path.suffix.lower() not in ['.pptx','.mp4','.pyc'],name
  payload[name]=path.read_bytes()
 index=json.loads(payload['artifacts/final/evidence/index.json'])
 subset={run:index[run] for run in plan['portable_run_ids']}
 assert len(subset)==185
 for row in subset.values():assert row['file'] in payload and digest(payload[row['file']])==row['sha256']
 payload['artifacts/final/evidence/index.json']=encoded(subset)
 payload['release/submission-files.json']=invpath.read_bytes()
 files={name:{'sha256':digest(data),'bytes':len(data)} for name,data in sorted(payload.items())}
 publication=json.loads((ROOT/'artifacts/final/evaluation/publication.json').read_text())
 manifest={'format':'group4-source-evidence-release-v2','created_utc':datetime.now(timezone.utc).isoformat(),
  'repository':'https://github.com/raj-gigt/mmsys24-starlink-livestreaming/tree/anjan',
  'assembly_parent_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'measured_source_publication':publication,
  'freeze_sha256':digest((ROOT/'artifacts/final/evaluation/freeze.json').read_bytes()),
  'files':files,'payload_bytes':sum(r['bytes'] for r in files.values()),'portable_event_runs':185,
  'scope':'Focused submission: report, developed source with original dependency paths, full measured player snapshot, selected native/JS models, compact data and 179 final plus six calibration raw event payloads.',
  'external_dependencies':'Pinned Docker dependency/media images for new browser experiments; Python libraries from requirements. Saved results require only numpy/matplotlib.',
  'transformation':'Only portable evidence index is subset to the 185 bundled run payloads; parent full research index remains unchanged.',
  'excluded_categories':plan['excluded_categories'],
  'human_outstanding':['Individual contribution statements intentionally remain blank per user instruction','Portal upload by user'],
  'presentation_scope':'Deferred; no presentation/demo/learning files or execution requirement in this release'}
 manifest_bytes=encoded(manifest);(release/'manifest.json').write_bytes(manifest_bytes)
 target=Path(args.output);target=target if target.is_absolute() else ROOT/target;target.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
  for name,data in sorted(payload.items()):archive.writestr(name,data)
  archive.writestr('release/manifest.json',manifest_bytes)
 checksum=digest(target.read_bytes());(release/'SHA256SUMS').write_text(checksum+'  '+target.name+'\n')
 print(json.dumps({'zip':str(target),'sha256':checksum,'zip_bytes':target.stat().st_size,'files':len(files)+1,'portable_event_runs':185}))

if __name__=='__main__':main()
