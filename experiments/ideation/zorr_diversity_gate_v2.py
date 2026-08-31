#!/usr/bin/env python3
"""ZORR anti-fixation diversity gate R02.

Uses canonical structural tags and weighted Jaccard distance instead of raw-string
inequality, so trivial renaming/synonyms cannot fake novelty.
Stdlib only.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

WEIGHTS = {
    'framing':1.0,'camera':1.0,'pose':1.2,'hand_role':1.2,'face_mechanism':1.2,
    'body_effort':1.2,'space_operator':1.0,'lighting':0.8,'palette':0.7,
    'render_language':0.8,'environment_logic':1.0,'temporal_state':1.0,
}
KEY_DIMS=('framing','camera','pose','hand_role','face_mechanism','space_operator','lighting')
DEFAULTS={
    'min_weighted_distance':0.60,
    'min_changed_dimensions':7,
    'max_key_signature_similarity':0.48,
    'recent_window':4,
    'cooldown_repeat_limit':3,
    'min_emotion_channels':4,
}
CHANNELS=('face','body','hands','space','light_value','environment','temporal_rhythm')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def tags(c,d): return set(c.get('canonical',{}).get(d,[]))
def jaccard(a,b):
    if not a and not b: return 1.0
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)

def weighted_distance(a,b):
    total=sum(WEIGHTS.values()); acc=0.0; changed=0; per={}
    for d,w in WEIGHTS.items():
        sim=jaccard(tags(a,d),tags(b,d)); dist=1.0-sim; per[d]=round(dist,4)
        acc+=w*dist
        if dist>=0.50: changed+=1
    return acc/total, changed, per

def key_similarity(a,b):
    vals=[jaccard(tags(a,d),tags(b,d)) for d in KEY_DIMS]
    return sum(vals)/len(vals)

def active_channels(c):
    x=c.get('emotion_channels',{})
    return sum(bool(x.get(k)) for k in CHANNELS)

def schema_errors(c):
    e=[]
    if not c.get('emotion_goal'): e.append('missing:emotion_goal')
    if not c.get('far_analogy'): e.append('missing:far_analogy')
    can=c.get('canonical')
    if not isinstance(can,dict): return e+['missing:canonical']
    for d in WEIGHTS:
        if not isinstance(can.get(d),list) or not can.get(d): e.append(f'missing:canonical.{d}')
    return e

def cooldown_violations(c,history,cfg):
    recent=history[-int(cfg['recent_window']):]
    lim=int(cfg['cooldown_repeat_limit'])
    out=[]
    for d in KEY_DIMS:
        counts={}
        for h in recent:
            for t in tags(h,d): counts[t]=counts.get(t,0)+1
        for t in tags(c,d):
            if counts.get(t,0)>=lim:
                out.append(f'cooldown:{d}:{t} used {counts[t]}x in recent window')
    return out

def gate(c,history,cfg=None):
    cfg={**DEFAULTS,**(cfg or {})}; reasons=schema_errors(c)
    ds=[]
    for h in history:
        dist,changed,per=weighted_distance(c,h)
        ds.append((dist,changed,per,h.get('id') or h.get('emotion_goal','history')))
    if ds:
        nearest=min(ds,key=lambda x:x[0]); min_dist,min_changed,per,near_id=nearest
    else:
        min_dist,min_changed,per,near_id=1.0,len(WEIGHTS),{},None
    if min_dist<float(cfg['min_weighted_distance']):
        reasons.append(f'fixation:weighted_distance={min_dist:.3f} < {cfg["min_weighted_distance"]:.3f} nearest={near_id}')
    if min_changed<int(cfg['min_changed_dimensions']):
        reasons.append(f'fixation:changed_dimensions={min_changed} < {cfg["min_changed_dimensions"]}')
    if history:
        ks=max((key_similarity(c,h), h.get('id') or h.get('emotion_goal','history')) for h in history[-int(cfg['recent_window']):])
        if ks[0]>float(cfg['max_key_signature_similarity']):
            reasons.append(f'key_signature_similarity={ks[0]:.3f} > {cfg["max_key_signature_similarity"]:.3f} near={ks[1]}')
    reasons += cooldown_violations(c,history,cfg)
    ch=active_channels(c)
    if ch<int(cfg['min_emotion_channels']): reasons.append(f'weak_emotion_channels={ch}')
    far=str(c.get('far_analogy','')).lower()
    if any(x in far for x in ('anime','manga','jojo','bleach','berserk')): reasons.append('far_analogy_not_far')
    return {
        'status':'PASS' if not reasons else 'REJECT',
        'nearest':near_id,
        'min_weighted_distance':round(min_dist,4),
        'min_changed_dimensions':min_changed,
        'active_emotion_channels':ch,
        'per_dimension_distance':per,
        'reasons':reasons,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--concept',required=True); ap.add_argument('--history',required=True); ap.add_argument('--config')
    a=ap.parse_args(); c=load(a.concept); h=load(a.history); cfg=load(a.config) if a.config else None
    r=gate(c,h,cfg); print(json.dumps(r,ensure_ascii=False,indent=2)); return 0 if r['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
