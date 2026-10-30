"""Bounded unauthenticated access check; no large archives or pickle execution."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

SOURCES = {
 'StarNet-US':'https://uillinoisedu-my.sharepoint.com/:f:/g/personal/zikunliu_illinois_edu/IgBaSUJKNIjlQI6KeF1tWc6-AZMwiOlyueqSY4KzOYsVEfw?e=pD0Ix8',
 'LENS-current':'https://lens-starlink.jinwei.me',
}
def check(item):
    name,url=item
    row={'source':name,'url':url,'checked_utc':datetime.now(timezone.utc).isoformat()}
    try:
        with requests.get(url, timeout=(10,20), stream=True) as response:
            body=next(response.iter_content(16384),b'').decode('utf-8',errors='replace')
            row.update(status=response.status_code,content_type=response.headers.get('Content-Type'),
                       final_host=urlparse(response.url).hostname,bytes_inspected=len(body),
                       login_redirect='login.microsoftonline' in response.url or 'sign in' in body.lower())
    except requests.RequestException as exc:
        row['error_type']=type(exc).__name__
    row['raw_measurements_acquired']=False
    return row
rows=list(ThreadPoolExecutor(max_workers=2).map(check,SOURCES.items()))
out=Path('data/manifests/external-access.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'checks':rows,'decision':'Use audited local-plus-synthetic package for the mid-review pilot. No external measurement bytes acquired.',
    'follow_up':'Obtain an accessible, provenance-preserving StarNet subset and independent LENS sessions before broad generalization claims.',
    'lens_older_archive_size':'Old monthly CSV bundles are 21-50+ GB; not acquired for this bounded pilot.',
    'sources':['https://github.com/ConnectedSystemsLab/StarNet','https://github.com/clarkzjw/LENS']},indent=2))
print(json.dumps(rows,indent=2))
