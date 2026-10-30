"""Measure the shaped egress path in isolation, then restore trace replay."""
import json
from pathlib import Path
import time
from browser_trial import docker, set_profile

records = []
try:
    for rate in [2, 8]:
        set_profile(rate)
        time.sleep(1)
        docker('exec', '-d', 'dashjs-nginx', 'iperf3', '-s', '-1')
        result = json.loads(docker('run', '--rm', '--network', 'dashjs', '--entrypoint', 'iperf3',
                                  'clarkzjw/dashjs-runner:master', '-c', 'nginx', '-R', '-t', '6', '-J'))
        measured = result['end']['sum_received']['bits_per_second'] / 1e6
        records.append({'configured_mbps': rate, 'measured_mbps': measured})
        assert rate * 0.55 < measured < rate * 1.25, (rate, measured)
    healthy = docker('exec', 'leo_abr_rl-stat-server-1', 'ping', '-c', '4', '-W', '1', 'nginx')
    set_profile(8, delay=40, loss=100)
    time.sleep(1)
    lost = docker('exec', 'leo_abr_rl-stat-server-1', 'sh', '-c', 'ping -c 3 -W 1 nginx || true')
    assert '100% packet loss' in lost, lost
    set_profile(8, delay=40, loss=0)
    time.sleep(1)
    recovered = docker('exec', 'leo_abr_rl-stat-server-1', 'ping', '-c', '3', '-W', '1', 'nginx')
    assert '0% packet loss' in recovered
    report = {'capacity_checks': records, 'healthy_ping': healthy,
              'outage_ping': lost, 'recovery_ping': recovered,
              'interpretation': 'Outgoing nginx delay=40ms; measured ping RTT includes this once, not twice.'}
    out = Path('artifacts/setup/link-verification.json')
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
finally:
    set_profile(None)
