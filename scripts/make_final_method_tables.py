"""Generate source/configuration tables; no hand-entered performance results."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/final/tables';OUT.mkdir(parents=True,exist_ok=True)
def write(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
policies=[
 {'policy':'Original CMAB','inputs':'Throughput, playback rate, legacy RTT','learning':'Online LinTS; slot resets; repeated highest-arm starts','runtime':'Synchronous Pyodide','status':'Preserved source control'},
 {'policy':'Guarded CMAB','inputs':'9 physical context coordinates; buffer/live delay/RTT validity','learning':'30 linked completed outcomes; explicit download surrogate; conservative starts and action ceiling','runtime':'Synchronous Pyodide','status':'Validation-selected primary'},
 {'policy':'Guard only','inputs':'Same current throughput/buffer/live-delay/RTT-health ceiling','learning':'None; also replaces conservative forced choices','runtime':'JavaScript within sibling controller','status':'Heuristic control, not a pure learning-only removal'},
 {'policy':'Throughput','inputs':'Native dash.js throughput history','learning':'Native ThroughputRule and configured auxiliary rules','runtime':'JavaScript','status':'Built-in reference'},
 {'policy':'BOLA','inputs':'Native buffer-occupancy logic','learning':'Native BolaRule and configured auxiliary rules','runtime':'JavaScript','status':'Built-in reference'},
 {'policy':'Conventional A2C','inputs':'36 causal history/buffer/previous-quality/rate coordinates','learning':'Same eight-action A2C recipe and fixed physical reward','runtime':'Synchronous Float32 JavaScript','status':'Compatible retrained baseline; not faithful released Pensieve weights'},
 {'policy':'LEO A2C','inputs':'64 = conventional36 +28 RTT-health/live-delay coordinates','learning':'Same A2C recipe, scenarios, budget and hidden layers','runtime':'Synchronous Float32 JavaScript','status':'Compatible adaptation; not unchanged released Gelato/Maguro weights'}]
write('T1-policy-design.csv',policies)
data=[]
for role in ['train','validation','test']:
    d=json.loads((ROOT/f'data/manifests/{role}.json').read_text())
    data.append({'dataset':'Neural '+role,'cases':len(d['scenarios']),'source':'Seychelles20240130 chronological block',
        'measured':'RTT only','generated':'Capacity, interruptions and recovery','use':'Training' if role=='train' else 'Checkpoint selection' if role=='validation' else 'Legacy simulator split; unused in final selection or reported browser results'})
for role in ['development','validation','test','reserve']:
    d=json.loads((ROOT/f'configs/final/workloads/{role}.json').read_text())
    data.append({'dataset':'Browser '+role,'cases':len(d['cases']),'source':'Seychelles20240130' if role in ['development','validation'] else 'Seychelles20240130 + Victoria20251114',
        'measured':'RTT windows or explicitly constant RTT','generated':'Capacity, interruptions and recovery','use':'Development' if role=='development' else 'Candidate selection' if role=='validation' else 'Frozen final comparison' if role=='test' else 'Untouched fallback cohort'})
write('T2-data-scenarios.csv',data)
media=json.loads((ROOT/'data/manifests/media.json').read_text())
write('T2-media-ladder.csv',[{k:r[k] for k in ['action','nominal_bps','mean_encoded_bps','width','height','representation_id']} for r in media['representations']])
rules=json.loads((ROOT/'configs/final/protocol.json').read_text())
write('T3-common-settings.csv',[{'setting':k,'value':json.dumps(v)} for k,v in rules.items()])
project=json.loads((ROOT/'configs/final/project.json').read_text())
contribution_path=OUT/'T6-contributions-template.csv'
existing={r['roll']:r.get('specific_completed_work_2_to_3_sentences','') for r in csv.DictReader(contribution_path.open(encoding='utf-8'))} if contribution_path.exists() else {}
write('T6-contributions-template.csv',[{**m,'specific_completed_work_2_to_3_sentences':existing.get(m['roll'],'')} for m in project['members']])
print('Created T1/T2/T3 method tables and requested blank T6 contribution template')
