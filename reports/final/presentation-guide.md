# Final presentation and demo guide

The eight-slide deck reads the final analysis directly. Use the submitted report
and T4 tables for exact numbers; do not quote validation scores as final results.
This guide prepares a roughly ten-minute talk. Actual team rehearsal is still a
human task. The report's individual contribution templates remain intentionally
blank until each member supplies their actual work.

## Speaking sequence

| Slide | Speaker / assigned domain | Time | What to explain |
|---|---|---:|---|
| 1 | Rajat / integration | 0:20 | Project identity; primary CMAB study plus neural comparison. |
| 2 | Rajat / integration | 1:15 | Docker source → shaped network → Chrome; original LinTS decisions, resets, immediate proxy. |
| 3 | Anjan / algorithms | 1:25 | Matched completed feedback, nine inputs, conservative restart and guard; negative memory result and guard-only control. |
| 4 | Anjan / training | 1:25 | Compatible A2C, 36/64 causal inputs, five seeds, early validation peaks, synchronous export. |
| 5 | Deviprasad / evaluation | 1:10 | Measured RTT versus generated capacity, common player/score, frozen 179-session inventory. |
| 6 | Deviprasad / evaluation | 1:15 | Primary paired effect, stalls and quality tradeoff; explain conditional interval. |
| 7 | Deviprasad / evaluation | 1:00 | Family differences, guard-only/neural comparison, separate raw replay and limitations. |
| 8 | Rajat + Anjan | 0:40 | Evidence-backed conclusion, reproducibility and demo transition. |

This is approximately 8:30 of speaking, leaving 1:30 for a short recorded/live
demo extract. The complete recovery recording is longer; do not play it in full
inside a strict ten-minute slot. Assigned speaking domains do not establish who
completed each code change.

## Explain the main mechanisms simply

**CMAB:** a contextual multi-armed bandit chooses a bitrate using the latest
measurements and rewards from previous actions. LinTS means linear Thompson
sampling: fit a linear estimate of reward for each action, then sample plausible
estimates to balance trying alternatives with choosing a promising bitrate.
It does not learn a multi-step value function like our actor-critic model.

**Original feedback issue:** the supplied controller computes a quality proxy
immediately. It cannot yet know how that request will affect later playback.
Its single-segment P1203 input has no stalling events. This does not mean P1203
itself is a bad metric; the limitation is how this implementation uses it.

**Our CMAB feedback:** associate an action with its actual completed media
request and update once, using the context available when it was chosen. The
download reward penalizes exceeding the decision-time buffer budget, bitrate
changes and excess delay. It is explicitly a surrogate, separate from the final
actually-played score. Cancelled or unmatched requests do not get invented
outcomes, so completed-only feedback still has selection bias.

**Safety guard:** when a proposal is too aggressive, cap it at a bitrate below
recent measured throughput. The multiplier is more conservative with low buffer,
high delay or invalid probes. This cannot eliminate stalls when even the lowest
bitrate exceeds the link. Guard-only is a serious competing control, not a
throwaway baseline. It also changes restart choices, so its comparison with the
full controller does not isolate learning perfectly.

**Actor-critic:** the actor outputs a score for each of eight bitrate choices;
the critic estimates future return while training. The critic is not deployed.
Reward combines quality, rebuffering, switching and live delay. RL trains through
simulated consequences, not by treating old CMAB choices as correct labels.
An initial causal heuristic provides a warm start, followed by A2C updates.

**Neural inputs:** the conventional 36-vector is eight completed transfer rows
of four values plus four playback values. The 64-vector adds eight completed
probe rows of three values plus four delay/health values. All values are past or
current observations with fixed scaling. Future channel profiles are invisible
to the actor and critic. Probe failure is not a ground-truth handover label.

**Why synchronous JS:** the small actor is two dense 64-unit ReLU layers and
eight output scores. Exported weights plus a Float32 forward pass return an
action immediately, which fits dash.js's decision call. This runs on the Chrome
host CPU main thread; PyTorch is used for training only. Float32 preprocessing,
logits and argmax match native model fixtures and actual browser decisions.
This choice is simple and has small observed overhead, but CPU/main-thread time
and supported operations limit much larger models. We did not implement an
asynchronous worker or infer mobile performance from this laptop.

## Likely questions and precise answers

**Did the new algorithm outperform CMAB?** Give the primary held-out effect and
its fixed-suite interval from slide 6, then the stall/played-bitrate tradeoff.
State the exact workload scope. Also show the guard-only and native throughput/
BOLA rows; beating the reference does not imply beating every baseline or that
RL is the best method here.

**What does a negative QoE mean?** It is a utility-minus-penalties score with an
arbitrary zero, not a probability or percentage accuracy. A less negative value
is an improvement. Never express a relative percentage increase in QoE across
zero. Stall reduction can be expressed as a percentage with its baseline given.

**Why not use MongoDB as a model input?** The browser already has recent
throughput/buffer/playback observations and a cached RTT health stream. MongoDB
stores experiment evidence. Querying it on each bitrate decision would add
unnecessary delay and synchronization. Actual-player data is verified through
decision/request links, advancing video, production probes and stored records.

**Why was more data needed?** The one-hour reference CSV mostly supplies RTT
and an emulator convention for loss. It is not a synchronized dataset of
capacity, segment outcomes and optimal bitrate actions. We derived controlled
capacity/outage scenarios and used another measured RTT session, with honest
provenance. These are controlled tests, not a large collection of independently
measured Starlink links.

**How did we avoid leakage?** Chronological train/validation/test ranges have
guards; final browser cases, policies, weights, scoring and repeat inventory were
frozen before their performance was read. Hyperparameters/checkpoints/seeds were
selected using validation only. Final outcomes did not trigger changes to the
tested controller. A revised controller would require a fresh reserve cohort.

**Why keep multiple seeds and earlier checkpoints?** RL can improve and then
degrade. Five fresh seeds describe variability; each seed keeps its best
validation checkpoint, then the median validation seed is deployed. Neither the
luckiest seed nor the final training step is automatically selected. Curves
retain late degradation, and more training was not assumed to help.

**Why CPU with an RTX4060 available?** We benchmarked the working GPU against
CPU on this actual small, eight-environment workload. CPU collected decisions
faster. Main training took about 44.3 minutes; no 18-hour estimate was imposed.

**How faithful is the simulator?** It uses actual encoded segment bytes and
models full-segment availability, retries, buffer, playback rate and seeks.
Six real browser calibration cases quantified errors. Buffer MAE was about
0.495 s; overall delay MAE was 2.061 s, missing its 1 s target. Browser testing,
not simulator score alone, supports deployment claims. The model is a transport
approximation, not exact TCP.

**Are the intervals general Starlink confidence intervals?** No. They describe
paired browser repeatability conditional on the ten tested cases. Related
windows and thousands of video segments are not independent measured networks.
With only two/three repeats, raw case points and regressions matter too.

**Did we reproduce the paper exactly?** Phase A regenerated author figures and
made the reference artifact run. The final supplementary raw replay follows the
distributed code, whose shaping differs from the paper's stated background and
handover settings. We label it repository replay and keep its scores separate.

**Was the rest of the system unchanged?** Compared policies share the media,
shaper, playback target/catch-up and measurement machinery. Common fixes include
typed RTT health, local-source builds and guest-clock control. Original CMAB's
decision logic is preserved; passive instrumentation and common runtime setup
are disclosed. Native throughput/BOLA retain their own configured auxiliary
rules, so original-versus-improved CMAB is the strongest controlled attribution.

## Demo preparation checklist

1. Copy the report, deck and MP4 fallback locally. Read `demo/*.json` to know
   which real policy/run is shown. The video is not the final comparison dataset.
2. Check `bash scripts/testbed.sh status`. Open http://localhost:7900 and verify
   the recording/live screen is visible. Do not launch two trials in parallel.
3. Run `python scripts/demo_final.py --policy improved`; compare the saved
   original run or launch original sequentially. Show actual playing video and
   logged selected/played quality, buffer and delay, then the same-run plot.
4. If time is short, use a 30-45 s section around the interruption/recovery in
   the recorded fallback and explain its policy/run identity.
5. Rehearse the transitions and one failure recovery. Each member fills their
   actual contribution template. Confirm the course's final speaking duration
   if the instructor supplies a different limit.

No human rehearsal, contribution confirmation or portal upload is claimed by
the automated project checks.
