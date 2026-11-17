"""Compact portable evidence for complete experiments, independent of MongoDB."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['telemetry.json','summary.json','scenario.json','applied-profile.json','samples.json']
def main():
    p=argparse.ArgumentParser();p.add_argument('ledgers',nargs='+');args=p.parse_args()
    target=ROOT/'artifacts/final/evidence';target.mkdir(parents=True,exist_ok=True)
    index_path=target/'index.json';index=json.loads(index_path.read_text()) if index_path.exists() else {}
    for ledger_name in args.ledgers:
        ledger=Path(ledger_name);rows=json.loads(ledger.read_text())
        try:ledger_identity=ledger.resolve().relative_to(ROOT).as_posix()
        except ValueError:ledger_identity=ledger.as_posix()
        if isinstance(rows,dict): rows=rows['runs']
        for row in rows:
            if row.get('status') not in ['complete','retained_unscored_retry_same_case']:continue
            run_id=row['run_id'];folder=ROOT/'artifacts/runs'/run_id
            payload={name:json.loads((folder/name).read_text(encoding='utf-8')) for name in FILES if (folder/name).exists()}
            assert {'telemetry.json','summary.json'}<=payload.keys(),run_id
            assert payload['summary.json']['run_id']==run_id
            # Zero gzip timestamp makes equivalent evidence byte reproducible.
            encoded=json.dumps(payload,separators=(',',':'),sort_keys=True).encode()
            compressed=gzip.compress(encoded,compresslevel=6,mtime=0)
            output=target/(run_id+'.json.gz');output.write_bytes(compressed)
            assert json.loads(gzip.decompress(output.read_bytes()))==payload
            index[run_id]={'file':output.relative_to(ROOT).as_posix(),
                'sha256':hashlib.sha256(compressed).hexdigest(),'bytes':len(compressed),
                'files':list(payload),'ledger':ledger_identity,'scientific_status':row['status']}
    index_path.write_text(json.dumps(index,indent=2,sort_keys=True))
    print(json.dumps({'portable_runs':len(index),'compressed_bytes':sum(r['bytes'] for r in index.values())}))
if __name__=='__main__':main()
