"""Explicit release roots plus audited Python import closure; no development-tree copy."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

ENTRY_SCRIPTS=['reproduce_final.py','analyse_final.py','analyse_final_contrasts.py','analyse_four_policies.py',
 'summarize_final_deployment.py','prepare_player.py','browser_trial.py','freeze_final.py','run_final_matrix.py',
 'experiment_clock.py','prepare_data.py','prepare_final_workloads.py','plot_final_architecture.py',
 'plot_cmab_ablation.py','plot_cmab_validation.py','select_cmab_final.py','build_final_report.py',
 'build_submission.py','submission_inventory.py','verify_submission.py','verify_remote_publication.py','archive_final_runs.py']

def inventory():
    files={};missing=[];queue=[]
    def add(name,category,reason,required=True):
        path=ROOT/name
        if not path.is_file():
            if required:missing.append(name)
            return
        if name not in files:
            files[name]={'category':category,'reason':reason}
            if path.suffix=='.py':queue.append(path)
    def tree(name,category,reason):
        for p in sorted((ROOT/name).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':add(p.relative_to(ROOT).as_posix(),category,reason)
    frozen=json.loads((ROOT/'artifacts/final/evaluation/freeze.json').read_text())
    for name in frozen['sources']:add(name,'measured_source','Required unchanged measured source/config or player-build snapshot')
    for name in ENTRY_SCRIPTS:add('scripts/'+name,'entry_point','Saved-results, build, data, analysis or experiment command')
    for name in ['train_final','final_env','pilot_env','features','warmstart','export_final','export_layers','metrics','recovery','evidence','decision_validation','__init__']:
        add('rl/'+name+'.py','training_or_metrics','Final training/export/metric dependency; pilot_env is an active base class')
    for name in ['README.md','release/report-check.json','release/component-check.json','scripts/testbed.sh','scripts/check_final_export.cjs','Dockerfile-runner','Dockerfile-nginx-emulation',
        'requirements-results.txt','requirements-report.txt','.dockerignore','.gitattributes','.gitmodules',
        'pyproject.toml','poetry.lock','LICENSE','dash.js/LICENSE.md','dash.js/package.json',
        'runner/trace/isl-trace.csv','runner/trace/irtt/seychelles-irtt-10ms-1h-2024-01-30-01-00-00.csv',
        'experiments/batch-example.json','shaper/tc-phase-a.py','shaper/entrypoint.sh','shaper/supervisord.conf',
        'rl/reference/LICENSE.abr_rl_test']:
        add(name,'build_data_license','Referenced build configuration, raw verification/data input or retained attribution')
    for p in (ROOT/'runner').glob('*.py'):add(p.relative_to(ROOT).as_posix(),'inherited_build','Upstream runner Dockerfile source dependency')
    for name in ['stats-server','etc','data/manifests','data/processed','configs/final','models/final']:
        tree(name,'runtime_data_configuration','Final service/configuration, processed data, model contracts/weights')
    for p in (ROOT/'reports/final/tables').glob('*.csv'):add(p.relative_to(ROOT).as_posix(),'result_table','Compact scientific results or metric/contribution definitions')
    figures=['F1-system','F3-four-policy','F4-four-policy','F5-four-policy-regression','F7-report-training','F6-validation-components']
    for stem in figures:
        for ext in ['png','svg']:add('reports/final/figures/'+stem+'.'+ext,'report_figure','Selected report figure',required=False)
    for name in ['reports/final/Group4-final-report.pdf','reports/final/reproduction.md','reports/final/cmab-audit.md']:
        add(name,'report_document','Final paper or focused supporting/reproduction documentation',required=False)
    evaluation=['freeze','publication','runs','analysis','contrasts','four-policy-analysis','deployment','saved-results-check','step19-review']
    for name in evaluation:add('artifacts/final/evaluation/'+name+'.json','evaluation_evidence','Frozen inputs or final reproducible analysis')
    for name in ['runs','comparison','benchmark-cpu','benchmark-cuda','environment-checks']:
        add('artifacts/final/calibration/'+name+'.json','calibration','Quantified model/environment fidelity or compute benchmark',required=False)
    for name in ['main-selection','screen-selection','main-checks','screen-checks','learning-checks']:
        add('artifacts/final/training/'+name+'.json','training_summary','Selection, multi-seed learning or integrity evidence',required=False)
    for p in (ROOT/'artifacts/final/training').glob('*/*/*.json'):
        if p.name in ['curve.json','manifest.json','initialization.json','selected-validation.json']:
            add(p.relative_to(ROOT).as_posix(),'training_summary','Small seed/recipe records; resume caches and redundant weights excluded')
    selection=json.loads((ROOT/'artifacts/final/training/main-selection.json').read_text())
    for kind,r in selection['selected'].items():add(f'artifacts/final/training/main/{kind}-{r["seed"]}/selected.zip','export_dependency','Exact selected native checkpoint required by export_final; other seed weights stay in GitHub history')
    ledgers=['artifacts/final/evaluation/runs.json','artifacts/final/calibration/runs.json',
        'artifacts/final/development/memory-startup-v1/runs.json','artifacts/final/development/feedback-v1/runs.json',
        'artifacts/final/development/context-guard-v2/runs.json','artifacts/final/validation/finalists-v2/runs.json']
    ids=set()
    for name in ledgers:
        add(name,'supporting_study','Source ledger for main evidence, calibration, H1-H6 or validation')
        if name in ledgers[:2]:ids.update(r['run_id'] for r in json.loads((ROOT/name).read_text()) if r['status']=='complete')
    add('artifacts/final/validation/finalists-v2/selection.json','selection','Validation-only controller selection')
    idx=json.loads((ROOT/'artifacts/final/evidence/index.json').read_text())
    for run in sorted(ids):add(idx[run]['file'],'portable_event_evidence','Hash-checked final or calibration raw events; no MongoDB dependency')
    add('artifacts/final/evidence/index.json','portable_event_index','ZIP transforms this into a subset containing only bundled run payloads')
    # Resolve local imports by actual source location. External libraries remain
    # pinned requirements, never copied environments or site-packages.
    seen=set()
    while queue:
        path=queue.pop()
        if path in seen:continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            modules=[]
            if isinstance(node,ast.Import):modules=[(n.name,0) for n in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:modules=[(node.module,node.level)]
            for module,level in modules:
                rel=Path(*module.split('.'));bases=[ROOT,path.parent,ROOT/'scripts'] if not level else [path.parents[level-1]]
                for base in bases:
                    candidate=base/rel.with_suffix('.py')
                    if candidate.is_file() and candidate.is_relative_to(ROOT):add(candidate.relative_to(ROOT).as_posix(),'python_dependency','Transitive local import of '+path.relative_to(ROOT).as_posix());break
    return {'format':'group4-submission-inventory-v1','files':dict(sorted(files.items())),
        'portable_run_ids':sorted(ids),'missing_required':sorted(set(missing)),
        'planned_generated':['reports/final/Group4-final-report.pdf'],
        'excluded_categories':['presentation/demo/learning materials','verbose execution logs','PhaseA reports','unused pilot/reference weights','redundant seed checkpoints/resume caches','unrelated upstream infrastructure','Git internals/environments/scratch'],
        'preserved_dependencies':['complete measured dash.js source/testplayer and rl/web snapshot','pilot_env base class','selected seed checkpoints for export','frozen Compose build paths'],
        'evaluator_entry':'ZIP root README maps final implementations and commands; historical research remains in existing GitHub repository'}

if __name__=='__main__':
    d=inventory();assert not d['missing_required'],d['missing_required'];p=ROOT/'release';p.mkdir(exist_ok=True)
    (p/'submission-files.json').write_text(json.dumps(d,indent=2));print(json.dumps({'files':len(d['files']),'portable_runs':len(d['portable_run_ids']),'bytes':sum((ROOT/n).stat().st_size for n in d['files'])}))
