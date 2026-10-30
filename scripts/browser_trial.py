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
 model_load_ms:window.LEO_ABR && window.LEO_ABR.modelLoadMs||null,
 rendered:window.__anjanRendered||[],player_errors:window.__phaseaErrors||[],
 callbacks:window.__anjanCallbackDurations||[],
 dropped_frames:v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality().droppedVideoFrames : null}));
"""


def run(args: argparse.Namespace) -> dict:
    run_id = f"phasea-{args.algorithm}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
    out = ROOT / "artifacts" / "runs" / run_id
    out.mkdir(parents=True)
    options = webdriver.ChromeOptions()
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("ignore-certificate-errors")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Remote(os.getenv("LEO_SELENIUM", "http://localhost:4444"), options=options)
    stages = [(float(pair.split(":")[0]), float(pair.split(":")[1])) for pair in args.stages.split(",")] if args.stages else []
    samples, applied = [], []
    params = {"experimentID": run_id,
              "mpdURL": "https://nginx/livesim2/vectors/switching_sets/12.5_25_50/ss1/2023-04-28/stream.mpd",
              "targetLatency": args.target, "constantVideoBitrate": -1,
              "abrGeneral": args.algorithm, "maxDrift": 5, "minCatchupPlaybackRate": -0.17,
              "maxCatchupPlaybackRate": 0.17, "abrAdditionalAbandonRequestRule": "true",
              "cmabAlpha": 1.0, "catchupMechanism": args.catchup}
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
        driver.execute_script(r"""
          window.__phaseaEvents=[];
          window.__phaseaErrors=[];
          const v=document.querySelector('video');
          ['playing','waiting','stalled','seeking','seeked','pause','error','loadedmetadata'].forEach(n=>v.addEventListener(n,()=>window.__phaseaEvents.push({event:n,at_ms:performance.now(),media_time:v.currentTime})));
        """)
        set_profile(stages[0][1] if stages and stages[0][0] == 0 else None)
        if getattr(args, 'align_minute', False):
            while datetime.now(timezone.utc).second != 0:
                time.sleep(0.2)
        driver.find_element(By.ID, "load-button").click()
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
        if final:
            final["elapsed_s"] = time.monotonic() - started
            samples.append(final)
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
                   "controlled_stages": applied, "samples": len(samples), "mongo_documents": counts,
                   "media_time_end": final.get("media_time"), "ladder": final.get("ladder"),
                   "build": final.get("build"), "model": final.get("model"),
                   "page_load_to_ready_ms":page_ready_ms,"model_assets_cold_load_ms":final.get('model_load_ms'),
                   "decision_count": len(decisions),
                   "played_advance_s": sum(b['media_time'] - a['media_time'] for a, b in zip(samples, samples[1:])
                        if not b['paused'] and b['ready_state'] >= 3 and
                        0 < b['media_time'] - a['media_time'] < (b['elapsed_s'] - a['elapsed_s']) * 1.5),
                   "completed_video_requests": len([r for r in final.get('requests', []) if r['type'] == 'MediaSegment' and r['code'] == 200 and r['finish']]),
                   "player_errors": final.get('player_errors', []),
                   "console_severe": [c for c in console if c.get("level") == "SEVERE"][-30:]}
        (out / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
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
    run(parser.parse_args())
