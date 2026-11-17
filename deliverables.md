# Final-project deliverables: CMAB improvement and neural comparison

Prepared: 17 November 2026. Group 4, CS6048.

This is the deliverables specification requested in planning Step 1. It defines what we must produce and what evidence makes each item complete. The Step 2 phase-by-phase execution plan is now in [roadmap.md](roadmap.md), with the 18 November 08:00 submission deadline, 20 November presentation/demo and RTX 4060 compute context incorporated. Planning does not authorize implementation or commits.


## Submission/presentation separation (revision:18 November2026)

Submission execution is complete through Step22: eight-page report, balanced four-policy analysis, evaluator README and checked75.53MB focused ZIP. All179 final sessions reproduce from raw evidence; all835 curated source inputs were retrieved from published Git. Contribution details remain deliberately blank. The user handles portal upload; Step23 is deferred.

This revision and roadmap Steps20-23 supersede older combined hand-in wording below. Steps8-19 are completed evidence; no new training or browser experiment campaign is planned.

- Main scientific story: compare original CMAB, improved CMAB, conventional A2C and LEO-aware A2C together. Main table/figures use the common two repeats across ten cases (80 sessions). Preserve the third CMAB repeats, guard-only/native baselines, ablations and9 raw replays as explicitly labelled support. Raw replay has no A2C comparison; do not imply otherwise. Add direct matched pair contrasts and disclose small-repeat/fixed-case uncertainty.
- Submission run: Step20 balanced analysis and dependency/file inventory; Step21 report/evaluator-facing GitHub handoff; Step22 focused ZIP, clean reproduction and publication. Presentation, demo execution/video, learning guides and rehearsal are excluded from this run and ZIP.
- Step23 covers PPT/demo/learning/rehearsal only after18November08:00IST and a new user instruction. Existing prepared sources are reusable drafts, not authorization to generate them now.
- Keep the existing repository/submodules/required paths. GitHub retains the complete research record with clear final entry points and historical/support labels; the ZIP is a curated release, not a copy of the development tree. No new repository or history rewrite is needed.
- Build the exact file list from imports, build paths and result dependencies. Include required player source, selected models/contracts, necessary modules/scripts/configurations/data, report figures/tables, compact evidence and licenses. Exclude duplicate logs/checkpoints, obsolete prototypes and unrelated upstream material unless a real dependency requires them. An old filename alone is not grounds for removal.
- Confirmed user inputs (18November): target a technical, concise6-8-page academic research-paper/LaTeX-style report; reserve an empty contribution template without filling specific work; no known ZIP restrictions; user handles portal upload.
- The prior instruction to keep contribution details blank remains valid until the user supplies actual statements. Do not invent them. Portal upload is a separate human handoff unless explicitly requested with access.

## 1. Objective, scope and submission obligations

**Primary objective:** develop and explain an ABR controller that improves on the reference repository's CMAB implementation under a common streaming system. Track 1 improves CMAB itself. Track 2 provides a trained, player-compatible Gelato/Plume-inspired actor-critic comparison, including LEO observations where usable.

The comparison must explain *why* a change helps or hurts, not merely show that a new policy runs. Keep the video, network workload, target delay, catch-up settings and shared infrastructure comparable across policies. A common traffic-shaper repair is infrastructure, not an algorithmic contribution.

Use the simplest working synchronous execution route: retain existing Pyodide for CMAB and the existing synchronous JavaScript export for compatible neural actors. Do not plan an asynchronous worker bridge, an ONNX/Pyodide/JS runtime competition, a new streaming service, congestion-control changes, or a large model zoo. A short decision-cost measurement is sufficient to establish deployment feasibility.

### What the submission image requires

| Requirement | Concrete submission evidence |
|---|---|
| Names and individual contributions | A report table identifying all three members, with 2-3 sentences of specific completed work per member. |
| Problem statement and related work | A concise report section establishing the exact CMAB reference, the LEO/live-streaming problem and the relevant bandit/RL alternatives. |
| Methodology | Exact policy changes, state/action/reward definitions, data provenance, experiment controls, training and selection procedure. |
| Results and analysis with figures/graphs | The main comparison, component metrics, scenario breakdowns, explanatory trajectories and ablations specified below. |
| Demo, if applicable | Deferred presentation work in Step23; no demo files/video or demo execution requirement for the submission ZIP. |
| ZIP containing report and developed code; GitHub with scripts and results; GitHub link in report | A checked release ZIP, accessible pinned repositories/submodules, model/configuration assets, compact results and reproduction commands. |

The original proposal also requires throughput, buffer-based and Pensieve-style baselines; a trained LEO-aware RL policy; five scenario families; six playback/QoE metrics; reproducible code; graphs; a presentation and a demonstration. The primary emphasis can move to CMAB improvement, but the neural deliverable remains part of the proposal. Describe the track split explicitly in the final report. The optional congestion-control extension stays excluded.

### Existing foundation to reuse

- Phase A has a verified local-source player build, shared shaper repair, archived-figure reproduction and fresh controller operation checks. Recheck the host and identities before new runs; do not redo the completed research or treat the old short checks as final evaluation.
- The custom rule, action/request logging and synchronous neural export are reusable. The original CMAB remains available as the primary control.
- The current neural pilot is a separately trained `36 -> 64 -> 64 -> 8` actor, not an unchanged released Gelato checkpoint. It has one-seed integration evidence, not a demonstrated QoE advantage.
- The data package has 48/18/18 generated train/validation/test scenarios, largely derived from one RTT recording with synthetic capacity/outages. A separate LENS RTT session is reserved. These counts are not independent measured sessions; the existing simulator needs calibration.
- The public dash.js fork and parent reference are already recorded. The mid-review material is now outside this repository in `../mid-review/`; it is historical supporting material, not the final report.

## 2. The claims we must be able to support

1. We understand the reference CMAB's actual implementation, including how observations, decisions, rewards, resets and playback outcomes are connected.
2. One or more targeted CMAB changes improve the common QoE outcome, with the contributing mechanisms supported by controlled comparisons.
3. A trained compatible neural policy provides a credible comparator under the same media/network conditions, with its adaptation from the reference method explained.
4. The selected deployed controller uses observations actually available at decision time, controls real video requests and remains operational during startup, missing data, interruption and recovery.
5. Another team can recreate the reported tables/figures and run the demo from the submitted code and documented dependencies.

Before final tests, define the selection rule and the acceptable tradeoffs. The intended success evidence is a positive paired QoE improvement over original CMAB with uncertainty reported, accompanied by acceptable stall/live-latency/startup behaviour and explicit per-family regressions. Phase 2 must choose numeric margins and repetition budgets on development evidence, before final-test inspection. Do not pick a favourable scoring formula or a winning checkpoint after seeing test results. Do not promise a percentage gain in advance.

Freeze a candidate's configuration before testing, while allowing each bandit to continue its intended online updates using its own past observations. Test data must remain unavailable for offline weight updates, tuning and winner selection. If results do not establish an advantage, retain and explain that outcome; changing the evidence standard to manufacture a win is not a completion criterion.

## 3. Track 1: the CMAB study and improved controller

### D1. Source-backed CMAB audit

**Artifact:** one concise technical specification with source paths/commit IDs, a decision/update timeline, and instrumented browser traces.

It must describe:

- The fitted three-feature context: throughput, playback rate and RTT/network latency. Live latency affects the reward but is absent from that context; buffer is also absent.
- The LinTS arm model, scaling/refitting behaviour, exploration parameter, action mapping and random-state behaviour.
- Fixed 15-second history resets and the initial highest-representation selections until `K-1` choices have been recorded. Measure how many decisions actually reach learned selection in a slot.
- The P.1203-derived reward, its selected-bitrate stall-share term and the timing of its calculation before the newly selected download completes.
- Actual stall attribution, audio/video events, quality switching, request deduplication, cancellation/retry/seek handling, and which assumptions could distort the learning feedback.
- RTT probe freshness and failure semantics. A repeated last-success value must not silently be interpreted as a fresh measurement.
- The difference between the paper's description, implementation behaviour and our hypotheses. P.1203 itself must not be blamed for limitations of the supplied single-segment/empty-stalling input.

**Completion evidence:** a worked example can be traced from input through chosen representation and reward to later request/playback outcomes. Observed limitations are distinguished from suspected causes. The unchanged control's behaviour remains reproducible.

### D2. Hypothesis and experiment ledger

**Artifact:** a small versioned ledger linking hypothesis -> source evidence -> isolated variant -> expected physical effect -> validation result -> accept/reject/refine decision -> run IDs.

The initial hypothesis families to investigate are:

| ID | Hypothesis to test, rather than assume | Candidate change and evidence needed |
|---|---|---|
| H1: memory | Clearing history each slot leaves too little useful experience and causes relearning. | Compare the original reset with rolling/discounted history or selective forgetting. Measure learned-decision fraction, switching, QoE and adaptation after a genuine shift. Long memory may also hurt; test that case. |
| H2: startup/restart | Repeated highest-bitrate initial choices cause avoidable buffer depletion and stalls. | Compare original startup with a measured-throughput/buffer-based initialization or limited safe exploration. Check cold start and post-interruption recovery without permanently suppressing quality. |
| H3: feedback | Scoring a choice before its realized outcome and using stall share weakens action credit. | Associate observations/actions with completed requests and played outcomes, then test explicit stall/switch/delay costs. Separate reward timing/attribution changes from reward-formula changes where feasible. |
| H4: context | Buffer, live delay, recent throughput/RTT trends or interruption evidence distinguish situations hidden by the current context. | Add a small set of causal, freshness-aware features and test removals. Feature access and missingness must be logged; no future outage labels. |
| H5: estimation/exploration | Tiny-slot scaling, refitting or exploration settings produce unstable action preferences. | Audit first, then test bounded normalization/regularization/exploration alternatives. Change one mechanism at a time before combinations. Retain an explicit exploration seed where supported. |
| H6: action stability | Unnecessary up/down changes and aggressive recovery damage playback without useful quality gain. | If traces support it, test a modest switching margin or buffer-aware action constraint. Report when a safety rule overrides the bandit and test whether it slows beneficial recovery. |

Do not implement every possible combination. The completion requirement is an evidence-backed investigation, isolated tests of the main mechanisms, and a justified final combination. The execution plan will prioritize and bound the search. Include unsuccessful changes, not only the winner. If a guard/heuristic helps, compare it alone so improvements are not incorrectly attributed to learning.

### D3. Versioned improved CMAB and integration

**Artifact:** a selectable controller, its settings and state/update definition, plus the minimal isolated variants needed for explanation. Prefer a sibling implementation or explicit policy labels over overwriting the original CMAB.

Include bounded history/reset behaviour, deterministic configuration/seed controls where available, fresh/missing observation handling, causal update logic, valid eight-representation mapping and reset semantics. Keep reusable measurement changes common; changes affecting original CMAB's decisions are a separate variant, not a silently repaired control.

**Completion evidence:** live observation -> decision -> requested representation -> playback links, checks for startup/seek/reset/stale inputs and finite rewards, and a reproduced validation result. Final superiority is established only through D8's browser comparison, not unit tests or simulated scores.

## 4. Track 2: a credible trained neural comparator

### D4. Compatible Gelato/Plume-inspired training package

**Artifacts:** calibrated environment, preprocessing/reward modules, a conventional actor-critic baseline, a LEO-aware variant, training configurations and logs.

- Record the exact reference source/license and distinguish Gelato's policy/training method from Plume's representative workload-sampling ideas.
- Reuse the compatible training/export foundation. Audit whether pretrained weights can actually be reused. The released reference has ten actions and future size/SSIM inputs unavailable in the current interface; changing inputs/outputs requires documented adaptation and retraining. If weights cannot be meaningfully reused, train the adapted policy from scratch and label it accurately.
- Provide one conventional-input policy and one using usable RTT history, live delay and causal interruption/recovery information. A matched retrained feature-removal variant can serve as the conventional baseline; it need not become another unrelated model project.
- Use the standard development sequence in the later plan: environment checks/calibration, useful simple-case learning, training-only preprocessing, validation-based tuning/checkpoint selection, repeated training seeds, held-out evaluation, deployment verification.
- Keep an optimizer/trainer reusable across observation designs. Start with the existing actor-critic route; add another optimizer/architecture only when a diagnosed failure justifies it. A small architecture search is not a deliverable by itself.
- Preserve native checkpoints, selected exports, optimizer/RNG state for resume, source/config/data identities and full training/validation histories. Teacher initialization, if used, must remain training-only and be reported separately from RL improvement.

**Completion evidence:** useful and reproducible learned behaviour, multiple training seeds, validation-selected checkpoints and a browser-compatible export. Report failed/collapsed runs and the existing pilot's limitations. The pilot is a starting asset, not the final trained result.

### D5. Deployment assets for both tracks

**Artifacts:** runtime-ready controller/model files; actor weights, normalization, action mapping and example I/O for the neural policy; one manifest per submitted policy; a player build/configuration selecting each policy.

Use synchronous Pyodide or JavaScript as appropriate. Verify native/browser outputs when porting a model. Record preload/cold-start behaviour, per-decision timing and fallback counts on the actual demo host; a full alternative-runtime study is excluded.

**Completion evidence:** real Chrome execution, correct requested/played representations, no unsupported synchronous return values and a recorded timeout/fallback policy where meaningful. A synchronous timer cannot preempt a blocked main-thread calculation; do not call a measured timing target a hard deadline guarantee.

## 5. Shared data, experiments and evaluation

### D6. Data and scenario release

**Artifacts:** provenance/source catalog, retrieval/preparation scripts, actual media-byte catalog, immutable split manifests, scenario configurations and integrity checks.

Include recording IDs, dates/locations where known, duration, units, gaps, hashes, licensing and measured-versus-generated labels. Obtain independent bandwidth/RTT sessions where feasible; if not available, keep claims limited to the tested synthetic-assisted workloads. Reassess the reserved LENS session's role before using it for calibration; it cannot simultaneously be untouched final test data.

Split by original session before window generation; when only a single recording is available, retain chronological guards and state that limitation. Keep all variants/derivatives of a source window together. Fit transforms only on training data. Do not equate the count of generated windows with independent real measurements.

Cover steady bandwidth, bandwidth variation, RTT variation, interruption and post-interruption recovery, plus a small mixed workload. Distinguish a controlled interruption from a proven satellite handover. Do not reinterpret probe loss as full-path outage without evidence. Audit actual segment sizes, source availability and looping rather than using nominal bitrate times duration as exact bytes.

**Completion evidence:** reproducible generation and source download/hash checks, no overlapping split derivatives, unit/range checks and an explicit independence/generalization statement.

### D7. Common experiment and metric package

**Artifacts:** policy adapters, experiment matrix/configurations, a shared measurement ledger, run manifests and automated checks.

**Mandatory comparisons:** original CMAB, final improved CMAB, throughput baseline, BOLA, conventional/Pensieve-style RL and LEO-aware neural policy. Reuse existing throughput/BOLA implementations. Add Dynamic/L2A-LL/LoL+ to final charts only if they answer an additional question; Phase A already established operation checks for them.

Use development cases for variants/tuning. Reserve held-out cases for the selected finalists and required baselines. Keep the same source/representations, target delay, catch-up, shared shaper, playback duration, player build and relevant host settings. Match trace offset and live-source/wall-clock phase, and balance run ordering. Original CMAB's reset schedule makes wall-clock alignment important. Keep policy histories isolated between sessions.

Collect at least:

- Time-weighted actually played bitrate/quality utility; played duration/coverage.
- Absolute video rebuffering duration and stall count, with startup separated and audio-only events labelled.
- Played-quality switch frequency and magnitude, rather than callback/action-count changes alone.
- Startup delay and its measurement boundary.
- Live-latency mean and tail, including how it is sampled during waits/stalls.
- One common offline QoE score with explicit quality, stall, variation and excess-latency units/coefficients, startup accounting and normalization horizon.
- Interruption recovery time, skipped media/discarded bytes and decision/fallback counts where they explain behaviour.

Keep the original CMAB internal reward as a diagnostic, not the sole common comparison score. Report component metrics and a small plausible coefficient-sensitivity check so an apparent gain cannot be explained only by our preferred weights.

**Completion evidence:** hand-checkable metric fixtures, matched workloads, run IDs connecting logs to configs/policy identities and an explicit rule for incomplete/failed runs. An algorithm-induced failure is an outcome, not an inconvenient sample to drop; infrastructure failures/retries are separately identified. Replay archived author data and fresh experiments must remain distinctly labelled.

### D8. Repeatable result and analysis release

**Artifacts:** per-run compact raw exports, per-decision/event records needed for analysis, a tidy per-run metrics table, aggregate/paired-effect tables, analysis code and selected comparison figures.

Every reported number must resolve to source run IDs, policy/config/data/commit identities, scenario IDs, seeds, durations and completion status. Keep measured units and aggregation rules explicit. Store repetition/training-seed variability and paired confidence intervals at the session/scenario level; individual segments and related windows are not independent trials. With one measured source session, browser repeat intervals quantify repeatability, not generalization across all Starlink sessions.

The headline answer must identify the winning/losing conditions and the size/uncertainty of the improvement, with physical tradeoffs. Retain the original-CMAB control, isolated accepted changes and at least one informative failed variant or regression case. Main conclusions must survive actual-browser testing; a calibrated simulator screens candidates and supports training, but does not replace the deployed comparison.

## 6. Exact figure and table inventory

IDs here are stable planning IDs, not fixed final report numbering. All result figures must be generated from saved data by scripts; provide vector PDF/SVG where practical and readable PNGs for slides. Label policies, units, repeats and uncertainty. The main report uses a compact subset; supporting plots stay in an appendix or repository rather than inflating the report.

### Figures

| ID | Figure to deliver | What it answers / source | Placement |
|---|---|---|---|
| F1 | System and decision/update diagram, with our changed components highlighted | Where observations, online updates/offline training, action selection, requests and logging occur; what remains shared. Based on the actual code, with attribution for any reused diagram. | Main methodology. |
| F2 | Original-CMAB diagnostic timeline across reset boundaries | Marks reset, forced versus learned choices, reward creation and later segment/playback events; includes learned-decision fraction and buffer/stall context. Tests whether the proposed mechanism actually exists in traces. | Compact diagnostic in methodology if legible; full version in appendix. |
| F3 | Overall paired QoE difference from original CMAB, with uncertainty | Selected methods on the same held-out workload; show per-session effects/repeats and absolute baseline context, not just an unexplained percentage bar. | Main results. |
| F4 | Scenario-family breakdown | QoE difference, stall duration and live-latency effects across all five mandatory families; avoid an aggregate hiding an outage/recovery regression. | Main results, multi-panel. |
| F5 | Matched event trajectories | Capacity/RTT or interruption schedule, actual played bitrate, buffer, stalls and live delay for original CMAB, improved CMAB and neural finalist. Include a normal/change case and an interruption/recovery case; add a failure case when necessary. Use a declared selection rule, not only the best-looking run. | Main explanatory results; extra cases in appendix. |
| F6 | CMAB component/ablation effects | Contribution of the retained mechanisms, selected isolated changes and their final combination; report QoE with stalls/delay where tradeoffs matter. Use development/validation evidence for development choices, clearly labelled. | Main mechanism analysis. |
| F7 | Neural learning and validation curves across seeds | Training progress, common validation QoE and a physical metric such as stalls, teacher/pre-RL baseline if used, and checkpoint-selection point. Do not equate incomparable training rewards with common evaluation QoE. | Main neural results, compact. |
| F8 | Simulator-to-browser calibration | Predicted versus measured segment download time plus representative buffer/stall/latency trajectories and residuals. Quantifies why the training environment is credible and where it is approximate. | Appendix/supporting evidence; concise summary in methodology. |

If coefficient sensitivity, RTT freshness/detection delay or reset-phase mismatch changes the conclusion, add one focused robustness plot in the appendix. Otherwise summarize that check in text/a compact results file. No separate figure is needed for every trial or every tuning setting.

### Tables

| ID | Table to deliver | Required entries | Placement |
|---|---|---|---|
| T1 | Policy and variant comparison | Original CMAB, final CMAB, required conventional baselines and neural policies; actual observations, memory/update rule, reward, runtime and exact modification. Identify inherited versus our work. | Main methods; full settings in configs. |
| T2 | Dataset and scenario inventory | Source sessions, measured/generated channels, durations, split membership/guarding, five families, count of independent sessions versus generated scenarios and limitations. | Main methods. |
| T3 | Controlled experimental setup | Segment/ladder/source, target/catch-up, host/images, trace and wall-clock alignment, trial duration, repetitions/seeds, model selection and failure/retry rules. | Compact methods table or appendix, depending on space. |
| T4 | Main quantitative results | Per-policy QoE, played bitrate, stall seconds/count, switch frequency/magnitude, startup, mean/tail live delay and run counts/uncertainty. Use two aligned panels if the columns are too wide. | Main results. |
| T5 | Hypothesis/ablation outcome summary | Change, predicted effect, isolated observed effect, retained/rejected status and tradeoffs. Include at least the informative negative outcomes. | Main analysis. |
| T6 | Team contributions | All three names/roll numbers and 2-3 sentences of specific completed work each. Base this on actual work, including work performed across the initial domain split. | Required report section. |
| T7 | Metric and reward definitions | Formula, units, sampling/normalization, startup/stall distinction, quality proxy, switching definition, latency/skipping treatment and uncertainty unit. | Appendix; essential QoE formula in main methods. |
| T8 | Deployment feasibility | Actual runtime/host, model size, cold setup versus warm full-decision time, sample count and fallback/error counts. | Short appendix table; one sentence in main results. No runtime research track. |

The aggregate results table, family figure and trajectories are complementary: they establish the overall effect, locate where it occurs and explain the behaviour. Ablations establish which changes caused it. Learning curves and calibration support the neural result without taking over the networks-course story.

## 7. Concrete report and presentation contents

### Final report PDF

Use a concise main report with a short technical appendix. There is no page limit stated in the supplied image, so do not invent one as a course rule. Reuse the figures/tables above and avoid repeating the same finding in several sections.

1. **Title, team and abstract:** project identity, GitHub link and a short factual result summary written after evaluation; use T6 for the required specific contribution statements.
2. **Problem and objective:** live-streaming quality/stall/delay tradeoff under LEO variation; joint question of how the three developed policies compare with original CMAB; mandatory-only scope.
3. **Reference system and related work:** exact Zhao/Pan implementation and limitations, contextual bandit versus sequential RL, relevant Gelato/Plume/Pensieve and BOLA work, and the gap we investigate. Verify citations against the actual primary sources; distinguish the reference paper from other papers mentioned in the proposal.
4. **CMAB investigation and changes:** original control flow/reward/reset audit, H1-H6 evidence, selected improved design and isolated variants. Explain online learning and any heuristic guard separately. Use T1 and selected F2 evidence.
5. **Neural comparator:** compatible state/action/reward, model/weight provenance, LEO inputs, architecture/trainer, workload sampling, split discipline, checkpoint/seed procedure and synchronous deployment. Explicitly distinguish the Phase A pilot from final trained policies. Include a compact F7 result or reference it from results.
6. **Experimental methodology:** F1, T2/T3, calibrated environment, real-browser validation, common metrics/QoE, matched conditions, budgets, repetitions, uncertainty and failed-run handling. Distinguish original archive reproduction from new measurements.
7. **Results and analysis:** headline comparison (F3/T4), family outcomes (F4), behavioural explanation (F5), component contributions/negative experiments (F6/T5), neural results (F7) and required tradeoff interpretation. Every conclusion must point to a measured result.
8. **Limitations and conclusion:** measured-versus-synthetic limitations, independence, approximation/quality-proxy limitations, where policies lose, deployment cost and the actual answer to the research question. No unimplemented future feature should be counted as a contribution.
9. **Reproduction and references:** repository/revision, short commands for saved-results reproduction, evaluation and training, hardware/time expectations, data/license attribution and primary citations. Put long configurations, F8, T7/T8 and additional failure traces in the appendix/repository.

### Final presentation

The proposal includes a presentation, although the supplied final-submission image does not prescribe a new deck length. Deliver one concise final deck using the same selected result figures: objective/system, original CMAB weakness, changes/hypotheses, neural method, controlled experiment, main gains/tradeoffs, explanatory ablation and conclusions/contributions. Set its final length/timing when course presentation rules are known. Do not turn the deck into a second implementation project.

## 8. Code and reproducibility deliverables

Paths are proposed destinations within the existing repository; Phase 2 should reuse/extend current files instead of duplicating them under competing names.

| ID | Code/package component | Concrete output and verification |
|---|---|---|
| C1 | Policy implementations and adapters | Original CMAB preserved; improved CMAB and bounded variants; existing throughput/BOLA adapters; conventional/LEO neural policies. Consistent selectable policy IDs, valid actions, lifecycle and telemetry checks. |
| C2 | Shared dynamics and metrics | Extend `rl/` with reusable environment, explicit observation/reward/metric definitions and calibration fixtures. Verify time/byte/buffer conservation, startup/outage/recovery/seek behaviour and outcome attribution. |
| C3 | Data preparation | Extend `scripts/prepare_data.py` and source/split manifests. Retrieval, parsing, integrity, split and deterministic regeneration commands; measured/synthetic labels survive exports. |
| C4 | Training and candidate selection | Configuration-driven train/evaluate/resume commands, bounded multi-seed runs, training-only transforms, validation selection and complete histories. Preserve meaningful failed attempts in the ledger. |
| C5 | Model artifacts | Native final checkpoints, deployable actor/controller assets, normalization/action manifests, versions/hashes/licenses and example input/output. Verify parity and actual browser control. |
| C6 | Experiment runner | Reuse `scripts/browser_trial.py`/matched-run infrastructure; add a matrix runner with readiness checks, matched phase/workloads, repetition/order control, run isolation, failure classification and safe resume. Avoid re-running verified completed trials on resume. |
| C7 | Analysis and plotting | One shared metrics-export route, paired-summary code and deterministic generators for F1-F8/T1-T8 as applicable. All plots/tables derive from versioned metadata/results rather than manually entered final numbers. |
| C8 | Demo build and launcher | Reuse the local-source Dockerfile/Compose overrides/testbed script, pinned accessible submodules/images and prebuilt policy assets. Provide a short validated scenario and a clear view of policy, link conditions, bitrate, buffer/latency and real playback. |
| C9 | Reproduction entry points | Distinct documented commands for environment/checks, data preparation, training, fresh evaluation, plots-from-saved-results and demo. A full reproduction command may compose them, but must not force retraining to regenerate existing plots. |
| C10 | Release/diagnostic checks | Check run completeness/required metrics, missing assets, config/model/data hashes, result-to-figure traceability, accessible submodule commits and ZIP contents. Keep diagnostic logs for errors without adding unrelated test infrastructure. |

All CLI entry points should expose or document configuration, seeds, input/output paths and required host/runtime. Commands should produce actionable errors and return nonzero on failed verification. Keep caches/environments/build scratch outside the project, and keep all new permanent work in this repository. Do not add a project `tmp` directory. Commit/push authorization was explicitly granted during this run; use it for the reviewed publication set without requesting it again.

### Reproduction levels the README must distinguish

1. **Review saved evidence (submission):** regenerate final metrics, tables and figures from the supplied compact run exports, without Docker/GPU or retraining where possible.
2. **Run the browser demo (deferred presentation only):** build/select the player, start the common stack, run a fixed network scenario and verify actual requests/playback.
3. **Repeat the evaluation:** run the declared comparison matrix with the published policies, then regenerate results.
4. **Repeat learning/development:** prepare the data and rerun the selected neural training configurations; separately reproduce chosen CMAB hypothesis comparisons. Report realistic compute/time/storage needs and stochastic variability rather than promise identical reward curves.

## 9. Demonstration and submission package

### Working demo

- Provide a named, repeatable bandwidth-change/interruption/recovery scenario, with original CMAB and the selected improved policy under the same conditions. Make the trained neural policy selectable as well.
- Show actual advancing video, policy identity and measured bitrate/buffer/live-delay behaviour; include logs linking actions to requests. Do not substitute a scripted quality sequence or a dashboard animation for a working controller.
- Provide one launch/run/verify instruction sequence, a short explanation of expected observations, and a saved comparison plot. A short screen recording is a fallback if the course permits it; the recording demonstrates this run, not universal superiority.
- Verify from a clean checkout or separate clean workspace on a supported host; document prerequisites. Keep default/demo credentials out of publicly exposed services and exclude personal credentials/tokens from release assets.

### Final ZIP and GitHub state

The release must contain:

- Final report PDF and focused code/results/reproduction material. No PPT, video, demo-only launcher, learning guide or rehearsal material in this submission ZIP.
- Developed parent code and the modified player source, or a documented source snapshot that can be obtained without private/unpublished submodule commits. A GitHub ZIP alone does not automatically include submodule contents; verify the packaged player source explicitly.
- Exact dependency/build/experiment configurations; model/controller assets; data provenance/retrieval/split manifests.
- Compact per-run results needed to rebuild the reported metrics/figures, aggregate tables and final figures. For large/raw assets that cannot sensibly be included, provide working retrieval URLs with hashes and access/license requirements; required evidence must not exist only in a local MongoDB volume.
- A top-level reproduction README, artifact index mapping report figure/table IDs to scripts and input files, source/license attribution and a manifest of release identities/checksums.

Publish the intended reviewed revision and all required submodule commits only after explicit commit/push authorization. The report must link to the actual accessible GitHub repository/branch or release. Verify its link and source availability from a separate checkout. Exclude virtual environments, caches, Docker layers, personal credentials and duplicate raw archives. ZIP extraction plus the saved-results reproduction route is the final packaging check; a successful ZIP command alone is insufficient.

## 10. Definition of completion and scope control

The submission hand-in is ready when the verified four-policy analysis, required supporting metrics, source-backed report/figures, evaluator-facing GitHub and focused reproducible ZIP have their verification evidence. Presentation/demo/learning/rehearsal readiness is a separate Step23 outcome. The strength and limitations of any claimed improvement must match held-out browser results.

The default excludes congestion control, async/worker bridging, runtime comparison studies, many unrelated RL optimizers, a new video service/UI, perceptual-quality model training and dashboards beyond what the demo needs. Independent measured data and simulator fidelity are pursued to the extent needed for credible claims, not as open-ended data collection or networking-framework rewrites.

This inventory is flexible. During execution, record a change when a deliverable becomes infeasible, redundant or requires a different method. Preserve submission/proposal coverage, the primary CMAB comparison, honest conclusions and reproducibility. Phase 2 should create the sequential plan from this inventory, preserve completed Phase A assets and replace obsolete worker/runtime-study priorities in the existing roadmap.

## Source basis

- User-provided submission-guidelines image: `codex-clipboard-fa030352-4cdf-4e39-b3bb-3af42e7373f9.png`.
- `../resources/CS6048_Group4_Project_Proposal.pdf`, especially mandatory deliverables and member identities.
- `../resources/LeoPaper(1).pdf`: Zhao and Pan's MMSys 2024 reference study, including short-timeslot/repeated-exploration limitations.
- Actual `dash.js/src/streaming/rules/abr/cmab/CMABAbrController.js` and `CMABRule.js`; `stats-server/app.py`.
- `roadmap.md`, `reports/phase-a/README.md`, `artifacts/phase-a-completion.json`, `scripts/matched_pilot_trials.py` and existing integration/export evidence.
- `models/reference/manifest.json`, `models/pilot/manifest.json`, `artifacts/training/learning-verification.json`, `rl/pilot_env.py`, and current source/split/media/LENS manifests.
- Primary reference checked during this planning step: [Plume/Gelato repository](https://github.com/sagar-pa/plume), describing Gelato's relationship to Plume and the latter's training-distribution balancing. Use the exact relevant commit when adapting code.
- Workflow reference checked during this planning step: [Stable-Baselines3 RL tips](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html), covering custom-environment checks, normalization, repeated runs, reward iteration and separate evaluation. Our train/validation/test roles remain explicitly separated rather than treating a frequently inspected validation set as untouched test data.

Existing supporting documents may still describe the earlier RL-first or runtime-study plan. The user's current two-track and synchronous-runtime instructions govern this inventory; the revised roadmap.md supersedes the old execution priorities. The numerical budgets, step order, verification gates and autonomous execution rules belong to that roadmap.
