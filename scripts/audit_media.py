"""Audit the actual eight-representation source and its encoded segment byte sizes."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from browser_trial import docker

parser=argparse.ArgumentParser()
parser.add_argument('--archive',type=Path,default=Path.home()/'AppData/Local/LEO-RL/cache/WAVE.zip')
args=parser.parse_args()
ns={'m':'urn:mpeg:dash:schema:mpd:2011'}
with ZipFile(args.archive) as archive:
    mpd_path=next(n for n in archive.namelist() if n.endswith('/stream.mpd'))
    source=ET.fromstring(archive.read(mpd_path))
    adaptation=source.find('m:Period/m:AdaptationSet',ns)
    template=adaptation.find('m:SegmentTemplate',ns)
    timing=template.find('m:SegmentTimeline/m:S',ns)
    timescale=int(template.attrib['timescale']); duration=int(timing.attrib['d'])
    starts=[int(timing.attrib['t'])+i*duration for i in range(int(timing.attrib['r'])+1)]
    reps=sorted(adaptation.findall('m:Representation',ns),key=lambda r:int(r.attrib['bandwidth']))
    runtime=ET.parse('artifacts/setup/runtime.mpd').getroot()
    live={r.attrib['id']:int(r.attrib['bandwidth']) for r in runtime.findall('.//m:Representation',ns)}
    catalog=[]
    for action,rep in enumerate(reps):
        rid=rep.attrib['id']; assert live[rid]==int(rep.attrib['bandwidth'])
        prefix=mpd_path.rsplit('/',1)[0]+'/'+rid+'/'
        segments=[]
        for at in starts:
            info=archive.getinfo(prefix+str(at)+'.m4s')
            segments.append({'start_tick':at,'bytes':info.file_size})
        if action in [0,7]:
            relative=prefix+'0.m4s'
            expected=hashlib.sha256(archive.read(relative)).hexdigest()
            actual=docker('exec','leo_abr_rl-livesim2-1','sha256sum','/livesim2/'+relative).split()[0]
            assert actual==expected, 'Cached archive does not match the actual serving container'
        catalog.append({'action':action,'dash_quality_index':action,'representation_id':rid,
            'nominal_bps':int(rep.attrib['bandwidth']),'width':int(rep.attrib['width']),
            'height':int(rep.attrib['height']),'segments':segments,
            'mean_encoded_bps':sum(s['bytes'] for s in segments)*8/(len(starts)*duration/timescale)})
    output={'source_url':'https://starlink-dash-live.jinwei.me/WAVE.zip',
        'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'source_mpd':mpd_path,'segment_s':duration/timescale,'loop_s':60,
        'availability':'Runtime MPD is dynamic, full segments available at segment end; no availabilityTimeOffset signalled.',
        'license_attribution':source.find('m:ProgramInformation/m:Copyright',ns).text,
        'representations':catalog,'byte_sizes':'Actual static encoded .m4s bytes; live moof timestamp rewriting may add small overhead.',
        'container_cross_checks':'Lowest/highest first-segment SHA256 match serving livesim2 image.'}
Path('data/manifests/media.json').write_text(json.dumps(output,indent=2))
print([(r['action'],r['nominal_bps'],round(r['mean_encoded_bps'])) for r in catalog])
