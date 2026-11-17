# Group 4: reproduction and demo

Use the final report for results and interpretation. This document describes the
actual commands and the distinction between replaying saved evidence and running
new experiments. Team contribution details in the report are intentionally blank.

## 1. Inspect or reproduce the submitted results

The submission ZIP includes the player source needed by our Dockerfile. A normal
GitHub ZIP of the parent repository omits Git submodule contents.

In a new Python 3.11 environment, from the extracted submission root:

```sh
python -m pip install -r requirements-results.txt
python scripts/prepare_player.py
python scripts/reproduce_final.py --saved-results
```

This checks all 303 frozen source identities, all 179 trial keys, compressed-event
hashes, actual playback metrics, shared observation cutoffs, epoch/monotonic clock
agreement, applied network schedules and source phase. It regenerates
`artifacts/final/evaluation/analysis.json`, F3-F5 and T3-T4. It needs neither Docker
nor MongoDB nor the original local `artifacts/runs` directory. There is no training
or new network experiment in this command. Windows/Linux text line endings are
normalized only for the scientific source identity; the release manifest records
exact payload bytes separately.

The report and presentation are delivered ready to view. To rebuild the report:

```sh
python -m pip install -r requirements-report.txt
python scripts/build_final_report.py
```

The authored presentation source is `scripts/build_final_presentation.mjs`. It uses
the Codex bundled `@oai/artifact-tool` runtime, with runtime/skill paths provided
as environment variables described at the top of that source. Viewing/editing
the delivered PPTX does not require that runtime.

## 2. Obtain a full developer checkout

```sh
git clone --branch anjan --recurse-submodules https://github.com/raj-gigt/mmsys24-starlink-livestreaming LEO_ABR_RL
cd LEO_ABR_RL
git submodule update --init --recursive
python scripts/prepare_player.py
```

The parent pins a published commit in `https://github.com/anjanrd/dash.js`.
`artifacts/final/evaluation/publication.json` maps the pretest freeze to the
published measured source. The freeze's older parent Git anchor alone does not
identify subsequently published files; the canonical file hashes do.

Keep the directory name **LEO_ABR_RL** for live experiments: the existing browser
runner uses the corresponding Compose player container name. On Windows the
runner invokes Docker in **Ubuntu-22.04 WSL**, as tested. Linux can run Docker
directly. The no-browser saved-results route works in other folder names.

## 3. Start the real testbed

Requirements: Docker Engine/Compose on Linux or WSL, network access to the pinned
images, available ports 443/4444/7900/8081/8888/27017, and space for images/media.
The pinned livesim2 image already contains the shared video; no separate large
WAVE download is needed. Avoid running multiple browser trials concurrently.

From a WSL/Linux shell in the checkout:

```sh
bash scripts/testbed.sh up
bash scripts/testbed.sh status
```

The script builds the local modified player and typed RTT statistics sidecar,
then starts the pinned services without rebuilding upstream Nginx. It uses all
five Compose files in the project. Do not use only the upstream Compose file:
that selects a prebuilt player and omits our common fixes/instrumentation.

In the Python environment used for browser trials:

```sh
python -m pip install -r requirements-phase-a.txt
python scripts/demo_final.py --policy improved --record
python scripts/demo_final.py --policy original --record
```

Watch **http://localhost:7900** (the Selenium image's default VNC password is
`secret`). Each command uses the same named 90-second development recovery case,
the actual ABR controller, completed video downloads and MongoDB playback
records. Recordings, compressed evidence, screenshots and summaries go to
`reports/final/demo`. Demo sessions are excluded from the final performance table.
The recorder uses the upstream Selenium video sidecar, pinned by digest.

The launcher refuses to share Chrome with an unfinished final matrix. Stop the
prior trial before starting another. It temporarily pauses WSL guest NTP and
restores the previous state, preventing wall-clock steps observed in earlier
diagnostics. Linux users need permission to manage `systemd-timesyncd` (for
example, run the launcher through `sudo -E /absolute/venv/bin/python`). The
explicit `hostClock=1` option is valid for this single-host emulator, not a claim
that independently clocked remote clients need no synchronization.

If playback/testbed readiness fails, inspect `bash scripts/testbed.sh status`, the
demo log, and `docker logs dashjs-nginx`. Reset the testbed with
`bash scripts/testbed.sh down` followed by `up`; this does not delete the MongoDB
volume. Check the clock guard after any forced process termination:

```sh
python scripts/experiment_clock.py status
python scripts/experiment_clock.py release
```

## 4. Policy selection and integration

The player is at the mapped port reported by `docker compose -f
docker-compose-emulation.yaml port dashjs 3000`, under
`/samples/starlink/testplayer/`. The scripted demo sets all necessary URL/player
options. Policy query choices are:

| Policy | Query choice |
|---|---|
| Reference | `abrGeneral=abrCMAB` |
| Selected CMAB | `abrGeneral=abrCMABImproved&cmabVariant=guard` |
| Safety-only control | `abrGeneral=abrCMABImproved&cmabVariant=guard_only` |
| Conventional A2C | `abrGeneral=abrAnjanRL&neuralVariant=conventional` |
| LEO A2C | `abrGeneral=abrAnjanRL&neuralVariant=leo` |

CMAB uses the existing synchronous Pyodide path. The neural actor is a synchronous
Float32 JavaScript forward pass on the Chrome host CPU. Its 36/64-input contracts,
normalization, action mapping, weights and examples are in `models/final` and
`configs/final`. A background RTT poll caches completed measurements before an
ABR decision; a policy does not query MongoDB or return a Promise to dash.js.
`node scripts/check_final_export.cjs` reproduces native/JS fixture agreement.

## 5. Data preparation and training

The included processed arrays and manifests are sufficient for training. They
contain 48 training, 18 validation and 18 old simulator-test scenarios; only
training/validation feed model selection. Final browser testing has its own
separately frozen cases. Measured RTT, generated bandwidth/outages and missing
probe observations are distinguished in the manifests. Actions recorded by CMAB
are not treated as optimal supervised labels.

To regenerate arrays in a disposable developer copy:

```sh
python scripts/prepare_data.py
python scripts/prepare_final_workloads.py
```

The Victoria one-second cache is included. Recreating it from original probes
requires downloading the URL in `data/manifests/lens-reserve.json` to the listed
path and matching its SHA256 before processing. The 36.4MB original archive is
omitted from the compact submission. Retain the LENS attribution/license.

To train **new fits**, use a disposable copy and move its existing
`artifacts/final/training` folder to an external archive first. The trainer skips
already completed fits; invoking it in the submitted tree alone does not retrain.

```sh
python -m rl.train_final --stage screen --device cpu
python -m rl.train_final --stage main --device cpu
python -m rl.export_final
node scripts/check_final_export.cjs
```

There are four equal-budget recipes/two screening seeds, then five fresh main
seeds per observation type. Both use the same selected recipe. Each seed keeps
its best validation checkpoint, then the median validation seed is exported.
All curves, native checkpoints and unsuccessful late training are retained.
The main phase took approximately 44.3 minutes for 10.004 million decisions on
the measured laptop. A working RTX4060 was benchmarked; CPU was faster for these
small networks. These are observed times, not guarantees on other machines.
Training is a compatible A2C adaptation inspired by Pensieve/Gelato/Plume, not an
unchanged published pretrained model. The published Maguro reference has
incompatible inputs/actions and is retained separately with its MIT license.

## 6. Full new browser evaluation

Keep the delivered ZIP immutable. Use a fresh **recursive Git checkout** named
LEO_ABR_RL, start the testbed, and archive that copy's existing
`artifacts/final/evaluation` directory outside the checkout. This avoids both
overwriting submitted evidence and accidentally skipping its completed keys.
Do not alter the controller based on submitted test scores and call the same
suite untouched; revised policies need the sealed reserve or new workloads.

```sh
python scripts/experiment_clock.py hold
python scripts/freeze_final.py
python scripts/run_final_matrix.py
python scripts/archive_final_runs.py artifacts/final/evaluation/runs.json
python scripts/reproduce_final.py --saved-results
```

The freeze refuses overwrite and verifies the running Docker source. The runner
resumes completed keys and restores clock control in `finally`. A normal run has
170 controlled 120-second sessions and nine separate 180-second repository
replays: about nine hours of measured source-aligned cycles on the original
host. Only explicit dual-clock faults are automatically retried, with failed
recordings retained. Bad QoE or no useful playback is never an exclusion rule.
After a deliberate interruption, rerun the matrix command to resume; a hard kill
may additionally require `experiment_clock.py release`.

## 7. Scientific scope and licenses

The common score uses actually played nominal-quality utility, stalls, startup,
quality variation and excess live delay. It is not MOS/VMAF. Fitted CMAB download
feedback is a surrogate; it is not the independently evaluated playback score.
Conditional repeat intervals on fixed cases are not population-wide Starlink
confidence intervals. Related windows from two RTT recordings are not independent
measured capacity sessions. Raw repository replay differs from the paper's
stated emulator parameters and is reported separately.

Parent code: GPLv3 (`LICENSE`). Player: retained dash.js BSD notices. Reference
model: retained Sagar Patel MIT license. Croatia2019 video: EBU/CTA, CC-BY4.0;
delivered by the pinned upstream image. LENS traces/derived arrays: Jinwei Zhao
and Jianping Pan, MMSys2024, doi:10.1145/3625468.3652170, CC-BY-SA4.0 as recorded
in the manifests. Reproduction requires honoring these original notices.
