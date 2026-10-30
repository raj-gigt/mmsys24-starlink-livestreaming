"""Create a compact evidence index and diagnostic comparison chart from saved runs."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
out=root/'reports/phase-a';out.mkdir(parents=True,exist_ok=True)
matched=json.loads((root/'artifacts/integration/matched-pilot-trials.json').read_text())
fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
rows=[]
for run in matched['runs']:
    samples=json.loads((root/'artifacts/runs'/run['run_id']/'samples.json').read_text())
    label={'abrCMAB':'CMAB','abrAnjanSimple':'Simple custom rule','abrAnjanRL':'A2C integration pilot'}[run['algorithm']]
    times=[s['elapsed_s'] for s in samples]
    ladder={r['qualityIndex']:r['bitrate']/1000 for r in run['ladder']}
    axes[0].step(times,[ladder.get(s['quality'],np.nan) for s in samples],where='post',label=label)
    axes[1].plot(times,[s['buffer'] for s in samples],label=label)
    axes[2].plot(times,[s['latency'] if s['latency'] and s['latency']<100 else np.nan for s in samples],label=label)
    rows.append({'algorithm':label,'run_id':run['run_id'],'verified_playback_progress_s':run['played_advance_s'],
        'mongo_documents':run['mongo_documents'],'load_utc':run['load_wall_clock_utc'],
        'controlled_stages':run['controlled_stages'],'player_errors':run['player_errors']})
for ax in axes:
    ax.axvspan(25,50,color='gray',alpha=.12)
    ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper left')
axes[0].set_ylabel('Selected nominal bitrate (kbps)')
axes[1].set_ylabel('Video buffer (s)')
axes[2].set_ylabel('Live latency (s)');axes[2].set_xlabel('Seconds after Load')
axes[2].axhline(3,color='gray',linestyle='--',linewidth=.8)
fig.suptitle('Matched 75-second integration demonstrations: 8 → 1 → 8 Mbps\nOne run per policy; shaded capacity-drop interval; not a final performance study',fontsize=11)
fig.tight_layout();fig.savefig(out/'matched-playback.png',dpi=160);plt.close(fig)
timing=json.loads((root/'artifacts/exports/browser-parity-and-timing.json').read_text())
record={'updated_utc':datetime.now(timezone.utc).isoformat(),'phase_a_steps_1_to_6':'verification pending final audit',
    'archived_figures':25,'fresh_matched_demos':rows,'browser_actor':timing,
    'data':json.loads((root/'artifacts/data/verification.json').read_text()),
    'model':json.loads((root/'models/pilot/manifest.json').read_text()),
    'learning':json.loads((root/'artifacts/training/learning-verification.json').read_text()),
    'next_step':'Step 7: mid-review PPT (not executed in this batch).',
    'limits':['Pilot is imitation-initialized and A2C-updated, not unchanged pretrained Gelato.',
              'Final LEO features, calibrated training and CMAB improvement remain Phase B.',
              'Single short browser run per policy; no statistical performance conclusion.',
              'StarNet throughput not imported; training capacity is synthetic.',
              'All changes local on anjan; no remote push.']}
(out/'evidence-index.json').write_text(json.dumps(record,indent=2))
print('Evidence index and diagnostic chart generated from existing measurements.')
