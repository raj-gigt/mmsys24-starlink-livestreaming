"""Portable replay of deployed decisions and request-identity invariants.

Uses exported dense weights and numpy only; no browser, database or PyTorch.
Poor playback and explicitly logged safety fallback remain scored outcomes.
"""
from functools import lru_cache
import json
import math
from pathlib import Path
import numpy as np
from .features import features

ROOT=Path(__file__).resolve().parents[1]


@lru_cache(maxsize=2)
def actor(kind):
    return json.loads((ROOT/f'models/final/{kind}/actor.json').read_text())


def check_decisions(payload,plan):
    t=payload['telemetry.json'];s=payload['summary.json']
    assert s['actual_abr_strategy']==plan['algorithm'] and s['auto_switch_video'] is True
    assert s['clock_mode']=='host' and s['utc_synchronization_enabled'] is False
    count=0;fallbacks=0;max_error=0.;links=0
    if plan.get('neural_variant'):
        kind=plan['neural_variant'];spec=actor(kind)
        assert s['model']['kind']==kind and s['model']['sha256']==spec['identity']
        for d in t['custom_decisions']:
            count+=1;assert isinstance(d['action'],int) and 0<=d['action']<8
            if d['result'].get('fallback'):
                fallbacks+=1;assert d['action']==0;continue
            x=features(d['observation'])
            if kind=='leo':
                obs=d['observation'];history=obs.get('probes',[])[-8:];extra=[]
                for i in range(8):
                    j=i-(8-len(history));r=history[j] if j>=0 else None
                    extra.extend([np.clip(r['rtt_ms']/200,0,5) if r and r['ok'] else 0,
                        np.clip(r['age_s']/4,0,1) if r else 1,1 if r and r['ok'] else 0])
                extra.extend([np.clip(obs['live_latency_s']/3,0,8),
                    np.clip(obs.get('probe_success_age_s',99)/3,0,1),int(obs.get('probe_valid',False)),
                    sum(not r['ok'] for r in history)/len(history) if history else 1])
                x=np.concatenate([x,np.asarray(extra,dtype=np.float32)])
            np.testing.assert_allclose(x,d['input'],atol=2e-6,rtol=0)
            assert len(x)==spec['input_dim'] and np.isfinite(x).all()
            z=x
            for i,layer in enumerate(spec['layers']):
                z=np.asarray(layer['w'],dtype=np.float32).reshape(layer['shape'])@z+np.asarray(layer['b'],dtype=np.float32)
                if i<2:z=np.maximum(z,0)
            actual=np.asarray(d['result']['logits']);np.testing.assert_allclose(z,actual,atol=2e-4,rtol=2e-4)
            assert int(z.argmax())==d['action']
            max_error=max(max_error,float(np.max(np.abs(z-actual))))
            assert spec['action_bitrates'][d['action']]==d['bitrate_bps']
            links+=sum(any(q['url']==r['url'] and q['quality']==r['quality'] for r in t['requests']) for q in d['requests'] if q['at_ms']<=t['stopped_at_ms'])
    else:
        for d in t['cmab_decisions']:
            count+=1;assert isinstance(d['action'],int) and 0<=d['action']<8
            if plan.get('variant'):
                assert d['variant']==plan['variant'];x=d['model_input']
                assert len(x)==9 and x[0]==1 and all(math.isfinite(v) for v in x)
                assert x[6] in [0,1] and 0<=x[7]<=1
                if not d['observation']['probe_valid']:assert x[3]==0 and x[6]==0
                if plan['variant']=='guard':assert d['action']==min(d['proposal'],d['guard_maximum'])
                else:assert plan['variant']=='guard_only' and d['action']==d['guard_maximum']
    feedback=t['feedback'];starts={r['request_id']:r for r in feedback if r['type']=='request-start'}
    ends=[r for r in feedback if r['type']=='request-outcome'];accepted=[r for r in ends if r['accepted']]
    assert len({r['request_id'] for r in ends})==len(ends)
    assert len({r['decision_id'] for r in accepted})==len(accepted)
    known={r['id']:r for r in t['cmab_decisions']}
    for r in accepted:
        start=starts[r['request_id']];choice=known[r['decision_id']]
        assert r['outcome']=='complete' and r['epoch']==start['epoch']
        assert choice['action']==start['quality'] and choice['at_ms']<=start['start_ms']<=r['at_ms']
        assert math.isfinite(r['reward']) and r['elapsed_s']>=0
        assert any(q['url']==start['url'] and q['quality']==start['quality'] for q in t['requests'])
    assert all(r['reward'] is None for r in ends if not r['accepted'])
    return {'run_id':s['run_id'],'policy':plan['policy'],'decisions':count,
        'neural_fallbacks':fallbacks,'max_dense_replay_logit_error':max_error,
        'neural_completed_request_links':links,'accepted_cmab_updates':len(accepted),
        'censored_or_unmatched_outcomes':len(ends)-len(accepted)}
