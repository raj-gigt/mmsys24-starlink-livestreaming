# Project completion roadmap: improve CMAB and evaluate a neural alternative

Updated: 17 November 2026. Group 4 / CS6048. Deliverable definitions and figure/table IDs are in [deliverables.md](deliverables.md).

## 1. Objective, authorization and deadlines

**Primary track:** understand the reference CMAB in detail, test causal hypotheses, refine it and measure whether the resulting controller improves actual live playback. **Second track:** train a player-compatible Gelato/Plume-inspired actor-critic comparator, with conventional and LEO-aware observations. Preserve the proposal's required throughput/BOLA/RL comparisons and mandatory-only scope.

The user has authorized both this plan and autonomous execution ("begin autonomous run"). **Execution is active from Step 8.** Once that run is authorized, execute the pending steps sequentially without requesting a new mode selection or design agreement at every step. Routine design choices, diagnoses, fixes, verification and continuation are autonomous. The older per-step Codex/manual/coordination approval rule and runtime-study priorities are superseded.

**Commit/push authorization is now granted for the autonomous run**, by the user's message: "you can commit/push whenever you need to". Publish verified milestones; push edited submodule commits before the parent reference. Do not push unverified or unrelated changes. Retain all permanent code/configuration/result work in LEO_ABR_RL, parent branch anjan and anjan in any edited submodule. Preserve unrelated changes and historical evidence. Keep environments/caches/scratch outside the repository; no project tmp directory. No paid compute, unsolicited external messages or replacement repository.

Deadlines, in Asia/Calcutta:
- **Submission: 18 November 2026, 08:00.**
- **Presentation/demo: 20 November 2026, 11:00.**
- User's timing reference: 17 November, 02:50, giving 29 hours 10 minutes until submission. Recalculate the actual remaining time at execution start; do not pretend planning time leaves the full original window.
- Aim for a verified submission candidate by 18 November 05:00 and an immutable local release by 07:00, leaving upload/last-mile margin. The assistant prepares the package; portal submission requires access and explicit authorization if the user wants it performed.
- Freeze the submission's source/results/report identities before submission. Later slide/rehearsal improvements must not silently replace the report or introduce new results as if they were in the submitted release.

Use the existing synchronous routes: original CMAB/Pyodide where practical and synchronous JavaScript for the neural actor. No worker scheduling bridge, runtime comparison research, new congestion controller or model zoo. Asynchronous event logging or ordinary telemetry collection is allowed; the ABR decision still returns a completed synchronous result.

## 2. Reuse completed Phase A; do not start over

Historical work completed on 30 October is an existing foundation, not a claim that the host or final algorithms were tested today.

| Existing steps | Reusable assets/evidence | Remaining distinction |
|---|---|---|
| 1: checkout/host | Recursive checkout, pinned service/player revisions, WSL/Docker and NET_ADMIN checks | Recheck readiness and accessible commits; do not reinstall/reclone routinely. |
| 2: archived reproduction | 25 regenerated author figures and reproduction verification | Archived measurements are not our fresh final experiments. |
| 3: fresh operation checks | CMAB, Dynamic, L2A-LL, LoL+ and measured shaper checks | Short operation checks do not rank final policies. |
| 4: custom player integration | AnjanRule, simple policy, real observations/request mapping and lifecycle checks | Extend common instrumentation and add separately selectable CMAB variants. |
| 5: data preparation | Media byte catalog; 48/18/18 scenarios; provenance/split checks; LENS reserve | Synthetic-assisted data and one main RTT session limit generalization. |
| 6: neural deployment | Faithful released-reference export; separate 36-64-64-8 pilot; parity/browser evidence | Pilot is not unchanged pretrained Gelato or demonstrated CMAB improvement. |
| 7: mid-review | PPT and learning guide now in ../mid-review/ | Final report/deck must use new verified results and actual contributions. |

Current planning snapshot: parent branch anjan at ebfb427; player f31314a7 in the accessible anjanrd/dash.js fork. Re-read identities/status at execution start.

Do not overwrite models/pilot, old manifests, Phase A raw evidence or published reference assets while developing final variants. Version new outputs separately.

## 3. Execution method and experiment discipline

For every step:
1. Read its pending state and relevant evidence. Refine the local actions to match observed conditions without rewriting the whole roadmap.
2. State objective, simple intuition, concrete actions and verification in a concise progress update.
3. Implement the step, verify behavioural evidence and store commands/configuration/identities/results.
4. Update this tracker with status, evidence and any justified deviation, then continue to the next step.
5. On error: formulate a diagnosis -> create/run the smallest useful diagnostic -> inspect observations -> choose a fix -> implement -> rerun the failing check and relevant regression checks -> continue. A process exit alone is not verification.

Maintain a compact execution ledger under artifacts/final/ and this roadmap's status table. Record current step, completed run keys, actual throughput/runtime, hypothesis decisions, failed attempts and next action. Resume verified work rather than rerunning it after an interruption. A run key includes scenario, source phase, policy/config/model hashes, seed and repeat.

Run one browser streaming trial at a time on the shared shaped link. Do not run another browser experiment or a GPU/CPU-saturating training job concurrently with measured trials. Vectorized training environments within a training step are fine; algorithm development steps still proceed sequentially.

### Working layout and implementation entry points

Reuse existing files where their responsibilities fit. Proposed new paths are destinations for later implementation, not files created by this planning step:

| Component | Existing foundation / planned extension |
|---|---|
| CMAB controller | Preserve cmab/CMABAbrController.js and CMABRule.js; add sibling improved-controller/rule code with named variant configurations. Register one improved policy and forward its whitelisted variant configuration through the player/runner. |
| Observations, environment and training | Extend rl/features.py, rl/pilot_env.py, rl/train_pilot.py and rl/web/; extract shared outcome/metric code rather than duplicate it across policies. |
| Experiment definitions | configs/final/ for policy, training, metric, scenario/matrix and release settings; reference existing data/manifests/ rather than copy the data inventory. |
| Automation | Extend scripts/browser_trial.py; add focused matrix, analysis, verification and packaging entry points under scripts/. Separate final verification from historical verify_phase_a.py checks. |
| Models | models/final/conventional/ and models/final/leo/ with per-seed checkpoint identities, selected exports and feature/action manifests. Retain old models/pilot and models/reference unchanged. |
| Evidence | artifacts/final/ for the ledger, compact per-run exports, aggregates, attribution diagnostics and calibration/training checks. Heavy scratch/raw logs may stay ignored but required reproduction inputs must enter the release. |
| Report, plots and slides | reports/final/ for report source/PDF, generated figures/tables, demo instructions/recording and final deck. Reuse mid-review material only with correct historical labels. |
| Submission | A named release ZIP and manifest under a dedicated releases/ path, built from an explicit allowlist and tested after extraction outside the project. Avoid committing a duplicate archive as source by accident. |

Stop for genuine access/host failures that cannot be repaired within authorized scope, an unavoidable trajectory-changing decision, required human information, or commit/push/portal authorization. Do not stop for an ordinary test failure, a weak candidate, or a recoverable installation issue. Do not discard a poor result to make an improvement claim.

### Capacity and deadline management

RTX 4060 is available. Existing recorded CPU timings are about 16 seconds for 50,176 pilot decisions and 105 seconds for 500,224 in another run; these are evidence that training need not take hours, not forecasts for the revised environment. The current Python lock uses CPU-only PyTorch. Benchmark a separate CUDA-compatible external environment if needed, without breaking the working CPU environment.

Compare complete environment-plus-training throughput on CPU and RTX 4060, including validation overhead. Small MLP A2C can be faster on CPU; use measured throughput rather than either assuming GPU acceleration or ignoring available GPU capacity. Do not spend hours provisioning Colab/Kaggle when local training works.

These are working allocations/ceilings, **not durations to wait out or predictions that training will consume them**:

| Work | Default allocation within remaining window | How to expand intelligently |
|---|---|---|
| Foundation, Steps 8-10 | About 2.5 hours | Fix measurement defects before increasing run count. |
| Primary CMAB study, Steps 11-14 | About 5 hours | Spend saved time on justified hypotheses/ablations, not a full grid. |
| Neural calibration/training/deployment, Steps 15-17 | About 3 hours initially | Millions of decisions and five seeds are the default; extend from measured throughput and validation evidence. |
| Final browser evaluation, Step 18 | About 7.5 hours for the default matrix | Real playback and phase alignment constrain this; precompute runtime before starting. |
| Analysis, Step 19 | About 1 hour | Automatically generate from saved logs, then inspect explanations/outliers. |
| Report, Step 20 | About 2 hours | Build tables/sections as evidence arrives, not from scratch at the end. |
| Demo/deck, Step 21 | About 45 minutes for submission assets | Final presentation polish/rehearsal can continue after submission. |
| Packaging/clean verification, Step 22 | About 1.5 hours | Reserve time for real extraction/reproduction and authorization. |

The initial allocations sum to about 23 hours 15 minutes, leaving roughly 5 hours 55 minutes against the user's original clock reference. Recalculate at execution start. Unused allocation immediately becomes available for stronger evidence or earlier release. Do not reduce the research scope merely because a model is labelled RL. Protect the final report/reproduction/upload margin.

Target checkpoints: foundation usable around 06:00 on 17 November; primary candidate by late morning; both tracks available and final protocol frozen around 13:00; core measurements complete around 21:00; report/release checks overnight. These are targets to recompute from actual start, with the fixed submission deadline taking precedence.

If running late, remove optional searches and matrix extensions first, then reduce additional refinement cycles before touching required baselines, scenario coverage, physical metrics or release checks. Any unavoidable reduction to the core submission scope is a trajectory change to flag to the user. Never conceal it in a smaller sample count.

## 4. Common evaluation protocol to implement before tuning

### Policies and controls

- B0: original reference CMAB on the shared corrected infrastructure. Preserve its decisions/reward/reset behaviour, including awkward behaviour; passive observation is allowed.
- C*: the validation-selected improved CMAB. Its online updates continue during each evaluation session using only its own past feedback.
- THR: existing throughput rule.
- BOLA: existing buffer-based rule.
- N-CONV: trained conventional-input actor-critic baseline.
- N-LEO: trained LEO-observation actor-critic.
- Fixed low/mid/high and the Phase A simple rule are development diagnostics, not extra mandatory final-series entries.

Use the same media catalog, representation mapping, player build, target delay (initial default 3 seconds), catch-up mode (existing explicit LoL+ override), shaper implementation and relevant host settings. No policy-specific TCP/source/catch-up improvement. Keep raw original-CMAB paper-replay settings as a labelled additional group; do not blend them silently with controlled zero-background-loss cases.

Preload policy dependencies, then start measured playback at the planned phase. Measure cold setup separately. Startup delay for the main experiment is load/play trigger to first actual playback, with the initialization boundary stated; do not mix one policy's cold Pyodide download into a warm actor comparison. A cold-start sample remains part of deployment evidence.

### Common played-outcome ledger and scoring

Initial common score, reusing the pilot's interpretable components:
- Q: sum over actually played media of log(nominal representation bitrate / 300 kbps), weighted by media seconds / 2.
- B: video stall seconds, excluding startup, deliberate pause and user-initiated seek; automatic catch-up seek waiting is included and separately reported.
- S: startup seconds.
- V: sum of absolute log-utility changes at actually played quality boundaries.
- A: integral over wall time of max(0, live delay - target delay), including waits/stalls where observable.
- **QoE_total = Q - 4 B - 1 S - 0.3 V - 0.1 A.** Also report QoE_total / measured wall duration to compare different-length supplementary runs.

This is an explicit bitrate-utility proxy, not a perceptual MOS/SSIM/VMAF result. Use actual encoded bytes for transfers; do not use nominal bitrate as exact segment size. Track skipped media, discarded bytes, coverage and seeking so catch-up cannot create an unexplained reward gain.

Define metrics and units in T7 before comparing candidate outcomes. Verify edge cases with hand-calculated fixtures. Fix a unit/accounting defect if discovered and rescore all affected policies from logs; invalidate derived comparisons consistently rather than keeping favourable old scores.

The main coefficients are not tuned to make a policy win. Before final testing, rescore validation logs using one-at-a-time factors of 0.5 and 2 for stall, variation and latency weights; report whether the ordering is fragile. The original CMAB's internal reward is an additional diagnostic, not the shared headline metric.

Default validation selection:
1. Valid integration and useful playback.
2. Highest equal-family mean common QoE, subject to mean stalls not worsening by more than max(0.5 seconds per 120-second session, 10% of B0), p95 live delay not worsening by more than 0.5 seconds, and mean startup not worsening by more than 1 second.
3. Within measurement noise, prefer the simpler controller and lower variability.

These margins are initial engineering choices, not course requirements. They may be revised once using metric fixtures/reference variability before candidate search; record the reason and freeze them. Report physical tradeoffs even when the scalar/guardrails pass. Do not choose margins after viewing held-out results.

### Data and final workload

Reuse existing train/validation/test source boundaries and 60-second guards. Never change memberships to favour a result. Add versioned workload manifests rather than replacing Phase A manifests.

Default final controlled workload: **10 sealed 120-second scenarios: two per mandatory family**. Prefer one derived from the existing Seychelles test block and one from the previously reserved Victoria RTT session per family. Treat the entire Victoria session as final-only if it has not already been used for performance-based decisions; audit its history first. If it has been used, reserve another disjoint source/block and disclose that weaker independence. Inspect metadata/integrity without viewing policy scores. These are measured-RTT plus synthetic-capacity cases, not ten independent real Starlink recordings.

For new 120-second recipes, place interruptions early enough to observe full recovery before the end, e.g. development recipe around 30 seconds and final recipe in a predeclared 35-60-second range, not at 105 seconds with recovery clipped by the horizon. Keep final parameters/seeds separate from development. Do not truncate an existing 180-second scenario and silently change its meaning.

Include at least one capacity-limited and one easy ordinary condition; do not choose only conditions that make original startup fail. RTT variation, outage severity and recovery rate must be declared before final policy runs. Ground-truth profile labels/future values remain evaluator-only.

Create a separate sealed reserve cohort before any final performance inspection, with disjoint source windows/parameter seeds where available. This allows one legitimate validation-refinement cycle followed by a fresh comparison if necessary and time permits. Its role and weaker source independence, if applicable, must be explicit. Do not generate a favourable replacement test after seeing the original failures.

Add a supplementary original-paper-replay comparison of B0 versus C*: 3 repetitions each, 180 seconds, same raw-trace phase and shared original replay convention. Original nonpositive-RTT-to-outage and background loss are labelled emulation choices, not proof of measured full-path outages.

## 5. Phase B: trustworthy measurement and a usable workbench

### Step 8 - Revalidate the host and audit original CMAB
**Status:** Complete. **Owner:** Anjan; Rajat/Deviprasad support only when actual access is needed. **Deliverables:** D1, C1, C10, F2.

**Objective / intuition:** make sure we are improving the real reference controller rather than an outdated build or an assumed algorithm.

**Actions:**
1. Inspect parent/submodule branches, dirty files, recorded commits, existing Python environments, Docker/WSL readiness, space and current image identity. Preserve all completed assets; do not reinstall/reclone unless necessary.
2. Capture the exact original CMAB source/config/hash separately from new variants. Reconcile the paper with CMABRule, CMABAbrController, the sample page, existing event logging, sidecar and rule-selection/catch-up path.
3. Trace context/scaler, LinTS fitting/selection, reset boundaries, K-1 forced choices, reward time, stall attribution and exceptions. Audit the pinned MABWiser 2.7.0 RNG: determine whether recreating the MAB also repeats its default seed/draw pattern. Do not assume repeated trials imply distinct exploration.
4. Reuse the existing node/lifecycle/link checks where applicable and run a short real B0 control. Identify actual dependency readiness, request progression and database evidence.
5. Start the source-backed audit/hypothesis ledger, naming source evidence, measurement required and expected adverse case for H1-H6.

**Verification / exit:** intended build plays real media; configured link is independently checked; source-backed decision/update trace explains a B0 example; no silent baseline modification. Store readiness failures separately from policy failures. A serious infrastructure issue is diagnosed before evaluating new policies.

### Step 9 - Implement common event attribution, metrics and observation freshness
**Status:** Complete. **Dependency:** 8. **Deliverables:** D1, D5, D7, C2/C6/C10, T7/T8.

**Objective / intuition:** trustworthy rewards and comparisons require knowing what actually played and which action caused which request.

**Actions:**
1. Extend passive logging common to all policies. Join decision, request start/completion, representation, media interval, rendered quality and playback events using stable request/segment/epoch IDs; do not attach a completion to whichever decision is merely newest.
2. Register startup/waiting/playing/seeking/error events before load. Record lightweight timestamped playback/buffer/latency observations at a sufficient interval (initial target 100-250 ms for playback accounting), and download/probe data with actual timestamps. Avoid ever-growing full snapshots each poll; export compact events.
3. Handle startup, audio versus video stall, duplicate callbacks, init segments, retries, cancellation, seeks, final partial intervals and run cutoff. A rendered-quality event plus actual media advancement establishes played quality; requested quality alone does not.
4. Expose RTT timestamp/validity/failure through a minimal new endpoint or logged sidecar record; keep the existing scalar endpoint's original-CMAB semantics intact. Provide causal missingness/age for new policies. Use browser memory or a simple synchronous read where needed; no MongoDB read or asynchronous inference bridge. Compose currently uses a prebuilt statistics-server image: if app.py changes, build/select the local stats-server/Dockerfile through an explicit override and verify the served build, rather than assuming source edits are active.
5. Implement shared offline Q/B/S/V/A metrics and per-run exports. Give every policy the same observer, and test that passive instrumentation does not materially alter B0's choices/behaviour beyond normal variability.
6. Populate the report skeleton and machine-readable artifact index with definitions now; fill results only when produced.

**Verification / exit:** hand-calculated fixtures pass; known stalls/seeks cannot be double counted; selected/requested/played distinctions are demonstrable; unresolved associations are visible, not assigned invented reward. New feature values have known units/age. Original B0 behaviour is preserved.

### Step 10 - Implement repeatable scenario replay and freeze the development protocol
**Status:** Complete. **Dependencies:** 8-9. **Deliverables:** D6/D7, C3/C6, T2/T3.

**Objective / intuition:** every policy should face the same changing network, with enough observation time to explain recovery.

**Actions:**
1. Extend the current bandwidth-step runner to scheduled capacity, outgoing delay, loss/outage and recovery profiles inside the shaper container. Preload schedules and record actual applied times/state; do not let slow browser polling delay profile changes.
2. The existing shaper rejects zero rate. Represent a complete controlled outage with 100% loss and a valid positive rate, then restore the configured state. Verify actual packet behaviour and avoid double-counting one-direction delay as two RTT additions.
3. Restart/reset replay offsets per trial; match playback/source/wall-clock phase. Existing 60-second source looping and B0's slot schedule require explicit actual-start timestamps/tolerances.
4. Audit source/split/media manifests; keep validation for design choices and test sealed. Limit new external acquisition to a small easily retrievable subset; no large download prerequisite. Reserve/test the LENS session role before performance use.
5. Create 90-second development cases for fast diagnostics and six validation cases (five families plus mixed), with distinct source windows/parameters. Build the sealed final 120-second recipes specified above. Keep measured/synthetic and independence labels.
6. Benchmark a few real trial cycles including ready/load/phase wait/flush/teardown. Freeze metric definitions, initial guardrails, readiness policy and selection rules. Record matrix runtime forecasts from measured cycles.

**Verification / exit:** independent checks confirm capacity/delay/outage/recovery; repeat B0 on matching development cases and explain variability; complete profile has time for recovery; workload hashes and split checks pass. The runner preserves failed sessions and can resume completed keys without rerunning them.

## 6. Phase C: primary CMAB hypothesis experiments

Candidate configuration budget: initially at most 12 named CMAB settings and 72 development/validation/ablation browser trials of about 90 seconds each. This is a bounded search budget, not a target to exhaust. Reserve coverage for the major hypotheses and confirmations. Reuse a reference run only if all workload/build/protocol identities match.

### Step 11 - Isolate memory/reset and startup effects
**Status:** Complete. **Dependency:** 10. **Deliverables:** D2/D3, C1, F2/F6, T1/T5.

**Objective / intuition:** test the two strongest source-backed limitations before changing the reward or model family.

**Actions:**
1. Implement separately selectable experimental CMAB settings around the original synchronous LinTS route. Retain original features/reward for this step.
2. Compare original reset+forced startup, memory-only, startup-only and their combination on steady, capacity-drop and interruption development cases.
3. Separate history retention from forced-choice scheduling with explicit counters where feasible: retaining data must not silently be credited for an unreported startup-policy change. If they remain coupled in an implementation, label the treatment as a reset/restart package and do not claim an isolated memory effect.
4. Start with a bounded rolling history (for example 30-60 seconds) and conservative data-dependent startup. Avoid forcing seven maximum-rate downloads on every slot. Keep safe exploration observable; do not replace all learning with a hidden throughput rule.
5. Measure learned-decision fraction, history coverage, stalls, switches, quality and recovery. Test the adverse case where long memory delays adaptation.

**Verification / exit:** each treatment's actual mechanism is logged; actions remain valid; source-state changes match the named hypothesis; a provisional result is supported by paired development runs. Retain both favourable and unfavourable outcomes. Use no test scores.

### Step 12 - Test reward timing and outcome-based feedback
**Status:** Complete. **Dependency:** 11. **Deliverables:** D2/D3, C1/C2, F2/F6, T5.

**Objective / intuition:** teach the bandit from the action's consequences instead of giving a new choice credit for conditions observed before it was requested.

**Actions:**
1. Keep a pending-feedback record containing the original observation, action and stable request/media identity. Mature updates when the corresponding outcome is known; never update an old action using the newest context.
2. First compare feedback timing/attribution with the reward form otherwise held fixed where meaningful. Then test the common played-quality/stall/switch/excess-delay reward against the original proxy, separately labelled.
3. For played-outcome feedback, credit only played media, switching at its played boundary and stalls only when the responsible blocking segment is identified. Account for session-level/unattributable effects separately; do not arbitrarily charge the current bitrate. Handle cancellation, seeks, censored end-of-run outcomes and delayed updates explicitly.
4. Log attribution coverage/residuals. Test two simple scripted outcomes by hand, then steady/change and outage cases. Full session QoE remains independently computed even if the online learner uses a simpler defensible incremental target.
5. If exact played-outcome attribution is not robust, retain a tested timing-only variant or defer the complex target. Record why; do not ship fabricated action labels merely to claim H3 was implemented.

**Verification / exit:** synthetic known-outcome fixtures and real linked requests agree; no duplicate updates/quality credit for unplayed media; attribution ambiguity is reported. Adopt a reward change only on validation benefit and correct accounting, not because it produces larger internal numbers.

### Step 13 - Test context, estimator/exploration and stability changes
**Status:** Running. **Dependency:** 12. **Deliverables:** D2/D3/D5, C1, F6, T1/T5.

**Objective / intuition:** determine whether extra information or better estimation helps beyond the reset/startup changes.

**Actions:**
1. Add buffer and actual live delay first, then a small RTT-history/freshness/disruption feature group if logging supports it. No future profile values, trace identity or ground-truth outage labels enter inference.
2. Use consistent normalization and a bounded history. Online partial_fit is appropriate only with stable feature coordinates; do not keep accumulated model statistics while silently changing their scaler. Rolling-window refit is an acceptable simple alternative.
3. Audit/test the MABWiser 2.7.0 API before using incremental updates. Verify unseen-arm handling and persistent RNG behaviour, rather than assuming the newest documentation exactly matches the installed wheel.
4. Test a small exploration/regularization alternative if diagnostics show unstable or excessive exploration. Keep changes isolated from the context comparison.
5. If traces show harmful switching/recovery, test a modest buffer-aware action guard or switching margin. Count overrides and compare the guard alone against the simple rule so a heuristic improvement is not misattributed to LinTS.
6. Use a shifted/reset-phase or stale-RTT development case to expose brittle clock dependence or unavailable features. Keep every extra setting within the configuration/trial budget.

**Verification / exit:** causally available inputs, finite updates, bounded memory and correct scaling; validation metrics show which mechanism helped/hurt. Do not promote unnecessary complexity or infer handover ground truth from probe loss.

### Step 14 - Combine, ablate and select the primary candidate
**Status:** Pending. **Dependency:** 13. **Deliverables:** D2/D3/D8, F6, T1/T5.

**Objective / intuition:** obtain a strong controller whose gain can be explained by a few tested mechanisms.

**Actions:**
1. Combine only the most useful changes; compare original B0, accepted isolated versions, the combination and removals of its main contributions.
2. Confirm the top two candidates on the six validation cases, including ordinary conditions and adverse recovery. Use fresh repeats for a promising result rather than selecting the single best-looking run.
3. Select C* with the common QoE/guardrail rule. Record parameters, changed components, runtime cost and known losses.
4. If no candidate improves validation, diagnose the dominant failure and use a limited refinement cycle within the available budget: inspect requests/accounting/state coverage first, then adjust one mechanism. Do not keep adding unrelated algorithms.
5. Freeze a provisional primary candidate for the later common test; continue only with documented validation evidence if a subsequent integration/calibration defect invalidates it.

**Verification / exit:** F6/T5 can already be generated from saved validation results; C* is reproducibly selectable; original CMAB is preserved. A positive development outcome is not yet a final-test improvement claim.

## 7. Phase D: trained neural comparison with measured compute use

### Step 15 - Calibrate the fast environment and benchmark CPU/GPU
**Status:** Pending. **Dependencies:** 10 and 14. **Deliverables:** D4/D6, C2/C4, F8.

**Objective / intuition:** train quickly in an environment that captures the browser effects relevant to bitrate decisions.

**Actions:**
1. Extend the existing environment rather than reimplementing a general network simulator. Match actual encoded bytes, source availability, playback/live clocks, buffer, stalls, target/catch-up/seek/discard logic, elapsed-time rewards and observation ages.
2. Add causal RTT/probe validity/disruption estimates to simulated observations with the same semantics as the deployed collector. The evaluator may know future profiles; the policy/critic must not.
3. Verify constant-rate transfer, a capacity change mid-download, full outage/recovery, startup, reset, seek and episode cutoff. Model measured goodput versus configured capacity distinctly; avoid charging latency/loss twice.
   Distinguish time-limit truncation from true terminal failure in Gymnasium/SB3 return bootstrapping and test reset/rollout boundaries; otherwise the critic can learn incorrect values despite plausible playback.
4. Compare fixed-low/mid/high and one adaptive policy with Chrome on a small development calibration set. Initial acceptance targets: median segment-time relative error about 20% or less outside near-zero durations, buffer/live-delay MAE about 1 second or less and correct qualitative stall/recovery behaviour. Set or refine tolerances using repeated reference variability before fitting.
5. Repair material mismatch, then recheck. If TCP/chunk details cannot be represented cheaply, quantify the limitation and use the environment for candidate training/screening while relying on browser outcomes for final claims. Do not label a failed calibration as passed.
6. Benchmark end-to-end training with representative batches on working CPU and RTX 4060, recording environment steps/s, optimizer throughput, validation overhead and memory. Keep the CPU environment intact while establishing CUDA if necessary. Use the faster feasible configuration; reallocate saved time to stronger training/evidence.

**Verification / exit:** conservation/edge-case checks pass; F8 quantifies discrepancies; runtime forecast uses measured steps/s rather than an assumed 18-hour training estimate. Stop a severe dynamics bug before interpreting training gains.

### Step 16 - Train compatible conventional and LEO-aware candidates
**Status:** Pending. **Dependency:** 15. **Deliverables:** D4, C4/C5, F7.

**Objective / intuition:** establish genuine useful learning, then test whether LEO observations help under a controlled trainer/data comparison.

**Actions:**
1. Reuse the 36-input conventional interface and compact two-layer actor initially; add a versioned LEO feature manifest for RTT history with validity/age, actual live-delay context and recent causal interruption/recovery estimates. Derive the feature count from the checked interface rather than calling the old 36-input pilot LEO-aware.
2. Start with SB3 A2C, preserving the Gelato/Plume provenance and explaining our compatible adaptation. Use balanced scenario-family sampling for both observation variants; label it Plume-inspired rather than claiming the full original clustering framework.
3. Do not silently truncate ten released actions to eight or invent native future SSIM metadata. Reuse weights only where shapes and meanings are genuinely compatible; otherwise retrain the adapted actor. Preserve the faithful reference export separately.
4. Default screening budget: up to 4 justified trainer/sampler settings x 2 pilot seeds x 2 observation variants x 250,000 decisions, about 4 million interactions. Compare common validation QoE and physical metrics, not just each run's training reward.
5. Check gradients/weight changes, value/reward scales, action distribution, actual buffer/stall outcomes and easy-case competence. Compare fixed policies and teacher/pre-RL performance; a policy need not use every action to be valid.
6. If random starts collapse, use one documented training-only imitation initialization from a causal teacher and compare before/after RL. Never treat logged MongoDB choices as optimal labels.
7. If two diagnosed A2C refinement attempts remain unproductive, allow one bounded PPO or architecture pilot, changing only that factor under the same state/reward/data. A larger temporal model is justified by a demonstrated limitation, not by GPU availability alone.
8. Select one common final training recipe where possible for the conventional/LEO comparison. Allow model-specific tuning only if it is reported and does not masquerade as a pure feature ablation.

**Verification / exit:** saved validation curves, learning checks and compatible candidate weights; failed/collapsed runs retained; no sealed-test selection. Fix data/reward/dynamics/normalization defects before declaring that the optimizer itself is the problem.

### Step 17 - Repeat training, select representatives and verify deployment
**Status:** Pending. **Dependency:** 16. **Deliverables:** D4/D5, C4/C5, F7, T8.

**Objective / intuition:** demonstrate that the neural result is reproducible and executable in the actual player.

**Actions:**
1. Default main budget: 5 fresh seeds per conventional/LEO variant, initially 1 million decisions each (10 million total). Save/resume optimizer/RNG/config/split identities and validation curves. Checkpoint periodically, e.g. every 100,000 decisions, with affordable full validation.
2. Extend up to 3 million decisions per seed or add a focused sampler/architecture ablation if validation is still improving and measured runtime fits the reserved deadline. Use learning evidence and remaining time, not a predetermined long wait. Do not stop for low training return alone when common validation QoE is improving.
3. Select checkpoints by the predeclared validation rule. For the main browser matrix, use the median-validation-quality seed's selected checkpoint from each variant rather than choosing a lucky seed on test results. Preserve all five seeds for simulated held-out reporting.
4. Export the actor to the existing synchronous JavaScript route with identical preprocessing, action ordering, supported operators and model identity. Recheck any architecture/operator change.
5. Run numerical fixtures including recorded real inputs and missing/stale/extreme cases, then verify actual Chrome decisions against native inference. Verify no invalid actions, real requests/played quality, reset/fallback behaviour and decision timing.
6. Run short validation browser comparisons. If deployment exposes a material discrepancy, diagnose/export-fix/reverify; retrain only if the observation or dynamics semantics actually changed.

**Verification / exit:** N-CONV/N-LEO are actual trained deployable policies; five-seed learning/validation evidence exists, subject to explicitly recorded compute-driven deviations; representative seed selection is traceable. A learning curve or parity pass alone does not prove better QoE than B0.

## 8. Phase E: frozen common testing and analysis

### Step 18 - Lock the protocol and run the final browser matrix
**Status:** Pending. **Dependencies:** 14 and 17. **Deliverables:** D7/D8, C6/C10, F3/F4/F5, T3/T4.

**Objective / intuition:** measure the finished controllers under matched conditions without using final results to redesign them.

**Actions:**
1. Freeze policy/config/model/source/workload hashes, metric/guardrail definitions, seed/checkpoint rule, scenario weights, repetitions, run order, representative-trajectory rule and uncertainty method before opening test performance.
2. Default core controlled matrix: 10 scenarios x 6 policies x 2 repeats = 120 browser trials. Add a third repeat for B0 and C* on all 10 cases = 20 more. Add B0/C* original-paper replay with 3 repeats each = 6 trials. **Total default: 146 browser trials.**
3. Controlled playback time is 140 x 120 seconds plus 6 x 180 seconds = **4 hours 58 minutes**, before initialization, phase waiting, flush and teardown. With approximately 180-second controlled cycles and 240-second supplementary cycles, a planning allowance is about **7 hours 24 minutes**. Replace this with the Step 10 measured forecast; it is not an unconditional promise.
4. Before unsealing, activate predeclared extensions only if runtime and remaining report/release reserve permit: add the remaining policies' third repeats (40 trials); a second validation-selected neural seed on a small fixed browser subset; mixed/phase-shift stress cases. Do not decide repetition count from whether a p-value or curve looks favourable.
5. Run paired workloads in balanced/randomized policy order with isolated controller state, matched source/trace phase and the same dependency readiness. Original B0 preserves its own online adaptation. Record actual phase/schedule deviations and classify infrastructure faults separately.
6. Every finalized run exports enough compact events/metrics to reproduce results without the live database. Check completed requests, actual played coverage, measurement integrity and failure/censoring status before marking a run complete. A policy causing no playback remains an outcome.
7. Evaluate all five neural seeds on the sealed simulator suite after selection; the main browser result uses the declared representative seed. Clearly separate training-seed variation from browser-repeat variation.
8. Resume from valid completed run keys. Retry a diagnosed infrastructure failure with the reason retained; do not silently replace algorithmic failures.

**Verification / exit:** complete frozen-matrix inventory or an explicitly disclosed incomplete portion; all scored runs have identities/logs/valid metrics; correct counts and phase/schedule checks. No new tuning uses this test suite.

**Negative outcome rule:** if final C* does not beat B0, preserve it and use a focused diagnosis/validation refinement if budget permits. Activate the previously sealed reserve cohort for one new B0-versus-revised-C* comparison (initial budget: 5 families x 2 cases x 2 policies x 3 repeats = 60 controlled trials). Both initial and reserve outcomes remain reported; do not combine an inspected development result with a new holdout and call everything untouched. Recompute the runtime before this extension and protect the release gate. If no legitimate fresh evaluation fits, do not manufacture a win or hide the result. Escalate only if a material change to the project's final direction is needed.

### Step 19 - Analyse effects, uncertainty and mechanisms; generate results
**Status:** Pending. **Dependency:** 18. **Deliverables:** D8, C7, F1-F8 and T1-T8 as applicable.

**Objective / intuition:** explain the size, reliability and cause of gains, including where the policy loses.

**Actions:**
1. Generate per-run metrics and paired differences using equal weights for the five required families and equal case weights within each. Keep supplementary paper-replay outcomes separate.
2. Report absolute values, paired QoE effect, per-family stalls/delay, startup, switching and played bitrate. Include raw paired points and 95% intervals where replication supports them.
3. Treat scenarios/recordings and repeated sessions correctly: never count video segments or related windows as independent experiments. With only two measured RTT sessions and synthetic capacity, intervals describe repeatability on fixed tested workloads, not population-wide Starlink generalization. State the limitations of 2/3 repeats; show ranges/raw data rather than unjustifiably precise significance.
4. Generate the hypothesis/ablation table from validation evidence and the final performance tables from sealed testing; label those sources. Plot selected trajectories using the frozen rule and include at least one informative failure/regression.
5. Rescore the frozen sensitivity coefficients from existing logs; no extra learning or test-driven coefficient selection. Check whether apparent gains are simply lower quality, more skipped media or hidden startup.
6. Verify all figures/tables resolve to source run IDs and calculations. Inspect axes, units, legends, uncertainty, missing runs and component-score sums. Generate PDF/SVG or readable PNG exports and report-ready tables.

**Verification / exit:** F3-F7/T4-T5 answer what improved, where, why and with what tradeoffs; F2/F8/T7/T8 support the mechanism and method. No curve is a manually entered final number and no unsupported improvement wording appears.

## 9. Phase F: report, demo and submission release

### Step 20 - Finish the concise evidence-backed report
**Status:** Pending. **Dependency:** 19; skeleton started in 9. **Deliverables:** final report PDF, D1-D8 synthesis, T6.

**Objective / intuition:** turn the tested work into a clear networks-course argument rather than an implementation diary.

**Actions:**
1. Write the sections specified in deliverables.md: team/abstract; problem and related work; CMAB audit and hypotheses; selected CMAB; neural adaptation/training; controlled methodology; results/mechanisms; limitations/conclusion; reproduction/references.
2. Use the six most useful main-result/system figures and compact policy/data/results/ablation/contribution tables. Put long settings, detailed audit/calibration and deployment evidence in an appendix/repository. Do not invent a page limit; keep the prose concise.
3. Every result claim cites its actual figure/table, experiment scope and uncertainty. Label measured versus generated channels, unchanged reference versus our modifications, and the compatible neural adaptation versus published weights.
4. Include all names/roll numbers and 2-3 sentences of actual work per member. Use verifiable contributions and seek factual clarification if needed; do not infer that a person did work merely from their initial assigned role.
5. Include the accessible GitHub link and exact release/workspace identity; update it after any authorized publication. Give saved-results, demo, evaluation and training reproduction commands with measured hardware/time expectations.
6. Compile, extract text and render the final PDF; inspect every page and all cross-references. Verify the requirements image's five report items and the proposal's mandatory coverage.

**Verification / exit:** readable concise PDF, correct contributions/references, complete graphs/tables, source-backed numbers and no placeholders/mid-review claims presented as final results. Source and report remain reproducible.

### Step 21 - Prepare the working demo and submission presentation assets
**Status:** Pending. **Dependencies:** 17-20. **Deliverables:** C8, demo commands/recording, final-results deck draft.

**Objective / intuition:** show real controlled streaming behaviour and make the project presentable without depending on a fragile live experiment.

**Actions:**
1. Build/select the final local-source image with all relevant policy assets; keep original CMAB and neural options selectable. Ensure scripts/prepare_player.py and packaging do not require the historical Phase A patch to match every later source edit.
2. Provide a short, named bandwidth-change/interruption/recovery demo with actual video, policy identity, selected/played bitrate and buffer/live delay; use the same settings for B0 and C*. Save logs and a comparison plot.
3. Record a short real run as a fallback, plus launcher/readiness/reset instructions. Do not replace the working policy with a scripted action sequence or an animation.
4. Create a concise final deck reusing the verified report figures: objective/system, CMAB mechanism/change, neural comparison, experiment, gains/tradeoffs, ablations and conclusions/contributions. Keep the exact duration/page count adjustable because presentation rules have not been supplied.
5. Perform the executable demo and slide visual/factual checks now. Actual team speaking/rehearsal is a human activity; provide the rehearsal checklist rather than falsely marking it complete.

**Verification / exit:** real advancing playback and linked media requests; demo can be restarted safely; recording and slides agree with submitted results. Full worker/runtime comparison is not introduced.

### Step 22 - Verify clean reproduction and assemble the submission
**Status:** Pending. **Dependencies:** 20-21. **Deliverables:** C9/C10, final ZIP, release manifest, GitHub publication readiness.

**Objective / intuition:** someone else should be able to inspect the evidence, reproduce plots and run the demonstrated source.

**Actions:**
1. Provide distinct documented commands for prerequisites, data preparation, training, evaluation, plots-from-saved-results and demo. Reuse scripts/testbed.sh and the established build/requirements where possible.
2. Allowlist the final report/deck, developed code, actual modified player source, model/controller assets, configurations, compact evidence, tables/figures, licenses and artifact index. Exclude environments, caches, personal credentials and duplicate huge/raw data.
3. Audit .gitignore: artifacts/runs, figures, processed/raw data, checkpoint folders and most PNGs are ignored. Required results/plots must be intentionally included in the release and, when authorized, in the published artifact set. A local ignored file is not available to teammates.
4. A normal GitHub parent ZIP does not include submodule contents. Bundle the exact required player source or a complete versioned patch+base/recreation route, and verify the resulting source hashes. Preserve the historical Phase A patch separately.
5. Since no commits are implicit, identify uncommitted parent and submodule edits in the release manifest using source/file hashes and a reproducible patch/snapshot. Do not claim an old committed SHA fully identifies new workspace contents.
6. When the exact tested code/results/report publication set is reviewable, use the already granted commit/push authorization, publish verified child commits before the parent, and verify fresh remote retrieval. Do not ask again for the authorization already granted.
7. Extract the ZIP outside the project. Regenerate final metrics/figures from its included exports, inspect generated figures/PDFs, verify model/action/normalization assets and check demo build/source preparation. Test accessible submodule commits/retrieval separately; no hidden dependency on an unpublished local commit or MongoDB volume.
8. Compute the final ZIP/report/source/result hashes, check internal links/references and generate a concise submission checklist. Confirm the report links to the intended accessible GitHub state. Prepare the upload-ready package before 07:00; actual portal upload is separate if access/authorization is required.

**Verification / exit:** extracted package reproduces saved-results analysis; exact demo source/model is recoverable; report, code, results and manifest identities agree. Missing remote publication or portal submission is explicitly outstanding rather than falsely marked submitted. A successful ZIP command alone is insufficient.

## 10. Phase G: presentation/demo readiness after submission

### Step 23 - Final presentation polish and rehearsal preparation
**Status:** Pending; human rehearsal outstanding. **Dependencies:** immutable submission package. **Deadline:** ready by 19 November evening; presentation 20 November 11:00.

**Objective / intuition:** explain the verified contribution clearly and recover gracefully if the live testbed fails.

**Actions:**
1. Preserve the submitted ZIP/report/evidence unchanged. Refine slides and speaker notes around their exact results; mark any later correction/update explicitly.
2. Confirm the course's presentation duration/format if supplied, then trim the deck and assign speakers using the existing domain split: Rajat integration/builds, Anjan algorithms/training, Deviprasad experiments/QoE.
3. Prepare short answers for reward attribution, reset/memory evidence, data independence, neural adaptation, test leakage, ablations, negative outcomes and reproduction.
4. Run a final demo/readiness check and keep the recorded fallback locally available. Give the team concise start/reset/troubleshooting commands and a timed rehearsal checklist.
5. Human members rehearse and confirm their contribution statements. Do not autonomously send group messages or schedule follow-up jobs unless explicitly requested.

**Verification / exit:** slides/video/demo agree with the frozen submission; the team has a clear speaking/demo plan. Human rehearsal is not claimed complete by a script. Most assets are prepared during Step 21; this step is not permission to spend the remaining submission window polishing slides instead of finishing the report.

## 11. Stop, escalation and scope rules

- A broken test initiates the diagnosis/fix/verify loop; it does not require a design meeting.
- A hypothesis not helping is a result. Refine within validation budgets or reject/defer it with evidence.
- A calibration limitation is reported honestly. Do not silently replace real browser comparison with simulator-only claims.
- If all good candidates lose on final test, retain the result and apply Step 18's fresh-test rule. Ask only if a consequential project-direction change becomes necessary; do not use repeated test tuning as autonomous persistence.
- Freeze final experiment additions when remaining time threatens the report/clean-release checks. Extra training uses measured spare capacity, not the upload margin.
- Public portal uploads, protected access, paid resources and unavailable required human facts are genuine authorization/input boundaries; commit/push approval is already granted for this run. Prepare the concrete work before asking.
- Do not promise that a future test must yield a win. The objective is a better controller; the scientific obligation is accurate evidence, including limitations and failures.

## 12. Active progress tracker

Autonomous execution is active; see the per-step tracker and artifacts/final/state.json. Phase A evidence is reused, not re-executed. Fill exact evidence/status/deviation links during the authorized run.

| Step | Status | Next verification gate / main output |
|---|---|---|
| 8 | Complete | artifacts/final/reference-audit.json; artifacts/final/link-verification.json; real CMAB control phasea-abrCMAB-20261116T214650-ee42c4 |
| 9 | Complete | Played-quality ledger and fixtures pass; typed RTT Flask checks pass; passive-source equality verified; observer-checks/phasea-abrCMAB-20261116T220201-450cb8.json |
| 10 | Complete | Verified 86 live schedule transitions within 14ms; physical outage/100ms RTT/recovery passed; six development/six validation/ten test/ten sealed reserve cases; raw offset replay checked |
| 11 | Complete | 12 paired development sessions complete; startup improves all three cases, retained memory alone does not; paired-results.json preserves every outcome |
| 12 | Complete | 9 browser sessions; six request-identity checks pass; explicit download surrogate improves all three development cases; original delayed proxy mixed; completion-censoring limitation disclosed |
| 13 | Running | Test physical normalization/intercept, causal context and action guard; correct shared CMAB dependency prewarm before validation |
| 14 | Pending | Validation-selected C*, F6/T5 |
| 15 | Pending | Quantified environment calibration and CPU/RTX benchmark, F8 |
| 16 | Pending | Compatible conventional/LEO training candidates |
| 17 | Pending | Repeated training, representative checkpoints, real-browser export checks |
| 18 | Pending | Frozen final matrix and complete run inventory |
| 19 | Pending | Verified common results, figures/tables and claim boundaries |
| 20 | Pending | Reviewed final report PDF and contributions |
| 21 | Pending | Working demo, recording and report-consistent slide draft |
| 22 | Pending | Extracted/reproduced release ZIP and publication/submission status |
| 23 | Pending | Presentation/demo polish and human rehearsal checklist |

### Method references used for this revision

- Source of truth for CMAB behaviour: pinned CMABAbrController.js/CMABRule.js and the local Zhao/Pan reference paper. Inspect the installed 2.7.0 wheel before relying on newer API details.
- [MABWiser public API](https://fidelity.github.io/mabwiser/api.html): fit/partial_fit, arm handling and linear policies.
- [Gelato/Plume training source](https://github.com/sagar-pa/plume/blob/main/puffer_abr/puffer_abr_training/train.py): actor-critic training and workload sampling; adapt without importing the full Puffer/Ray system.
- [Stable-Baselines3 A2C guidance](https://stable-baselines3.readthedocs.io/en/master/modules/a2c.html): CPU/vectorized execution can outperform GPU for small non-CNN policies; measure actual throughput.
- [SB3 RL development/evaluation guidance](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html): custom-environment checks, normalization, repeated runs and separate evaluation.
