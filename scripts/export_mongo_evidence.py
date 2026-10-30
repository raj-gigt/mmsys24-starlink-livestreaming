"""Retain the actual experiment-scoped MongoDB records outside the database volume."""
import gzip
import json
from pathlib import Path
from bson import json_util
from pymongo import MongoClient

db=MongoClient('mongodb://starlink:starlink@localhost:27017/')['starlink']
matched=json.loads(Path('artifacts/integration/matched-pilot-trials.json').read_text())['runs']
baseline=json.loads(Path('artifacts/baselines/verified.json').read_text())['runs']
rows={r['run_id']:r for r in baseline+matched}
report=[]
for run_id in rows:
    out=Path('artifacts/runs')/run_id/'mongo';out.mkdir(exist_ok=True)
    counts={}
    for kind in ['events','metric','qoe','decisions']:
        records=list(db[kind+'-'+run_id].find({}))
        with gzip.open(out/(kind+'.json.gz'),'wt',encoding='utf-8') as stream:stream.write(json_util.dumps(records))
        counts[kind]=len(records)
    report.append({'run_id':run_id,'collection_documents':counts,'path':str(out).replace('\\','/')})
Path('artifacts/integration/mongo-export.json').write_text(json.dumps(report,indent=2))
print('Actual MongoDB evidence snapshots exported for',len(report),'verified runs.')
