"""Retrieve both public branches afresh and check measured source identities."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1]
TEXT={'.js','.cjs','.ts','.py','.html','.css','.json','.xml','.txt','.yaml','.yml','.md'}


def git(folder,*args):
    return subprocess.check_output(['git','--git-dir='+str(folder),*args])


def verify(cache):
    repos={'parent':'https://github.com/raj-gigt/mmsys24-starlink-livestreaming',
           'player':'https://github.com/anjanrd/dash.js'}
    revisions={};archives={}
    freeze=json.loads((ROOT/'artifacts/final/evaluation/freeze.json').read_text())
    for kind,url in repos.items():
        folder=cache/kind;folder.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','init','--bare',str(folder)],check=True,stdout=subprocess.DEVNULL)
        # Fetch the parent's exact player pin even if a teammate has advanced
        # the player branch; recursive clones also resolve this pinned object.
        ref='anjan' if kind=='parent' else git(cache/'parent','ls-tree','FETCH_HEAD','dash.js').decode().split()[2]
        subprocess.run(['git','--git-dir='+str(folder),'fetch','--depth=1',url,ref],check=True)
        revisions[kind]=git(folder,'rev-parse','FETCH_HEAD').decode().strip()
        if kind=='player':names=['src','samples/starlink/testplayer']
        else:names=[p for p in freeze['sources'] if not p.startswith('dash.js/')]
        data=git(folder,'archive','FETCH_HEAD','--',*names)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archives[kind]={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    pointer=git(cache/'parent','ls-tree','FETCH_HEAD','dash.js').decode().split()[2]
    assert pointer==revisions['player'],'Parent submodule does not pin the retrieved player branch'
    for name,expected in freeze['sources'].items():
        kind='player' if name.startswith('dash.js/') else 'parent'
        key=name[len('dash.js/'):] if kind=='player' else name
        data=archives[kind][key]
        if Path(key).suffix.lower() in TEXT or Path(key).name.startswith('Dockerfile'):
            data=data.replace(b'\r\n',b'\n')
        assert hashlib.sha256(data).hexdigest()==expected,name
    result={'status':'PASS','parent_revision':revisions['parent'],'player_revision':revisions['player'],
            'verified_frozen_files':len(freeze['sources']),
            'method':'Fresh public shallow fetches, tar object contents and parent submodule pin; not local remote-tracking refs',
            'scope':'Measured file contents recoverable from published parent and player fork'}
    out=ROOT/'artifacts/final/remote-retrieval-check.json';out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-dir',type=Path);args=p.parse_args()
    if args.cache_dir:
        cache=args.cache_dir.resolve();assert not cache.is_relative_to(ROOT.resolve())
        verify(cache)
    else:
        with tempfile.TemporaryDirectory(prefix='leo-publication-') as directory:verify(Path(directory))


if __name__=='__main__':main()
