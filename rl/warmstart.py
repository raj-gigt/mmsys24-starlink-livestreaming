"""Explicit teacher initialization from training-simulator observations only.

The teacher is the simple causal throughput/buffer policy, not an oracle and not
MongoDB actions relabelled as optimal. A2C subsequently updates the actor.
"""
from collections import Counter
import json
from pathlib import Path
import numpy as np
import torch
from .pilot_env import PilotLiveEnv

def teacher_action(x):
    rows=np.asarray(x[:32]).reshape(8,4)
    h=rows[(rows[:,3]>.5)&(rows[:,2]<.5)&(rows[:,0]>0)][-4:]
    if not len(h):return 0
    harmonic=len(h)/sum(1/(h[:,0]*10))
    buffer=float(x[32])*3
    safe=harmonic*(.45 if buffer<1 else .78)
    action=max(0,int(np.searchsorted([.3,.45,.9,1.2,1.5,4.9,5.1,6],safe,side='right')-1))
    return max(0,action-1) if buffer<.35 else action

def initialize_actor(model,samples=12000,epochs=25):
    rng=np.random.default_rng(211)
    env=PilotLiveEnv('train');obs,_=env.reset(seed=211)
    inputs=[];labels=[];groups=set()
    for _ in range(samples):
        action=teacher_action(obs)
        inputs.append(obs.copy());labels.append(action);groups.add(env.row['id'])
        executed=action if rng.random()<.7 else int(rng.integers(8))
        obs,_,_,done,_=env.step(executed)
        if done:obs,_=env.reset()
    x=torch.tensor(np.array(inputs),dtype=torch.float32)
    y=torch.tensor(labels,dtype=torch.long)
    permutation=rng.permutation(samples);cut=int(samples*.8)
    train,test=permutation[:cut],permutation[cut:]
    counts=np.bincount(np.array(labels)[train],minlength=8)
    weights=1/np.sqrt(np.maximum(counts,1));weights/=weights.mean()
    loss_fn=torch.nn.CrossEntropyLoss(weight=torch.tensor(weights,dtype=torch.float32))
    params=list(model.policy.mlp_extractor.policy_net.parameters())+list(model.policy.action_net.parameters())
    optimizer=torch.optim.Adam(params,lr=1e-3)
    losses=[]
    for _ in range(epochs):
        order=rng.permutation(train);total=0
        for i in range(0,len(order),256):
            batch=order[i:i+256]
            logits=model.policy.action_net(model.policy.mlp_extractor.forward_actor(x[batch]))
            loss=loss_fn(logits,y[batch]);optimizer.zero_grad();loss.backward();optimizer.step()
            total+=float(loss.detach())*len(batch)
        losses.append(total/len(train))
    with torch.no_grad():
        predicted=model.policy.action_net(model.policy.mlp_extractor.forward_actor(x[test])).argmax(dim=1)
        agreement=float((predicted==y[test]).float().mean())
    report={'method':'Behaviour cloning of the simple causal policy, followed by A2C',
        'teacher_input':'Only the same 36 causal observations available to the deployed actor',
        'source_split':'train only','training_scenario_ids':sorted(groups),'samples':samples,'epochs':epochs,
        'teacher_action_counts':dict(Counter(labels)),'loss_per_epoch':losses,
        'within_training_state_holdout_teacher_agreement':agreement,
        'clarification':'This agreement measures imitation fidelity, not ABR optimality or final test accuracy.'}
    Path('artifacts/training/warmstart.json').write_text(json.dumps(report,indent=2))
    return report
