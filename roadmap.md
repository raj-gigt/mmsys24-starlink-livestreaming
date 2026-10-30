# LEO-aware RL ABR execution roadmap

## Objective and execution rules

Improve the paper's existing CMAB bitrate controller while keeping the rest of the streaming system the same. Complete only the proposal's mandatory deliverables. The first checkpoint is the mid review on **31 October 2026**; the final phase develops and evaluates the improved RL policy.

- Keep all project code, configurations, models, results and presentation work inside `LEO_ABR_RL`. Work on the parent repository's **`anjan`** branch. Create an `anjan` branch in a submodule before editing its source; a parent branch alone does not protect a submodule's detached checkout.
- Execute one step at a time. Before execution, explain its objective, intuition, actions and verification, and offer **Codex / manual / coordination**. The user's selection authorizes that step. Verify it, update its status here, then wait before advancing. Routine fixes within the authorized step do not need another design-approval phase.
- Preserve the upstream experiment configurations. Use separate overrides and new policy labels. Store checksums, source revisions, image identities and commands with actual results. Keep environments, package caches and scratch work outside the project; do not create a project `tmp` folder.
- Use live measurements collected by the player and its in-memory history to make decisions. Continue using the existing backend/MongoDB path to record and inspect evidence. A database read is not a prerequisite for each decision.
- For the mid review, both the simple test policy and neural-policy execution use a **synchronous JavaScript call**. Python/PyTorch remain offline development tools. Compare alternative runtimes after the review.
- The old roadmap's feature count, layer sizes, reward coefficients and worker choice are not automatically reinstated. Select model details from the compatibility checks and validation below; keep a small actor as the initial candidate.

## Phase A - Establish the system and prepare the mid review

Execution: Steps 1-6 authorized as one autonomous batch on 30 October 2026.

| Step | Status | Evidence |
|---|---|---|
| 1 | Complete | `artifacts/setup/`: Docker/Compose metadata and successful NET_ADMIN container probe; parent/player branches `anjan` |
| 2 | Complete | 25 archived-data figures; `artifacts/reproduction/verification.json` and visually inspected contact sheet |
| 3 | Complete | Fresh CMAB/Dynamic/L2A/LoL+ playback and MongoDB evidence; `artifacts/baselines/verified.json`; measured 2/8-Mbps shaping, outage and recovery. Failed trace CMAB run retained. |
| 4 | Complete | `artifacts/integration/phasea-abrAnjanSimple-20261029T222254-d1324b.json`: 40 live decisions, 39 matched completed requests, MongoDB path and played-quality response verified; lifecycle tests passed |
| 5 | Complete | 84 deterministic, labelled scenarios; source/split/media manifests; leakage/unit/hash checks passed; independent LENS RTT reserve acquired; StarNet throughput acquisition remains follow-up |
| 6 | Complete | Reference parity: 64 fixtures; pilot parity: 44 fixtures; 39 real Chrome decisions matched Python, zero fallbacks, complete-decision p99 0.4ms. `artifacts/phase-a-completion.json` and `reports/phase-a/README.md`; final LEO training remains Phase B. |

### Step 1 - Prepare the repository and experiment host

**Objective / intuition:** obtain the complete, reproducible codebase and a machine capable of running its Linux networking setup.

**Actions**

1. Use the [team fork](https://github.com/raj-gigt/mmsys24-starlink-livestreaming). The fresh-checkout sequence, from its intended parent directory, is:

   ```bash
   git clone --recurse-submodules https://github.com/raj-gigt/mmsys24-starlink-livestreaming LEO_ABR_RL
   cd LEO_ABR_RL
   git switch -c anjan
   git submodule update --init --recursive
   git submodule status --recursive
   ```

   If the checkout or branch already exists, inspect and reuse it rather than cloning over it or resetting changes. **Execution: repository and host/runtime checks completed on 30 October 2026; see `artifacts/setup/`.**
2. Read `README.md`, `starter.md`, `.gitmodules`, Compose files and Dockerfiles. Record the current parent/submodule commits before edits.
3. Prefer the team's available Linux x86-64 experiment host. This laptop has WSL2 Ubuntu distributions; verify Docker Engine/Compose and daemon access inside the chosen Linux environment. A Windows Docker CLI was not found during planning. Installation, administrator access or using another teammate's host may require coordination.
4. Verify Chrome-container support, sufficient disk/RAM/shared memory, Docker socket access, bind-mount paths, required ports and `NET_ADMIN` support for shaping. Run Compose from a Linux shell and verify the resolved `${PWD}` paths. Do not provision paid cloud infrastructure implicitly.
5. For player edits, create `anjan` inside `dash.js`. Deliver submodule changes through a team-accessible fork/commit and parent pointer, or a parent-tracked patch applied by the build. Verify a teammate can recreate the modified player without unpublished local changes.

**Verify / output:** correct origin and branch; populated submodules with no `-`, `+` or `U` status prefixes; expected source files present; working Docker/Compose and networking capabilities. Save a host/setup record under `artifacts/setup/` when executed.

**Owner / dependency:** Anjan with Rajat and Deviprasad for the experiment host. Host installation/access can require coordination; the remaining CLI work is suitable for Codex.

### Step 2 - Regenerate the authors' figures from archived results

**Objective / intuition:** prove the analysis pipeline works before spending time running new streaming experiments.

**Actions**

1. Inspect `paper-data/README.md`, `paper-data/src/Makefile` and the archived data. Preserve the supplied data unchanged.
2. From the repository root on the Linux experiment host, follow the README's reproduction route:

   ```bash
   docker run --rm \
     -v "$PWD/paper-data/data:/data:ro" \
     -v "$PWD/paper-figures:/app/src/figures" \
     clarkzjw/mmsys24-reproducibility
   ```

3. Record the actual image digest. If the prebuilt image is unavailable, build an equivalent analysis image from the pinned `paper-data` sources and record that substitution.
4. Check the streaming, latency and throughput figure groups, including bitrate, live latency, rebuffering, switching and QoE. Inspect axes, legends, data counts and correspondence to supplied results.

**Verify / output:** nonempty, readable figures and successful analysis logs, with source data and image identities. Label these **regenerated figures from the authors' archived measurements**, not newly reproduced network experiments.

**Owner / dependency:** Anjan/Deviprasad; Step 1. Codex can complete this once the host is ready.

### Step 3 - Run and verify fresh baseline experiments

**Objective / intuition:** establish that the real player, network controls, measurement storage and result export work together.

**Actions**

1. Start with the actual mounted `experiments/batch-example.json`: one 60-second CMAB round, target latency 3 seconds, with an explicit LoL+ catch-up override. Do not assume Compose selects the README's long batch.
2. Inspect configuration, pull the images and start the stack:

   ```bash
   docker compose -f docker-compose-emulation.yaml config
   docker compose -f docker-compose-emulation.yaml pull
   docker compose -f docker-compose-emulation.yaml up -d
   docker logs -f dashjs-runner
   ```

3. Verify readiness of livesim2, the player/proxy, Selenium Chrome, statistics server and MongoDB. Inspect playback through the existing noVNC viewer on port 7900. `VIDEO=0` disables the extra recording container, not that viewer.
4. Verify the active `runner/tc-trace.py`, launched by `shaper/supervisord.conf`. Inspect shaping logs and `tc -s qdisc/class show dev eth0`, then measure effective delay, loss, outages and throughput. The script omits root-qdisc creation and specifies HTB rates above their ceilings; commands may fail even while video plays. Resolve necessary defects, record the exact correction, and rerun CMAB on the corrected setup before comparing any new algorithm.
5. Treat the hour-long CSV as latency/loss-related input, not varying-bandwidth data. Verify which direction is delayed and distinguish configured egress delay from measured RTT. Log trace start/playback offset, live-source phase and wall-clock phase; align these for paired comparisons. The existing CMAB catch-up controller uses specific seconds of the minute, so matching only the trace offset is insufficient.
6. Check experiment-specific MongoDB event/metric collections and exported JSON/PNG files. Actual current output is `figures/emulation/target-<n>s/<experiment-id>/`, rather than assuming the README's `figures-emulation` location. Verify nonempty time series and real advancing playback, not just a successful container exit.
7. In separate short configurations, run CMAB, Dynamic, L2A-LL and LoL+. Retain a baseline snapshot. Use short runs for the review; schedule the full original matrix separately: 160 five-minute trials, approximately 13.3 hours of playback plus overhead.
8. Preserve results and database data when stopping the stack with `docker compose -f docker-compose-emulation.yaml down`; do not remove its persistent volume as routine cleanup.

**Verify / output:** fresh playback evidence, verified shaping measurements, experiment logs, populated MongoDB records and readable exported plots. Separate unchanged-source reproduction, any common bug repairs, and later policy modifications in the result labels.

**Owner / dependency:** Deviprasad leads emulation, Rajat supports the player/build, Anjan verifies data needed for ML; Steps 1-2. Coordination may be needed for host access.

### Step 4 - Add a simple custom JavaScript policy using actual player data

**Objective / intuition:** prove that our own policy really controls video requests before introducing a neural model.

**Actions**

1. Inspect the actual extension points:

   | Purpose | Source location |
   |---|---|
   | Algorithm identifiers | `dash.js/src/streaming/constants/Constants.js` |
   | Rule selection and synchronous calls | `dash.js/src/streaming/rules/abr/ABRRulesCollection.js` |
   | Existing mixed JavaScript/Python example | `dash.js/src/streaming/rules/abr/cmab/CMABRule.js` and `CMABAbrController.js` |
   | Other implementations | `ThroughputRule.js`, `BolaRule.js`, `L2ARule.js`, `lolp/LoLpRule.js`; Dynamic selection in `AbrController.js` |
   | Player controls and measurements | `dash.js/samples/starlink/testplayer/testplayer.html` and `main.js` |
   | Batch configuration propagation | `runner/config.py`, `single_runner.py`, `experiments/` |
   | Storage and plots | `stats-server/app.py`, `runner/plot.py` |

2. Add a dedicated label such as `abrAnjanSimple` and an `anjan/` rule, following FactoryMaker/SwitchRequest integration. Preserve every existing algorithm. Connect the label through rule registration, player controls, URL parsing and runner configuration; explicitly propagate any new fields.
3. Implement a small synchronous throughput-and-buffer heuristic in JavaScript. For example, start low, select a representation below conservatively estimated recent delivery rate, and step down when the buffer is low. Treat its safety factor as a demonstration setting, not an optimized model.
4. Obtain buffer, completed video-download history, previous quality, live latency and playback rate from the player's APIs. Add RTT only through an observed, freshness-aware probe result when needed. Use current observations/in-memory history; send decision records through the existing experiment-specific logging route asynchronously. Do not introduce a MongoDB read or network inference request into the ABR call.
5. Build the modified local player. The upstream `Dockerfile-dashjs` clones a remote branch, and Compose uses a prebuilt image: add a deliberate local-source build/override and verify a unique build marker in Chrome. Keep the other services unchanged except shared necessary repairs from Step 3.
6. Map actions through actual representation IDs. Associate a decision with its real request; handle repeated callbacks, initialization requests, retries and seeks without duplicate actions. Preserve CMAB's effective rule-selection behaviour for the main replacement comparison.
7. Use separate configurations with the same media, network, target, catch-up and other playback settings as the corresponding CMAB control. New strategy names otherwise receive a different catch-up default in the current runner, so copy `CATCH_UP` explicitly.

**Verify / output:** a live-data decision log linking observations -> selected representation -> actual HTTP request -> played quality, matched MongoDB records, and a short demo in which a controlled capacity change causes an explainable policy response. Test startup/missing data and reset behaviour. A hard-coded action sequence or fixture-only test does not satisfy this step.

**Owner / dependency:** Rajat leads player wiring; Anjan implements policy/preprocessing and checks evidence; Deviprasad supplies controlled conditions. Step 3. Codex can implement this with a working testbed.

### Step 5 - Prepare and separate the data

**Objective / intuition:** build a defensible development dataset before fitting a model, while keeping final test conditions unseen.

**Actions**

1. Inventory local RTT recordings, the two short downlink throughput examples under `paper-data/src/throughput/downlink/`, archived playback results and our new player logs. Record origin, units, dates, duration, gaps, invalid values, checksums and licenses. The derived/local RTT CSVs may represent the same recording; do not count them as independent sessions.
2. Separate **network inputs** from **policy-dependent playback outcomes**. RL creates experience by interacting with a simulator; MongoDB's stored bitrate decisions are not a complete supervised dataset of correct actions. Use real browser logs for calibration and optional explicitly labelled imitation pretraining.
3. Seek a manageable independent Starlink-throughput subset from [StarNet](https://github.com/ConnectedSystemsLab/StarNet); audit available latency channels separately. Use [LENS](https://github.com/clarkzjw/LENS) for additional latency/loss diversity where accessible. Verify download access, size and provenance before acquiring large archives. Do not assume satellite-ID metadata is available to the deployed policy.
4. When matched measurements are unavailable, combine measured RTT/loss with documented synthetic bandwidth/interruption/recovery cases. Label independently combined channels as synthetic-assisted, not synchronized real Starlink recordings. Preserve the original paper-replay workload as a separate comparison group.
5. Split by original recording/session/day or location before cropping and augmentation. Use approximately 60/20/20 train/validation/test only when there are enough independent groups. If only one recording is available, use separated chronological blocks with guard gaps and explicitly limit the generalization claim. Put all derivatives in the same split.
6. Generate the five mandatory scenario families and mixed/shifted stress cases with disjoint split seeds/parameter combinations. Never smooth away all outages or turn missing RTT into zero; a lost probe alone is not proof of a full data-path outage.
7. Save `data/manifests/` entries and immutable split manifests; keep raw data under ignored `data/raw/` with retrieval instructions. Fit any learned transforms using training data only. Seal test data from model selection.
8. For tomorrow, time-box external acquisition to one hour. If unavailable, finish a truthful local-plus-synthetic development package and record richer acquisition as follow-up. Do not claim this small package establishes broad LEO performance.

**Verify / output:** source inventory, runnable parsers/scenario generation, split manifests and checks showing no recording/window leakage, correct units, reproducible seeds and explicit measured/synthetic labels. No final training configuration is selected from the test set.

**Owner / dependency:** Anjan, with Deviprasad's scenarios and logs; Step 3 and preferably Step 4. Codex can complete normal CLI work; restricted dataset access can require coordination.

### Step 6 - Export and integrate a synchronous neural baseline

**Objective / intuition:** establish a real executable neural policy and verify its calculations before treating it as an improved ABR controller.

**Actions**

1. Use [Gelato/Plume](https://github.com/sagar-pa/plume) as the starting reference. Inspect its A2C training code and [released actor definitions/checkpoints](https://github.com/sagar-pa/abr_rl_test). Pin source/checkpoint identity, verify the model's provenance and license, and identify the exact matching architecture. The earlier proposed 128-by-128 actor is a design candidate, not an existing trained model.
2. Check compatibility before deployment. The inspected Puffer actors assume ten actions and five-chunk size/quality metadata; our supplied source has eight representations, to be re-audited against the running MPD. The Puffer observation interface also exposes information ordinary dash.js does not. Do not silently clamp ten actions to eight, invent SSIM/TCP inputs, or describe changed inputs/weights as the unchanged published policy.
3. First port a verified released actor's forward calculation faithfully to JavaScript, including its actual dense/convolutional layers and activations. Export numerical weights plus executable `predict()` code and a model manifest. Preload assets before timed playback. `predict()` must return a completed numeric result synchronously; an ONNX `session.run()` Promise does not provide this interface.
4. Establish Python-to-JavaScript parity on native-format fixtures and recorded inputs: preprocessing, intermediate shapes, numerical output tolerance, action agreement, near ties and invalid-input behaviour. Use Float32-compatible calculations and deterministic selection. Node verifies calculations; Chrome playback is still required to measure deployment behaviour.
5. Deploy unchanged pretrained weights only if their full input/action requirements really match the player. The expected path is a **player-compatible Gelato-inspired A2C baseline**, clearly labelled as an adaptation rather than pretrained Gelato: retain only causal player-observable inputs and produce one score per actual representation.
6. If adaptation requires new weights, use Step 5's training-only development scenarios and a minimal, hand-checked streaming environment for a bounded pilot fit. Reuse the simulator approach of Step 8, including live availability and the measured catch-up behaviour; benchmark a short run before choosing its budget. Preserve the released-model export as the numerical reference. Record how many decisions were used and whether the resulting checkpoint is pilot-trained or untrained. A random/re-headed actor is not evidence of a trained baseline. Full calibration, tuning and final model training follow after review.
7. Register a separate label such as `abrAnjanRL`. Use the same real measurement collector and request actuator proven in Step 4, preload the actor, and log model identity and complete decision duration. No Pyodide installation is required by this new policy; the original CMAB can retain its existing runtime.
8. Exercise the neural policy on matched short cases and trace its action to the actual requested representation. Measure cold load separately and warmed-up decision percentiles during playback. Set a strict main-thread budget using measured device performance; do not reuse a 50-ms worker target as an acceptable main-thread stall. A JavaScript timer cannot interrupt synchronous calculation midway.

**Verify / output:** an executable JavaScript actor, weight/config identity, Python/JS parity report, real-player decision trace and a labelled pilot checkpoint where fitting was required. Keep **faithful published-model export**, **player-compatible adaptation**, and **demonstrated performance improvement** as distinct claims. The first two do not establish the third.

**Owner / dependency:** Anjan leads export/model work, Rajat integrates; Steps 4-5. Codex can perform the software work once the testbed is accessible. Treat checkpoint adaptation as a visible schedule risk; if incomplete by review, present its actual status and the verified simple-policy demo rather than fabricate a learned-model result.

### Step 7 - Build and rehearse the mid-review presentation

**Objective / intuition:** present reproducible implementation progress and a credible route to a better RL controller.

**Actions**

1. Reserve at least the final two preparation hours for the deck and rehearsal; do not let large downloads, the full 13.3-hour matrix or model tuning consume this time.
2. Consolidate executed evidence from Steps 1-6 into `reports/mid-review/`, including commands, plots, model/export checks and a recorded demo. Reference the original proposal/paper and the model source accurately.
3. Create `reports/mid-review/mid-review.pptx` with approximately 10-12 slides: problem and mandatory scope; unchanged testbed architecture; reproduction method; regenerated versus fresh artifacts; existing ABR choices; simple custom-policy integration; proof of real player-data use and MongoDB records; reference-model export/adaptation and actual status; data inventory/splits; next-stage RL training; runtime-comparison design; remaining milestones/limitations.
4. Explain the three planned runtimes: direct synchronous JavaScript; synchronous Python/NumPy through Pyodide/WebAssembly; ONNX Runtime Web in an asynchronous worker. Show why dash.js's synchronous `getMaxIndex()` caller needs an explicit scheduling bridge for a worker response, and why returning a Promise alone does not wait. Keep this study a future phase.
5. Include future training plans: calibrated live environment, strong A2C baseline, causal LEO inputs, balanced training, development-only tuning, repeated seeds, sealed testing and comparison primarily against CMAB. State that the improved LEO model is future work unless actually completed.
6. Render and inspect every slide, validate chart labels/units and claims, check the demo from a clean start, and prepare a video/log fallback. Clearly distinguish archived results, fresh runs, fixture tests, pilot learning and final evidence.

**Verify / output:** readable PPTX, inspected slide renders, a rehearsed explanation and an evidence-backed demo package for 31 October. No unsupported improvement claim and no slide marked complete solely because a command exited successfully.

**Owner / dependency:** Anjan consolidates ML/data results, Rajat supplies integration/demo evidence, Deviprasad supplies experiment results; Steps 1-6 with incomplete items honestly labelled.

## Mid-review checkpoint

Target evidence: reproducible checkout/host setup; regenerated paper figures; verified fresh baseline run(s); a selectable custom policy using real player observations; a faithful model-export/parity result and, where compatible or pilot-adapted, a synchronous neural player policy; a separated development/validation/test data package; and the reviewed presentation. An unresolved learned-policy adaptation is a reported gap, not permission to label the simple rule or random weights as a pretrained model.

## Phase B - Develop a better RL bitrate controller

### Step 8 - Complete and calibrate the fast live-streaming environment

**Objective / intuition:** train cheaply in Python while making the learned behaviour transfer to the unchanged player.

**Actions**

1. Implement one reusable Gymnasium environment under `rl/`, separate from the A2C/PPO trainer. Reuse useful reference code, but remove video-on-demand assumptions such as fixed RTT, a 60-second buffer or remaining-video features.
2. Represent actual segment byte sizes, source release times, playback/live clocks, buffer, startup, stalls, catch-up, seeks/discards and request retries. Reproduce the existing CMAB catch-up controller's wall-clock phase when it is the matched control setting, without presenting that schedule as universal satellite ground truth. Advance transfers across changing bandwidth samples. Check whether active low-latency chunk delivery requires partial-segment availability rather than assuming whole-segment playback.
3. Model measured goodput and synthetic link capacity differently; avoid charging RTT/loss twice when already embedded in a trace. Include policy-decision waiting and observed telemetry age/missingness.
4. Hand-check constant capacity, capacity change during a transfer, source wait, outage/recovery, startup, seeking and episode boundaries. Enforce byte/time conservation, finite rewards and nonnegative buffer. Distinguish time-limit truncation from true termination for value bootstrapping.
5. With Deviprasad and Rajat, compare fixed-low/middle/high-quality runs and existing controllers against Chrome on separate development cases. Compare download time, buffer, stall, latency and catch-up trajectories. Set tolerances from repeated-run variability before fitting parameters; accept no unexplained qualitative mismatch.

**Verify / output:** tested environment, shared reward/metric ledger, calibration plots and measured discrepancies. Fix important discrepancies before expensive training; retrain affected pilot models after meaningful dynamics changes.

**Owner / dependency:** Anjan leads; Rajat supplies the instrumented player and fixed-quality controls, Deviprasad supplies verified shaping/calibration runs. Steps 3-6. Target the first 3-4 working days after review.

### Step 9 - Establish a strong conventional RL baseline

**Objective / intuition:** demonstrate useful learning before attributing gains to satellite-specific information.

**Actions**

1. Train a player-compatible, Pensieve-style actor-critic using SB3 A2C and PyTorch. Follow the useful [Gelato training implementation](https://github.com/sagar-pa/plume/blob/main/puffer_abr/puffer_abr_training/train.py), without copying unsupported Puffer inputs or reward-scaled hyperparameters blindly.
2. Start with conventional streaming observations. Benchmark a compact MLP; compare a small causal temporal encoder only if development evidence justifies it. Freeze a feasible architecture after checking browser export cost.
3. Use easy-to-mixed training cases, then a balanced scenario sampler inspired by Plume. Keep workload sampling independent of policy randomness. Add save/load/resume, optimizer/RNG state, diagnostics and periodic validation.
4. Verify sensible behaviour against fixed-quality, throughput and BOLA policies. Reuse the browser's existing throughput/BOLA implementations for final comparisons; simulator approximations must be labelled/calibrated.
5. Retain A2C initially. If justified by instability or a measured development advantage, run a small matched A2C/PPO pilot and choose one common trainer before main training. Do not change the observation set and optimizer simultaneously when identifying their effects.

**Verify / output:** useful learning on simple cases, repeatable checkpoints, learning/validation plots and a deployable baseline. A completed training loop is insufficient if its policy always stalls, chooses only the lowest quality or fails an easy case.

**Owner / dependency:** Anjan; Steps 5 and 8. Aim for a stable reference during the first post-review week.

### Step 10 - Build and tune the LEO-aware policy

**Objective / intuition:** reduce the damage caused by abrupt delay/capacity changes and interruptions while retaining useful video quality and low live delay.

**Actions**

1. Add measured RTT history, live latency and a causal recent-disruption indicator to the same controller. Implement the corresponding collector/probe health code in the browser/backend; the current `/ping` can return zero or repeat the last success after failure, so extend freshness/outcome reporting before treating it as current truth.
2. Treat the disruption flag as an estimate, not satellite-handover ground truth. Train with realistic detection delay, missed/false events and stale samples. Keep future outages and test-trace identity hidden from the actor and critic.
3. Use the proposal's reward structure: played-quality utility minus stalls, quality variation and excessive live latency. Define units, time accounting and seek/startup treatment explicitly. Charge latency during long waits/outages and avoid quality credit for discarded media.
4. Tune a bounded development budget, for example six configurations with two pilot seeds, for learning settings and reward tradeoffs. Evaluate every policy with the same final objective and physical metrics; raw returns from different training rewards cannot be ranked directly.
5. Borrow [Genet's](https://arxiv.org/html/2202.05940v2) development-only hard-case sampling idea where the policy loses to conventional methods. Preserve ordinary cases so improved disruption handling does not destroy normal playback.
6. Modify architecture only after diagnosing data, dynamics, units, reward and optimization. Keep model versions and a short experiment ledger under `artifacts/`; avoid a large algorithm-by-state-by-reward grid.

**Verify / output:** a validation-selected LEO policy, component metrics, tuning history and event-level recovery plots. Compare primarily against CMAB in the matched testbed; use conventional-versus-LEO RL and feature removals to explain contributions.

**Owner / dependency:** Anjan with Rajat's actual observation collector and Deviprasad's development cases; Steps 8-9. Target the second post-review week.

### Step 11 - Run repeatable main training and focused robustness checks

**Objective / intuition:** establish that a promising pilot is not an unusually lucky training run.

**Actions**

1. Freeze the selected training configuration and reward before main runs. Aim for five fresh independent seeds for both conventional and LEO policies, with matched interaction/tuning budgets. Benchmark laptop/Colab/Kaggle CPU and GPU throughput before allocating compute; a small policy need not benefit from a GPU.
2. Save native checkpoints, selected exports, dependencies, code/data hashes, seeds, optimizer/RNG states and complete training/validation curves. Choose checkpoints on validation with a declared rule; never pick a seed using final test performance.
3. Inspect interruption/recovery behaviour, noisy or missing telemetry, unseen parameter combinations and normal-link regressions. Run a limited retrained feature ablation; distinguish it from masking inputs only at inference.
4. Track severe sessions and tail stalls alongside average QoE, taking inspiration from [SafeSABR](https://arxiv.org/html/2605.23560v2). Add risk-sensitive training only if a demonstrated failure warrants it and time permits. A new predictor/action shield is an additional algorithm component that must be evaluated and reported separately, not hidden as a player setting.

**Verify / output:** complete seed results, robustness/ablation plots and honest uncertainty/limitations. If the measured budget permits fewer seeds, report the actual study size rather than claiming the planned one was run.

**Owner / dependency:** Anjan; Step 10. Main training follows the configuration freeze and can overlap runtime engineering using frozen candidate checkpoints.

### Step 12 - Compare the three inference runtimes

**Objective / intuition:** choose the deployment route using the same trained policy and real playback measurements.

**Actions**

1. Implement equivalent forward passes for the same checkpoint, input transform, action mapping and deterministic postprocessing: (a) direct synchronous JavaScript; (b) synchronous Python/NumPy in the existing Pyodide/WebAssembly runtime; (c) ONNX Runtime Web/WASM in a worker. Export only inference-required actor components.
2. For the worker route, add a bounded asynchronous scheduling bridge: capture the intended decision, hold its next media request without blocking the main thread, accept a matching result or fallback, then resume the normal request/quality-switch lifecycle. `ABRRulesCollection` immediately reads `getMaxIndex()` results; simply returning a Promise or moving ONNX to the main thread does not make that caller await it.
3. Deduplicate callbacks, discard obsolete responses after seeks/resets/timeouts and prevent late answers changing committed requests. If cached precomputation is explored, label it as a different observation-timing mode and reproduce its staleness in training; do not mix it into the fresh-input runtime comparison.
4. First verify numerical/action agreement on identical recorded fixtures, including near ties. Then run repeated browser trials on the same host/resource allocation with the same scenarios and background load. Randomize runtime order and record Chrome/runtime versions and thread settings.
5. Measure complete decision p50/p95/p99, cold load, memory/CPU, responsiveness, stale responses, fallback frequency and resulting playback QoE. Separate model calculation from preprocessing, messaging and scheduling delay. Use each synchronous implementation's measured main-thread blocking; do not claim a timer can enforce a hard timeout during a blocked call.
6. Compare outcomes using common fallback rules where applicable and report raw predictions separately from the deployed policy-plus-fallback. Keep JS as the established review route until evidence supports changing it; update simulator timing and retrain only if the chosen mechanism materially changes the learning environment.

**Verify / output:** parity report, runtime benchmark table, playback comparisons and a justified deployment choice. Python/Node-only speed measurements do not establish browser performance.

**Owner / dependency:** Anjan exports/checks models; Rajat owns runtime integration/scheduling; Deviprasad runs matched trials. Steps 6 and 9; complete before final evaluation.

### Step 13 - Freeze and run the final comparison

**Objective / intuition:** test whether the new ABR algorithm improves the authors' system rather than benefiting from unrelated player changes.

**Actions**

1. Freeze models, code, runtime choice and sealed test manifests. Use a common running player build with selectable policies, the same media/ladder, transport, source, network implementation and start offsets, source/wall-clock phase, target latency, catch-up, seek/retry behaviour, startup settings and resource allocation. Change the bitrate decision rule only in the primary comparison. Shared necessary instrumentation/repair is present for both sides.
2. Make **CMAB versus the proposed LEO policy** the primary comparison. Explicitly carry CMAB's catch-up setting into the new algorithm's configuration, because the runner otherwise assigns its default mode. Preserve the authors' Dynamic/L2A-LL/LoL+ configurations for their reference comparisons, and include proposal-required throughput, BOLA and Pensieve-style baselines. Label any controller-specific playback differences.
3. Run the five mandatory scenario families plus predefined mixed/shifted diagnostics, using five-minute trials where practical. Cover the authors' 3/4/5/6-second latency targets. Pair policies on conditions, repeat browser trials and randomize order; do not treat adjacent trace crops as independent experiments.
4. Compute one common offline QoE objective from time-aligned physical events, rather than comparing the authors' CMAB internal reward numerically against an RL training return. Report average played bitrate, rebuffering duration, switch frequency/magnitude, startup, live latency and QoE; include played duration, skipped content, dropped frames and policy/fallback timing.
5. Report paired differences with uncertainty across independent recording groups and training seeds. Examine per-scenario regressions and severe sessions. Predefine acceptable quality/stall/latency tradeoffs on validation before unsealing tests. Retain failed/no-playback runs. Report mixed or null results honestly.
6. Complete the full authors' emulation matrix when the remaining time budget permits and identify exactly which parts were rerun. Keep synthetic, emulated-browser and real-satellite evidence distinct; no real Starlink deployment is implied by Docker results.

**Verify / output:** sealed evaluation configuration, comparable raw logs, aggregate and temporal plots, confidence intervals and a result explaining whether/where the proposed policy improves CMAB. Avoid percentage QoE gains when the reference score is zero or negative.

**Owner / dependency:** Deviprasad leads execution/analysis, Anjan supplies frozen models and validates findings, Rajat verifies builds and policy control. Steps 11-12. Reserve the final several project days for this and delivery.

### Step 14 - Package, reproduce and deliver

**Objective / intuition:** make the trained controller and evidence usable by the team and independently repeatable.

**Actions**

1. Deliver Python training/environment code, native model checkpoints, the selected browser artifact, input transform and action mapping, example inputs/outputs, model/data/config identities, and the training/validation/final-result plots under the repository.
2. Keep a clear layout: `rl/` for ML code and exporters, `experiments/` for run configurations, ignored `data/` for source material plus tracked manifests, `artifacts/` for run evidence, and `reports/` for presentations/report material. Keep useful manifests/scripts tracked even when large binaries/results are ignored.
3. Verify the team can recreate the player including submodule changes and the custom image, load the identified model, and reproduce one short experiment from a clean checkout. Do not leave required player commits accessible only in Anjan's local submodule.
4. Consolidate with Rajat's integration and Deviprasad's evaluation. Create the final report/presentation/demo using actual completed results and limitations; preserve the mid-review deck as the earlier checkpoint.

**Verify / output:** reproducible clean-checkout demonstration, complete mandatory-deliverable checklist and final team handoff. Completion requires working commands, correctly loaded weights and credible measurements, not only a successful build.

**Owner / dependency:** all three teammates; Step 13.
