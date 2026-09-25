"""One finite programme, two matched controls, and one mesh pilot."""
from dataclasses import replace
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from functions.core import Model, State, advance, observe, placement, stationary
from functions.observables import trade_record,finish_tape

VERSION='v0.5.0'
CONFIG='config/experiments-'+VERSION+'.json'


def dump(path, obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def aligned(u, du):
    n=round(u/du)
    if not np.isfinite(u) or abs(n*du-u)>1e-10:raise ValueError('Time must align with the registered grid')
    return n


def schedule(c, m):
    n=aligned(c['horizon'],m.du)
    if n<1:raise ValueError('Horizon must be positive')
    events=np.zeros((n,2))
    for e in c['events']:
        if set(e)!={'u','side','volume'}:raise ValueError('Unknown event key')
        j=aligned(e['u'],m.du)
        if not 1<=j<=n or e['side'] not in ('buy','sell') or not np.isfinite(e['volume']) or e['volume']<=0:
            raise ValueError('Invalid event')
        events[j-1,1 if e['side']=='buy' else 0]+=e['volume']
    return events


def load_config(root):
    c=json.loads((root/CONFIG).read_text())
    keys={'version','model','stationarity_tolerance','stationarity_max_u','horizon','sample_du','field_du','events','cases','snapshots','video','checks','assessment','statistics'}
    if set(c)!=keys or c['version']!=VERSION:raise ValueError('Unknown or incomplete experiment configuration')
    if c['cases']!={'moving':{},'immediate':{'completion_time':0.},'fixed':{'chi_s':0.,'chi_m':0.}}:
        raise ValueError('Only the three registered matched controls are in scope')
    if set(c['video'])!={'seconds','fps','dpi'} or any(v<=0 for v in c['video'].values()):raise ValueError('Invalid video controls')
    if set(c['checks'])!={'budget_atol','ledger_atol','unfilled_atol','no_event_drift_atol'} or any(v<=0 for v in c['checks'].values()):raise ValueError('Invalid numerical checks')
    m=Model(**c['model']);schedule(c,m)
    for h in ('sample_du','field_du'):
        if aligned(c[h],m.du)<1:raise ValueError('Invalid output sampling')
    for s in c['snapshots']:
        if set(s)!={'u','phase','label'} or s['phase'] not in ('pre','post') or not 0<=s['u']<=c['horizon']:
            raise ValueError('Invalid snapshot')
        aligned(s['u'],m.du)
        if s['phase']=='pre' and s['u'] not in [e['u'] for e in c['events']]:raise ValueError('Pre phase requires an event')
    if c['statistics']['burn_events']<1 or c['statistics']['maximum_lag']>=c['statistics']['events']-2:
        raise ValueError('Invalid statistical burn or lag window')
    return c,m


def run_case(name,m,c,initial,events,out,fields=False):
    state=State(initial.copy());records=[];frames=[];frame_rows=[];event_rows=[];event_arrays=[];trades=[];fills=[]
    sample=aligned(c['sample_du'],m.du)
    special={aligned(s['u'],m.du) for s in c['snapshots']}
    event_steps=set(np.flatnonzero(np.any(events,axis=1))+1)
    keep={k+d for k in event_steps for d in (-1,0,1)}
    maxes={'budget_error':0.,'ledger_error':0.,'positivity_load':0.,'crossings_b':0,'crossings_a':0}
    max_drift=0.;min_spread=float('inf');min_slope=float('inf');unfilled=0.

    def frame(rho,u,phase,q,pending):
        obs=observe(m,rho);frames.append(rho.copy())
        frame_rows.append({'frame':len(frames)-1,'u':u,'phase':phase,'q_b':q[0],'q_a':q[1],
            'p_b':obs['p_b'],'p_a':obs['p_a'],'spread':obs['spread'],'Q_sum':float(pending.sum())})

    if fields:frame(initial,0.,'initial',placement(m,[0,0]),np.zeros(2))
    for n,e in enumerate(events,1):
        state,r,d=advance(m,state,e)
        r.update(cumulative_buy=float(state.initiated[0]),cumulative_sell=float(state.initiated[1]),
            cumulative_completed_bid=float(state.completed[0]),cumulative_completed_ask=float(state.completed[1]))
        for key in maxes:maxes[key]=max(maxes[key],r[key])
        min_spread=min(min_spread,r['spread']);min_slope=min(min_slope,abs(r['slope_b']),abs(r['slope_a']))
        unfilled+=r['unfilled_buy']+r['unfilled_sell']
        max_drift=max(max_drift,float(np.max(np.abs(state.rho-initial))))
        if n==1:
            zero={k:0 for k in r};zero.update(observe(m,initial))
            q=placement(m,[0,0]);zero.update(q_b=q[0],q_a=q[1],Sigma=q[1]-q[0],mu=q.mean(),
                pre_p_b=zero['p_b'],pre_p_a=zero['p_a'],mass_bid=m.dx*initial[0,1:-1].sum(),mass_ask=m.dx*initial[1,1:-1].sum())
            records.append(zero)
        if n%sample==0 or n in keep or n==len(events):records.append(r)
        if n in event_steps:
            event_rows.append({k:r[k] for k in ('u_end','requested_buy','executed_buy','unfilled_buy','requested_sell','executed_sell','unfilled_sell','pre_p_b','pre_p_a','p_b','p_a')})
            if r['executed_buy']+r['executed_sell']>0:
                trade,child_fills=trade_record(m,r,d['removed'],len(trades)+1,parent_order_id=0)
                trades.append(trade);fills.extend(child_fills)
            if fields:
                event_arrays.append(d)
                frame(d['pre_consumption'],r['u_end'],'pre',np.array([r['q_b'],r['q_a']]),np.array([r['Q_B_quote'],r['Q_A_quote']]))
        if fields and (n%aligned(c['field_du'],m.du)==0 or n in event_steps or n in special or n==len(events)):
            frame(state.rho,r['u_end'],'post',np.array([r['q_b'],r['q_a']]),state.pending)
    write_csv(out/(name+'-'+VERSION+'.csv'),records)
    if event_rows:write_csv(out/(name+'-events-'+VERSION+'.csv'),event_rows)
    if trades:
        finish_tape(trades);write_csv(out/(name+'-trades-'+VERSION+'.csv'),trades)
        write_csv(out/(name+'-fills-'+VERSION+'.csv'),fills)
    if fields:
        write_csv(out/('density-index-'+VERSION+'.csv'),frame_rows)
        arrays={key:np.stack([d[key] for d in event_arrays]) for key in event_arrays[0]}
        np.savez_compressed(out/('density-'+VERSION+'.npz'),x=m.x,rho=np.stack(frames),initial=initial,**arrays)
    summary={'updates':len(events),'saved_scalar_rows':len(records),'maxima':maxes,'minimum_spread':min_spread,
        'minimum_abs_selected_slope':min_slope,'max_field_departure':max_drift,'unfilled':unfilled,
        'executed_buy':float(state.initiated[0]),'executed_sell':float(state.initiated[1]),
        'completed_bid':float(state.completed[0]),'pending_bid':float(state.pending[0]),
        'completed_ask':float(state.completed[1]),'pending_ask':float(state.pending[1])}
    for key,limit in [('budget_error','budget_atol'),('ledger_error','ledger_atol')]:
        if maxes[key]>c['checks'][limit]:raise ValueError('Registered '+key+' tolerance exceeded')
    if unfilled>c['checks']['unfilled_atol']:raise ValueError('Unfilled demand prevents a matched-volume comparison')
    return summary,records


def run_experiments(root,c,m,tests):
    out=root/'outputs';out.mkdir(exist_ok=True)
    initial,relaxation=stationary(m,c['stationarity_tolerance'],c['stationarity_max_u'])
    events=schedule(c,m)
    report={'version':VERSION,'status':'diagnostic experiments; numerical convergence and scientific acceptance pending','tests_passed':tests,
        'stationary_initialization':relaxation,'cases':{}}
    series={}
    for name,overrides in {'no-event':{},**c['cases']}.items():
        mm=replace(m,**overrides)
        report['cases'][name],series[name]=run_case(name,mm,c,initial,np.zeros_like(events) if name=='no-event' else events,out,fields=name=='moving')
        print('Completed '+name,flush=True)
    if report['cases']['no-event']['max_field_departure']>c['checks']['no_event_drift_atol']:
        raise ValueError('No-event stationary drift exceeds registered tolerance')
    # No-event dynamics are identical for all controls: empty pending stock,
    # hence no completion supply and q=(mu0 +/- Sigma0/2) for every case.
    target=[(r['executed_buy'],r['executed_sell']) for r in series['moving']]
    for name in ('immediate','fixed'):
        np.testing.assert_allclose([(r['executed_buy'],r['executed_sell']) for r in series[name]],target,rtol=0,atol=c['checks']['unfilled_atol'])
    report['assessment_file']='assessment-comparisons-'+VERSION+'.json'
    dump(out/('verification-'+VERSION+'.json'),report)
    return report


def input_paths(root):
    return sorted([root/CONFIG,root/'pyproject.toml',root/'scripts/run_all.py']+list((root/'functions').glob('*.py'))+list((root/'tests').glob('*.py')))


def save_manifest(root):
    files=input_paths(root)+sorted(p for p in (root/'outputs').iterdir() if p.is_file() and p.name!='manifest-'+VERSION+'.json')
    dump(root/'outputs'/('manifest-'+VERSION+'.json'),{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


def verify_manifest(root):
    data=json.loads((root/'outputs'/('manifest-'+VERSION+'.json')).read_text())
    required={p.relative_to(root).as_posix() for p in input_paths(root)}
    required.update(p.relative_to(root).as_posix() for p in (root/'outputs').iterdir() if p.is_file() and p.name!='manifest-'+VERSION+'.json')
    if set(data)!=required:raise ValueError('Manifest membership differs from the registered input/output set')
    for name,digest in data.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed input/data: '+name+'; run the complete route')
