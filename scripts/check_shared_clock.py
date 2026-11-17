"""Verify the emulator-only host-clock assumption using WSL/Linux time."""
import json
import os
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]
def main():
    if os.name=='nt':
        linux='/mnt/'+ROOT.drive[0].lower()+ROOT.as_posix()[2:]
        subprocess.run(['wsl','--distribution','Ubuntu-22.04','--user','root','--cd',linux,'--exec','python3','scripts/check_shared_clock.py'],check=True)
        return
    rows=[]
    for name,command in [('leo_abr_rl-dashjs-1',['node','-e','console.log(Date.now()/1000)']),
                         ('dashjs-nginx',['python3','-c','import time;print(time.time())']),
                         ('leo_abr_rl-stat-server-1',['python3','-c','import time;print(time.time())'])]:
        before=time.time();remote=float(subprocess.check_output(['docker','exec',name,*command],text=True));after=time.time()
        assert before-.02<=remote<=after+.02,(name,before,remote,after)
        rows.append({'container':name,'container_unix_s':remote,'wsl_before_s':before,'wsl_after_s':after,'midpoint_difference_s':remote-(before+after)/2})
    result={'status':'PASS','reference':'Shared WSL/Linux kernel clock, not Windows command-dispatch clock',
        'scope':'Single-host emulator only; not remote client/server clock synchronization','checks':rows}
    (ROOT/'artifacts/final/shared-clock-check.json').write_text(json.dumps(result,indent=2))
    print('PASS: browser, media and statistics clocks agree with shared kernel within command bounds')
if __name__=='__main__':main()
