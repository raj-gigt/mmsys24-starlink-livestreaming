/** Build the eight-slide final deck from verified artifacts, using ArtifactTool.
 * Environment: LEO_ARTIFACT_RUNTIME = bundled dependencies directory;
 * LEO_PRESENTATION_SKILL = presentations skill directory;
 * LEO_DECK_BUILD = private external build directory (not inside the project).
 * Run using the bundled Node executable. No substitute presentation library.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const RUNTIME=process.env.LEO_ARTIFACT_RUNTIME;
const SKILL=process.env.LEO_PRESENTATION_SKILL;
const BUILD=process.env.LEO_DECK_BUILD;
if(!RUNTIME || !SKILL || !BUILD) throw new Error('Set the three LEO_* authoring paths documented in this source');
if(path.resolve(BUILD).startsWith(ROOT+path.sep)) throw new Error('Use a private build directory outside the project');
process.env.RUNTIME_NODE_MODULES ||= path.join(RUNTIME,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(RUNTIME,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const read=async p=>JSON.parse(await fs.readFile(path.join(ROOT,p),'utf8'));
const result=await read('artifacts/final/evaluation/analysis.json');
if(result.sessions!==179)throw new Error('Final results are incomplete');
const project=await read('configs/final/project.json');
const selection=await read('artifacts/final/training/main-selection.json');
const font=resolvePresentationFont({fontFamily:'Arial'});
const C={navy:'#263B58',teal:'#128C86',gray:'#7B8796',blue:'#4C78A8',amber:'#C17A18',ink:'#263342',light:'#E3E9EF',white:'#FFFFFF'};
const labels={original:'Original CMAB',improved:'Guarded CMAB',guard_only:'Guard only',throughput:'Throughput',bola:'BOLA',conventional:'Conv. A2C',leo:'LEO A2C'};
const colors={original:C.gray,improved:C.teal,guard_only:C.amber,throughput:'#8C6BB1',bola:'#A65F55',conventional:C.blue,leo:'#1B566D'};
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
let n=0;
function text(slide,value,x,y,w,h,size=25,color=C.ink,bold=false){
  const s=slide.shapes.add({name:'text-'+(++n),geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=value;s.text.style={fontFamily:font,fontSize:size,color,bold};return s;
}
function slide(title,notes){
  const s=presentation.slides.add();s.background.fill=C.white;
  text(s,title,64,42,1152,66,43,C.navy,true);
  text(s,'CS6048  |  Group 4',64,676,500,24,15,C.gray);
  text(s,String(presentation.slides.items.length).padStart(2,'0')+' / 08',1130,676,90,24,15,C.gray);
  s.speakerNotes.text=notes;return s;
}
function nativeTable(s,values,x,y,width,height,columnWidths,size=23){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths,values});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
    const cell=t.getCell(r,c);cell.text.style={fontFamily:font,fontSize:size,color:r===0?C.navy:C.ink,bold:r===0};
    cell.fill=r===0?'#EEF3F6':C.white;
  }
  return t;
}
function chart(s,type,config){
  const base={chartFill:'none',chartLine:{fill:'none',width:0},plotAreaFill:'none',plotAreaLine:{fill:'none',width:0},
    xAxis:{textStyle:{typeface:font,fontSize:20,fill:C.ink},line:{fill:C.light,width:1}},
    yAxis:{textStyle:{typeface:font,fontSize:20,fill:C.ink},numberFormatCode:'0.0',majorGridlines:{fill:C.light,width:1}},
    legend:{position:'bottom',textStyle:{typeface:font,fontSize:20,fill:C.ink}}};
  const ch=s.charts.add(type,{...base,...config,xAxis:{...base.xAxis,...config.xAxis},yAxis:{...base.yAxis,...config.yAxis}});
  applyPresentationChartFont(ch,{fontFamily:font});return ch;
}
const overall=Object.fromEntries(result.overall.map(r=>[r.policy,r]));
const effect=result.paired.improved;
const reduction=100*(overall.original.stall_s-overall.improved.stall_s)/overall.original.stall_s;
const fmt=(v,d=2)=>Number(v).toFixed(d);
const signed=(v,d=2)=>(v>=0?'+':'')+fmt(v,d);

// 1: exact proposal/team identity, mandatory ABR scope only.
{
  const s=slide('LEO-Aware Live Video Streaming','Cover: mandatory ABR scope from configs/final/project.json and the proposal. Assigned speaking domains are not statements of completed individual contributions.');
  text(s,'RL-Based Adaptive Bitrate Selection',64,137,1130,88,47,C.navy,true);
  text(s,'CMAB refinements and a compatible actor-critic comparison',64,260,1090,80,31,C.teal);
  text(s,'Modern Networking Methods (Beyond TCP & IP)\nFinal project  |  November 2026',64,390,1110,78,27,C.ink);
  text(s,project.members.map(m=>m.name+'  ·  '+m.roll).join('\n'),64,505,1080,125,25,C.ink);
}
// 2: reference mechanism; reuse the source-backed technical diagram.
{
  const s=slide('Reference system and CMAB policy','Sources: upstream README and assets/Emulation-Testbed.png (supplied project diagram); reports/final/cmab-audit.md; pinned CMABAbrController.js and CMABRule.js; Zhao & Pan, MMSys2024, doi:10.1145/3625468.3647616. Original reward uses an immediate single-segment P1203 proxy, not observed eventual playback. This criticism concerns its use here, not P1203 generally.');
  s.images.add({path:path.join(ROOT,'assets/Emulation-Testbed.png'),alt:'Supplied README diagram of the Docker emulator',fit:'contain',position:{left:54,top:136,width:670,height:370}});
  text(s,'Original policy',768,137,435,45,29,C.teal,true);
  text(s,'LinTS: throughput, playback rate and legacy RTT\n\n15 s resets; first 7 callbacks force the highest quality',768,195,435,164,25);
  text(s,'Chrome → Nginx/tc → live source',64,536,650,43,29,C.navy,true);
  text(s,'Same services and media; our build copies the modified player source.',64,594,650,64,25);
  text(s,'Immediate reward proxy',768,380,435,42,28,C.teal,true);
  text(s,'O46 × target/L × bitrate/max\n− selected-quality stall share',768,436,435,85,24);
  text(s,'Weak outcome attribution\nMissing buffer and RTT health',768,560,435,81,25,C.ink);
}
// 3: native editable evidence table; keep the guard-only caveat visible.
{
  const s=slide('CMAB changes and validation evidence','Sources: configs/final/cmab-interface.json; models/final/cmab/manifest.json; artifacts/final/validation/finalists-v2/selection.json; T5 validation/development CSVs. Cold/warm exploratory development had external UTC confounding, so it is not a clean causal effect estimate. Guard-only also replaces forced startup choices; it is not a pure learning removal.');
  nativeTable(s,[['Mechanism','Implemented change'],
    ['Restart / memory','Conservative restart; retain 30 matched outcomes'],
    ['Feedback','One decision → one completed request; explicit surrogate'],
    ['Context','9 scaled inputs, including buffer, delay and RTT health'],
    ['Safety','Clip aggressive proposals to a throughput ceiling']],64,139,1150,336,[310,840],25);
  text(s,'Validation selected the guarded controller; memory alone did not help.',64,509,1135,62,27,C.teal,true);
  text(s,'Guard-only remained competitive. Extra benefit from the bandit/restart package is not established.',64,586,1135,64,25,C.ink);
}
// 4: native line chart from all five seeds, no invented result values.
{
  const s=slide('Neural adaptation and training','Sources: rl/final_env.py, rl/train_final.py, configs/final/neural-interface.json, artifacts/final/training/main/*/curve.json and main-selection.json. Compatible A2C inspired by Pensieve/Gelato/Plume, not their unchanged published weights. Means below are descriptive across five seeds, not confidence intervals. Main training actual44.33min CPU; screen4.004m plus main10.004m interactions. Validation peak selection precedes final testing.');
  const seedCurves={};for(const kind of ['conventional','leo']){
    seedCurves[kind]=[];for(const seed of [47,71,101,131,167])seedCurves[kind].push(await read(`artifacts/final/training/main/${kind}-${seed}/curve.json`));
  }
  const xs=seedCurves.conventional[0].map(r=>r.steps);
  function interp(curve,x){let a=curve[0];for(const b of curve){if(b.steps>=x)return b.steps===a.steps?b.validation_qoe:a.validation_qoe+(b.validation_qoe-a.validation_qoe)*(x-a.steps)/(b.steps-a.steps);a=b;}return a.validation_qoe;}
  chart(s,'line',{position:{left:55,top:162,width:745,height:425},categories:xs.map(x=>fmt(x/1e6,1)),
    series:['conventional','leo'].map(kind=>({name:labels[kind],values:xs.map(x=>seedCurves[kind].reduce((a,c)=>a+interp(c,x),0)/5),line:{fill:colors[kind],width:3},marker:{symbol:'none'}})),
    hasLegend:true,xAxis:{title:'Collected decisions (millions)'},yAxis:{title:'Validation QoE / wall s'}});
  text(s,'36 vs 64 causal inputs\n64 → 64 hidden layers\n8 discrete bitrates',840,157,372,157,28,C.navy,true);
  text(s,'5 fresh seeds per model\n10.004m main decisions\n44.3 min measured CPU',840,353,372,141,25);
  text(s,'Best validation checkpoint, then median seed. Late decline retained.',840,523,372,100,25,C.teal);
  text(s,'Same recipe / reward / scenarios; added LEO inputs are a bundle, not an isolated RTT effect.',64,622,1145,36,21,C.gray);
}
// 5: source/measurement constraints, with concise editable protocol table.
{
  const s=slide('Data and controlled evaluation','Sources: data/manifests, configs/final/protocol.json, configs/final/workloads/test.json, freeze.json and rl/metrics.py. Only two measured RTT recordings; capacity/outages generated. Conventional inputs can indirectly reflect delay via playback rate. Native throughput/BOLA retain their configured auxiliary rules; primary original-vs-improved comparison is strongest. 170controlled +9repository replay179.');
  nativeTable(s,[['Shared protocol','Setting'],['Network / data','Seychelles + Victoria RTT (LENS); generated capacity / outages'],
    ['Controlled suite','5 families × 2 cases; 120 s per session'],['Policies / repeats','7 policies; 2 repeats, 3 for CMAB / improved / guard only'],
    ['Player / source','Same video, 8 bitrates, 2 s segments, 3 s target, LoL+'],['Independent score','Actually played quality, stalls, startup, changes, delay']],64,142,1150,358,[310,840],24);
  text(s,'QoE / wall s = (Q − 4B − startup − 0.3V − 0.1A) / duration',64,528,1150,59,29,C.teal,true);
  text(s,'RTT alone lacks capacity and bitrate outcomes: use fixed scenarios and real player logs.\n170 controlled sessions + 9 separate replays; no final-test tuning.',64,605,1150,64,24);
}
// 6: final means and the primary conditional interval, all sourced dynamically.
{
  const s=slide('Held-out performance against original CMAB','Source: artifacts/final/evaluation/analysis.json and T4-paired-effects.csv. Native bars show equal-family paired mean effects. The primary interval resamples matched browser repeats within each fixed case; it does not resample related windows as independent Starlink recordings. Full ten raw case points and intervals for all policies appear in report Figure6 / F3. No result-based policy changes were made.');
  const compare=['improved','guard_only','throughput','bola','conventional','leo'];
  chart(s,'bar',{position:{left:52,top:153,width:780,height:448},categories:compare.map(p=>labels[p]),
    series:[{name:'Paired QoE difference / wall s',values:compare.map(p=>result.paired[p].mean_difference),fill:C.teal,
      points:compare.map((p,idx)=>({idx,fill:colors[p]}))}],hasLegend:false,
    barOptions:{direction:'column',grouping:'clustered',gapWidth:90},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{typeface:font,fontSize:21}},
    yAxis:{title:'Paired QoE difference / wall s'},xAxis:{textStyle:{fontSize:18,typeface:font}}});
  text(s,signed(effect.mean_difference,3),867,155,340,76,58,C.teal,true);
  text(s,'Primary QoE effect\n95% conditional interval\n['+signed(effect.ci95_low,3)+', '+signed(effect.ci95_high,3)+']',867,238,340,131,25);
  text(s,fmt(overall.original.stall_s,1)+' → '+fmt(overall.improved.stall_s,1)+' s stalls\n'+fmt(overall.original.played_bitrate_bps/1e6,2)+' → '+fmt(overall.improved.played_bitrate_bps/1e6,2)+' Mbps played',867,414,340,117,26,C.navy,true);
  text(s,effect.positive_cases+'/10 positive case means',867,564,340,46,25);
  text(s,'Intervals describe repeatability on fixed cases; quality utility is nominal bitrate, not subjective quality.',64,624,1150,36,21,C.gray);
}
// 7: scenario heterogeneity; native grouped data, not a screenshot of a chart.
{
  const s=slide('Scenario effects and claim boundaries','Sources: analysis.json paired cases and raw_replay; simulator comparison.json. This chart averages paired case effects within each family. Raw replay uses the distributed measuredRTT/1%loss shaper, distinct from paper40ms/.1% background and100ms/1% handover profile. Main limitations: two RTT sessions, generated capacity, completed-only CMAB feedback, no confirmed handover truth, approximate simulator (all-case delayMAE2.06s).');
  const families=['steady_bandwidth','bandwidth_variation','rtt_variation','handover_interruption','post_handover_recovery'];
  chart(s,'bar',{position:{left:53,top:137,width:1160,height:365},categories:['Steady','Capacity','RTT','Interruption','Recovery'],
    series:['improved','guard_only','leo'].map(p=>({name:labels[p],fill:colors[p],values:families.map(f=>{
      const cases=result.paired[p].cases.filter(c=>c.family===f);return cases.reduce((a,c)=>a+c.difference,0)/cases.length;
    })})),hasLegend:true,barOptions:{direction:'column',grouping:'clustered',gapWidth:80},yAxis:{title:'Paired QoE difference / wall s'}});
  const raw=Object.fromEntries(result.raw_replay.map(r=>[r.policy,r]));
  text(s,'Separate repository replay: CMAB '+fmt(raw.original.qoe_per_wall_s,3)+' → guarded '+fmt(raw.improved.qoe_per_wall_s,3)+' QoE/s',64,531,1150,44,26,C.teal,true);
  text(s,'Two RTT recordings; generated bandwidth/outages. Simulator delay error: 2.06 s overall.\nGuard-only isolates a competitive heuristic, not a pure removal of learning.',64,593,1150,67,24);
}
// 8: evidence-backed takeaway and a real restartable demo, no fake contributions.
{
  const s=slide('Conclusions, demo and reproduction','Sources: analysis.json, reports/final/reproduction.md, scripts/demo_final.py, configs/final/project.json. Assigned speaking domains shown here are not actual completed contribution statements; the report deliberately retains the requested blank template. Real demo uses a90-second development recovery case and does not add to final performance evidence. Human rehearsal and portal upload remain human tasks.');
  text(s,effect.mean_difference>0?'Guarded CMAB improves this declared test suite':'The declared suite does not establish the intended CMAB gain',64,141,1145,76,35,C.teal,true);
  text(s,'Inspect the quality / stall tradeoff and guard-only control.\nNeural results are a compatible retrained comparison, not published pretrained weights.',64,248,1145,96,27);
  text(s,'Real demo: original vs guarded CMAB on the same recovery case\nRecorded playback and raw evidence are included as a fallback.',64,385,1140,93,27,C.navy,true);
  text(s,'python scripts/demo_final.py --policy improved\npython scripts/reproduce_final.py --saved-results',64,503,1140,74,24,C.ink);
  text(s,'Rajat: integration / builds   ·   Anjan: algorithms / training   ·   Deviprasad: evaluation',64,612,1145,45,22,C.gray);
}

await fs.mkdir(path.join(BUILD,'draft'),{recursive:true});await fs.mkdir(path.join(BUILD,'output'),{recursive:true});
const candidate=path.join(BUILD,'draft/candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const stamp=new Date().toISOString().replace(/[:.]/g,'-');
const finalPath=path.join(BUILD,'output','Group4-final-'+stamp+'.pptx');
await finalizePresentation({workspaceDir:BUILD,candidatePath:candidate,finalPath,
  pythonExecutable:path.join(RUNTIME,'python/python.exe'),
  integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
  explicitTotalSlideCount:8,requiredNativeTableOwnerSlides:[3,5],requiredNativeChartOwnerSlides:[4,6,7],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[font]},
  verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation-'+stamp+'.json')});
const finalPresentation=await Presentation.load(finalPath);
for(const [i,s] of finalPresentation.slides.items.entries()){
  const png=await finalPresentation.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(BUILD,'slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
}
await fs.copyFile(finalPath,path.join(ROOT,'reports/final/Group4-final-presentation.pptx'));
console.log(JSON.stringify({status:'created_pending_visual_review',slides:8,finalPath,previewDirectory:BUILD}));
