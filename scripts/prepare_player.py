"""Restore the parent-packaged dash.js changes in a clean recursive checkout."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PIN='fdd27c559dc2ea8a1e3a6d5f3d4aa88d9bbbbffc'
def git(*args,check=True):
    return subprocess.run(['git',*args],cwd=ROOT,check=check,capture_output=True,text=True)

def main():
    assert git('branch','--show-current').stdout.strip()=='anjan','Switch the parent repository to anjan before applying source changes'
    recorded_pin=git('rev-parse','HEAD:dash.js').stdout.strip()
    assert git('-C','dash.js','rev-parse','HEAD').stdout.strip() in {PIN,recorded_pin},'Unexpected dash.js revision'
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
