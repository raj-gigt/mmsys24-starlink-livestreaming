"""Recreate the player changes from the parent patch in external build scratch."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
cache=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.cache')))/'LEO-RL/cache/builds'
cache.mkdir(parents=True,exist_ok=True)
scratch=cache/('player-patch-check-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
assert not scratch.exists()
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True)
run(['git','clone','--shared','--no-checkout',str(root/'dash.js'),str(scratch)])
assert run(['git','-C',str(scratch),'rev-parse','refs/heads/anjan']).stdout.strip()=='fdd27c559dc2ea8a1e3a6d5f3d4aa88d9bbbbffc'
run(['git','-C',str(scratch),'checkout','anjan'])
patch=root/'patches/dashjs-anjan.patch'
run(['git','-C',str(scratch),'apply','--check',str(patch)])
run(['git','-C',str(scratch),'apply',str(patch)])
files=['samples/starlink/testplayer/testplayer.html','src/streaming/constants/Constants.js',
       'src/streaming/rules/abr/ABRRulesCollection.js','src/streaming/rules/abr/anjan/AnjanRule.js']
def normalized(path):return path.read_text(encoding='utf-8').replace('\r\n','\n').encode()
hashes={}
for name in files:
    actual=normalized(scratch/name);expected=normalized(root/'dash.js'/name)
    assert actual==expected,name
    hashes[name]=hashlib.sha256(actual).hexdigest()
report={'status':'PASS','base_commit':'fdd27c559dc2ea8a1e3a6d5f3d4aa88d9bbbbffc',
    'scratch_branch':'anjan','patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),
    'files_recreated_identically':hashes,'method':'Fresh shared clone outside the project, branch created before patch application',
    'scratch_path':str(scratch)}
(root/'artifacts/setup/patch-reproducibility.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
