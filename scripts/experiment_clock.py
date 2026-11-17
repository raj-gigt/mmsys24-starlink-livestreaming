"""Temporarily pause guest NTP corrections; restore the prior service state."""
import argparse,json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['hold','release','status']);args=p.parse_args()
    if os.name=='nt':
        linux='/mnt/'+ROOT.drive[0].lower()+ROOT.as_posix()[2:]
        subprocess.run(['wsl','--distribution','Ubuntu-22.04','--user','root','--cd',linux,'--exec','python3','scripts/experiment_clock.py',args.action],check=True);return
    path=ROOT/'artifacts/final/clock-control.json';state=json.loads(path.read_text()) if path.exists() else {}
    active=subprocess.run(['systemctl','is-active','--quiet','systemd-timesyncd']).returncode==0
    if args.action=='hold':
        if not state.get('held'):
            state.update(was_active=active,held_at_utc=datetime.now(timezone.utc).isoformat(),
                before_status=subprocess.run(['timedatectl','timesync-status'],text=True,capture_output=True).stdout,
                reason='Observed0.41s wall-clock step relative to monotonic time during a browser recording')
        subprocess.run(['systemctl','stop','systemd-timesyncd'],check=True)
        state['held']=True
    elif args.action=='release':
        if state.get('held') and state.get('was_active'):subprocess.run(['systemctl','start','systemd-timesyncd'],check=True)
        state.update(held=False,released_at_utc=datetime.now(timezone.utc).isoformat())
    state.update(current_active=subprocess.run(['systemctl','is-active','--quiet','systemd-timesyncd']).returncode==0,
        checked_at_utc=datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(state,indent=2));print(json.dumps(state,indent=2))
    with (path.parent/'clock-control-history.jsonl').open('a') as f:f.write(json.dumps({'action':args.action,**state})+'\n')
if __name__=='__main__':main()
