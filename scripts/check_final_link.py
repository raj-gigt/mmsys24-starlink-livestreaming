"""Physically verify container-clock scheduled outage and RTT, then restore replay."""
import json
from pathlib import Path
import re
import time
from browser_trial import docker, set_schedule, set_profile

ROOT = Path(__file__).resolve().parents[1]
start = time.time()+2
profile = {'profile_id': 'physical-final-link-check', 'start_at_unix_s': start, 'stages': [
    {'at_s': 0, 'rate_mbit': 8, 'delay_ms': 40, 'loss_percent': 0},
    {'at_s': 4, 'rate_mbit': 0, 'delay_ms': 40},
    {'at_s': 7, 'rate_mbit': 8, 'delay_ms': 100, 'loss_percent': 0},
    {'at_s': 11, 'rate_mbit': 8, 'delay_ms': 40, 'loss_percent': 0}]}


def until(offset):
    remaining = start+offset-time.time()
    if remaining > 0:
        time.sleep(remaining)


try:
    set_schedule(profile)
    until(1)
    healthy = docker('exec', 'leo_abr_rl-stat-server-1', 'ping', '-c', '1', '-W', '1', 'nginx')
    until(4.2)
    lost = docker('exec', 'leo_abr_rl-stat-server-1', 'sh', '-c', 'ping -c 1 -W 1 nginx || true')
    assert '100% packet loss' in lost
    until(7.4)
    delayed = docker('exec', 'leo_abr_rl-stat-server-1', 'ping', '-c', '1', '-W', '1', 'nginx')
    measured = float(re.search(r'time=([\d.]+)', delayed)[1])
    assert 85 < measured < 150, delayed
    until(11.4)
    recovery = docker('exec', 'leo_abr_rl-stat-server-1', 'ping', '-c', '1', '-W', '1', 'nginx')
    assert '0% packet loss' in recovery
    applied = json.loads(docker('exec', 'dashjs-nginx', 'cat', '/run/leo-profile-applied.json'))
    report = {'status': 'PASS', 'healthy': healthy, 'outage': lost,
              'configured_delayed_ms': 100, 'measured_delayed_rtt_ms': measured,
              'recovery': recovery, 'applied': applied}
    (ROOT/'artifacts/final/scheduled-link-check.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
finally:
    set_profile(None)
