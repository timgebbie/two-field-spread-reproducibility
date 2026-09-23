"""Verify and run the small v0.3.0 core fixture. No figure production."""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from functions.core import Model, State, advance, stationary


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def schedule(config,m):
    count=round(config['horizon']/m.du)
    if count<1 or abs(count*m.du-config['horizon'])>1e-12:
        raise ValueError('Horizon must align with the operational grid')
    events=np.zeros((count,2))
    for event in config['events']:
        end=round(event['u']/m.du)
        if not 1<=end<=count or abs(end*m.du-event['u'])>1e-12:
            raise ValueError('Child execution time must be a positive grid-aligned endpoint')
        if event['side'] not in ('buy','sell') or not np.isfinite(event['volume']) or event['volume']<0:
            raise ValueError('Invalid child event')
        events[end-1,1 if event['side']=='buy' else 0]+=event['volume']
    return events


def run_case(name,m,initial,events,stride,out):
    state=State(initial.copy());records=[];snapshots=[];indices=[]
    for step,event in enumerate(events):
        state,record,detail=advance(m,state,event)
        records.append(record)
        if step==0 or (step+1)%stride==0 or np.any(event) or step==len(events)-1:
            snapshots.append(detail)
            indices.append({'snapshot':len(snapshots)-1,'step':step,
                'u_incoming':record['u_start'],'u_pre_consumption':record['u_end'],
                'u_post_consumption':record['u_end'],'event':int(np.any(event)),
                'q_b_used':record['q_b'],'q_a_used':record['q_a']})
    for stem,rows in [(name,records),(name+'-snapshots',indices)]:
        with (out/(stem+'-v0.3.0.csv')).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    arrays={key:np.stack([s[key] for s in snapshots]) for key in snapshots[0]}
    arrays.update(x=m.x,initial=initial,final=state.rho)
    np.savez_compressed(out/(name+'-states-v0.3.0.npz'),**arrays)
    return {'updates':len(records),'snapshot_updates':len(indices),
        'max_budget_error':max(r['budget_error'] for r in records),
        'max_completion_ledger_error':max(r['ledger_error'] for r in records),
        'max_positivity_load':max(r['positivity_load'] for r in records),
        'minimum_density':min(r['min_density'] for r in records),
        'total_executed_sell':sum(r['executed_sell'] for r in records),
        'total_executed_buy':sum(r['executed_buy'] for r in records),
        'total_unfilled':sum(r['unfilled_buy']+r['unfilled_sell'] for r in records),
        'pending_bid_end':float(state.pending[0]),'pending_ask_end':float(state.pending[1]),
        'completed_bid':float(state.completed[0]),'completed_ask':float(state.completed[1]),
        'max_field_change_from_reference':float(np.max(np.abs(state.rho-initial))),
        'boundary_order_exits':0}


def main():
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    config=json.loads((ROOT/'config/core-v0.3.0.json').read_text())
    m=Model(**config['model']);events=schedule(config,m)
    initial,relaxation=stationary(m,config['stationarity_tolerance'],config['stationarity_max_u'])
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    report={'version':'v0.3.0','scope':'core verification, not final scientific acceptance',
        'tests_passed':result.testsRun,'tests_failed':len(result.failures)+len(result.errors),
        'stationary_initialization':relaxation,'cases':{}}
    for name,programme in [('no-event',np.zeros_like(events)),('execution-check',events)]:
        report['cases'][name]=run_case(name,m,initial,programme,config['snapshot_stride'],out)
    dump(out/'verification-v0.3.0.json',report)
    dump(out/'environment-v0.3.0.json',{'python':platform.python_version(),'numpy':np.__version__,'platform':platform.system()})
    tracked=list((ROOT/'config').glob('*.json'))+list((ROOT/'functions').glob('*.py'))+list((ROOT/'tests').glob('*.py'))+[Path(__file__).resolve()]
    files=tracked+[p for p in out.iterdir() if p.is_file() and p.name not in ('data-manifest-v0.3.0.json','.gitkeep')]
    dump(out/'data-manifest-v0.3.0.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
    print(json.dumps(report,indent=2))
    print('v0.3.0 core route complete. No publication figures or video generated.')


if __name__=='__main__':main()
