"""Acquire one small independent public LENS RTT session for post-review calibration.

This reserve is not incorporated into the chronological pilot split or model selection.
Stream validation avoids materializing the very large raw JSON object in memory.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import requests

URL='https://lens-starlink.jinwei.me/victoria/irtt/2025/11/2025-11-14/irtt-sttlwax1-10ms-1h-2025-11-14-19-00-00.json.gz'
path=Path('data/raw/lens/victoria-irtt-20251114-1900.json.gz')
path.parent.mkdir(parents=True,exist_ok=True)
if not path.exists():
    with requests.get(URL,stream=True,timeout=(10,30)) as response, path.open('wb') as out:
        response.raise_for_status()
        total=0
        for chunk in response.iter_content(1024*1024):
            total+=len(chunk)
            if total>64*1024*1024: raise ValueError('Archive exceeds the explicit 64MiB pilot acquisition cap')
            out.write(chunk)
with gzip.open(path,'rb') as data:
    prefix=data.read(1024*1024)
    size=len(prefix)
    while chunk:=data.read(1024*1024): size+=len(chunk)
assert b'"round_trips"' in prefix
header=prefix.split(b'"round_trips"',1)[0].rstrip().rstrip(b',')+b'}'
metadata=json.loads(header)
record={'url':URL,'path':str(path).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'downloaded_utc':datetime.now(timezone.utc).isoformat(),'compressed_bytes':path.stat().st_size,
    'validated_uncompressed_bytes':size,'gzip_crc_check':'PASS','kind':'independent measured RTT session',
    'recording_id':'victoria-20251114-1900','license':'CC-BY-SA-4.0',
    'attribution':'Jinwei Zhao and Jianping Pan, LENS: A LEO Satellite Network Measurement Dataset, MMSys 2024, doi:10.1145/3625468.3652170',
    'stats':metadata.get('stats',{}),'purpose':'Post-review calibration reserve; never loaded by the Phase A trainer',
    'contains_throughput':False,'used_in_pilot_split':False}
Path('data/manifests/lens-reserve.json').write_text(json.dumps(record,indent=2))
access=Path('data/manifests/external-access.json')
if access.exists():
    report=json.loads(access.read_text())
    report['acquired_reserve']={k:record[k] for k in ['url','path','sha256','compressed_bytes','purpose']}
    report['decision']='Pilot uses the audited local chronological split plus synthetic capacity. An independent LENS RTT session was acquired and reserved for post-review calibration. StarNet throughput was not acquired.'
    access.write_text(json.dumps(report,indent=2))
print(json.dumps({k:record[k] for k in ['recording_id','compressed_bytes','validated_uncompressed_bytes','gzip_crc_check','sha256']},indent=2))
