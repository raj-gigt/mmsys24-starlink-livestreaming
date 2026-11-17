"""Reproduce an exported real CMAB proposal using its pinned browser runtime."""
import json
from pathlib import Path
import time
from selenium import webdriver
ROOT=Path(__file__).resolve().parents[1]
example=json.loads((ROOT/'models/final/cmab/example-state.json').read_text())
code="""
import numpy as np
from mabwiser.mab import MAB, LearningPolicy
from js import LEO_CMAB_REPLAY_INPUT
record=LEO_CMAB_REPLAY_INPUT.to_py()
replay_mab=MAB(arms=list(range(8)),learning_policy=LearningPolicy.LinTS(alpha=float(record['alpha'])),seed=int(record['seed']))
replay_mab.fit(decisions=[int(a) for a in record['actions']],rewards=record['rewards'],contexts=np.array(record['contexts'],dtype=float))
int(replay_mab.predict(np.array([record['input']],dtype=float)))
"""
options=webdriver.ChromeOptions();options.add_argument('ignore-certificate-errors')
driver=webdriver.Remote('http://localhost:4444',options=options)
try:
    driver.set_page_load_timeout(120);driver.set_script_timeout(120)
    driver.get('http://pyodide/samples/starlink/testplayer/testplayer.html')
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        if driver.execute_script('return typeof window.LEO_PREWARM_CMAB === "function"'):break
        time.sleep(.25)
    else:raise RuntimeError('Runtime unavailable')
    result=driver.execute_async_script("""
        window.LEO_CMAB_REPLAY_INPUT=arguments[0];const code=arguments[1],done=arguments[arguments.length-1];
        window.LEO_PREWARM_CMAB().then(runtime=>done({proposal:runtime.runPython(code)}))
            .catch(e=>done({error:String(e)}));
    """,example,code)
    assert 'error' not in result,result
    assert result['proposal']==example['expected_proposal'],result
    action=min(result['proposal'],example['guard_maximum']) if example['variant']=='guard' else result['proposal']
    assert action==example['expected_action']
    report={'status':'PASS','run_id':example['run_id'],'decision_id':example['decision_id'],
        'history_rows':len(example['actions']),'replayed_proposal':result['proposal'],'replayed_action':action,
        'qualification':'Exact replay of recorded online state, not performance evaluation'}
    (ROOT/'artifacts/final/cmab-example-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:driver.quit()
