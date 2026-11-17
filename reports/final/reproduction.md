# Reproducing the final submission

Start with the eight-page report and root README. This guide separates verification
of measured evidence from new training or network experiments. Individual
contribution statements are included in Section 1.1; no presentation files or demo
execution are required by this submission.

## 1. Verify and recompute saved results

Use Python 3.11 and an external virtual environment. In an extracted submission
root (any folder name for this route):

```sh
python -m pip install -r requirements-results.txt
python scripts/prepare_player.py
python scripts/reproduce_final.py --saved-results
```

Only NumPy/Matplotlib and their installed dependencies are needed: no PyTorch,
MongoDB, Docker, browser, local run folders or Git history. `prepare_player.py`
verifies the manifested player snapshot in a ZIP and preserves committed source
in a recursive Git clone. The reproduction command checks:

- All 303 canonical frozen source/configuration identities and both model hashes.
- All 179 distinct planned trial keys and compressed event hashes.
- Per-session clock/cutoff consistency, applied link schedules and source phase.
- Actual observation preprocessing, neural logits/actions and unique CMAB feedback.
- Independent playback score/component recomputation to numerical tolerance.

It regenerates full-matrix `analysis.json`, all six balanced direct contrasts in
`four-policy-analysis.json`, deployment summaries, report figures and supporting
tables. Main CSV files are `T4-four-policy.csv`, `T4-four-policy-pairs.csv` and
`T4-four-policy-families.csv`. Main report figures are F1, F3-four-policy,
F4-four-policy, F5-four-policy-regression and F7-report-training. Development and
validation summaries are supporting evidence, not final-test tuning. Text CRLF/LF
normalization is used only for measured source identity; release hashes record
exact payload bytes.

With Node.js, separately verify all 394 native/JS export fixtures:

```sh
node scripts/check_final_export.cjs
```

Rebuild the paper with `pip install -r requirements-report.txt` followed by
`python scripts/build_final_report.py`. Its source uses ReportLab with Times
serif, numbered sections, scientific tables/figures and references; it does not
require a TeX installation. The user-approved contribution statements are stored
in `reports/final/tables/T6-contributions-template.csv`;
if filled later, rebuild and inspect the report and reverify/repackage the ZIP.

## 2. Full GitHub source versus the focused ZIP

### Paper figure/table source index

| Paper item | Reproducible source / output |
|---|---|
| Figure 1: system | `plot_final_architecture.py` → `figures/F1-system.*` |
| Figure 2: learning | `analyse_four_policies.py` + ten `training/main/*/curve.json` → `figures/F7-report-training.*` |
| Figure 3: paired effects | Same analysis + frozen `evaluation/runs.json` → `figures/F3-four-policy.*` |
| Figure 4: family differences | Same analysis → `figures/F4-four-policy.*`, `tables/T4-four-policy-families.csv` |
| Figure 5: regression | Same analysis + actual event payloads → `figures/F5-four-policy-regression.*` |
| Table 1: four-policy metrics | `tables/T4-four-policy.csv`, balanced analysis JSON |
| Table 2: all six contrasts | `tables/T4-four-policy-pairs.csv`, balanced analysis JSON |
| Table 3: hypotheses | Source audit + `plot_cmab_ablation.py` / `plot_cmab_validation.py` → supporting T5 tables |
| Table 4: runtime | `summarize_final_deployment.py` + actual decisions → `tables/T8-deployment.csv`, `evaluation/deployment.json` |

Script paths above are under `scripts/`; figure/table paths under `reports/final/`;
training/evaluation paths under `artifacts/final/`. T7 defines the exact score
semantics; T3 retains every final run, and T4 supporting tables retain complete
matrix, sensitivity, recovery and raw-replay results. The contribution table uses
T6 with the three user-approved statements.

```sh
git clone --branch anjan --recurse-submodules https://github.com/raj-gigt/mmsys24-starlink-livestreaming LEO_ABR_RL
cd LEO_ABR_RL
git submodule update --init --recursive
python scripts/prepare_player.py
```

The published player fork is `https://github.com/anjanrd/dash.js`, pinned at
`60f56693032bb7e12c174951da4ee05818383527`. The measured-source publication is
`be131536f260d64a6c7e6e4478d51e01e60bcf62`; the freeze file's older parent anchor
alone is not a complete source identity. `publication.json` explains this and
individual source hashes identify the measured snapshot. Later report/packaging
changes preserve those hashes.

A normal parent GitHub ZIP cannot include submodule contents. The **curated ZIP**
does include the full measured player source and its runtime dependencies at their
original paths. `release/submission-files.json` records the dependency closure,
classification and exclusions; `release/manifest.json` hashes every payload file.
The ZIP includes 179 final and six calibration event payloads with a matching
185-run subset index. Supporting development/validation ledgers remain compact;
their larger raw recordings and additional research records remain on GitHub.
Redundant training weights, resume caches, environments, execution logs,
presentation material and unrelated upstream infrastructure are omitted.

## 3. Data and training reproduction

Delivered arrays are sufficient for training: 48 train, 18 validation and 18 older
simulator-test scenarios. Final browser workloads are separately frozen; training
and checkpoint selection use only their intended train/validation inputs.
The trace supplies RTT, not measured capacity, true handover labels or expert ABR
actions. Generated schedules and causal probe masks are explicitly recorded.

In a **disposable copy**, these commands regenerate scenario arrays and workloads:

```sh
python scripts/prepare_data.py
python scripts/prepare_final_workloads.py
```

`prepare_data.py` reads both bundled Seychelles CSV aliases, verifies timing/RTT
equality and uses seeded windows with guarded splits. Without the optional
`paper-data` submodule, auxiliary source-log metadata are absent; scenario values
do not depend on those logs. The Victoria one-second cache is bundled. To recreate
that cache from probes, download the source URL in `data/manifests/lens-reserve.json`
to its listed location and check the recorded SHA-256; the 36.4 MB original archive
is omitted from the focused ZIP. Never overwrite the submitted data/manifests when
checking regenerated numeric values.

For **new fits**, install `requirements-phase-a.txt` in a separate Python 3.11
environment (the historical filename pins the active ML dependencies). Use a
disposable copy, and move that copy's existing `artifacts/final/training` to an
external backup first. The trainer skips a completed manifest; leaving delivered
summaries in place does not retrain the models.

```sh
python -m rl.train_final --stage screen --device cpu
python -m rl.train_final --stage main --device cpu
python -m rl.export_final
node scripts/check_final_export.cjs
```

Screening runs four recipes × two seeds × two observation variants, 250k decisions
each. Main training uses the joint-selected recipe with five fresh seeds per
variant, one million decisions each. Each seed retains its best validation
checkpoint; the median-validation seed is exported per variant. The delivered
ZIP retains curves/selection records for every fit, plus both selected native
checkpoints at their original export paths and `models/final` deployment copies.
Additional checkpoints and interrupted-run resume state are not needed to inspect
the result. CPU measured faster than the tested RTX 4060 configuration for these
small networks; observed main fitting time was 44.33 minutes, not a hardware guarantee.
The A2C actors were trained from fresh networks after causal teacher initialization;
they are not unchanged pretrained Gelato weights or the full Plume pipeline.

## 4. Testbed and new browser measurements

Use a disposable **recursive Git clone** named `LEO_ABR_RL` for a new campaign;
the browser runner refers to that Compose project/container name. Windows was
tested with Ubuntu-22.04 WSL; Linux can run Docker directly. Install Docker Engine
and Compose, allow ports 443/4444/7900/8081/8888/27017, and retain network access
and disk space for pinned images. The livesim2 image already contains the shared
media. Full upstream cloud provisioning is not necessary for this emulation.

From the clone in Linux/WSL:

```sh
bash scripts/testbed.sh up
bash scripts/testbed.sh status
```

The script uses five Compose overlays, builds local modified player source and
the typed probe sidecar, and starts pinned upstream services without rebuilding
Nginx. Using only the original Compose file would select the upstream player.
Install `requirements-browser.txt` in the host trial environment (NumPy and
Matplotlib from `requirements-results.txt` are needed for analysis). The runner
drives container Chrome, where service hostnames resolve; an arbitrary host
Chrome tab is not the same network context. Keep browser trials sequential.

Policy choices in the player URL are:

| Controller | Query options |
|---|---|
| Original CMAB | `abrGeneral=abrCMAB` |
| Improved CMAB | `abrGeneral=abrCMABImproved&cmabVariant=guard` |
| Guard-only control | `abrGeneral=abrCMABImproved&cmabVariant=guard_only` |
| Conventional A2C | `abrGeneral=abrAnjanRL&neuralVariant=conventional` |
| LEO-aware A2C | `abrGeneral=abrAnjanRL&neuralVariant=leo` |

CMAB retains synchronous Pyodide; neural policies execute synchronous JavaScript
on the Chrome host CPU. Player histories and timestamped cached RTT health are
the inputs. MongoDB logs outcomes and is not queried by synchronous inference.

Before a **fresh full matrix**, archive that clone's existing
`artifacts/final/evaluation` directory externally; do not erase the delivered
evidence or leave completed keys that cause every trial to be skipped. Do not tune
a policy on submitted test scores and describe the same suite as unseen: revised
policies need the sealed reserve or new workloads.

```sh
python scripts/experiment_clock.py hold
python scripts/freeze_final.py
python scripts/run_final_matrix.py
python scripts/archive_final_runs.py artifacts/final/evaluation/runs.json
python scripts/reproduce_final.py --saved-results
```

Freeze creation refuses overwrite and checks running player source against the
clone. It requires Git metadata; use the recursive clone for a newly recorded
freeze. The runner restores clock control in `finally`; only dual-clock faults
are retried automatically, with invalid evidence retained. Poor QoE/no playback
is never an exclusion criterion. The full schedule contains 170 controlled
120-second sessions plus nine 180-second raw replays, about nine hours including
source-phase alignment on the original host. A rerun measures fresh noisy outcomes;
exact equality is expected only for saved-evidence recomputation.

The explicit single-host clock option and temporary NTP pause avoid measured
guest-clock steps. Linux users need permission to manage `systemd-timesyncd`;
Windows invokes the tested WSL distribution. After a hard kill, inspect/release:

```sh
python scripts/experiment_clock.py status
python scripts/experiment_clock.py release
```

## 5. Evidence interpretation and release verification

The common score integrates played nominal-quality utility, startup, rebuffering,
played-quality variation and excess live delay. Catch-up wait remains rebuffering;
skipped media earns no played utility. It is not MOS/VMAF or the CMAB internal
download surrogate. All six main contrasts use identical two-repeat pairs.
Supporting three-repeat CMAB effects are separately labeled. Related RTT windows,
synthetic capacity, calibration error and limited repeats restrict generalization.
Raw repository replay differs from the paper's stated settings and is separate.

To assemble or verify another focused ZIP from a Git checkout:

```sh
python scripts/build_submission.py
python scripts/verify_submission.py release/Group4-submission.zip --extract-dir /absolute/external/new/LEO_ABR_RL
```

Use a new/empty extraction directory outside the project. Verification checks
every manifest byte, no unexpected files, the absence of presentation/cache
material, player snapshot preparation, and exact full/joint analysis agreement
after replaying all saved evidence. `release/clean-extraction-check.json` and
`SHA256SUMS` identify the actually checked archive. This is a release-integrity
check, not another 179-session campaign. The user uploads the ZIP to the portal.

Parent code retains GPL-3.0 (`LICENSE`), dash.js its BSD notices, studied Maguro
code its MIT attribution, Croatia media EBU/CTA CC BY 4.0, and LENS RTT/derived
arrays Zhao/Pan CC BY-SA 4.0. Source URLs and hashes accompany the data manifests.
