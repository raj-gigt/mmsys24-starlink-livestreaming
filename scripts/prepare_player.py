"""Restore the parent-packaged dash.js changes in a clean recursive checkout."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PIN='fdd27c559dc2ea8a1e3a6d5f3d4aa88d9bbbbffc'
def git(*args,check=True):
    return subprocess.run(['git',*args],cwd=ROOT,check=check,capture_output=True,text=True)

def main():
    if not (ROOT/'.git').exists():
        # Submission ZIPs contain the exact required player snapshot, not Git
        # submodule metadata. Verify its byte manifest before building it.
        manifest_path=ROOT/'release/manifest.json'
        if not manifest_path.is_file():
            raise RuntimeError('Not a Git checkout or a manifested submission snapshot')
        manifest=json.loads(manifest_path.read_text())
        required=[name for name in manifest['files'] if name.startswith(('dash.js/src/','dash.js/samples/starlink/testplayer/','rl/web/'))]
        assert required and 'dash.js/src/streaming/rules/abr/anjan/AnjanRule.js' in required
        for name in required:
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest['files'][name]['sha256'],name
        print('Verified manifested player source snapshot; no historical patch or Git metadata required.')
        return
    recorded_pin=git('rev-parse','HEAD:dash.js').stdout.strip()
    assert git('-C','dash.js','rev-parse','HEAD').stdout.strip() in {PIN,recorded_pin},'Unexpected dash.js revision'
    committed_rule=git('-C','dash.js','cat-file','-e','HEAD:src/streaming/rules/abr/anjan/AnjanRule.js',check=False)
    if committed_rule.returncode == 0:
        print('Committed custom player source present; preserve local edits and build this checkout.')
        return
    branch=git('-C','dash.js','branch','--show-current').stdout.strip()
    if branch!='anjan':
        if not branch:
            existing=git('-C','dash.js','show-ref','--verify','--quiet','refs/heads/anjan',check=False).returncode==0
            git('-C','dash.js','switch',*(['anjan'] if existing else ['-c','anjan']))
        else:raise RuntimeError('Switch the player submodule to anjan before applying the packaged patch')
    patch=str(ROOT/'patches/dashjs-anjan.patch')
    if git('-C','dash.js','apply','--reverse','--check',patch,check=False).returncode==0:
        print('Packaged player source is already applied.');return
    check=git('-C','dash.js','apply','--check',patch,check=False)
    if check.returncode:raise RuntimeError('Player source differs from the packaged patch; preserve edits and inspect before applying.\n'+check.stderr)
    git('-C','dash.js','apply',patch)
    print('Packaged player patch applied on anjan.')

if __name__=='__main__':main()
