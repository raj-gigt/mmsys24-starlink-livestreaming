# Reference CMAB audit

The original controller's decision code is unchanged; common runtime initialization and a pre-decision buffer-event guard are separately documented below. Exact source/wheel hashes and the completed control run are in artifacts/final/reference-audit.json.

The controller uses MABWiser 2.7.0 LinTS with throughput, playback rate and network latency. It fits StandardScaler on the current slot's past samples, constructs a new MAB, fits past choices/rewards, and predicts one action. Buffer and live delay are absent from the fitted input; live delay appears in reward.

At second boundaries 12, 27, 42 and 57, the implementation clears choice/reward/bitrate history. For eight representations the next seven decisions select the highest representation. These are decision calls, not necessarily seven distinct completed media downloads: callback/request attribution must be measured separately.

After choosing, the code creates single-segment P.1203 input, with empty stalling input, and computes quality multiplied by target/current live delay and selected/max nominal bitrate, minus selected-bitrate stall share. This happens before the new chosen media download finishes. This is not its realized playback reward. P.1203 itself is not inherently restricted to the limited input supplied here.

The served wheel's default seed is 123456. A newly created MAB receives that same default on each fitted decision. The experiment must distinguish persistent seeded exploration from repeatedly resetting the random generator; the source fact alone does not prove a QoE effect.

The sidecar's legacy /ping endpoint can repeat last successful RTT after a failed probe. Original scalar behaviour remains the control; new policies require explicit freshness and validity.

The 17 November readiness control streamed under configured 8 Mbps/40 ms, produced completed requests, advancing playback and database metrics. Independent tests measured 1.915/7.612 Mbps for configured 2/8 Mbps, confirmed complete outage and restoration. Some webpack hot-reload websocket errors occur on the proxy route; distinguish these from video errors rather than marking every severe console entry a playback failure.

Hypotheses H1-H6 remain hypotheses until isolated and combined experiments establish effects. No superiority is claimed from this audit.

## Additional estimator issue to test

Inspection of the served 2.7.0 linear-model code shows prediction as a dot product between context and sampled coefficients, without an explicit intercept in that calculation. The caller first mean-centres all three context columns using StandardScaler. At an exactly zero transformed context, all arm scores and their Thompson-sampling variation are zero regardless of coefficient samples. This is a conditional mathematical property, not a claim that every real observation is exactly zero. A pinned-runtime fixture and an isolated bias/normalization intervention are required before assigning it an experimental effect (H5). Adding a constant before StandardScaler would erase it; an intercept test must append it after centering or use explicit physical normalization.

## First controlled development results

The 12-session memory/startup factorial used three distinct 90-second development cases, one repetition each, randomized policy order and minute-aligned source/network phase. Shortened conservative startup improved common QoE in every case: steady -4.82 to -3.24, bandwidth change -1.87 to -1.36, recovery -3.23 to -2.53 per wall second. These are descriptive development outcomes, not independent replication or held-out significance. Memory-only left almost no learned calls under bad conditions and did not help. Combining memory and startup was best on the bandwidth-change case, but worse than startup-only on the other two. The restart treatment changes both initial rate and forced-choice duration; it is not an isolated safety-factor result.

## Request-feedback experiment

The new request ledger attaches the most recent matching, unconsumed choice to the exact request object at download start; initial/unmatched requests are reported, not assigned a guessed action. It stores the original observation/action, consumes each decision at most once, ignores duplicate completion, and censors seek-cancelled/error/abandoned transfers. Only successful matched outcomes enter the bounded 30-row training set. This completion-only selection introduces censoring bias, which is measured and disclosed.

`delayed` evaluates the original proxy at completion. It changes both timing and the training/update clock from decision callbacks to linked completed requests; it is not a pure time-shift ablation. `outcome` replaces that proxy with explicit completed-download utility, buffer-budget starvation, selection-change and latency costs. Buffer-budget excess is a surrogate, not measured rebuffering, and completed-download quality is not claimed as played quality. Session comparisons still use the independent played ledger. Exact online played-outcome credit is deferred because live seeks and buffering make its causal association unreliable.

The first 35-second 8 Mbps browser integration check linked 15 completed outcomes, with 84% of starts linked to a choice; preceding initial requests were untrained. Hand-calculated fixtures cover duplicate callbacks, identical URLs with different objects, seek censoring, errors, unmatched requests and bounded histories.

## Initialization boundary to correct before validation

The first six request-feedback development runs enter their first CMAB decision approximately 8.18-9.21 seconds after Load. Browser console timestamps identify about eight seconds inside Pyodide/package initialization, rather than media/network observation time alone. The existing rule starts this work only after playback initialization. Both treatments in each development comparison share that cold initialization path, but the neural actor preloads before Load. Therefore validation/final trials must expose a common prewarm entry point for both CMAB rules, await dependencies before the measured Load trigger, and separately record setup cost. Keep the decision algorithm unchanged in original CMAB. Do not pool cold and warm trials as interchangeable repetitions or attribute a common readiness repair to the improved algorithm.

The controlled common catch-up setting is the repository's explicit LoLP override, also present in experiments/batch-example.json. The runner otherwise defaults CMAB to its custom liveCatchupModeCMAB. A supplementary original raw-replay pair should explicitly use that custom mode for both B0 and the improved CMAB, labelled separately from the controlled ABR-isolation comparison.

The nine-session request-feedback comparison completed. Versus the matched immediate-proxy `both` variant, delayed original-proxy QoE differences were +0.112, +0.233 and -0.264 per wall second on steady/change/recovery. The explicit request-outcome surrogate differences were +0.296, +0.245 and +0.865; stall reductions were 5.00, 7.00 and 18.78 seconds. Advance the outcome surrogate for development, without claiming a validated win or ignoring its 71.8 seconds of stalls on the steady low-capacity case. All six delayed/outcome runs passed request-identity checks; acceptance/censoring counts are in the portable raw evidence and paired table.

## Shared initialization repair and estimator fixture verified

The warm check exposed an original lifecycle error: once Pyodide is ready early, the initial BUFFER_LOADED event can execute `rebufferingEvents.get(currentBitrateKbps).push(...)` before any bitrate has been selected. The unknown map key throws and stops scheduling. Both CMAB rules now skip that unassignable startup interval; actual startup remains in the independent ledger. This common guard does not change the controller's feature/action/reward/reset code. A failing real warm run is retained (`phasea-abrCMAB-20261117T013036-f92710`), and the actual-rule lifecycle fixture plus corrected real warm runs pass.

The served MABWiser 2.7.0/Pyodide fixture confirmed zero scores at exactly zero centered inputs. Appending a constant after scaling produced distinguishable approximately0.667/1.333 fitted scores for rewards1/2. Reconstructing with the same seed repeated scores; varying the seed changed them. The pinned API rejects alpha0, so the near-deterministic fixture uses alpha1e-8. Candidate experiments retain alpha1. Cold dependency preparation measured7.64 seconds; a cached lookup measured0.1ms. These are initialization/conditional estimator checks, not standalone QoE improvement evidence.

The next warm development comparison isolates fixed scaling+intercept (`scaled`), buffer/live-delay additions (`buffer`), RTT validity/age/history additions (`context`), a reproducibly changing refit seed (`seeded`), a clipping guard (`guard`) and the same ceiling without LinTS (`guard_only`). The changing-seed variant is not described as an incrementally fitted persistent model. Guards, source readiness and network measurements are logged explicitly.

## Integer RTT parsing defect and controlled restart

Input checks found frequent invalid typed probes. The original sidecar regex accepts decimal ping times only. At an independently configured120ms link, actual iputils output was `time=120 ms`, zero packet loss, yet the regex did not match. New typed health had inherited this parser and falsely reported an unavailable probe. The typed endpoint now parses decimal, integer and `<1` upper-bound formats; the original `/ping` scalar parser/state remain unchanged. The physical corrected endpoint reports valid120ms while the legacy scalar remains0 in the same fresh process, demonstrating control preservation.

Four completed context/guard-v1 runs are retained as diagnostic-only; they are excluded from candidate selection. One next session was interrupted and cleaned. The complete21-session comparison restarts ascontext-guard-v2, with statistics-server/shaper/metric identities now included alongside player/observer/workload hashes. The original memory/startup and request-feedback comparisons did not use typed RTT in their learner, so their treatment results are unaffected.

## Corrected warm development result

The full21-session context/guard-v2 batch completed under corrected typed RTT. Three-family mean common QoE/wall-second was approximately-2.32(outcome),-2.12(scaled),-1.58(buffer),-1.31(context),-1.52(changingseed),-0.40(guardedCMAB) and-0.18(guardonly). These means describe exactly three development cases, one run each, and are not held-out generalization estimates. Extra context helped steady/recovery but not the RTT-variation case. Changing the refit seed was not promoted.

GuardedCMAB improved every case against context-only, but guard-only was better in allthree. The proper interpretation is evidence for the guard, with no established incremental benefit from LinTS. Validation will compare originalCMAB, the best unguarded bandit(context), guardedCMAB and guard-only. The primary modified-CMAB selection remains among the bandit variants, while the heuristic is separately reported and shipped; neither can be labelled RL.

## Paper versus distributed emulator

The supplied paper(PDFpage7, printedpage115, Section5) describes40ms/0.1%background loss outside fixed handover moments and100ms/1%during them. The distributed repository's shaper instead replays measured RTT, applies1%loss for positive RTT and100%for nonpositive RTT, at20Mbps. These are different experiment profiles. Therefore our supplementary group is labelled **author-repository raw replay**, not an exact recreation of the publication's stated emulator settings. PhaseA archived figure regeneration remains a separate reproduction of supplied measurements. Our fresh conclusions concern the checked implementation under declared controlled and repository-replay conditions.

## Startup-gate failure and external clock diagnosis

The first24-session validation returned no eligible bandit. GuardedCMAB improved mean QoE and stalls, but mean startup5.38s versus original3.54s exceeded the unchanged+1s gate. Context-only failed the useful-playback gate. No controller was promoted. The unusually long startup preceded any ABR decision: one guarded run waited10.44s before its first media request, then chose at11.285s and played at11.293s.

The runtime MPD advertises external Akamai UTC timing. ResourceTiming diagnostics reproduced minute-aligned HTTP/HTTPS clock requests consuming2.52s+1.48s in one guarded run and0.67s+2.10s in originalCMAB before stream initialization. An explicit single-host-only `hostClock=1` option disables that external synchronization; the default for remote clients is unchanged. Player/proxy/statistics container clocks were checked against their common WSL kernel, rather than assuming Windows command-dispatch time is identical. Under the option, minute-aligned diagnostic startups were0.830s and0.834s, and no external time resources were requested. This is a shared infrastructure repair, not an algorithmic startup win.

Allfour policies are revalidated on allsix cases under that same clock option. The numeric gates and QoE definition are unchanged. First-pass external-clock validation and all diagnostic data remain available. Early development effects remain exploratory because variable clock setup also changes initial live-source phase; final conclusions require the corrected common protocol. The initial72-research-trial budget is expanded to90 to repeat24 validation sessions after this measured infrastructure repair, without adding policy candidates or reducing held-out testing/release checks.

The guard-only control always chooses its ceiling, including forced-slot callbacks; guardedCMAB also retains the more conservative restart choice before learned selection. Thus their difference concerns the **bandit/restart package**, not a perfectly isolated on/off learning intervention. A heuristic win does not by itself prove learning is harmful; it shows the additional package has not demonstrated incremental value.
