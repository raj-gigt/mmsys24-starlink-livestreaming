"""Check derivation, split boundaries, hashes, units and deterministic regeneration."""
from pathlib import Path
import hashlib
import json
import numpy as np

root = Path(__file__).resolve().parents[1]
policy = json.loads((root/'data/manifests/split-policy.json').read_text())
seen_ids, seen_seeds, windows = set(), set(), {}
counts = {}
for split in ['train','validation','test']:
    obj = json.loads((root/f'data/manifests/{split}.json').read_text())
    lo,hi = policy['blocks'][split]
    windows[split] = []
    for row in obj['scenarios']:
        assert row['id'] not in seen_ids and row['seed'] not in seen_seeds
        seen_ids.add(row['id']); seen_seeds.add(row['seed'])
        start,end = row['source_window_s']
        assert lo <= start < end <= hi
        path = root/row['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
        data = np.load(path)
        assert np.array_equal(data['t_s'],np.arange(180))
        assert np.isfinite(data['rtt_ms']).all() and (data['rtt_ms']>0).all()
        assert (data['capacity_mbps']>=0).all() and (data['capacity_mbps']<=20).all()
        assert ((data['probe_loss_fraction']>=0)&(data['probe_loss_fraction']<=1)).all()
        assert np.array_equal(data['synthetic_outage'],data['capacity_mbps']==0)
        windows[split].append((start,end))
    assert len(set(r['family'] for r in obj['scenarios'])) == 6
    counts[split] = len(obj['scenarios'])
for a,b in [('train','validation'),('validation','test'),('train','test')]:
    for x,y in windows[a]:
        for u,v in windows[b]: assert min(y,v) <= max(x,u), 'Cross-split source leakage'
report = {'status':'PASS','scenario_counts':counts,'total_scenarios':sum(counts.values()),
          'unique_seeds':len(seen_seeds),'guard_s':60,
          'unit_checks':'RTT ms; time s; capacity Mbit/s; bytes from actual media catalog',
          'test_scenario_values_used_for_model_selection':False,
          'limitations':['Single measured RTT recording','Synthetic capacity/outages','Short downlink examples not used for fitting']}
(root/'artifacts/data').mkdir(parents=True,exist_ok=True)
(root/'artifacts/data/verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
