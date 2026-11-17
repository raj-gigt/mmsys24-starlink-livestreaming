"""Run a short instrumented trial against the existing Docker/Selenium testbed.

Instrumentation observes all policies equally. The policy never reads MongoDB;
decision logs are copied from the browser to an experiment-scoped collection.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode
import uuid

import requests
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from plot_run_timeline import plot_run

ROOT = Path(__file__).resolve().parents[1]
WSL_ROOT = "/mnt/" + ROOT.drive[0].lower() + ROOT.as_posix()[2:] if os.name == "nt" else str(ROOT)


def docker(*args: str) -> str:
    prefix = ["wsl", "--distribution", "Ubuntu-22.04", "--user", "root", "--cd", WSL_ROOT, "--exec"] if os.name == "nt" else []
    return subprocess.check_output([*prefix, "docker", *args],
                                  text=True, encoding="utf-8").strip()


def set_profile(rate: float | None, delay: float = 40, loss: float = 0) -> None:
    if rate is None:
        code = "from pathlib import Path; Path('/run/leo-link-profile.json').unlink(missing_ok=True)"
        docker("exec", "dashjs-nginx", "python3", "-c", code)
    else:
        code = "import sys;from pathlib import Path;Path('/run/leo-link-profile.json').write_text(sys.argv[1])"
        docker("exec", "dashjs-nginx", "python3", "-c", code,
               json.dumps({"rate_mbit": rate, "delay_ms": delay, "loss_percent": loss}))


def set_schedule(profile: dict) -> None:
    code = "import sys;from pathlib import Path;p=Path('/run/leo-link-profile.new');p.write_text(sys.argv[1]);p.replace('/run/leo-link-profile.json')"
    docker('exec', 'dashjs-nginx', 'python3', '-c', code, json.dumps(profile))


SNAPSHOT = r"""
const a=window.app, p=a && a.player, v=document.querySelector('video');
if (!p || !v) return null;
const m=p.getDashMetrics();
const req=m.getHttpRequests('video').slice(-160).map(r=>({
 type:r.type,url:r.url,start:r.trequest,first:r.tresponse,finish:r._tfinish,
 code:r.responsecode,quality:r._quality,duration:r._mediaduration,
 bytes:(r.trace||[]).reduce((n,t)=>n+(t.b ? t.b[0] : 0),0)}));
let ladder=[]; try {ladder=p.getBitrateInfoListFor('video').map(x=>({qualityIndex:x.qualityIndex,bitrate:x.bitrate,width:x.width,height:x.height}));}catch(e){}
return JSON.parse(JSON.stringify({at_ms:performance.now(),media_time:v.currentTime,
 ready_state:v.readyState,paused:v.paused,buffer:m.getCurrentBufferLevel('video'),
 latency:p.getCurrentLiveLatency(),rate:v.playbackRate,quality:p.getQualityFor('video'),
 ladder:ladder,requests:req,decisions:window.__anjanDecisionLog||[],
 events:window.__phaseaEvents||[],build:window.__anjanBuild||null,
 model:window.LEO_ABR && window.LEO_ABR.modelIdentity||null,
 utc_synchronization_enabled:p.getSettings().streaming.utcSynchronization.enabled, actual_abr_strategy:p.getSettings().streaming.abr.ABRStrategy,
 auto_switch_video:p.getSettings().streaming.abr.autoSwitchBitrate.video,
 shared_probe_active:window.LEO_SHARED_PROBE_ACTIVE===true,

 model_load_ms:window.LEO_ABR && window.LEO_ABR.modelLoadMs||null,
 rendered:window.__anjanRendered||[],player_errors:window.__phaseaErrors||[],
 callbacks:window.__anjanCallbackDurations||[],
 dropped_frames:v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality().droppedVideoFrames : null}));
"""


def run(args: argparse.Namespace) -> dict:
    run_id = f"phasea-{args.algorithm}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
    args._run_id = run_id
    out = ROOT / "artifacts" / "runs" / run_id
    out.mkdir(parents=True)
    options = webdriver.ChromeOptions()
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("ignore-certificate-errors")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Remote(os.getenv("LEO_SELENIUM", "http://localhost:4444"), options=options)
    stages = [(float(pair.split(":")[0]), float(pair.split(":")[1])) for pair in args.stages.split(",")] if args.stages else []
    scenario = None
    if getattr(args, 'scenario', None):
        spec = json.loads(Path(args.scenario).read_text())
        scenario = next(r for r in spec['cases'] if r['id'] == args.case)
        if scenario['role'] in ['test', 'reserve'] and not getattr(args, 'allow_test', False):
            raise ValueError('Sealed test workload requires explicit frozen-evaluation permission')
        if stages:
            raise ValueError('Use either a full scenario or legacy bandwidth steps')
        args.seconds = scenario['seconds']
    samples, applied = [], []
    params = {"experimentID": run_id,
              "mpdURL": "https://nginx/livesim2/vectors/switching_sets/12.5_25_50/ss1/2023-04-28/stream.mpd",
              "targetLatency": args.target, "constantVideoBitrate": getattr(args,'fixed_kbps',-1),
              "abrGeneral": args.algorithm, "maxDrift": 5, "minCatchupPlaybackRate": -0.17,
              "maxCatchupPlaybackRate": 0.17, "abrAdditionalAbandonRequestRule": "true",
              "cmabAlpha": 1.0, "catchupMechanism": args.catchup}
    if getattr(args,'local_clock',False):
        params['hostClock']=1
    if getattr(args, 'variant', None):
        params['cmabVariant'] = args.variant
    if getattr(args,'neural_variant',None):params['neuralVariant']=args.neural_variant
    url = "http://pyodide/samples/starlink/testplayer/testplayer.html?" + urlencode(params)
    clock_start = datetime.now(timezone.utc).isoformat()
    try:
        driver.set_page_load_timeout(120)
        page_started=time.perf_counter()
        driver.get(url)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            ready = driver.execute_script("return typeof window.app !== 'undefined' && (!window.LEO_ABR || window.LEO_ABR.ready)")
            if ready:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("Player/model assets did not become ready")
        page_ready_ms=(time.perf_counter()-page_started)*1000
        if getattr(args, 'final_telemetry', False):
            driver.execute_script('window.LEO_FINAL_DURATION_S=arguments[0]', args.seconds)
            driver.execute_script((ROOT/'rl/web/telemetry.js').read_text(encoding='utf-8'))
        driver.execute_script(r"""
          window.__phaseaEvents=[];
          window.__phaseaErrors=[];
          const v=document.querySelector('video');
          ['playing','waiting','stalled','seeking','seeked','pause','error','loadedmetadata'].forEach(n=>v.addEventListener(n,()=>window.__phaseaEvents.push({event:n,at_ms:performance.now(),media_time:v.currentTime})));
        """)
        runtime_prewarm_ms = None
        if getattr(args,'simulate_model_failure',False):
            driver.execute_script('window.LEO_ABR.predict=()=>{throw new Error("diagnostic-missing-model")};')
        if args.algorithm in ['abrCMAB','abrCMABImproved'] and getattr(args,'prewarm',True):
            driver.set_script_timeout(120)
            warmed=driver.execute_async_script("""
                const done=arguments[arguments.length-1],t=performance.now();
                window.LEO_PREWARM_CMAB().then(()=>done({ok:true,ms:performance.now()-t}))
                    .catch(e=>done({ok:false,error:String(e)}));
            """)
            assert warmed['ok'], warmed
            runtime_prewarm_ms=warmed['ms']
        scheduled_start = None
        if scenario:
            guest_now=driver.execute_script('return Date.now()/1000')
            scheduled_start = guest_now+2
            if getattr(args, 'align_minute', False):
                scheduled_start = (int((guest_now+2)/60)+1)*60
            profile = {'profile_id': run_id, 'start_at_unix_s': scheduled_start}
            if scenario.get('mode') == 'trace':
                profile.update(mode='trace', trace_offset_s=scenario['trace_offset_s'])
            else:
                profile['stages'] = scenario['stages']
            set_schedule(profile)
            while True:
                remaining=scheduled_start-driver.execute_script('return Date.now()/1000')
                if remaining<=0:break
                time.sleep(min(.1,max(.001,remaining)))
        else:
            set_profile(stages[0][1] if stages and stages[0][0] == 0 else None)
        if getattr(args, 'align_minute', False) and not scenario:
            while datetime.now(timezone.utc).second != 0:
                time.sleep(0.2)
        # Invoke the page's normal Load handler without relying on the
        # viewport position of the control in the Selenium container.
        load_button = driver.find_element(By.ID, "load-button")
        driver.execute_script("arguments[0].click()", load_button)
        loaded_utc = datetime.now(timezone.utc).isoformat()
        driver.execute_script("window.app.player.on('error',e=>window.__phaseaErrors.push(JSON.parse(JSON.stringify(e))))")
        started = time.monotonic()
        next_stage = 1 if stages and stages[0][0] == 0 else 0
        if next_stage:
            applied.append({"at_s": 0, "rate_mbit": stages[0][1]})
        while time.monotonic() - started < args.seconds:
            elapsed = time.monotonic() - started
            if next_stage < len(stages) and elapsed >= stages[next_stage][0]:
                set_profile(stages[next_stage][1])
                applied.append({"at_s": time.monotonic()-started, "rate_mbit": stages[next_stage][1]})
                next_stage += 1
            sample = driver.execute_script(SNAPSHOT)
            if sample:
                sample["elapsed_s"] = elapsed
                samples.append(sample)
            now=time.monotonic()-started
            until_stage=stages[next_stage][0]-now if next_stage<len(stages) else 2
            time.sleep(max(.01,min(2,until_stage,args.seconds-now)))
        driver.save_screenshot(str(out / "browser.png"))
        console = driver.get_log("browser")
        (out / "console.json").write_text(json.dumps(console, indent=2), encoding="utf-8")
        final = driver.execute_script(SNAPSHOT)
        if getattr(args, 'final_telemetry', False):
            telemetry = driver.execute_script("const c=window.LEO_FINAL_COLLECTOR;c.stop();return {version:c.version,start_performance_ms:c.start,resource_timings:performance.getEntriesByType('resource').filter(r=>r.responseEnd>=c.start).map(r=>({name:r.name,start_ms:r.startTime,duration_ms:r.duration,end_ms:r.responseEnd,initiator:r.initiatorType})),started_at_ms:c.started_at_ms,stopped_at_ms:c.stopped_at_ms,samples:c.samples,events:c.events,requests:c.requests,probes:c.probes,cmab_decisions:(window.__LEO_CMAB_TRACE||[]).filter(r=>r.at_ms<=c.stopped_at_ms),custom_decisions:(window.__anjanDecisionLog||[]).filter(r=>r.at_ms<=c.stopped_at_ms),feedback:(window.__LEO_FEEDBACK_TRACE||[]).filter(r=>r.at_ms<=c.stopped_at_ms)};")
            (out/'telemetry.json').write_text(json.dumps(telemetry),encoding='utf-8')
        if final:
            final["elapsed_s"] = time.monotonic() - started
            samples.append(final)
        if scenario:
            applied_profile = json.loads(docker('exec', 'dashjs-nginx', 'cat', '/run/leo-profile-applied.json'))
            assert applied_profile['profile_id'] == run_id, 'Wrong active link schedule'
            # Raw replay changes at much more than1Hz; the bounded live status
            # view alone cannot preserve an entire180s experiment.
            full = docker('exec','dashjs-nginx','cat','/run/leo-profile-applied.jsonl')
            applied_profile['applied']=[json.loads(line) for line in full.splitlines() if line.strip()]
            applied_profile['captured_at_unix_s']=float(docker('exec','dashjs-nginx','python3','-c','import time;print(time.time())'))
            assert applied_profile['applied'] and all(r['profile_id']==run_id for r in applied_profile['applied'])
            (out/'scenario.json').write_text(json.dumps(scenario, indent=2))
            (out/'applied-profile.json').write_text(json.dumps(applied_profile, indent=2))
            applied = [{'at_s': r.get('relative_s', 0), 'rate_mbit': r['rate_mbit'],
                        'delay_ms': r['delay_ms'], 'loss_percent': r['loss_percent']}
                       for r in applied_profile['applied']]
        # Existing player flush interval is 5 seconds. Keep it alive for one final flush.
        time.sleep(6)
        db = MongoClient(os.getenv("LEO_MONGO", "mongodb://starlink:starlink@localhost:27017/"), serverSelectionTimeoutMS=10000)["starlink"]
        final = final or {}
        decisions = final.get("decisions", [])
        if decisions:
            db[f"decisions-{run_id}"].insert_many([{**d, "experiment_id": run_id} for d in decisions])
        counts = {name: db[f"{name}-{run_id}"].count_documents({}) for name in ["events", "metric", "qoe", "decisions"]}
        summary = {"run_id": run_id, "algorithm": args.algorithm, "requested_seconds": args.seconds,
                   "started_utc": clock_start, "wall_clock_start_second": int(clock_start[17:19]),
                   "target_latency_s": args.target, "catchup": args.catchup, "url": url,
                   "load_wall_clock_utc": loaded_utc,
                   "scenario_id": scenario['id'] if scenario else None,
                   "variant": getattr(args, 'variant', None),
                   "actual_abr_strategy":final.get('actual_abr_strategy'),"auto_switch_video":final.get('auto_switch_video'),
                   "shared_probe_active":final.get('shared_probe_active'),"diagnostic_model_failure":getattr(args,'simulate_model_failure',False),
                   "fixed_kbps":getattr(args,'fixed_kbps',-1),"neural_variant":getattr(args,'neural_variant',None),
                   "scheduled_start_unix_s": scheduled_start,
                   "controlled_stages": applied, "samples": len(samples), "mongo_documents": counts,
                   "media_time_end": final.get("media_time"), "ladder": final.get("ladder"),
                   "build": final.get("build"), "model": final.get("model"),
                   "page_load_to_ready_ms":page_ready_ms,"runtime_prewarm_ms":runtime_prewarm_ms,"clock_mode":"host" if getattr(args,"local_clock",False) else "external","utc_synchronization_enabled":final.get("utc_synchronization_enabled"),"model_assets_cold_load_ms":final.get('model_load_ms'),
                   "decision_count": len(decisions),
                   "played_advance_s": sum(b['media_time'] - a['media_time'] for a, b in zip(samples, samples[1:])
                        if not b['paused'] and b['ready_state'] >= 3 and
                        0 < b['media_time'] - a['media_time'] < (b['elapsed_s'] - a['elapsed_s']) * 1.5),
                   "completed_video_requests": len([r for r in final.get('requests', []) if r['type'] == 'MediaSegment' and r['code'] == 200 and r['finish']]),
                   "player_errors": final.get('player_errors', []),
                   "console_severe": [c for c in console if c.get("level") == "SEVERE"][-30:]}
        (out / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Saved timeline: {plot_run(out)}")
        if not getattr(args, 'allow_poor_playback', False):
            assert summary['played_advance_s'] > 5, "No sustained real playback advancement"
            assert summary['completed_video_requests'] >= 3, "Too few successful video downloads"
        assert counts["metric"] > 0 and counts["events"] > 0, "No actual MongoDB playback evidence"
        print(json.dumps(summary, indent=2))
        return summary
    finally:
        driver.quit()
        set_profile(None)
        try:
            port = docker('compose', '-f', 'docker-compose-emulation.yaml', 'port', 'stat-server', '8000').rsplit(':', 1)[1]
            requests.post('http://localhost:' + port + '/ping/stop', timeout=10)
        except (requests.RequestException, subprocess.SubprocessError):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", default="abrCMAB")
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--target", type=int, default=3)
    parser.add_argument("--catchup", default="liveCatchupModeLoLP")
    parser.add_argument("--stages", default="", help="Controlled link: seconds:Mbps,...; blank replays original trace")
    parser.add_argument("--align-minute", action='store_true', help='Load at UTC minute boundary for matching source/catch-up phase')
    parser.add_argument('--final-telemetry', action='store_true', help='Capture passive 100ms actually-rendered playback ledger')
    parser.add_argument('--scenario', help='Versioned workload manifest')
    parser.add_argument('--case', help='Case ID within workload manifest')
    parser.add_argument('--allow-test', action='store_true', help='Only for frozen final evaluation')
    parser.add_argument('--local-clock',action='store_true',help='Explicit single-host emulator clock; avoid external UTC HTTP dependencies')
    parser.add_argument('--variant', help='Whitelisted improved-CMAB configuration')
    parser.add_argument('--fixed-kbps',type=float,default=-1,help='Calibration only: disable video ABR at this nominal rate')
    parser.add_argument('--neural-variant',choices=['conventional','leo'])
    run(parser.parse_args())
