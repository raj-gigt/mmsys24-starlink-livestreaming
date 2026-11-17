"""Exercise the served pinned MABWiser runtime and initialization boundary."""
import json
from pathlib import Path
import time
from selenium import webdriver
ROOT=Path(__file__).resolve().parents[1]
FIXTURE="""
import json
import numpy as np
from sklearn.preprocessing import StandardScaler
from mabwiser.mab import MAB, LearningPolicy
from importlib.metadata import version
x=np.array([[2.,1.,40.]]*4)
y=np.array([1.,2.,1.,2.]);arms=[0,1,0,1]
z=StandardScaler().fit_transform(x)
def scores(context,seed=123456,alpha=1):
    m=MAB([0,1],LearningPolicy.LinTS(alpha=alpha),seed=seed)
    m.fit(arms,y,context)
    return {str(k):float(v) for k,v in m.predict_expectations(context[-1:]).items()}
zero=scores(z)
bias=np.column_stack([z,np.ones(4)])
intercept=scores(bias,alpha=1e-8)
same=scores(bias)==scores(bias)
different=scores(bias,seed=123456)!=scores(bias,seed=123457)
assert all(v==0 for v in zero.values())
assert intercept['1']>intercept['0']>0
assert same and different
json.dumps({'version':version('mabwiser'),'zero_centered_scores':zero,
    'post_scaling_intercept_scores':intercept,'reset_seed_repeats_scores':same,
    'changing_seed_changes_scores':different})
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
    else:raise RuntimeError('Served player has no common prewarm entry point')
    report=driver.execute_async_script("""
      const code=arguments[0],done=arguments[arguments.length-1],t=performance.now();
      window.LEO_PREWARM_CMAB().then(runtime=> {
        const first=performance.now()-t;
        const fixture=JSON.parse(runtime.runPython(code));
        const t2=performance.now();
        window.LEO_PREWARM_CMAB().then(again=>done({status:'PASS',fixture,
            cold_runtime_setup_ms:first,warm_runtime_lookup_ms:performance.now()-t2,
            same_runtime:runtime===again}));
      }).catch(error=>done({status:'FAIL',error:String(error)}));
    """,FIXTURE)
    assert report['status']=='PASS' and report['same_runtime'],report
    assert report['fixture']['version']=='2.7.0'
    (ROOT/'artifacts/final/runtime-check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
finally:driver.quit()

