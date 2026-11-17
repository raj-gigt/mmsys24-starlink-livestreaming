"""Seal identities and exact paired inventory before any final performance run."""
import hashlib,json,random,subprocess
from datetime import datetime,timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_trial import docker
ROOT=Path(__file__).resolve().parents[1]
TEXT_SUFFIXES={'.js','.cjs','.ts','.py','.html','.css','.json','.xml','.txt','.yaml','.yml','.md'}

def source_hash(path):
    data=path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith('Dockerfile'):data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()

def identities():
    paths=[]
    for name in ['dash.js/src','dash.js/samples/starlink/testplayer','rl/web']:
        paths.extend(p for p in (ROOT/name).rglob('*') if p.is_file())
    paths.extend(ROOT/p for p in ['scripts/browser_trial.py','scripts/run_final_matrix.py','rl/metrics.py',
        'scripts/experiment_clock.py',
        'shaper/tc-final.py','stats-server/app.py','configs/final/protocol.json',
        'configs/final/workloads/test.json','configs/final/workloads/paper_replay.json',
        'models/final/cmab/manifest.json','models/final/conventional/manifest.json','models/final/leo/manifest.json'])
    paths.extend(ROOT/p for p in ['Dockerfile-player-anjan','docker-compose-emulation.yaml','docker-compose.lock.yaml',
        'docker-compose.phase-a.yaml','docker-compose.player.yaml','docker-compose.final.yaml','requirements-phase-a.txt','requirements-browser.txt'])
    return {p.relative_to(ROOT).as_posix():source_hash(p) for p in sorted(paths)}

def main():
    out=ROOT/'artifacts/final/evaluation';out.mkdir(parents=True,exist_ok=True)
    dest=out/'freeze.json';assert not dest.exists(),'Freeze already exists; do not overwrite after test access'
    selected=json.loads((ROOT/'models/final/cmab/manifest.json').read_text())['variant']
    subprocess.run([sys.executable,str(ROOT/'scripts/experiment_clock.py'),'status'],check=True,stdout=subprocess.DEVNULL)
    clock=json.loads((ROOT/'artifacts/final/clock-control.json').read_text());assert clock['held'] and not clock['current_active']
    assert selected=='guard'
    policies={
        'original':{'algorithm':'abrCMAB'},
        'improved':{'algorithm':'abrCMABImproved','variant':selected},
        'guard_only':{'algorithm':'abrCMABImproved','variant':'guard_only'},
        'throughput':{'algorithm':'abrThroughput'},'bola':{'algorithm':'abrBola'},
        'conventional':{'algorithm':'abrAnjanRL','neural_variant':'conventional'},
        'leo':{'algorithm':'abrAnjanRL','neural_variant':'leo'}}
    cases=json.loads((ROOT/'configs/final/workloads/test.json').read_text())['cases'];plan=[]
    order=list(policies);random.Random(1804).shuffle(order)
    for repeat in range(3):
        for i,case in enumerate(cases):
            group=order if repeat<2 else [p for p in order if p in ['original','improved','guard_only']]
            shift=(i+repeat)%len(group);group=group[shift:]+group[:shift]
            for p in group:plan.append({'case_id':case['id'],'policy':p,'repeat':repeat,
                'workload':'configs/final/workloads/test.json','catchup':'liveCatchupModeLoLP',**policies[p]})
    raw=json.loads((ROOT/'configs/final/workloads/paper_replay.json').read_text())['cases'][0]
    for repeat in range(3):
        group=['original','improved','guard_only'];group=group[repeat:]+group[:repeat]
        for p in group:plan.append({'case_id':raw['id'],'policy':p,'repeat':repeat,
            'workload':'configs/final/workloads/paper_replay.json','catchup':'liveCatchupModeCMAB',**policies[p]})
    assert len(plan)==179
    source=identities()
    # Running build must contain exact source/actor assets, not an upstream image.
    targets={}
    for path,sha in source.items():
        if path.startswith('rl/web/'):target='/dash.js/anjan/'+path[len('rl/web/'):]
        elif path.startswith('dash.js/'):target='/'+path
        else:continue
        targets[target]=sha
    # Batch source checks and normalize only CRLF/LF for portable Git checkouts.
    code="const fs=require('fs'),crypto=require('crypto'),p=require('path');for(const name of process.argv.slice(1)){let b=fs.readFileSync(name);if(['.js','.cjs','.ts','.py','.html','.css','.json','.xml','.txt','.yaml','.yml','.md'].includes(p.extname(name).toLowerCase()))b=Buffer.from(b.toString('utf8').replace(/\\r\\n/g,'\\n'));console.log(crypto.createHash('sha256').update(b).digest('hex')+' '+name)}"
    names=list(targets)
    for i in range(0,len(names),40):
        output=docker('exec','leo_abr_rl-dashjs-1','node','-e',code,*names[i:i+40])
        for line in output.splitlines():
            actual,name=line.split(' ',1);assert targets[name]==actual,('Rebuild player before freezing',name)
    result={'frozen_utc':datetime.now(timezone.utc).isoformat(),'status':'frozen_before_test_access',
        'parent_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'player_revision':subprocess.check_output(['git','-C','dash.js','rev-parse','HEAD'],text=True).strip(),
        'sources':source,'source_hash_normalization':'Text CRLF converted to LF only; native checkpoint hashes remain exact raw bytes. Release manifest also preserves exact file-byte identities.',
        'raw_source_byte_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source},
        'policies':policies,'plan':plan,
        'runtime_images':docker('inspect','--format','{{.Name}} {{.Config.Image}} {{.Image}}',
            'leo_abr_rl-dashjs-1','leo_abr_rl-chrome-1','dashjs-nginx','leo_abr_rl-stat-server-1').splitlines(),
        'extension_reason':'Guard-only competitive in development and validation; include as separate heuristic control before test access',
        'aggregation':'Equal five-family weights, equal case weights within family; raw replay separate',
        'uncertainty':'Keep10 cases fixed; resample paired browser repeats within each case for conditional95% repeatability intervals. Related windows are not resampled as independent recordings. Raw case/source effects remain descriptive; no Starlink population interval.',
        'trajectory_selection':'First Seychelles case for bandwidth_variation and post_handover_recovery, repeat0; add worst improved-vs-original QoE case to expose regression',
        'clock':'Verified shared-WSL guest clock; phase scheduled from browser guest epoch; guest NTP service temporarily paused and restored after testing; per-sample epoch/monotonic checks',
        'negative_outcome':'Retain results; no test tuning. Any revised controller needs sealed reserve cohort and explicit new protocol.'}
    dest.write_text(json.dumps(result,indent=2));print('FROZEN179 exact trials; no test performance read')
if __name__=='__main__':main()
