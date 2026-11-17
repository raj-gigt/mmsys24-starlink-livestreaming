"""Verify full high-rate applied-network history without running a video policy."""
import bisect,csv,gzip,hashlib,json,time
from pathlib import Path
from browser_trial import docker,set_schedule,set_profile
ROOT=Path(__file__).resolve().parents[1]
profile={'profile_id':'infrastructure-full-raw-log-check','mode':'trace','trace_offset_s':0,'start_at_unix_s':time.time()+2}
try:
    set_schedule(profile);time.sleep(8)
    bounded=json.loads(docker('exec','dashjs-nginx','cat','/run/leo-profile-applied.json'))
    text=docker('exec','dashjs-nginx','cat','/run/leo-profile-applied.jsonl');rows=[json.loads(s) for s in text.splitlines()]
    assert len(rows)>256 and len(bounded['applied'])<=256
    source=list(csv.DictReader((ROOT/'runner/trace/isl-trace.csv').open()));times=[float(r['since']) for r in source]
    for r in rows:
        assert r['profile_id']==profile['profile_id']
        at=r['source_trace_at_s'];i=min(bisect.bisect_left(times,at),len(times)-1)
        if i and abs(times[i-1]-at)<=abs(times[i]-at):i-=1
        raw=int(float(source[i]['rtt']));assert r['source_trace_index']==i
        assert (r['rate_mbit'],r['delay_ms'],r['loss_percent'])==(20,raw if raw>0 else 100,1 if raw>0 else 100)
    out=ROOT/'artifacts/final/network-validation';out.mkdir(parents=True,exist_ok=True)
    encoded=gzip.compress(json.dumps(rows,separators=(',',':')).encode(),mtime=0);(out/'raw-log-check.json.gz').write_bytes(encoded)
    report={'status':'PASS','scope':'Infrastructure-only development trace0; no video/controller or held-out policy performance',
        'full_events':len(rows),'bounded_status_events':len(bounded['applied']),'every_source_index_and_applied_tuple_verified':True,
        'full_log_sha256':hashlib.sha256(encoded).hexdigest(),'covered_trace_s':[rows[0]['source_trace_at_s'],rows[-1]['source_trace_at_s']]}
    (out/'full-log-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:set_profile(None)
