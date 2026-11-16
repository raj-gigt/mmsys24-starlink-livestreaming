# Reference CMAB audit

The control source is unchanged. Exact source/wheel hashes and the completed control run are in artifacts/final/reference-audit.json.

The controller uses MABWiser 2.7.0 LinTS with throughput, playback rate and network latency. It fits StandardScaler on the current slot's past samples, constructs a new MAB, fits past choices/rewards, and predicts one action. Buffer and live delay are absent from the fitted input; live delay appears in reward.

At second boundaries 12, 27, 42 and 57, the implementation clears choice/reward/bitrate history. For eight representations the next seven decisions select the highest representation. These are decision calls, not necessarily seven distinct completed media downloads: callback/request attribution must be measured separately.

After choosing, the code creates single-segment P.1203 input, with empty stalling input, and computes quality multiplied by target/current live delay and selected/max nominal bitrate, minus selected-bitrate stall share. This happens before the new chosen media download finishes. This is not its realized playback reward. P.1203 itself is not inherently restricted to the limited input supplied here.

The served wheel's default seed is 123456. A newly created MAB receives that same default on each fitted decision. The experiment must distinguish persistent seeded exploration from repeatedly resetting the random generator; the source fact alone does not prove a QoE effect.

The sidecar's legacy /ping endpoint can repeat last successful RTT after a failed probe. Original scalar behaviour remains the control; new policies require explicit freshness and validity.

The 17 November readiness control streamed under configured 8 Mbps/40 ms, produced completed requests, advancing playback and database metrics. Independent tests measured 1.915/7.612 Mbps for configured 2/8 Mbps, confirmed complete outage and restoration. Some webpack hot-reload websocket errors occur on the proxy route; distinguish these from video errors rather than marking every severe console entry a playback failure.

Hypotheses H1-H6 remain hypotheses until isolated and combined experiments establish effects. No superiority is claimed from this audit.

## Additional estimator issue to test

Inspection of the served 2.7.0 linear-model code shows prediction as a dot product between context and sampled coefficients, without an explicit intercept in that calculation. The caller first mean-centres all three context columns using StandardScaler. At an exactly zero transformed context, all arm scores and their Thompson-sampling variation are zero regardless of coefficient samples. This is a conditional mathematical property, not a claim that every real observation is exactly zero. A pinned-runtime fixture and an isolated bias/normalization intervention are required before assigning it an experimental effect (H5). Adding a constant before StandardScaler would erase it; an intercept test must append it after centering or use explicit physical normalization.
