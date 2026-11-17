"""Read hash-checked portable run evidence; never requires a database."""
import gzip
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_run(run_id,root=ROOT):
    index=json.loads((root/'artifacts/final/evidence/index.json').read_text())
    record=index[run_id];path=root/record['file'];data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Evidence hash mismatch: '+run_id)
    payload=json.loads(gzip.decompress(data))
    if payload['summary.json']['run_id']!=run_id:raise ValueError('Evidence identity mismatch')
    return payload
