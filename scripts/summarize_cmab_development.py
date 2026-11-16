"""Generate transparent development-only paired tables from the saved ledger."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--name', default='memory-startup-v1')
    args = p.parse_args()
    folder = ROOT/'artifacts/final/development'/args.name
    rows = json.loads((folder/'runs.json').read_text())
    baselines = {(r['case_id'], r['repeat']):r for r in rows if r['variant']=='original'}
    fields = ['case_id','variant','repeat','run_id','qoe_per_wall_s','stall_s','startup_s',
              'played_bitrate_bps','mean_live_latency_s','p95_live_latency_s','switches',
              'quality_attribution_fraction','played_media_s','skipped_media_s','learned_fraction',
              'paired_qoe_difference','paired_stall_difference_s']
    exported = []
    for r in rows:
        baseline = baselines.get((r['case_id'],r['repeat']))
        record = {k:r[k] for k in ['case_id','variant','repeat','run_id']}
        record.update({k:r['metrics'].get(k) for k in fields if k in r['metrics']})
        record['learned_fraction'] = r['learned']/max(1,r['decisions'])
        record['paired_qoe_difference'] = r['metrics']['qoe_per_wall_s']-baseline['metrics']['qoe_per_wall_s'] if baseline else None
        record['paired_stall_difference_s'] = r['metrics']['stall_s']-baseline['metrics']['stall_s'] if baseline else None
        exported.append(record)
    with (folder/'paired-results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(exported)
    report = {'scope':'Development-only, not held-out evaluation; do not infer significance from single repeats',
              'sessions':len(rows),'paired_rows':sum(r['paired_qoe_difference'] is not None for r in exported),
              'rows':exported}
    (folder/'paired-results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['scope','sessions','paired_rows']}))


if __name__ == '__main__':
    main()
