"""Hand-specified selection failures: stalls/startup/non-playback and mixed-case weighting."""
from copy import deepcopy
import json
from pathlib import Path
from select_cmab_final import choose,FAMILIES
ROOT=Path(__file__).resolve().parents[1]
rule=json.loads((ROOT/'configs/final/validation-selection.json').read_text());protocol=json.loads((ROOT/'configs/final/protocol.json').read_text())
rows=[]
for family in FAMILIES+['mixed_shifted']:
 for variant,score in [('original',0),('context',1),('guard',2),('guard_only',3)]:
  metrics=dict(qoe_per_wall_s=score,stall_s=2,startup_s=1,p95_live_latency_s=4,mean_live_latency_s=3.5,
    played_bitrate_bps=1e6,switches=1,played_media_s=80,skipped_media_s=0,duration_s=90)
  rows.append({'variant':variant,'family':family,'metrics':metrics})
assert choose(rows,rule,protocol)['selected']=='guard'
x=deepcopy(rows)
for r in x:
 if r['family']=='mixed_shifted' and r['variant']=='context':r['metrics']['qoe_per_wall_s']=9999
assert choose(x,rule,protocol)['selected']=='guard','Mixed stress must not distort mandatory-family weights'
x=deepcopy(rows)
for r in x:
 if r['variant']=='guard':r['metrics']['played_media_s']=10
assert choose(x,rule,protocol)['selected']=='context','No-playback cannot win a scalar-score comparison'
x=deepcopy(rows)
for r in x:
 if r['variant']=='guard':r['metrics']['stall_s']=10
assert choose(x,rule,protocol)['selected']=='context'
for r in x:
 if r['variant']=='context':r['metrics']['startup_s']=10
assert choose(x,rule,protocol)['selected'] is None
print('PASS: frozen selection excludes poor playback/physical regressions and keeps mixed stress separate')
