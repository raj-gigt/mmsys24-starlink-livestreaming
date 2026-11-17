# LEO-Aware Live Video Streaming: RL-Based Adaptive Bitrate Selection

**CS6048 · Group 4 · Final submission · branch `anjan`**

Anjan R D (ME23B157), Rajat Dugar (ME23B114), Deviprasad V K (ME23B164).
Specific individual contribution statements are intentionally blank in the report.

This course project extends Zhao and Pan's MMSys 2024 live-streaming artifact.
We improve its contextual multi-armed bandit (CMAB) and train compatible
conventional and LEO-aware A2C controllers. The same player, media, network
schedules and independent playback score evaluate all four policies.

## Start here

- [Final report (8 pages)](reports/final/Group4-final-report.pdf): methods, results, limits, references and GitHub link.
- [Reproduction instructions](reports/final/reproduction.md): saved evidence first, then optional training and new browser experiments.
- [CMAB source audit](reports/final/cmab-audit.md): original behavior, hypotheses, negative findings and common infrastructure corrections.
- [Release inventory](release/submission-files.json): exact focused ZIP contents and why each file is needed.
- [Release checks](release/): byte manifest, ZIP checksum and clean-extraction/publication verification receipts when assembled.

## Main result: a common four-policy comparison

| Policy | QoE / wall s ↑ | Rebuffering s ↓ | Played nominal Mbps | Mean live delay s ↓ |
|---|---:|---:|---:|---:|
| Original CMAB | -1.0773 | 49.75 | 5.65 | 6.39 |
| Improved (guarded) CMAB | 0.2145 | 16.99 | 2.97 | 4.35 |
| Conventional A2C | 0.2391 | 9.55 | 1.25 | 3.71 |
| LEO-aware A2C | 0.2399 | 9.14 | 1.23 | 3.71 |

These are **80 actual Chrome sessions**, four policies × ten cases × two matched
120-second repeats. All three developed controllers improve aggregate QoE over
original CMAB on this suite. Direct paired intervals among those three include
zero: neither a unique best controller nor a further LEO-input gain is established.
They trade nominal quality for less stalling and live delay. The paper report
shows all six contrasts, scenario differences, regressions and uncertainty limits.

The complete frozen evidence contains **179 sessions**: 170 controlled sessions
(seven policies, with a third repeat for the three CMAB/guard controls) plus nine
separate 180-second repository replays. Those different-repeat aggregates are
supporting results; they do not replace the balanced main table. RTT is measured;
capacity/outages are generated. Conditional intervals on fixed cases are not
population-wide Starlink guarantees. Full Plume trace clustering is not implemented.

## Recompute the results without Docker or MongoDB

Use Python 3.11 in an external virtual environment. From this repository or the
extracted submission root:

```sh
python -m pip install -r requirements-results.txt
python scripts/prepare_player.py
python scripts/reproduce_final.py --saved-results
```

This checks all 303 frozen source identities, two trained models and 179 raw-event
payloads; recomputes playback metrics; verifies applied schedules, clocks and actual
policy inputs/actions; then regenerates the analyses, report plots and supporting
tables. No training or new browser measurement runs. A standalone parent GitHub
ZIP omits submodules: use our curated submission ZIP or clone recursively below.

## Code map: what to inspect

| Component | Main files / folders | Ownership and role |
|---|---|---|
| Original CMAB | `dash.js/src/streaming/rules/abr/cmab/CMABAbrController.js`, `CMABRule.js` | Inherited reference decision logic; common initialization/observation guards documented separately |
| Improved CMAB | Same directory: `CMABImprovedController.js`, `CMABImprovedRule.js`, `CMABFeedback.js`, `CMABRuntime.js` | New guarded controller, causal completed-request feedback and runtime interface |
| Neural browser rule | `dash.js/src/streaming/rules/abr/anjan/AnjanRule.js`, `rl/web/final_core.js`, `sync_actor.js`, `final_models.js` | Our observation routing and synchronous JS actor; frozen compatibility helpers are still loaded |
| Neural training | `rl/train_final.py`, `final_env.py`, `features.py`, `warmstart.py`, `export_final.py` | Our compatible A2C workflow, simulator, causal feature contracts and export; standard SB3 optimizer/algorithm |
| Active base simulator | `rl/pilot_env.py` | Required base class for `final_env.py`; its historical name does not make it unused |
| Trained models | `models/final/{conventional,leo}` | Selected native checkpoints, JS layer arrays, manifests and parity examples |
| Data and workloads | `data/{manifests,processed}`, `configs/final/workloads` | Provenance, split/seed records, compact arrays and declared impairment schedules |
| Common testbed | `Dockerfile-player-anjan`, five `docker-compose*.yaml` overlays, `stats-server`, `shaper/tc-final.py` | Inherited service stack plus our local-source build, typed probe health, replay/instrumentation fixes shared across policies |
| Experiments and metrics | `scripts/browser_trial.py`, `run_final_matrix.py`, `freeze_final.py`, `rl/metrics.py` | Controlled Chrome trials, immutable source/workload plan and independent playback scoring |
| Analysis / integrity | `scripts/reproduce_final.py`, `analyse_final.py`, `analyse_four_policies.py`, `rl/{decision_validation,replay_validation}.py` | Raw-event verification, full matrix and balanced four-policy reporting |
| Evidence and paper | `artifacts/final/{evaluation,evidence,training}`, `reports/final` | Compact verified outcomes, seed/selection records, figures/CSV tables and final report |

The inherited Docker environment supplies unmodified upstream dependencies and
media. MongoDB is for logging; bitrate decisions use current player observations
and cached RTT, not a synchronous database query. CMAB keeps synchronous Pyodide;
both trained actors use synchronous JS on the Chrome host CPU, without a worker.

## Full developer checkout and testbed

```sh
git clone --branch anjan --recurse-submodules https://github.com/raj-gigt/mmsys24-starlink-livestreaming LEO_ABR_RL
cd LEO_ABR_RL
git submodule update --init --recursive
python scripts/prepare_player.py
# Linux / Ubuntu-22.04 WSL, Docker Engine and Compose:
bash scripts/testbed.sh up
bash scripts/testbed.sh status
```

The parent pins the published [team player fork](https://github.com/anjanrd/dash.js)
at `60f56693032bb7e12c174951da4ee05818383527`. Keep directory name `LEO_ABR_RL`
for live trials because the runner uses its Compose container name. The ZIP
contains the exact required player source without Git metadata. Pinned upstream
images still need network access and disk space; this is not an air-gapped release.
See the reproduction guide before regenerating data, training or starting a new
campaign, to avoid overwriting submitted evidence or skipping completed fits.

## Historical material and attribution

The same repository retains Phase A pilots, diagnostics, unsuccessful variants
and research history for traceability. They are not all required submission files;
the focused ZIP uses an explicit dependency/evidence inventory rather than copying
whole development folders. Required relative paths and submodule pins are preserved.
`roadmap.md` and `artifacts/final/state.json` track execution. Presentation/demo
work is deferred and excluded from this submission package.

[Original artifact documentation](https://github.com/clarkzjw/mmsys24-starlink-livestreaming#readme)
describes the inherited cloud/real-link setup; the commands above select our local
modified player and common final emulator. Parent code retains [GPL-3.0](LICENSE),
dash.js its [BSD notices](dash.js/LICENSE.md), and studied Maguro code its MIT
attribution. LENS RTT data/derived arrays credit Jinwei Zhao and Jianping Pan
([MMSys 2024](https://doi.org/10.1145/3625468.3652170), CC BY-SA 4.0).
The supplied Croatia video is EBU/CTA CC BY 4.0, delivered by the upstream media image.
