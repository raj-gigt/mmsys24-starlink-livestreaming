"""Fixed-action/causal-teacher controls on the same simulator validation set."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rl.train_final import evaluate
from rl.warmstart import teacher_action
class Control:
    def __init__(self,action):self.action=action
    def predict(self,x,deterministic=True):return (teacher_action(x) if self.action is None else self.action),None
ROOT=Path(__file__).resolve().parents[1]
results={str(a):evaluate(Control(a)) for a in range(8)}
results['teacher']=evaluate(Control(None))
out=ROOT/'artifacts/final/training';out.mkdir(parents=True,exist_ok=True)
(out/'validation-controls.json').write_text(json.dumps(results,indent=2))
print(json.dumps({a:{k:v for k,v in r.items() if k!='episodes'} for a,r in results.items()},indent=2))
