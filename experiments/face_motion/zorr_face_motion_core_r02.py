#!/usr/bin/env python3
"""ZORR Face Motion Core R02: deterministic single-source local 2D warp."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import cv2, numpy as np, yaml

VERSION="2.0.0"

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def ease(name,t):
    t=float(np.clip(t,0,1))
    if name=='linear': return t
    if name=='smoothstep': return t*t*(3-2*t)
    if name=='smootherstep': return t**3*(t*(t*6-15)+10)
    raise ValueError(f'unknown easing: {name}')

def validate(cfg):
    if not all(k in cfg for k in ('source','animation','regions')): raise ValueError('missing source/animation/regions')
    w,h=map(int,cfg['source']['expected_size']); assert w>0 and h>0
    ts=list(map(float,cfg['animation']['t_values']))
    if len(ts)<2 or any(t<0 or t>1 for t in ts) or any(b<=a for a,b in zip(ts,ts[1:])): raise ValueError('bad t_values')
    ease(cfg['animation'].get('easing','smootherstep'),.5)
    cap=float(cfg.get('qc',{}).get('max_displacement_px',24))
    names=set()
    for r in cfg['regions']:
        n=r['name']
        if n in names: raise ValueError(f'duplicate region {n}')
        names.add(n)
        if float(r.get('rbf_sigma_px',0))<=0: raise ValueError(f'{n}: bad sigma')
        if r['mask']['type'] not in ('ellipse','polygon'): raise ValueError(f'{n}: bad mask')
        for c in r.get('controls',[]):
            x,y=map(float,c['xy']); dx,dy=map(float,c['delta_at_1'])
            if not (0<=x<w and 0<=y<h): raise ValueError(f'{n}: control OOB')
            if math.hypot(dx,dy)>cap: raise ValueError(f'{n}: displacement cap')

def masks(shape,spec):
    h,w=shape; u=np.zeros((h,w),np.uint8)
    if spec['type']=='ellipse':
        c=tuple(map(lambda v:int(round(v)),spec['center'])); a=tuple(map(lambda v:int(round(v)),spec['axes']))
        cv2.ellipse(u,c,a,float(spec.get('angle',0)),0,360,255,-1,lineType=cv2.LINE_8)
    else:
        pts=np.asarray(spec['points'],np.int32).reshape((-1,1,2)); cv2.fillPoly(u,[pts],255,lineType=cv2.LINE_8)
    hard=u>0; f=float(spec.get('feather_inward_px',0))
    if f<=0: return hard,hard.astype(np.float32)
    alpha=np.clip(cv2.distanceTransform(u,cv2.DIST_L2,5).astype(np.float32)/f,0,1); alpha[~hard]=0
    return hard,alpha

def rbf_field(shape,r,amount):
    h,w=shape; hard,alpha=masks(shape,r['mask']); out=[]; inv=[]
    for c in r.get('controls',[]):
        x,y=map(float,c['xy']); dx,dy=np.asarray(c['delta_at_1'],float)*amount
        out.append([x+dx,y+dy]); inv.append([-dx,-dy])
    for x,y in r.get('locks',[]): out.append([float(x),float(y)]); inv.append([0.,0.])
    p=np.asarray(out,float); d=np.asarray(inv,float); s=float(r['rbf_sigma_px']); reg=float(r.get('regularization',1e-6))
    dd=p[:,None,:]-p[None,:,:]; K=np.exp(-np.sum(dd*dd,axis=2)/(2*s*s)); K.flat[::K.shape[0]+1]+=reg
    ax=np.linalg.solve(K,d[:,0]); ay=np.linalg.solve(K,d[:,1])
    ys,xs=np.where(hard); pad=int(max(8,2.5*s)); x0=max(0,int(xs.min())-pad); x1=min(w,int(xs.max())+1+pad); y0=max(0,int(ys.min())-pad); y1=min(h,int(ys.max())+1+pad)
    gy,gx=np.mgrid[y0:y1,x0:x1].astype(float); dx=np.zeros((h,w),np.float32); dy=np.zeros((h,w),np.float32); vx=np.zeros_like(gx); vy=np.zeros_like(gx)
    for i,(cx,cy) in enumerate(p):
        k=np.exp(-((gx-cx)**2+(gy-cy)**2)/(2*s*s)); vx+=ax[i]*k; vy+=ay[i]*k
    dx[y0:y1,x0:x1]=vx; dy[y0:y1,x0:x1]=vy; dx[~hard]=0; dy[~hard]=0
    return dx,dy,hard,alpha

def compose(shape,regions,amount):
    h,w=shape; sx=np.zeros((h,w),float); sy=np.zeros((h,w),float); sw=np.zeros((h,w),float); hard=np.zeros((h,w),bool); alpha=np.zeros((h,w),np.float32)
    for r in regions:
        dx,dy,hm,a=rbf_field(shape,r,amount); wt=a.astype(float); sx+=dx*wt; sy+=dy*wt; sw+=wt; hard|=hm; alpha=np.maximum(alpha,a)
    dx=np.zeros((h,w),np.float32); dy=np.zeros((h,w),np.float32); nz=sw>1e-12; dx[nz]=sx[nz]/sw[nz]; dy[nz]=sy[nz]/sw[nz]; dx[~hard]=0; dy[~hard]=0
    return dx,dy,hard,alpha

def render(src,dx,dy,hard,alpha,interp=cv2.INTER_LINEAR):
    h,w=src.shape[:2]; gy,gx=np.mgrid[0:h,0:w].astype(np.float32); wrp=cv2.remap(src,gx+dx,gy+dy,interp,borderMode=cv2.BORDER_REFLECT_101)
    a=alpha[...,None]; out=np.rint(src.astype(np.float32)*(1-a)+wrp.astype(np.float32)*a).clip(0,255).astype(np.uint8); out[~hard]=src[~hard]
    return out

def qc(src,out,hard):
    d=cv2.absdiff(src,out); outside=~hard; mag=np.max(d,axis=2)
    return {'outside_changed_pixels':int(np.count_nonzero(mag[outside])),'outside_exact_identity_ratio':1.0 if not np.any(outside) else 1-int(np.count_nonzero(mag[outside]))/int(np.count_nonzero(outside)),'inside_changed_pixels':int(np.count_nonzero(mag[hard]))}

def load(cfgp,source_override=None):
    cfg=yaml.safe_load(cfgp.read_text()); validate(cfg); sp=source_override or Path(cfg['source']['path']); src=cv2.imread(str(sp),cv2.IMREAD_COLOR)
    if src is None: raise RuntimeError(f'cannot read {sp}')
    h,w=src.shape[:2]
    if [w,h]!=list(map(int,cfg['source']['expected_size'])): raise RuntimeError('source size mismatch')
    sha=sha256_file(sp); exp=str(cfg['source'].get('sha256','')).lower()
    if exp and sha!=exp: raise RuntimeError('source sha mismatch')
    return cfg,src,sha

def run(cfgp,source_override=None,out=None,validate_only=False):
    cv2.ocl.setUseOpenCL(False); cv2.setNumThreads(1); cfg,src,sha=load(cfgp,source_override); h,w=src.shape[:2]
    base={'engine_version':VERSION,'source_size':[w,h],'source_sha256':sha}
    if validate_only: return {'status':'VALID',**base}
    if out is None: raise ValueError('out required'); out.mkdir(parents=True,exist_ok=True); frames=[]
    interp={'nearest':cv2.INTER_NEAREST,'linear':cv2.INTER_LINEAR,'cubic':cv2.INTER_CUBIC}[cfg.get('render',{}).get('interpolation','linear')]
    for i,t in enumerate(map(float,cfg['animation']['t_values'])):
        a=ease(cfg['animation'].get('easing','smootherstep'),t); dx,dy,hard,alpha=compose((h,w),cfg['regions'],a); frame=render(src,dx,dy,hard,alpha,interp); q=qc(src,frame,hard)
        if q['outside_changed_pixels']!=0: raise RuntimeError(f'QC exterior fail frame {i}')
        name=f'frame_{i:03d}.png'; cv2.imwrite(str(out/name),frame); frames.append({'frame':i,'raw_t':t,'eased':a,'qc':q,'file':name})
    m={'status':'PASS',**base,'frames':frames}; (out/'manifest.json').write_text(json.dumps(m,indent=2)); return m

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',type=Path,required=True); p.add_argument('--source',type=Path); p.add_argument('--out',type=Path); p.add_argument('--validate-only',action='store_true'); a=p.parse_args(); print(json.dumps(run(a.config,a.source,a.out,a.validate_only),indent=2))
if __name__=='__main__': main()
