"""Common repaired trace replay for baseline and new policies.

Keep the original outgoing-delay interpretation, 1% normal loss and <=0 RTT
outages. Repair the missing HTB root and invalid rate>ceil; use monotonic replay
and logarithmic lookup instead of rescanning 350k samples every iteration.
An optional /run/leo-link-profile.json supplies documented controlled tests.
"""
import bisect
import csv
import json
import os
from pathlib import Path
import subprocess
import time


def tc(*args):
    subprocess.run(["tc", *args], check=True, capture_output=True)


def main():
    rows = list(csv.DictReader(open("/trace/trace.csv")))
    times = [float(row["since"]) for row in rows]
    delays = [int(float(row["rtt"])) for row in rows]
    assert times == sorted(times)
    tc("qdisc", "replace", "dev", "eth0", "root", "handle", "1:", "htb", "default", "1")
    last = None
    started = time.monotonic()
    last_log = -1
    profile_file = Path("/run/leo-link-profile.json")
    while True:
        elapsed = time.monotonic() - started
        at = min(bisect.bisect_left(times, elapsed), len(times) - 1)
        if at and abs(times[at - 1] - elapsed) <= abs(times[at] - elapsed):
            at -= 1
        raw_rtt = delays[at]
        rate = float(os.getenv("LEO_SHAPER_RATE_MBIT", "20"))
        delay = raw_rtt if raw_rtt > 0 else 100
        loss = 1 if raw_rtt > 0 else 100
        mode = "trace"
        if profile_file.exists():
            profile = json.loads(profile_file.read_text())
            rate = float(profile.get("rate_mbit", rate))
            delay = float(profile.get("delay_ms", delay))
            loss = float(profile.get("loss_percent", loss))
            mode = "controlled"
        assert 0.05 <= rate <= 1000 and 0 <= delay <= 10000 and 0 <= loss <= 100
        current = (rate, delay, loss)
        if current != last:
            if last is None or rate != last[0]:
                tc("class", "replace", "dev", "eth0", "parent", "1:", "classid", "1:1",
                   "htb", "rate", f"{rate}mbit", "ceil", f"{rate}mbit")
            tc("qdisc", "replace" if last is None else "change", "dev", "eth0", "parent", "1:1",
               "handle", "10:", "netem", "delay", f"{delay}ms", "loss", f"{loss}%")
            last = current
        if int(elapsed) != last_log:
            print(json.dumps({"elapsed_s": round(elapsed, 3), "trace_at_s": times[at],
                              "rate_mbit": rate, "delay_ms": delay, "loss_percent": loss,
                              "mode": mode}), flush=True)
            last_log = int(elapsed)
        time.sleep(float(os.getenv("INTERVAL", "0.01")))


if __name__ == "__main__":
    main()
