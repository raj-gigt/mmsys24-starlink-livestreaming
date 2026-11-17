"""Common verified shaper plus container-clock scheduled profiles for every policy."""
import bisect
import csv
import json
import os
from pathlib import Path
import subprocess
import time


def profile_values(profile, now, defaults):
    """Pure schedule selection; future values are only visible to the evaluator."""
    row = profile
    if 'stages' in profile:
        stages = profile['stages']
        assert stages and stages[0]['at_s'] == 0
        assert all(a['at_s'] < b['at_s'] for a, b in zip(stages, stages[1:]))
        elapsed = max(0, now-profile['start_at_unix_s'])
        row = stages[max(0, bisect.bisect_right([s['at_s'] for s in stages], elapsed)-1)]
    rate = float(row.get('rate_mbit', defaults[0]))
    delay = float(row.get('delay_ms', defaults[1]))
    loss = float(row.get('loss_percent', defaults[2]))
    if rate == 0:
        rate, loss = .05, 100.  # valid HTB class plus total packet interruption
    assert .05 <= rate <= 1000 and 0 <= delay <= 10000 and 0 <= loss <= 100
    return rate, delay, loss


def tc(*args):
    subprocess.run(['tc', *args], check=True, capture_output=True)


def main():
    rows = list(csv.DictReader(open('/trace/trace.csv')))
    times = [float(r['since']) for r in rows]
    delays = [int(float(r['rtt'])) for r in rows]
    assert times == sorted(times)
    tc('qdisc', 'replace', 'dev', 'eth0', 'root', 'handle', '1:', 'htb', 'default', '1')
    started = time.monotonic()
    last = None
    profile_file = Path('/run/leo-link-profile.json')
    log_file = Path('/run/leo-profile-applied.json')
    full_log = Path('/run/leo-profile-applied.jsonl')
    identity = None
    applied = []
    last_trace_log = -1
    while True:
        elapsed = time.monotonic()-started
        index = min(bisect.bisect_left(times, elapsed), len(times)-1)
        if index and abs(times[index-1]-elapsed) <= abs(times[index]-elapsed):
            index -= 1
        raw = delays[index]
        defaults = (float(os.getenv('LEO_SHAPER_RATE_MBIT', '20')), raw if raw > 0 else 100, 1 if raw > 0 else 100)
        profile = None
        if profile_file.exists():
            try:
                profile = json.loads(profile_file.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                time.sleep(.01)
                continue
        now = time.time()
        if profile and profile.get('mode') == 'trace':
            at = max(0, now-profile['start_at_unix_s']) + profile.get('trace_offset_s', 0)
            index = min(bisect.bisect_left(times, at), len(times)-1)
            if index and abs(times[index-1]-at) <= abs(times[index]-at):
                index -= 1
            raw = delays[index]
            current = (20., raw if raw > 0 else 100, 1 if raw > 0 else 100)
        else:
            current = profile_values(profile, now, defaults) if profile else defaults
        profile_id = profile.get('profile_id', 'legacy-controlled') if profile else 'raw-trace'
        new_identity = profile_id != identity
        if new_identity:
            applied, identity = [], profile_id
            full_log.write_text('')
        changed = current != last
        if changed:
            rate, delay, loss = current
            if last is None or rate != last[0]:
                tc('class', 'replace', 'dev', 'eth0', 'parent', '1:', 'classid', '1:1',
                   'htb', 'rate', f'{rate}mbit', 'ceil', f'{rate}mbit')
            tc('qdisc', 'replace' if last is None else 'change', 'dev', 'eth0', 'parent', '1:1',
               'handle', '10:', 'netem', 'delay', f'{delay}ms', 'loss', f'{loss}%')
            last = current
        if profile and (changed or new_identity) or (not profile and int(elapsed) != last_trace_log):
            event = {'at_unix_s': time.time(), 'profile_id': profile_id,
                     'rate_mbit': current[0], 'delay_ms': current[1], 'loss_percent': current[2]}
            if profile and 'start_at_unix_s' in profile:
                event['relative_s'] = event['at_unix_s']-profile['start_at_unix_s']
            if profile and profile.get('mode') == 'trace':
                event.update(source_trace_at_s=at,source_trace_index=index)
            with full_log.open('a') as stream:
                stream.write(json.dumps(event,separators=(',',':'))+'\n')
            applied.append(event)
            applied = applied[-256:]
            temp = log_file.with_suffix('.new')
            temp.write_text(json.dumps({'profile_id': profile_id, 'applied': applied}))
            temp.replace(log_file)
            print(json.dumps(event), flush=True)
            last_trace_log = int(elapsed)
        time.sleep(.01)


if __name__ == '__main__':
    main()
