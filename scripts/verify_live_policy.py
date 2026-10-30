"""Verify live observations, actual requests, played qualities and independent Mongo logs."""
from pathlib import Path
import json
import sys
import numpy as np
from pymongo import MongoClient

run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(Path('artifacts/runs').glob('phasea-abrAnjanSimple*'))[-1]
summary = json.loads((run_dir / 'summary.json').read_text())
samples = json.loads((run_dir / 'samples.json').read_text())
final = samples[-1]
decisions = final['decisions']
assert len(decisions) >= 10
assert len({d['id'] for d in decisions}) == len(decisions)
assert len({d['key'] for d in decisions}) == len(decisions)
assert summary['build'] == 'anjan-phase-a-20261030-local-source-v1'
requests = [r for r in final['requests'] if r['type'] == 'MediaSegment' and r['code'] == 200]
linked = []
for d in decisions:
    assert d['observation']['ladder'][d['action']]['id'] == d['representation_id']
    assert d['observation']['ladder'][d['action']]['quality'] == d['quality']
    for h in d['observation']['history']:
        assert 0 <= h['finished_ms'] <= d['at_ms'], 'Future telemetry leaked into a decision'
        assert h['mbps'] >= 0 and h['download_s'] > 0 and h['bytes'] > 0
        assert abs(h['mbps'] - 8*h['bytes']/h['download_s']/1e6) < 1e-6
    for r in d['requests']:
        if r['quality'] == d['quality'] and r['representation_id'] == d['representation_id']:
            matches = [x for x in requests if x['url'] == r['url'] and x['quality'] == r['quality']]
            if matches:
                linked.append({'decision_id':d['id'], 'action':d['action'], 'representation_id':d['representation_id'], 'url':r['url']})
assert len(linked) >= 5, 'No evidence selected representations became completed requests'
assert len({r['quality'] for r in final['rendered']}) >= 2, 'No played-quality change'
db = MongoClient('mongodb://starlink:starlink@localhost:27017/')['starlink']
events = [e for doc in db['events-' + summary['run_id']].find() for e in doc.get('type', [])]
logged = [e for e in events if e.get('type') == 'anjanDecision']
assert len(logged) >= len(decisions) - 4, 'Existing asynchronous event-to-MongoDB path missing decisions'
assert db['decisions-' + summary['run_id']].count_documents({}) == len(decisions)
timing = np.percentile([d['duration_ms'] for d in decisions], [50,95,99]).tolist()
report = {'run_id':summary['run_id'], 'decisions':len(decisions),
          'selected_actions':sorted({d['action'] for d in decisions}), 'matched_completed_requests':len(linked),
          'mongo_logged_decisions_via_existing_route':len(logged), 'played_quality_indices':sorted({r['quality'] for r in final['rendered']}),
          'fallbacks':sum(bool(d['result'].get('fallback')) for d in decisions),
          'complete_new_decision_ms_p50_p95_p99':timing, 'examples':linked[:4],
          'scope':'Integration demonstration; no claim of final-policy improvement.'}
assert report['fallbacks']==0,'Valid live policy run unexpectedly used a fallback'
if summary['algorithm'] == 'abrAnjanSimple' and len(summary['controlled_stages']) == 3:
    start_ms = decisions[0]['at_ms']
    groups = [[d['bitrate_bps'] for d in decisions if lo <= (d['at_ms']-start_ms)/1000 < hi]
              for lo,hi in [(10,25),(35,50),(62,80)]]
    medians = [float(np.median(g)) for g in groups]
    assert medians[1] < medians[0] and medians[2] > medians[1], medians
    report['high_low_recovery_median_selected_bps'] = medians
out = Path('artifacts/integration')
out.mkdir(parents=True, exist_ok=True)
(out / (summary['run_id'] + '.json')).write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
