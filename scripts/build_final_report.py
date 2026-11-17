"""Build the course report from verified result tables and scientific figures."""
import json,csv
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/final';FIG=OUT/'figures'
NAVY=colors.HexColor('#263B58');TEAL=colors.HexColor('#128C86');LIGHT=colors.HexColor('#F0F4F7')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.4,leading=13,spaceAfter=7,textColor=colors.HexColor('#263342')))
styles.add(ParagraphStyle(name='SmallBody',parent=styles['Body'],fontSize=7.8,leading=10,spaceAfter=5))
styles.add(ParagraphStyle(name='ReportTitle',parent=styles['Body'],fontSize=24,leading=29,textColor=NAVY,spaceAfter=15))
styles.add(ParagraphStyle(name='SectionTitle',parent=styles['Body'],fontSize=16,leading=20,textColor=NAVY,spaceAfter=12))
styles.add(ParagraphStyle(name='Sub',parent=styles['Body'],fontSize=11,leading=14,textColor=TEAL,spaceBefore=6,spaceAfter=7))
STORY=[]
def p(text,style='Body'):STORY.append(Paragraph(text,styles[style]))
def h(text):p(text,'SectionTitle')
def sub(text):p(text,'Sub')
def page():STORY.append(PageBreak())
def figure(name,caption,width=487):
    from PIL import Image as PILImage
    path=FIG/name
    with PILImage.open(path) as im:w,h=im.size
    STORY.append(Image(str(path),width=width,height=width*h/w));p(caption,'SmallBody')
def table(rows,widths,small=True):
    data=[[Paragraph(escape(str(c)).replace('\n','<br/>'),styles['SmallBody' if small else 'Body']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#DCE3E8'))]))
    STORY.append(t);STORY.append(Spacer(1,8))
def readcsv(name):return list(csv.DictReader((OUT/'tables'/name).open(encoding='utf-8')))
def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(TEAL);canvas.setLineWidth(.7);canvas.line(54,36,541,36)
    canvas.setFont('Helvetica',7);canvas.setFillColor(NAVY);canvas.drawString(54,24,'CS6048  |  Group 4  |  LEO-aware live streaming');canvas.drawRightString(541,24,str(doc.page));canvas.restoreState()

def main():
    result=json.loads((ROOT/'artifacts/final/evaluation/analysis.json').read_text());assert result['sessions']==179
    project=json.loads((ROOT/'configs/final/project.json').read_text());training=json.loads((ROOT/'artifacts/final/training/main-selection.json').read_text())
    calibration=json.loads((ROOT/'artifacts/final/calibration/comparison.json').read_text());selection=json.loads((ROOT/'artifacts/final/validation/finalists-v2/selection.json').read_text())
    a={r['policy']:r for r in result['overall']};effect=result['paired']['improved'];baseline=a['original'];candidate=a['improved']
    stall_reduction=100*(baseline['stall_s']-candidate['stall_s'])/baseline['stall_s']
    positive=effect['mean_difference']>0
    contribution_rows=readcsv('T6-contributions-template.csv')
    contributions={r['roll']:r['specific_completed_work_2_to_3_sentences'].strip() for r in contribution_rows}
    assert len(contribution_rows)==len(project['members']) and set(contributions)=={m['roll'] for m in project['members']}
    p('LEO-Aware Live Video Streaming:<br/>RL-Based Adaptive Bitrate Selection','ReportTitle')
    p('CMAB refinements and a compatible actor-critic comparison','Sub')
    p('CS6048 - Modern Networking Methods (Beyond TCP &amp; IP)<br/><b>Group 4</b> | Final project report | November 2026')
    sub('Abstract')
    p(f'We extend the supplied MMSys2024 DASH/Starlink artifact while keeping the media, network replay and player settings common. Source inspection and browser ablations examine restart choices, memory, feedback attribution, feature scaling and action safety. The validation-selected guarded CMAB achieves a held-out paired QoE effect of <b>{effect["mean_difference"]:+.3f} per wall second</b> against original CMAB (95% paired-repeat interval on the fixed suite {effect["ci95_low"]:+.3f} to {effect["ci95_high"]:+.3f}). Mean stalls change from {baseline["stall_s"]:.1f} to {candidate["stall_s"]:.1f}s per controlled session. A separate guard-only control tests whether the bandit adds value. We also retrain conventional and LEO-aware A2C actors with five seeds each and synchronous JavaScript deployment. Results cover179 actual browser sessions, not a population-wide Starlink guarantee.')
    sub('1. Problem and scope')
    p('The question is whether changing the reference ABR controller improves actual low-latency live playback under constrained bandwidth, changing RTT, interruption and recovery. We pursue a primary CMAB study and a secondary neural comparison. The proposal\'s optional congestion-control extension is excluded. We do not alter the shared transport separately for a policy or equate a successful model call with better playback.')
    sub('Team and individual contributions')
    table([['Member','Roll number','Assigned domain','Specific completed work (2-3 sentences)']]+[[m['name'],m['roll'],m['domain'],contributions[m['roll']] or '________________________________\n________________________________\n________________________________'] for m in project['members']],[92,63,114,218])
    if not all(contributions.values()):
        p('Missing contribution details are intentionally left as a template at the team\'s request. Fill these with actual work before submission.','SmallBody')

    page();h('2. Reference system and related work')
    figure('F1-system.png','Figure1. Common testbed and our policy interfaces. Player observations and cached RTT health feed inference; MongoDB stores evidence rather than supplying synchronous decisions.')
    p('The supplied artifact [1,2] uses livesim2, an Nginx proxy with Linux tc/netem, Chrome/dash.js, an RTT/statistics sidecar and MongoDB. The player selects among eight representations of the same looping video. Our Docker build copies the team\'s local player source; the upstream prebuilt image would otherwise ignore local edits. Selenium controls repeatable sessions and exports the independent playback ledger.')
    p('Original CMAB runs MABWiser LinTS inside synchronous Pyodide/WebAssembly. Throughput and BOLA remain native dash.js references. Pensieve [3] motivates client-observation actor-critic control; our conventional baseline adapts that style rather than reproducing its released policy. Plume/Gelato [4,5] motivates actor-critic learning and attention to workload representation. We use balanced families, not the full Plume prioritization/clustering framework.')
    p('The retained Maguro/Puffer reference has10 actions, convolutional history branches and future size/SSIM metadata. The deployed player has8 actions and lacks those native metadata. Its published weights therefore cannot be dropped into this interface unchanged. The submitted neural actors are newly trained compatible adaptations; the faithful numerical reference remains separately available and licensed.')
    table([['Shared item','Controlled setting'],['Media','2s full segments;60s loop; video-only runtime MPD;8 representations'],['Playback','3s target; LoL+ catch-up; playback-rate range0.83-1.17;5s excess-delay seek'],['Readiness','Preload dependencies before Load; cold setup reported separately'],['Clock','Explicit hostClock=1 for verified single-WSL-host emulation only']],[110,377])

    page();h('3. What the original CMAB actually optimizes')
    p('The controller refits a scaler and a new linear Thompson sampler from the current slot\'s observations. Its three fitted features are throughput, playback rate and legacy RTT. Buffer and live delay are absent from this context, although delay appears in its reward. History clears at seconds12,27,42 and57. The next seven decision callbacks select the highest representation; these callbacks are not necessarily seven distinct completed downloads.')
    p('<b>Original internal reward:</b> r = O46 x (target delay/current delay) x (selected nominal bitrate/maximum nominal bitrate) - selected-bitrate stall share. The single-segment P.1203 input supplies an empty stalling list, and the new choice is scored before its download completes. This limits the supplied reward/attribution mechanism; it is not a claim that P.1203 itself cannot model stalling.')
    figure('F2-cmab-timeline.png','Figure2. Exploratory development timeline: selected actions, not necessarily played quality. Early development used external UTC setup; timing/source-phase variability prevents treating each local difference as an isolated causal estimate.')
    table([['Hypothesis','Implementation question','Development conclusion'],
        ['H1 memory','Keep30 observations instead of slot-only history','Memory alone did not consistently help.'],
        ['H2 restart','One conservative restart choice instead of7 highest choices','Useful improvement; confirm through selected combination.'],
        ['H3 feedback','Link the original state/action to one completed request','Explicit outcome surrogate helped; censoring remains.'],
        ['H4 context','Buffer, delay and fresh/missing RTT information','Mixed feature effects; context alone failed a validation playback gate.'],
        ['H5 estimation','Fixed physical scaling+bias; exploration seed variant','Zero-centered score degeneracy verified; reseeding not promoted.'],
        ['H6 safety','Clip aggressive proposals to a measured safe ceiling','Strong improvement; guard alone remains competitive.']],[66,202,219])

    page();h('4. Selected CMAB refinement and ablations')
    p('The selected controller retains an online LinTS learner with up to30 matched completed outcomes, alpha1 and seed123456. Its9-vector contains a bias, throughput, playback rate, valid RTT, buffer, live delay, probe validity, last-success age and recent valid RTT change. Fixed physical scaling avoids mixing accumulated history with a moving scaler. Missing RTT is masked and aged, not silently treated as a fresh zero-delay observation.')
    p('Each request object can consume only one matching decision, and duplicate completion cannot train it twice. Initial/unmatched, seek-cancelled, errored and abandoned transfers are recorded but censored. The update uses the original decision context. This is completed-request feedback with selection bias, not perfect causal attribution of all subsequent stalls.')
    p('<b>Download surrogate:</b> log(b/300kbps) x segment_s/2 -4 max(0,transfer_s-buffer_at_choice) -0.3 |log(b/previous_b)| -0.1 max(0,outcome_delay-target) x transfer_s. It rewards nominal quality and penalizes buffer-budget starvation, variation and delay. The common final score is independently computed from actual playback.')
    p('A startup choice uses measured throughput conservatively. The guard clips proposals to the highest nominal rate below throughput x0.55 when buffer&lt;1s, live delay&gt;target+2s or the probe is invalid; otherwise it uses x0.85. It cannot guarantee no stall when even the lowest representation exceeds delivery capacity. Guard-only always chooses this ceiling and also replaces forced startup choices, so it is not a pure removal of learning.')
    figure('F6-validation-components.png','Figure3. Corrected-clock validation, one session per case/policy. The first five families select the candidate; mixed stress is separate. Guarded CMAB passed unchanged useful-playback/stall/delay/startup gates. Guard-only scored slightly higher, so incremental benefit from the bandit/restart package is not established.')
    p('A real exported8-row online-state example reproduced proposal6 and clipped action6 in the pinned browser runtime. The context vector alone is insufficient to replay an online bandit: its fitted action/reward history also matters. Full configurations and negative ablations are retained in T5 and the source audit.','SmallBody')

    page();h('5. Data and neural training workflow')
    p('RTT traces contain no synchronized capacity or optimal-action labels, so we build seeded network scenarios and collect real-player outcomes. Seychelles is split into training 0-2088 s, validation 2148-2844 s and test 2904-3600 s, with 60 s guards. Neural preparation uses 48/18/18 generated cases. Browser development/validation use six cases each; final testing uses ten cases from Seychelles and a second public LENS RTT session from Victoria. Related windows and generated capacity/outages are not independent measured full-link recordings.')
    table([['Actor','Causal observations','Architecture'],['Conventional','8 completed-transfer rows x4; buffer, previous rate, playback rate, target','36 ->64 ReLU ->64 ReLU ->8'],['LEO-aware','Conventional36 +8 RTT rows x3 +live delay, success age, valid flag, failure fraction','64 ->64 ReLU ->64 ReLU ->8']],[79,260,148])
    p('RTT rows contain successful RTT, measurement age and success flag; only mature past probes are exposed. No actor/critic input includes future capacity, future RTT, outage labels, scenario identity or unavailable future SSIM. Normalization uses fixed physical constants. Conventional playback rate can indirectly reflect delay; the extension adds RTT freshness and explicit live delay together, not RTT alone.')
    p('Both actors use SB3 A2C, identical hidden layers, gamma0.99, eight environments and the same reward/scenarios. An8000-state training-only causal teacher initialization is followed by RL. Four learning-rate/rollout/entropy settings are screened with two seeds and250k decisions each, totaling about4million decisions. One joint validation recipe is then used for five seeds per actor at1million decisions each. Checkpoints maximize equal-family validation QoE; the median-validation seed represents each actor in Chrome. Optimizer, RNG and environment snapshots support continuation.')
    figure('F7-neural-training.png','Figure4. Neural validation curves across five seeds. Bands are min-max seed ranges, not confidence intervals. Step0 is imitation initialization, and circles identify the predeclared median-validation representatives.')
    p('The released ten-action network is not silently truncated to eight actions. Export contains the trained actor only, with Float32 dense/ReLU operations and deterministic argmax. Native/JS fixtures and actual Chrome decisions verify the mapping. Inference stays synchronous; cached network measurements may refresh asynchronously, but no Promise is returned to dash.js.','SmallBody')

    page();h('6. Calibration, metrics and frozen methodology')
    figure('F8-calibration.png',f'Figure5. Development calibration. Transfer median error {100*calibration["median_transfer_relative_error"]:.1f}%; buffer MAE {calibration["buffer_mae_s"]:.2f}s. Overall live-delay MAE {calibration["latency_mae_s"]:.2f}s misses the1s target; the overloaded no-playback case remains included. Playable-case delay MAE {calibration["playable_cases_latency_mae_s"]:.2f}s is a diagnostic subset, not an exclusion rule.')
    p('Actual segment bytes, full-segment availability, initial partial segments,500ms source retry scheduling and partial catch-up seeks are modeled. Fixed-policy development requests fit phenomenological payload/RTT transport constants; adaptive cases are not used for that fit. TCP retransmission tails and exact browser no-playback seek timing remain approximate. The simulator trains/screens candidates; it does not replace the deployed comparison.')
    p('<b>Common score:</b> QoE = [Q -4B -S -0.3V -0.1A]/T. Q integrates log(nominal bitrate/300kbps) over actually played media seconds, divided by2s; B is rebuffering seconds after startup; S is startup seconds; V sums played-quality log changes; A integrates max(0,live delay-3s) over wall time. Automatic catch-up wait remains in B. Deliberate user interactions are absent. Nominal bitrate is a declared quality proxy, not MOS, SSIM or VMAF.')
    p('We freeze source/model/config/workload identities, case weights, order, repeats and selection before opening test performance. The controlled matrix has10 cases x7 policies x2 repeats, plus a third repeat for original/guarded/guard-only CMAB on every case:170 sessions at120s. The separate author-repository raw replay has3 policies x3 repeats at180s:9 sessions. Total179. All five required families receive equal weight; each has two fixed cases. Policies run sequentially in balanced order with fresh state and matched minute/source/reset phase.')
    p('Paired comparisons match case and repeat. Intervals keep the10 cases fixed and resample paired browser repeats within each case. Related source windows are not treated as independent recordings. These conditional intervals describe repeatability on this suite, with only2-3 repeats per policy/case; they do not establish population-wide Starlink generalization. Algorithm-caused no playback remains a result. Clock/cutoff or link-identity faults are retained and classified before retrying, rather than dropping unfavorable performance.')
    p('Original code uses external UTC timing, which produced variable delays before any ABR decision. A shared, explicitly enabled single-host clock option removes that confound; remote-client defaults remain unchanged. Dependencies are prewarmed for all policies, with setup cost measured separately. The original controller logic and legacy RTT scalar are preserved; shared lifecycle/parser/measurement repairs are documented.','SmallBody')

    page();h('7. Held-out browser results')
    figure('F3-overall-paired.png','Figure6. Paired effects on ten held-out fixed cases. Intervals resample paired repeats conditionally on the fixed cases; neither segments nor related windows become independent Starlink recordings. Positive QoE differences favor the new method.')
    table([['Policy','QoE/s','Stall s','Start s','Played Mbps','Switches','Mean L s','p95 L s']]+[[{'original':'CMAB','improved':'Guarded CMAB','guard_only':'Guard only','throughput':'Throughput','bola':'BOLA','conventional':'Conv. A2C','leo':'LEO A2C'}[r['policy']],f'{r["qoe_per_wall_s"]:.3f}',f'{r["stall_s"]:.1f}',f'{r["startup_s"]:.2f}',f'{r["played_bitrate_bps"]/1e6:.2f}',f'{r["switches"]:.1f}',f'{r["mean_live_latency_s"]:.2f}',f'{r["p95_live_latency_s"]:.2f}'] for r in result['overall']],[88,49,49,49,69,58,62,63])
    p('Equal family/case weights apply to session statistics. The p95 column is the mean of session p95 delays, not a pooled percentile. Played Mbps weights observed nominal rates by media actually watched within each session.','SmallBody')
    table([['Playback coverage','Played media s','Skipped media s']]+[[{'original':'CMAB','improved':'Guarded CMAB','guard_only':'Guard only','conventional':'Conv. A2C','leo':'LEO A2C'}[r['policy']],f'{r["played_media_s"]:.1f}',f'{r["skipped_media_s"]:.1f}'] for r in result['overall'] if r['policy'] in ['original','improved','guard_only','conventional','leo']],[243,122,122])
    p(f'The primary guarded-CMAB effect is {effect["mean_difference"]:+.3f} QoE/wall-s, with interval [{effect["ci95_low"]:+.3f}, {effect["ci95_high"]:+.3f}] and positive case-mean effects in {effect["positive_cases"]}/10 cases. Mean stalls change from {baseline["stall_s"]:.1f} to {candidate["stall_s"]:.1f}s ({stall_reduction:.1f}% reduction). Played nominal bitrate changes from {baseline["played_bitrate_bps"]/1e6:.2f} to {candidate["played_bitrate_bps"]/1e6:.2f}Mbps; this quality/stall tradeoff is part of the result, not hidden by the score.')
    p('The guard-only and neural rows must be interpreted alongside their components and coverage. An improved aggregate does not by itself prove that extra context, learning or a larger model caused the gain. Validation ablations support mechanisms; the final suite measures the frozen complete controllers. Per-run rows, paired effects and every underlying portable event stream are released.')

    page();h('8. Scenario effects, robustness and limitations')
    figure('F4-family-effects.png','Figure7. Effects by the five required scenario families. Lower stalls and live delay are favorable even though those panels plot negative differences.')
    sub('Separate author-repository replay')
    table([['Policy','QoE/s','Stall s','Mean live delay s']]+[[r['policy'],f'{r["qoe_per_wall_s"]:.3f}',f'{r["stall_s"]:.1f}',f'{r["mean_live_latency_s"]:.2f}'] for r in result['raw_replay']],[139,100,100,148])
    p('Raw replay follows the distributed shaper:20Mbps, measured delay,1% loss for positive RTT and100% for nonpositive RTT. The paper\'s stated emulator profile instead uses40ms/0.1% background and100ms/1% handover periods. We therefore label this a repository replay, not exact reproduction of the publication\'s emulator settings. Archived author-figure regeneration remains a separate Phase A artifact.')
    sub('Robustness and what the evidence cannot show')
    primary_sensitivity=[r['differences']['improved'] for r in result['sensitivity']]
    p(f'One-at-a-time0.5x/2x rescoring of stall, variation and excess-delay coefficients gives guarded-CMAB differences ranging from {min(primary_sensitivity):+.3f} to {max(primary_sensitivity):+.3f} QoE/wall-s. These coefficients are not chosen from test outcomes. Recovery uses actual applied interruption times and requires2s of sustained playback; censored recoveries remain explicit.')
    p('Only two measured RTT sessions underpin the browser suite; capacity and interruptions are generated. Probe failure is a disruption proxy, not confirmed satellite handover ground truth. The nominal4.9Mbps representation actually averages about3.18Mbps; all transfer dynamics use encoded bytes while quality utility deliberately uses nominal rates. Completed-only bandit updates omit cancelled/unmatched actions. Small repeat counts, source-window dependence, simulator gaps and virtualized desktop Chrome limit broader conclusions.')
    p('The same catch-up settings, video and shaper are shared. Native throughput/BOLA include their configured built-in auxiliary rules; custom CMAB/neural paths retain their source rule structure. The primary original-versus-improved CMAB comparison is therefore the strongest controlled attribution. No mobile-device latency, subjective video-quality or production Starlink deployment claim is made.')

    page();h('9. Playback mechanism and least favorable case')
    figure('F5-post_handover_recovery.png','Figure8. Predeclared Seychelles recovery case, repeat0. Curves show actual played nominal bitrate, buffer and live delay. Large media-time jumps from catch-up seeks are not credited as watched video.',width=470)
    worst=result['worst_improved_case']
    p(f'The least favorable guarded-CMAB case is <b>{escape(worst["case_id"])}</b>, with paired QoE difference {worst["difference"]:+.3f}. Its trajectory is supplied as F5-worst-case alongside the predeclared capacity-change case. This preserves an informative regression or smallest gain instead of selecting only attractive traces.')
    p('The mechanism question is whether aggressive requests drain the short live buffer faster than the link can refill it. Conservative restarts and ceilings trade nominal quality for fewer long stalls and seeks. Retaining memory, adding context or fitting a bandit is not automatically beneficial. The guard-only control prevents attributing a heuristic gain to learning without evidence.')

    page();h('10. Reproduction, deployment and conclusions')
    p('Repository: <link href="https://github.com/raj-gigt/mmsys24-starlink-livestreaming/tree/anjan" color="#128C86">github.com/raj-gigt/mmsys24-starlink-livestreaming/tree/anjan</link>. The parent pins the published team dash.js fork. The release includes exact required player source, native checkpoints, synchronous actors, normalization/action contracts, configurations, compact raw evidence and all figure/table scripts. The release manifest records file hashes; the evaluation freeze records the measured identities.')
    publication=json.loads((ROOT/'artifacts/final/evaluation/publication.json').read_text())
    p(f'Measured source publication: parent {publication["published_parent_source_revision"][:8]}, player {publication["player_revision"][:8]}. Freeze SHA256: {publication["freeze_sha256"]}. The freeze\'s older parent Git anchor predates source publication; publication.json and canonical file hashes identify the measured contents. Later report/release commits are separate.','SmallBody')
    table([['Reproduction level','Entry point'],['Saved results','python scripts/reproduce_final.py --saved-results'],['Training','python -m rl.train_final --stage screen; then --stage main'],['Testbed','bash scripts/testbed.sh up (Docker/WSL or Linux; pinned images)'],['Demo','python scripts/demo_final.py --policy improved; compare --policy original'],['Full new evaluation','Freeze a new output inventory; run_final_matrix.py resumes the submitted frozen inventory without changing completed evidence']],[105,382])
    cpu=json.loads((ROOT/'artifacts/final/calibration/benchmark-cpu.json').read_text());gpu=json.loads((ROOT/'artifacts/final/calibration/benchmark-cuda.json').read_text())
    p(f'The actual eight-environment benchmark averages {sum(r["steps_per_s"] for r in cpu["runs"])/len(cpu["runs"]):.0f} decisions/s on CPU versus {sum(r["steps_per_s"] for r in gpu["runs"])/len(gpu["runs"]):.0f} on the RTX4060 laptop GPU. CPU was selected for this small MLP. Training logs report measured wall time rather than an assumed multi-hour estimate. Browser inference runs on the Chrome host CPU in the JavaScript main thread; CMAB uses the existing synchronous Pyodide route. Timing results are observed host measurements, not hard deadlines or mobile guarantees.')
    deployment=json.loads((ROOT/'artifacts/final/evaluation/deployment.json').read_text())['runs']
    table([['Actor','Params','Timed calls','p50 ms','p95 ms','Max ms','Fallbacks']]+[[{'conventional':'Conv. A2C','leo':'LEO A2C'}[r['policy']],r['actor_parameters'],r['timed_fresh_decisions'],f'{r["fresh_p50_ms"]:.2f}',f'{r["fresh_p95_ms"]:.2f}',f'{r["fresh_max_ms"]:.2f}',r['neural_fallbacks']] for r in deployment if r['policy'] in ['conventional','leo']],[82,53,67,67,67,66,85])
    p('Table T8 records final-browser fresh decision spans, cold page/assets and Pyodide prewarm separately. Cache hits are excluded above. CMAB controller timings omit outer-rule/feedback work and are not used for a direct speedup ratio. T7 supplies metric units and sampling details.','SmallBody')
    p(('The frozen browser comparison supports an improvement over the reference CMAB on this declared suite.' if positive else 'The frozen browser comparison does not establish the intended aggregate improvement over the reference CMAB.')+' The main contribution is a traceable implementation study with controlled deployment and explicit tradeoffs. Neural training, portable evidence and a real playback demo complement that study. Wider measured bandwidth/RTT sessions, better cancellation credit and more accurate transport modeling are appropriate future work; an asynchronous runtime bridge is outside this project scope.')
    sub('References and attribution')
    for text in [
        '[1] J. Zhao and J. Pan. Low-Latency Live Video Streaming over a Low-Earth-Orbit Satellite Network with DASH. ACM MMSys2024. doi:10.1145/3625468.3647616.',
        '[2] Reference implementation: github.com/clarkzjw/mmsys24-starlink-livestreaming; team fork and exact revisions are recorded in release/freeze manifests.',
        '[3] H. Mao, R. Netravali and M. Alizadeh. Neural Adaptive Video Streaming with Pensieve. SIGCOMM2017. doi:10.1145/3098822.3098843. web.mit.edu/pensieve/.',
        '[4] S. Patel et al. Plume: A Framework for High Performance Deep RL Network Controllers via Prioritized Trace Sampling. arXiv:2302.12403. github.com/sagar-pa/plume.',
        '[5] Released Maguro reference: github.com/sagar-pa/abr_rl_test, pinned b9c4069; native metadata and action incompatibilities documented in models/reference/manifest.json.',
        '[6] MABWiser API and installed2.7.0 source; fidelity.github.io/mabwiser/api.html. SB3 A2C and RL guidance: stable-baselines3.readthedocs.io.',
        'Licenses: parent GPLv3; dash.js BSD headers retained; Sagar Patel reference MIT. Croatia2019 video is credited to EBU/CTA under CC-BY4.0. LENS dataset attribution/license and source hashes are retained in data manifests.']:
        p(escape(text),'SmallBody')
    path=OUT/'Group4-final-report.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=54,leftMargin=54,topMargin=43,bottomMargin=48,
        title=project['submission_title'],author='Group4 - Anjan R D, Rajat Dugar, Deviprasad V K')
    doc.build(STORY,onFirstPage=footer,onLaterPages=footer);print(path)

if __name__=='__main__':main()
