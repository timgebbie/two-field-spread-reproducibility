"""Focused mesh, market-maker and order-flow experiments; unchanged core."""
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
import json
import hashlib
from pathlib import Path
import numpy as np
from functions.core import Model,State,advance,stationary,observe,placement,execute,external_source,placement_weights
from functions.observables import trade_record,finish_tape,lag_correlation


def grid_model(base,dx=None,du=None,half_width=12.,phase=0.,**overrides):
    dx=base['dx'] if dx is None else dx
    # Half-cell symmetric padding changes source/grid phase while retaining
    # exact buy/sell reflection. Domain sensitivity is checked separately.
    return Model(**dict(base,dx=dx,du=base['du'] if du is None else du,
        x_min=-half_width-phase*dx,x_max=half_width+phase*dx,**overrides))


def finite_run(job):
    name,base,options,events,horizon,sample=job
    m=grid_model(base,**options);initial,relax=stationary(m)
    state=State(initial.copy());times={round(e['u']/m.du):e for e in events}
    start=observe(m,initial);rows=[]
    keys=('p_b','p_a','midpoint','spread','Sigma','mu','Q_B_post','Q_A_post',
          'Q_B_quote','Q_A_quote','pre_p_b','pre_p_a')
    zero=dict(start,Sigma=m.Sigma0,mu=m.mu0,Q_B_post=0.,Q_A_post=0.,Q_B_quote=0.,Q_A_quote=0.,
              pre_p_b=start['p_b'],pre_p_a=start['p_a'])
    rows.append([0.]+[zero[k] for k in keys]);stride=round(sample/m.du)
    if not np.isclose(stride*m.du,sample):raise ValueError('Unaligned assessment sample')
    max_budget=max_ledger=max_load=unfilled=0.;min_spread=start['spread'];trades=[]
    for step in range(1,round(horizon/m.du)+1):
        e=times.get(step);request=[0.,0.]
        if e:request[1 if e['side']=='buy' else 0]=e['volume']
        state,r,d=advance(m,state,request)
        max_budget=max(max_budget,r['budget_error']);max_ledger=max(max_ledger,r['ledger_error'])
        max_load=max(max_load,r['positivity_load']);min_spread=min(min_spread,r['spread'])
        unfilled+=r['unfilled_buy']+r['unfilled_sell']
        if step%stride==0 or step in times:rows.append([step*m.du]+[r[k] for k in keys])
        if e:
            t,_=trade_record(m,r,d['removed'],len(trades)+1,0);trades.append(t)
    if unfilled>1e-10:raise ValueError('Unfilled volume in '+name)
    summary={'name':name,'options':options,'initial_spread':start['spread'],'late_spread_change':r['spread']-start['spread'],
      'maximum_spread_change':float(np.max(np.array(rows)[:,4]-start['spread'])),
      'max_budget_error':max_budget,'max_ledger_error':max_ledger,'max_positivity_load':max_load,
      'minimum_spread':min_spread,'unfilled':unfilled,'initialization':relax,
      'executed_volume':float(state.initiated.sum()),'pending_total':float(state.pending.sum())}
    return name,np.array(rows),summary,m.x,state.rho


def parent_distribution(beta,minimum,cap):
    """L=min(floor(minimum*(1-U)^(-1/beta)),cap), stored as exact PMF."""
    if not 1<beta<2 or not 1<=minimum<cap:raise ValueError('Invalid parent law')
    lengths=np.arange(1,cap+1)
    tail=np.minimum(1.,(minimum/lengths)**beta)
    probability=tail-np.r_[tail[1:],0.]
    return lengths,probability


def order_tape(count,seed,beta,minimum,cap):
    """Stationary renewal order splitting, with retained distinct parent IDs."""
    if count<1:raise ValueError('Empty tape')
    rng=np.random.default_rng(seed);lengths,p=parent_distribution(beta,minimum,cap)
    length=int(rng.choice(lengths,p=lengths*p/np.sum(lengths*p)))
    age=int(rng.integers(length));remaining=length-age
    signs=np.empty(count,dtype=np.int8);parents=np.empty(count,dtype=np.int32)
    runs=[];at=0;parent=0
    while at<count:
        sign=int(rng.choice([-1,1]));take=min(remaining,count-at)
        signs[at:at+take]=sign;parents[at:at+take]=parent
        runs.append([parent,sign,length,age,take]);at+=take;parent+=1
        if at<count:length=int(rng.choice(lengths,p=p));age=0;remaining=length
    return signs,parents,np.array(runs,dtype=np.int32)


def renewal_reference(lags,beta,minimum,cap):
    lengths,p=parent_distribution(beta,minimum,cap)
    return np.array([np.sum(p*np.maximum(lengths-k,0))/np.sum(lengths*p) for k in lags])


LONG_COLUMNS=('p_b','p_a','midpoint','spread','pre_p_b','pre_p_a','execution_log_price',
              'Q_B_post','Q_A_post','Sigma','mu','filled_quantity')


def source_membership(m,q):
    """Interior support intervals [start,stop), with the core's closed edges."""
    x=m.x[1:-1];b,a=q;w=m.placement_width
    return np.array([np.searchsorted(x,b,side='right'),np.searchsorted(x,a,side='left'),
        np.searchsorted(x,b-w,side='left'),np.searchsorted(x,b,side='right'),
        np.searchsorted(x,a,side='left'),np.searchsorted(x,a+w,side='right')],dtype=np.int32)


def membership_changes(old,new):
    external=int(abs(new[0]-old[0])+abs(new[1]-old[1]))
    completion=0
    for k in (2,4):
        l,r=old[k:k+2];ll,rr=new[k:k+2]
        completion+=int(r-l+rr-ll-2*max(0,min(r,rr)-max(l,ll)))
    return external,completion


def long_run(job):
    name,base,options,c,seed,kind=job
    m=grid_model(base,**options);initial,relax=stationary(m);state=State(initial.copy())
    n=c['events']+c['burn_events'];signs,parents,runs=order_tape(n,seed,c['beta'],c['minimum_parent'],c['parent_cap'])
    if kind=='iid':
        signs=np.random.default_rng(seed+c['iid_seed_offset']).choice([-1,1],size=n).astype(np.int8)
        parents=np.arange(n,dtype=np.int32);runs=np.empty((0,5),dtype=np.int32)
    gap=round(c['event_du']/m.du)
    if gap<1 or not np.isclose(gap*m.du,c['event_du']):raise ValueError('Unaligned long-run events')
    values=np.empty((n,len(LONG_COLUMNS)));max_budget=max_ledger=unfilled=0.;min_spread=float('inf')
    fills=[];offsets=[0];first_tape=[]
    diagnostic=c.get('resolution_diagnostics',False)
    support=np.zeros((n,9),dtype=np.int32) if diagnostic else None
    previous=source_membership(m,placement(m,state.pending)) if diagnostic else None
    start=0;checkpoint=Path(c['_checkpoint']) if c.get('_checkpoint') else None
    signature=hashlib.sha256(json.dumps([name,base,options,{k:v for k,v in c.items() if not k.startswith('_')},seed,kind],sort_keys=True).encode()+
        b''.join((Path(__file__).parent/f).read_bytes() for f in ('core.py','assessment.py','observables.py'))).hexdigest()
    if checkpoint and checkpoint.exists():
        with np.load(checkpoint) as saved:
            if str(saved['signature'])!=signature:raise ValueError('Changed resolution checkpoint inputs')
            start=len(saved['values']);values[:start]=saved['values'];support[:start]=saved['support']
            state=State(saved['rho'],saved['pending'],saved['initiated'],saved['completed'],int(saved['step']))
            fills=saved['fills'].tolist();offsets=saved['offsets'].tolist();previous=saved['previous']
            max_budget,max_ledger,unfilled,min_spread=saved['checks'].tolist()
        print(f'{name}: resumed at {start}/{n} events',flush=True)
    for event in range(start,n):
        changed=np.zeros(3,dtype=np.int32)
        for k in range(gap):
            request=[0.,0.]
            if k==gap-1:request[1 if signs[event]>0 else 0]=c['child_volume']
            state,r,d=advance(m,state,request)
            max_budget=max(max_budget,r['budget_error']);max_ledger=max(max_ledger,r['ledger_error'])
            min_spread=min(min_spread,r['spread']);unfilled+=r['unfilled_buy']+r['unfilled_sell']
            if diagnostic:
                current=source_membership(m,(r['q_b'],r['q_a']));ec,cc=membership_changes(previous,current)
                changed+=np.array([ec,cc,int(ec>0 or cc>0)]);previous=current
        t,ff=trade_record(m,r,d['removed'],event+1,int(parents[event]))
        values[event]=[t['execution_log_price'] if key=='execution_log_price' else t['filled_quantity'] if key=='filled_quantity' else r[key] for key in LONG_COLUMNS]
        for f in ff:fills.append([f['grid_index'],f['filled_quantity']])
        offsets.append(len(fills))
        if name=='lmf-moving-0':first_tape.append(t)
        if diagnostic:support[event]=np.r_[previous,changed]
        if checkpoint and ((event+1)%c['progress_every_events']==0 or event==n-1):
            checkpoint.parent.mkdir(parents=True,exist_ok=True);temporary=checkpoint.with_suffix('.tmp')
            with temporary.open('wb') as f:
                np.savez_compressed(f,signature=signature,values=values[:event+1],support=support[:event+1],
                    rho=state.rho,pending=state.pending,initiated=state.initiated,completed=state.completed,step=state.step,
                    fills=np.array(fills),offsets=np.array(offsets,dtype=np.int32),previous=previous,
                    checks=np.array([max_budget,max_ledger,unfilled,min_spread]))
            temporary.replace(checkpoint);print(f'{name}: saved {event+1}/{n} events',flush=True)
    if unfilled>1e-9:raise ValueError('Unfilled long-run demand: '+name)
    if first_tape:finish_tape(first_tape)
    return {**({'support':support} if diagnostic else {}),'name':name,'seed':seed,'kind':kind,'options':options,'values':values,'signs':signs,'parents':parents,
      'runs':runs,'fills':np.array(fills),'offsets':np.array(offsets,dtype=np.int32),'tape':first_tape,
      'summary':{'max_budget_error':max_budget,'max_ledger_error':max_ledger,'minimum_spread':min_spread,
                 'unfilled':unfilled,'initialization':relax,'events_including_burn':n}}


def resolution_runs(root,c,version,cache_dir=None):
    """Four paired paths; cache is optional scratch, never an accepted result."""
    s=dict(c['statistics'],resolution_diagnostics=True,progress_every_events=c['resolution']['progress_every_events'])
    jobs=[]
    for j in c['resolution']['replicates']:
        for dx in c['resolution']['dx']:
            name=f'resolution-{dx}-{j}';settings=dict(s)
            if cache_dir:settings['_checkpoint']=str(Path(cache_dir)/(name+'.npz'))
            options={k:c['resolution'][k] for k in ('du','phase','half_width')};options['dx']=dx
            jobs.append((name,c['model'],options,settings,s['seeds'][j],'lmf'))
    results=execute_jobs(long_run,jobs,c['assessment']['workers']);arrays={};meta=[]
    for r in sorted(results,key=lambda x:x['name']):
        for key in ('values','signs','parents','runs','fills','offsets','support'):arrays[r['name']+'-'+key]=r[key]
        meta.append({k:r[k] for k in ('name','seed','kind','options','summary')})
    np.savez_compressed(root/'outputs'/('resolution-paths-'+version+'.npz'),columns=np.array(LONG_COLUMNS),
        support_columns=np.array(['bid_external_stop','ask_external_start','bid_completion_start','bid_completion_stop',
        'ask_completion_start','ask_completion_stop','external_node_flips','completion_node_flips','changed_steps']),**arrays)
    (root/'outputs'/('resolution-runs-'+version+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
    return arrays,meta


def execute_jobs(worker,jobs,workers):
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(worker,j):j[0] for j in jobs}
        for future in as_completed(pending):
            result=future.result();results.append(result);print('Assessment completed: '+pending[future],flush=True)
    return results


def assess(root,c,version,names=None):
    a=c['assessment'];base=c['model'];out=root/'outputs'
    jobs=[(x['name'],base,x['options'],c['events'],c['horizon'],a['sample_du']) for x in a['runs'] if names is None or x['name'] in names]
    if names is not None and {j[0] for j in jobs}!=set(names):raise ValueError('Unregistered finite refinement')
    result=execute_jobs(finite_run,jobs,a['workers'])
    arrays={};summaries=[]
    if names is not None:
        with np.load(out/('assessment-'+version+'.npz')) as saved:arrays={k:saved[k] for k in saved.files}
        summaries=[r for r in json.loads((out/('assessment-'+version+'.json')).read_text())['runs'] if r['name'] not in names]
    for name,rows,summary,x,rho in sorted(result):
        arrays[name]=rows;arrays[name+'-x']=x;arrays[name+'-final-density']=rho;summaries.append(summary)
    summaries.sort(key=lambda r:r['name'])
    np.savez_compressed(out/('assessment-'+version+'.npz'),**dict(sorted(arrays.items())))
    (out/('assessment-'+version+'.json')).write_text(json.dumps({'runs':summaries,'status':'numerical assessment; see comparisons'},indent=2)+'\n')
    return arrays,summaries


def control_jobs(c):
    a=c['assessment'];s=a['control_refinement'];jobs=[]
    events=[dict(e,side='sell' if j%2 else 'buy') for j,e in enumerate(c['events'])]
    for phase in s['phases']:
        for dx in s['dx']:
            for mode in s['modes']:
                name=f'balanced-refined-{dx}-{phase}-{mode}'
                options=dict(dx=dx,du=s['du'],phase=phase,half_width=s['half_width'],**a['market_maker_modes'][mode])
                jobs.append((name,c['model'],options,events,c['horizon'],a['sample_du']))
    return jobs


def response_jobs(c):
    a=c['assessment'];s=a['response_refinement'];jobs=[]
    events=[dict(e,side='sell' if j%2 else 'buy') for j,e in enumerate(c['events'])]
    for phase in s['phases']:
        for dx in s['dx']:
            for mode in s['modes']:
                name=f'balanced-response-{dx}-{phase}-{mode}'
                options=dict(dx=dx,du=s['du'],phase=phase,half_width=s['half_width'],**a['market_maker_modes'][mode])
                jobs.append((name,c['model'],options,events,c['horizon'],a['sample_du']))
    return jobs


def market_maker_runs(root,c,version,refined_only=False):
    a=c['assessment'];base=c['model'];jobs=[]
    for resolution,grid in a['market_maker_grids'].items():
        for flow in ('directional','balanced'):
            events=[dict(e,side='sell' if flow=='balanced' and j%2 else 'buy') for j,e in enumerate(c['events'])]
            for mode,override in a['market_maker_modes'].items():
                if resolution=='fine' and (flow!='balanced' or mode not in ('moving','fixed','width-fixed')):continue
                prefix='' if resolution=='primary' else resolution+'-'
                jobs.append((prefix+flow+'-'+mode,base,dict(grid,**override),events,c['horizon'],a['sample_du']))
    jobs=response_jobs(c) if refined_only else jobs+control_jobs(c)+response_jobs(c)
    result=execute_jobs(finite_run,jobs,a['workers']);arrays={};summaries=[]
    if refined_only:
        with np.load(root/'outputs'/('market-maker-'+version+'.npz')) as saved:arrays={k:saved[k] for k in saved.files}
        names={j[0] for j in jobs}
        summaries=[r for r in json.loads((root/'outputs'/('market-maker-'+version+'.json')).read_text()) if r['name'] not in names]
    for name,rows,summary,x,rho in sorted(result):arrays[name]=rows;summaries.append(summary)
    arrays=dict(sorted(arrays.items()));summaries.sort(key=lambda r:r['name'])
    np.savez_compressed(root/'outputs'/('market-maker-'+version+'.npz'),**arrays)
    (root/'outputs'/('market-maker-'+version+'.json')).write_text(json.dumps(summaries,indent=2)+'\n')
    return arrays,summaries


def response_difference(left,right):
    """Compare sampled quotes without hiding stationary baseline offsets."""
    if left.shape!=right.shape or not np.array_equal(left[:,0],right[:,0]):
        raise ValueError('Unmatched control sample times')
    result={}
    for label,k in (('midpoint',3),('spread',4)):
        absolute=left[:,k]-right[:,k];response=absolute-absolute[0]
        i=int(np.argmax(abs(response)))
        result[label]={'initial_difference':float(absolute[0]),'max_absolute_difference':float(np.max(abs(absolute))),
            'max_response_difference':float(abs(response[i])),'response_peak_u':float(left[i,0]),
            'late_response_difference':float(response[-1])}
    return result


def control_report(root,c,version):
    out=root/'outputs';s=c['assessment']['control_refinement']
    with np.load(out/('market-maker-'+version+'.npz')) as saved:a={k:saved[k] for k in saved.files}
    meta={r['name']:r for r in json.loads((out/('market-maker-'+version+'.json')).read_text())}
    comparisons=[];effects=[];contrasts={};checks=c['checks']
    target=sum(e['volume'] for e in c['events'])
    for job in control_jobs(c)+response_jobs(c):
        name,_,options,_,_,_=job;r=meta[name];d=a[name]
        if r['options']!=options or r['unfilled']>checks['unfilled_atol'] or abs(r['executed_volume']-target)>checks['unfilled_atol']:
            raise ValueError('Unmatched actual control volume: '+name)
        if r['max_budget_error']>checks['budget_atol'] or r['max_ledger_error']>checks['ledger_atol']:
            raise ValueError('Control accounting tolerance exceeded: '+name)
        if r['initialization']['max_rate_residual']>c['stationarity_tolerance']:
            raise ValueError('Control initialization tolerance exceeded: '+name)
    for phase in s['phases']:
        for dx in s['dx']:
            prefix=f'balanced-refined-{dx}-{phase}-';fixed=a[prefix+'fixed'];moving=a[prefix+'moving']
            for mode in s['modes']:
                d=a[prefix+mode];np.testing.assert_array_equal(d[:,0],fixed[:,0])
                np.testing.assert_allclose(d[:,7:11],fixed[:,7:11],rtol=0,atol=checks['ledger_atol'])
                np.testing.assert_allclose(d[0,1:5],fixed[0,1:5],rtol=0,atol=checks['no_event_drift_atol'])
                override=c['assessment']['market_maker_modes'][mode];model=dict(c['model'],**override)
                np.testing.assert_allclose(d[:,5],model['Sigma0']+model['chi_s']*(d[:,9]+d[:,10]),rtol=0,atol=checks['ledger_atol'])
                np.testing.assert_allclose(d[:,6],model['mu0']-model['chi_m']*(d[:,10]-d[:,9]),rtol=0,atol=checks['ledger_atol'])
                if mode=='fixed':continue
                z=d.copy();z[:,1:7]-=fixed[:,1:7];contrasts[(dx,phase,mode)]=z
                effects.append({'dx':dx,'phase':phase,'mode':mode,**response_difference(d,fixed)})
            z=moving.copy();z[:,1:7]=moving[:,1:7]-a[prefix+'width-fixed'][:,1:7]-a[prefix+'centre-fixed'][:,1:7]+fixed[:,1:7]
            contrasts[(dx,phase,'interaction')]=z
            zero=z.copy();zero[:,1:7]=0.
            effects.append({'dx':dx,'phase':phase,'mode':'interaction',**response_difference(z,zero)})
        lo,hi=s['dx']
        for mode in s['modes']:
            left=a[f'balanced-refined-{lo}-{phase}-{mode}'];right=a[f'balanced-refined-{hi}-{phase}-{mode}']
            comparisons.append({'kind':'trajectory','phase':phase,'mode':mode,**response_difference(left,right)})
        for mode in ('moving','width-fixed','centre-fixed','interaction'):
            comparisons.append({'kind':'effect-from-fixed' if mode!='interaction' else 'interaction','phase':phase,'mode':mode,
                **response_difference(contrasts[(lo,phase,mode)],contrasts[(hi,phase,mode)])})
    refined=c['assessment']['response_refinement'];fine_comparisons=[];fine_effects=[];matched={}
    coarse,fine=refined['dx']
    for phase in refined['phases']:
        for dx in refined['dx']:
            prefix=f'balanced-response-{dx}-{phase}-';fixed=a[prefix+'fixed']
            for mode in refined['modes']:
                d=a[prefix+mode];np.testing.assert_array_equal(d[:,0],fixed[:,0])
                np.testing.assert_allclose(d[:,7:11],fixed[:,7:11],rtol=0,atol=checks['ledger_atol'])
                np.testing.assert_allclose(d[0,1:5],fixed[0,1:5],rtol=0,atol=checks['no_event_drift_atol'])
                model=dict(c['model'],**c['assessment']['market_maker_modes'][mode])
                np.testing.assert_allclose(d[:,5],model['Sigma0']+model['chi_s']*(d[:,9]+d[:,10]),rtol=0,atol=checks['ledger_atol'])
                np.testing.assert_allclose(d[:,6],model['mu0']-model['chi_m']*(d[:,10]-d[:,9]),rtol=0,atol=checks['ledger_atol'])
                if mode!='fixed':
                    fine_effects.append({'dx':dx,'phase':phase,'mode':mode,**response_difference(d,fixed)})
                    z=d.copy();z[:,1:7]-=fixed[:,1:7];matched[(dx,phase,mode)]=z
        for mode in refined['modes']:
            left=a[f'balanced-response-{coarse}-{phase}-{mode}'];right=a[f'balanced-response-{fine}-{phase}-{mode}']
            baseline=a[f'balanced-refined-{coarse}-{phase}-{mode}']
            fine_comparisons.append({'kind':'time','phase':phase,'mode':mode,**response_difference(baseline,left)})
            fine_comparisons.append({'kind':'space','phase':phase,'mode':mode,**response_difference(left,right)})
        for mode in ('moving','centre-fixed'):
            fine_comparisons.append({'kind':'effect-from-fixed-space','phase':phase,'mode':mode,
                **response_difference(matched[(coarse,phase,mode)],matched[(fine,phase,mode)])})
    report={'version':version,'registered_matrix':s,'new_runs':len(response_jobs(c)),'inherited_refinement_runs':len(control_jobs(c)),'comparisons':comparisons,'effects':effects,
        'response_refinement':{'registered_matrix':refined,'comparisons':fine_comparisons,'effects':fine_effects,
            'all_absolute_spread_comparisons_passed':all(r['spread']['max_absolute_difference']<=c['assessment']['quote_comparison_atol'] for r in fine_comparisons if r['kind'] in ('time','space'))},
        'absolute_spread_tolerance':c['assessment']['quote_comparison_atol'],
        'all_absolute_spread_comparisons_passed':all(r['spread']['max_absolute_difference']<=c['assessment']['quote_comparison_atol'] for r in comparisons if r['kind']=='trajectory'),
        'interpretation':s['interpretation'],'status':'diagnostic controls; D2 numerical/scientific acceptance remains pending'}
    (out/('control-comparisons-'+version+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def statistical_runs(root,c,version):
    s=c['statistics'];base=c['model'];out=root/'outputs';jobs=[]
    for group,kind,overrides in [('lmf-moving','lmf',{}),('iid-moving','iid',{}),('lmf-fixed','lmf',{'chi_s':0.,'chi_m':0.})]:
        for j,seed in enumerate(s['seeds']):
            jobs.append((group+'-'+str(j),base,dict(s['grid'],**overrides),s,seed,kind))
    for j in s['refinement_replicates']:
        jobs.append(('lmf-fine-'+str(j),base,dict(s['grid'],dx=s['fine_dx'],du=s['fine_du']),s,s['seeds'][j],'lmf'))
    results=execute_jobs(long_run,jobs,c['assessment']['workers']);arrays={};meta=[]
    for r in sorted(results,key=lambda x:x['name']):
        name=r['name']
        for key in ('values','signs','parents','runs','fills','offsets'):arrays[name+'-'+key]=r[key]
        meta.append({k:r[k] for k in ('name','seed','kind','options','summary')})
        if r['tape']:
            with (out/('example-trades-'+version+'.csv')).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(r['tape'][0]),lineterminator='\n');w.writeheader();w.writerows(r['tape'])
    np.savez_compressed(out/('statistics-paths-'+version+'.npz'),columns=np.array(LONG_COLUMNS),**arrays)
    (out/('statistics-runs-'+version+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
    return arrays,meta


def comparison_report(root,c,version):
    out=root/'outputs';a=np.load(out/('assessment-'+version+'.npz'))
    pairs=[('grid-on-node-coarse','mesh-0.1-0.0','mesh-0.05-0.0'),
      ('grid-on-node-middle','mesh-0.05-0.0','mesh-0.025-0.0'),
      ('grid-on-node-fine','time-fine-0.0','mesh-0.0125-0.0'),
      ('grid-half-cell-coarse','mesh-0.1-0.5','mesh-0.05-0.5'),
      ('grid-half-cell-middle','mesh-0.05-0.5','mesh-0.025-0.5'),
      ('grid-half-cell-fine','time-fine-0.5','mesh-0.0125-0.5'),
      ('time-coarse','time-0.001','time-0.0005'),('time-fine','time-0.0005','mesh-0.05-0.0'),
      ('domain-12-16','time-0.001','domain-16.0'),('domain-16-20','domain-16.0','domain-20.0'),
      ('execution-depth','depth-1.0','depth-4.0')]
    for phase in (0.,.5):
        pairs.extend([(f'grid-refined-{phase}',f'refine-space-0.0125-{phase}',f'refine-space-0.00625-{phase}'),
          (f'time-refined-0.0125-{phase}',f'mesh-0.0125-{phase}',f'refine-space-0.0125-{phase}'),
          (f'time-refined-0.00625-{phase}',f'refine-space-0.00625-{phase}',f'refine-time-0.00625-{phase}')])
    rows=[]
    for label,left,right in pairs:
        x,y=a[left],a[right];np.testing.assert_allclose(x[:,0],y[:,0],rtol=0,atol=1e-12)
        delta=np.max(np.abs(x[:,[3,4]]-y[:,[3,4]]),axis=0)
        response=np.max(np.abs((x[:,[3,4]]-x[0,[3,4]])-(y[:,[3,4]]-y[0,[3,4]])),axis=0)
        rows.append({'comparison':label,'left':left,'right':right,'max_mid_difference':float(delta[0]),
          'max_spread_difference':float(delta[1]),'max_mid_response_difference':float(response[0]),
          'max_spread_response_difference':float(response[1])})
    result={'quote_tolerance':c['assessment']['quote_comparison_atol'],'comparisons':rows,
      'finest_grid_tolerance_passed':all(x['max_spread_difference']<=c['assessment']['quote_comparison_atol'] for x in rows if x['comparison'].startswith('grid-refined-')),
      'finest_time_tolerance_passed':all(x['max_spread_difference']<=c['assessment']['quote_comparison_atol'] for x in rows if x['comparison'].startswith('time-refined-0.00625-')),
      'interpretation':'Maxima use the common 0.02 operational-time samples including all six event times, not every field update. Each grid is independently relaxed to the same rate-residual tolerance. Half-cell padding shifts each reservoir outward by dx/2; domain effects have separate inherited checks. Passing this bounded directional programme would not accept long-path correlations or D2.'}
    (out/('assessment-comparisons-'+version+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result


ACF_NAMES=('sign','mid_return','trade_return','abs_mid_return','abs_trade_return','spread')
CCF_NAMES=('sign_mid_return','sign_spread_change','mid_trade_return','mid_return_spread_change',
           'abs_mid_return_spread','abs_trade_return_spread')


def path_statistics(values,signs,burn,maxlag):
    # Align each retained sign and post-event spread with the increment ending
    # at that same executed event. Burn-in supplies the preceding price.
    rm=np.diff(values[burn-1:,2]);rt=np.diff(values[burn-1:,6]);ds=np.diff(values[burn-1:,3])
    spread=values[burn:,3];eps=signs[burn:]
    series=[eps,rm,rt,abs(rm),abs(rt),spread]
    lags=np.arange(maxlag+1);clags=np.arange(-maxlag,maxlag+1)
    acf=np.array([lag_correlation(x,x,lags)[0] for x in series])
    pairs=[(eps,rm),(eps,ds),(rm,rt),(rm,ds),(abs(rm),spread),(abs(rt),spread)]
    ccf=np.array([lag_correlation(x,y,clags)[0] for x,y in pairs])
    return acf,ccf


def analyse_statistics(root,c,version):
    out=root/'outputs';data=np.load(out/('statistics-paths-'+version+'.npz'));s=c['statistics']
    lags=np.arange(s['maximum_lag']+1);clags=np.arange(-s['maximum_lag'],s['maximum_lag']+1)
    groups=['lmf-moving','iid-moving','lmf-fixed'];arrays={};summary={'groups':{},'fine_grid_pairs':[],
      'estimator':'Mean of separately centred, pathwise overlapping Pearson correlations; descriptive mean +/- two between-path standard errors. No iid-event confidence band.',
      'event_count_per_path':s['events'],'replicates_per_group':len(s['seeds']),'burn_events':s['burn_events'],
      'calendar_clock':False,'transport_memory':False,'sign_reference':'Stationary single-active-parent renewal benchmark with declared truncation, not the full concurrent-parent LMF population.',
      'asymptotic_untruncated_sign_exponent':s['beta']-1,'numerical_acceptance':'pending'}
    rows=[]
    for group in groups:
        acfs=[];ccfs=[];means=[];halves=[]
        for j in range(len(s['seeds'])):
            name=group+'-'+str(j);v=data[name+'-values'];sign=data[name+'-signs']
            acf,ccf=path_statistics(v,sign,s['burn_events'],s['maximum_lag']);acfs.append(acf);ccfs.append(ccf)
            after=v[s['burn_events']:];means.append([float(after[:,2].mean()),float(after[:,3].mean())])
            halves.append([float(after[:len(after)//2,3].mean()),float(after[len(after)//2:,3].mean())])
        arrays[group+'-acf']=np.array(acfs);arrays[group+'-ccf']=np.array(ccfs)
        summary['groups'][group]={'mid_spread_path_means':means,'spread_first_second_half_means':halves,
          'acf_at_lag_one':dict(zip(ACF_NAMES,np.mean(acfs,axis=0)[:,1].tolist()))}
        for kind,names,lag_values in [('acf',ACF_NAMES,lags),('ccf',CCF_NAMES,clags)]:
            a=arrays[group+'-'+kind];mean=a.mean(axis=0);se=a.std(axis=0,ddof=1)/np.sqrt(len(a))
            for k,label in enumerate(names):
                for h,lag in enumerate(lag_values):rows.append({'group':group,'kind':kind,'observable':label,'lag':int(lag),
                  'mean':float(mean[k,h]),'two_standard_errors':float(2*se[k,h]),'independent_paths':len(a),
                  'pairs_per_path':s['events']-abs(int(lag))})
    for j in s['refinement_replicates']:
        coarse=data['lmf-moving-'+str(j)+'-values'];fine=data['lmf-fine-'+str(j)+'-values']
        sign=data['lmf-fine-'+str(j)+'-signs'];fa,fc=path_statistics(fine,sign,s['burn_events'],s['maximum_lag'])
        arrays['fine-'+str(j)+'-acf']=fa;arrays['fine-'+str(j)+'-ccf']=fc
        ca,cc=path_statistics(coarse,sign,s['burn_events'],s['maximum_lag'])
        difference=fine[s['burn_events']:, [2,3]]-coarse[s['burn_events']:, [2,3]]
        summary['fine_grid_pairs'].append({'replicate':j,'mid_spread_rms_difference':np.sqrt(np.mean(difference**2,axis=0)).tolist(),
          'mid_spread_max_difference':np.max(abs(difference),axis=0).tolist(),
          'maximum_acf_difference':dict(zip(ACF_NAMES,np.max(abs(fa-ca),axis=1).tolist())),
          'maximum_ccf_difference':dict(zip(CCF_NAMES,np.max(abs(fc-cc),axis=1).tolist()))})
    np.savez_compressed(out/('correlations-'+version+'.npz'),lags=lags,ccf_lags=clags,
      renewal_reference=renewal_reference(lags,s['beta'],s['minimum_parent'],s['parent_cap']),**arrays)
    with (out/('correlations-'+version+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    (out/('statistics-summary-'+version+'.json')).write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary


def analyse_resolution(root,c,version):
    out=root/'outputs';new=np.load(out/('resolution-paths-'+version+'.npz'))
    old=np.load(out/('statistics-paths-'+version+'.npz'));s=c['statistics'];burn=s['burn_events'];lag=s['maximum_lag']
    report={'paths':[],'pairs':[],'acceptance':'pending','scope':'Two matched full tapes; same physical child volume. Half-cell long paths; both source phases retained in the finite assessment.'}
    correlations={}
    for j in c['resolution']['replicates']:
        names=[('time-control-'+str(j),old,'lmf-fine-'+str(j))]+[(f'resolution-{dx}-{j}',new,f'resolution-{dx}-{j}') for dx in c['resolution']['dx']]
        for label,data,key in names:
            v=data[key+'-values'];sign=data[key+'-signs'];post=v[:,2];pre=v[:,4:6].mean(axis=1)
            jump=(post-pre)[burn:];field=pre[burn:]-post[burn-1:-1];total=np.diff(post[burn-1:])
            count=np.diff(data[key+'-offsets'])[burn:];acf,ccf=path_statistics(v,sign,burn,lag)
            correlations[label+'-acf']=acf;correlations[label+'-ccf']=ccf
            row={'name':label,'one_node_fraction':float(np.mean(count==1)),'mean_fill_nodes':float(count.mean()),'maximum_fill_nodes':int(count.max()),
                'execution_jump_std':float(jump.std()),'field_increment_std':float(field.std()),'mid_increment_std':float(total.std()),
                'jump_field_correlation':float(np.corrcoef(jump,field)[0,1]),'decomposition_max_error':float(np.max(abs(total-jump-field))),
                'placement_width_range':float(np.ptp(v[burn:,9])), 'acf_at_lag_one':dict(zip(ACF_NAMES,acf[:,1].tolist()))}
            if data is new:
                support=data[key+'-support'][burn:];row['external_node_flips']=int(support[:,6].sum());row['completion_node_flips']=int(support[:,7].sum())
                row['source_changed_step_fraction']=float(support[:,8].sum()/(len(support)*round(s['event_du']/c['resolution']['du'])))
                row['events_with_source_change_fraction']=float(np.mean(support[:,8]>0))
            report['paths'].append(row)
        for kind,left,right in [('time',names[0],names[1]),('space',names[1],names[2])]:
            ln,ld,lk=left;rn,rd,rk=right
            for key in ('signs','parents','runs'):np.testing.assert_array_equal(ld[lk+'-'+key],rd[rk+'-'+key])
            delta=rd[rk+'-values'][burn:,:4]-ld[lk+'-values'][burn:,:4]
            report['pairs'].append({'replicate':j,'comparison':kind,'left':ln,'right':rn,'matched_tape':True,
                'max_bid_ask_mid_spread_difference':np.max(abs(delta),axis=0).tolist(),'rms_bid_ask_mid_spread_difference':np.sqrt(np.mean(delta**2,axis=0)).tolist(),
                'maximum_acf_difference':dict(zip(ACF_NAMES,np.max(abs(correlations[rn+'-acf']-correlations[ln+'-acf']),axis=1).tolist())),
                'maximum_ccf_difference':dict(zip(CCF_NAMES,np.max(abs(correlations[rn+'-ccf']-correlations[ln+'-ccf']),axis=1).tolist()))})
    report['finite_assessment']=json.loads((out/('assessment-comparisons-'+version+'.json')).read_text())
    np.savez_compressed(out/('resolution-correlations-'+version+'.npz'),lags=np.arange(lag+1),ccf_lags=np.arange(-lag,lag+1),**correlations)
    (out/('resolution-summary-'+version+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def increment_covariance_parts(jump,field,lags):
    """Exact Pearson ACF decomposition, using the total increment denominator.

    Entries are Cov(J,J'), Cov(J,F'), Cov(F,J'), Cov(F,F') divided by
    sd(J+F)*sd(J'+F'), with separate means for each overlapping slice.
    They are signed contributions, not individual correlation coefficients.
    """
    jump=np.asarray(jump,dtype=float);field=np.asarray(field,dtype=float)
    if jump.ndim!=1 or jump.shape!=field.shape or not np.all(np.isfinite(jump+field)):
        raise ValueError('Invalid aligned increment components')
    rows=[]
    for lag in lags:
        if not isinstance(lag,(int,np.integer)) or not 0<=lag<len(jump)-1:
            raise ValueError('Invalid decomposition lag')
        left=np.array([jump[:len(jump)-lag],field[:len(jump)-lag]])
        right=np.array([jump[lag:],field[lag:]])
        left=left-left.mean(axis=1,keepdims=True);right=right-right.mean(axis=1,keepdims=True)
        denominator=left.sum(axis=0).std()*right.sum(axis=0).std()
        if denominator==0:raise ValueError('Zero-variance total increment')
        parts=(left@right.T/left.shape[1]/denominator).ravel()
        total=jump+field;actual=lag_correlation(total,total,[lag])[0][0]
        rows.append({'lag':int(lag),'contributions':parts.tolist(),'total_acf':float(actual),
                     'sum_residual':float(parts.sum()-actual)})
    return rows


def frozen_execution_probe(m,rho,subdivision,volume,side):
    """Resample the same piecewise-linear field; call unchanged core execution.

    Fixed endpoints and nested nodes retain every original knot. This is an
    operator probe, not a finer DTRW path, new initialization or new trade tape.
    The return contains only observations; the input field is never mutated.
    """
    if not isinstance(subdivision,int) or subdivision<1:raise ValueError('Invalid subdivision')
    if side not in (0,1) or not np.isfinite(volume) or volume<=0:raise ValueError('Invalid probe request')
    refined=replace(m,dx=m.dx/subdivision)
    sampled=np.array([np.interp(refined.x,m.x,y) for y in rho])
    request=np.zeros(2);request[side]=volume
    post,removed,actual,unfilled,pre=execute(refined,sampled,request);after=observe(refined,post)
    quantity=refined.dx*removed[side];ids=np.flatnonzero(quantity>0)
    price=float(quantity@refined.x/actual[side]) if actual[side]>0 else None
    baseline=observe(m,rho)
    keys=('p_b','p_a','midpoint','spread')
    return {'subdivision':subdivision,'dx':refined.dx,'volume':volume,'side':side,
        'pre':{k:float(pre[k]) for k in keys},'post':{k:float(after[k]) for k in keys},
        'pre_quote_difference':max(abs(pre[k]-baseline[k]) for k in ('p_b','p_a')),
        'fill_nodes':len(ids),'executed':float(actual[side]),'unfilled':float(unfilled[side]),
        'execution_log_price':price,'filled_indices':ids.tolist(),'filled_quantities':quantity[ids].tolist(),
        'midpoint_jump':float(after['midpoint']-pre['midpoint']),
        'spread_jump':float(after['spread']-pre['spread']),
        'mass_residual':float(refined.dx*(sampled[side]-post[side]).sum()-actual[side])}


def source_quadrature_probe(m,q):
    """Nodal source versus its exact integral over retained interior cells.

    Equal pilot amplitudes/lengths imply a constant outward total, but the
    antiderivative below also handles unequal exponentials. Completion's
    reference centroid is that of its unchanged uniform support interval.
    No reference value is fed into the evolving solver.
    """
    q=np.asarray(q);lit,latent=external_source(m,q);g=placement_weights(m,q)
    edges=np.array([m.x[1]-m.dx/2,m.x[-2]+m.dx/2])
    distances=np.array([q[0]-edges[0],edges[1]-q[1]])
    if np.any(distances<=0):raise ValueError('Unresolved exterior source interval')
    exact=m.lit_amplitude*m.lit_length*(-np.expm1(-distances/m.lit_length))+m.latent_amplitude*(distances-m.latent_length*(-np.expm1(-distances/m.latent_length)))
    reference=q+np.array([-1,1])*m.placement_width/2
    return {'external_error':(m.dx*(lit+latent).sum(axis=1)-exact).tolist(),
        'completion_centroid_error':(m.dx*(g*m.x).sum(axis=1)-reference).tolist(),
        'completion_norm_error':(m.dx*g.sum(axis=1)-1).tolist(),
        'completion_nodes':np.count_nonzero(g,axis=1).tolist()}


def diagnose_resolution(root,c,version):
    """Bounded, non-evolving diagnosis of source, quote and execution operators."""
    out=root/'outputs';settings=c['diagnosis'];m=Model(**c['model'])
    data=np.load(out/('density-'+version+'.npz'));np.testing.assert_array_equal(data['x'],m.x)
    replay=[];source=[];paths=[];probes=[]
    # The six archived pre-event fields retain their original nodal knots.
    for event,rho in enumerate(data['pre_consumption']):
        request=c['events'][event];side=1 if request['side']=='buy' else 0
        post,removed,actual,unfilled,_=execute(m,rho,np.eye(2)[side]*request['volume'])
        np.testing.assert_array_equal(post,data['post_consumption'][event])
        np.testing.assert_array_equal(removed,data['removed'][event])
        replay.append({'event':event,'exact_saved_execution_replay':True})
        for subdivision in settings['subdivisions']:
            for volume in settings['volumes']:
                for side in (0,1):
                    probes.append(dict(event=event,**frozen_execution_probe(m,rho,subdivision,volume,side)))
    # Fixed common placement quotes translated across one original mesh cell.
    # Refinement uses fixed endpoints; no reservoir or source formula moves.
    q0=placement(m,settings['source_pending']);shift=np.linspace(-m.dx/2,m.dx/2,settings['source_shift_steps']+1)
    for subdivision in settings['subdivisions']:
        mm=replace(m,dx=m.dx/subdivision);rows=[source_quadrature_probe(mm,q0+v) for v in shift]
        source.append({'subdivision':subdivision,'dx':mm.dx,'shifts':shift.tolist(),'rows':rows,
            'max_abs_external_error':float(np.max(abs(np.array([r['external_error'] for r in rows])))),
            'max_abs_completion_centroid_error':float(np.max(abs(np.array([r['completion_centroid_error'] for r in rows])))),
            'max_abs_completion_norm_error':float(np.max(abs(np.array([r['completion_norm_error'] for r in rows]))))})
    # A one-sided boundary probe measures the jump without time evolution.
    boundary=[]
    for subdivision in settings['subdivisions']:
        mm=replace(m,dx=m.dx/subdivision);qb=mm.x[np.argmin(abs(mm.x-q0[0]))];qa=mm.x[np.argmin(abs(mm.x-q0[1]))]
        epsilon=mm.dx*1e-8;states=[]
        for delta in (-epsilon,epsilon):
            q=np.array([qb,qa])+delta;lit,latent=external_source(mm,q);g=placement_weights(mm,q)
            states.append((lit+latent,g))
        boundary.append({'dx':mm.dx,'epsilon':epsilon,
            'external_volume_jump':(mm.dx*(states[1][0]-states[0][0]).sum(axis=1)).tolist(),
            'completion_L1_change':(mm.dx*np.abs(states[1][1]-states[0][1]).sum(axis=1)).tolist()})
    with np.load(out/('resolution-paths-'+version+'.npz')) as a:
        burn=c['statistics']['burn_events']
        for j in c['resolution']['replicates']:
            for dx in c['resolution']['dx']:
                name=f'resolution-{dx}-{j}';v=a[name+'-values'];post=v[:,2];pre=v[:,4:6].mean(axis=1)
                jump=(post-pre)[burn:];field=pre[burn:]-post[burn-1:-1];total=np.diff(post[burn-1:])
                changed=a[name+'-support'][burn:,8]>0
                conditioned=[]
                for flag in (False,True):
                    mask=changed==flag
                    conditioned.append({'source_changed':flag,'events':int(mask.sum()),
                        'mean_abs_midpoint_increment':float(np.mean(abs(total[mask]))),
                        'mean_abs_execution_jump':float(np.mean(abs(jump[mask]))),
                        'mean_abs_field_increment':float(np.mean(abs(field[mask])))})
                paths.append({'name':name,'conditional_descriptions':conditioned,
                    'acf_decomposition':increment_covariance_parts(jump,field,settings['decomposition_lags'])})
    comparison=[]
    for volume in settings['volumes']:
        for left,right in zip(settings['subdivisions'][:-1],settings['subdivisions'][1:]):
            lp=[p for p in probes if p['volume']==volume and p['subdivision']==left]
            rp=[p for p in probes if p['volume']==volume and p['subdivision']==right]
            comparison.append({'volume':volume,'left_subdivision':left,'right_subdivision':right,
                'max_abs_spread_jump_difference':max(abs(a['spread_jump']-b['spread_jump']) for a,b in zip(lp,rp)),
                'max_abs_execution_price_difference':max(abs(a['execution_log_price']-b['execution_log_price']) for a,b in zip(lp,rp))})
    report={'version':version,'scope':settings['interpretation'],'acceptance':'pending',
        'source_field':'Six pre-event states of the original finite programme; no field relaxation or evolution in these probes.',
        'nested_grid_note':'Fixed endpoints and subdivisions preserve the same piecewise-linear function; these are not the half-cell full-path grid comparison.',
        'source_reference_note':'Exact integral over retained interior cell intervals; completion centroid of the original uniform support. Diagnostic only.',
        'contribution_order':['execution_execution','execution_field','field_execution','field_field'],
        'causality_note':'Support-change conditioning is descriptive; events, inventory and field evolution are dependent. No causal fraction is inferred.',
        'replay':replay,'frozen_execution':probes,'frozen_comparison':comparison,'source_sweep':source,
        'source_boundary':boundary,'path_decomposition':paths,
        'max_pre_quote_difference':max(p['pre_quote_difference'] for p in probes),
        'max_mass_residual':max(abs(p['mass_residual']) for p in probes),
        'max_unfilled':max(p['unfilled'] for p in probes),
        'max_acf_sum_residual':max(abs(r['sum_residual']) for p in paths for r in p['acf_decomposition'])}
    (out/('diagnosis-'+version+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def continuous_fill_reference(x,density,quote,depth,volume,direction):
    """Exact volume and first moment of a frozen piecewise-linear density.

    Consume continuously outward from quote for comparison only. No field
    changes, new trade tape or alternate evolving solver is produced.
    """
    x=np.asarray(x,dtype=float);density=np.asarray(density,dtype=float)
    if x.ndim!=1 or len(x)<2 or density.shape!=x.shape or np.any(np.diff(x)<=0):
        raise ValueError('Invalid reference grid')
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(density)) or np.any(density<0):
        raise ValueError('Invalid reference density')
    if direction not in (-1,1) or not np.all(np.isfinite([quote,depth,volume])) or depth<=0 or volume<=0:
        raise ValueError('Invalid reference request')
    end=quote+direction*depth
    if not x[0]<=min(quote,end)<=max(quote,end)<=x[-1]:raise ValueError('Reference interval leaves grid')
    distance=direction*(x-quote);knots=np.r_[0.,np.sort(distance[(distance>0)&(distance<depth)]),depth]
    values=np.interp(quote+direction*knots,x,density)
    remaining=float(volume);filled=moment=0.;front=float(quote)
    for t0,t1,a,b in zip(knots[:-1],knots[1:],values[:-1],values[1:]):
        if remaining<=0:break
        width=t1-t0;slope=(b-a)/width;capacity=width*(a+b)/2
        if capacity<=0:continue
        take=min(remaining,capacity)
        length=width if take==capacity else 2*take/(a+np.sqrt(max(0.,a*a+2*slope*take)))
        start=quote+direction*t0
        moment+=start*take+direction*(a*length**2/2+slope*length**3/3)
        filled+=take;remaining-=take;front=quote+direction*(t0+length)
    return {'filled_quantity':float(filled),'unfilled_quantity':float(max(remaining,0.)),
        'mean_log_price':float(moment/filled) if filled>0 else None,'terminal_price':float(front)}


def audit_discretization(root,c,version):
    """Paper constraints and current-letter benchmarks, without evolution."""
    out=root/'outputs';m=Model(**c['model']);subdivisions=c['audit']['execution_subdivisions']
    comparisons=[];references=[];reaction=[]
    with np.load(out/('density-'+version+'.npz')) as saved:
        x=saved['x'];fields=saved['pre_consumption'];rho=saved['rho'];initial=saved['initial']
    with (out/('density-index-'+version+'.csv')).open() as f:index=list(csv.DictReader(f))
    for event,field in enumerate(fields):
        obs=observe(m,field)
        for side in (0,1):
            for volume in c['diagnosis']['volumes']:
                ref=continuous_fill_reference(x,field[side],obs['p_b' if side==0 else 'p_a'],m.execution_depth,volume,-1 if side==0 else 1)
                references.append(dict(event=event,side=side,volume=volume,**ref))
                for subdivision in subdivisions:
                    probe=frozen_execution_probe(m,field,subdivision,volume,side)
                    comparisons.append({'event':event,'side':side,'volume':volume,'dx':m.dx/subdivision,
                        'nodal_price':probe['execution_log_price'],'reference_price':ref['mean_log_price'],
                        'price_error':probe['execution_log_price']-ref['mean_log_price'],
                        'fill_nodes':probe['fill_nodes'],'unfilled':probe['unfilled']})
    error=[]
    for volume in c['diagnosis']['volumes']:
        for subdivision in subdivisions:
            rows=[r for r in comparisons if r['volume']==volume and r['dx']==m.dx/subdivision]
            error.append({'volume':volume,'dx':m.dx/subdivision,'max_abs_price_error':max(abs(r['price_error']) for r in rows),
                          'rms_price_error':float(np.sqrt(np.mean([r['price_error']**2 for r in rows])))})
    # A cell average cannot silently replace a literal nodal support formula.
    node=float(x[np.argmin(abs(x-6.))]);q=np.array([-node-m.dx/4,node+m.dx/4])
    left=x-m.dx/2;right=x+m.dx/2
    averaged=np.array([np.maximum(0,np.minimum(right,q[0])-left),np.maximum(0,right-np.maximum(left,q[1]))])/m.dx
    averaged[:,[0,-1]]=0;inward=np.array([x>q[0],x<q[1]])
    lit,latent=external_source(m,q);original=lit+latent
    counterexample={'q':q.tolist(),'candidate':'Cell average of the unit pilot source stored at node centres',
        'inward_nodes_with_candidate_supply':int(np.count_nonzero((averaged>0)&inward)),
        'inward_candidate_rate':float(m.dx*averaged[inward].sum()),'inward_nodal_rate':float(m.dx*original[inward].sum()),
        'decision':'Rejected as a drop-in replacement: violates literal discrete nodal support. A finite-volume interpretation needs an explicit changed contract.'}
    for frame,(field,row) in enumerate(zip(rho,index)):
        phi=field[0]-field[1];hits=np.flatnonzero(phi[:-1]*phi[1:]<0)
        roots=np.r_[x[phi==0],x[hits]-phi[hits]*(x[hits+1]-x[hits])/(phi[hits+1]-phi[hits])]
        unique=len(roots)==1 and not np.any((phi[:-1]==0)&(phi[1:]==0))
        mid=(float(row['p_b'])+float(row['p_a']))/2
        reaction.append({'frame':frame,'u':float(row['u']),'phase':row['phase'],'root_count':len(roots),
            'quoted_midpoint':mid,'reaction_price':float(roots[0]) if unique else None,
            'difference':float(roots[0]-mid) if unique else None})
    obs=observe(m,initial);q=placement(m,[0.,0.]);length=np.sqrt(m.D/m.nu)
    depth=np.array([obs['p_b']-q[0],q[1]-obs['p_a']]);point=np.exp(-depth/length)
    factor=-np.expm1(-m.placement_width/length)*length/m.placement_width
    kernel={'scope':'Frozen whole-line killed-diffusion reference only; no fit or validation of the nonlinear DTRW response.',
        'placement_width':m.placement_width,'cancellation_length':float(length),'width_over_length':float(m.placement_width/length),
        'initial_penetration_depth':depth.tolist(),'edge_point_attenuation':point.tolist(),
        'uniform_placement_attenuation':(point*factor).tolist(),'uniform_to_edge_point_ratio':float(factor),
        'decision':'Use the distributed-profile convolution for this pilot. This width is not a demonstrated narrow-placement limit.'}
    report={'version':version,'long_paper_version':'v1.1.9','letter_version':c['audit']['letter_version'],
        'letter_sha256':c['audit']['letter_sha256'],'letter_authors':['Christopher Angstmann','Derick Diana','Tim Gebbie'],
        'acceptance':'D2 pending; no production source/execution correction justified by this audit',
        'core_equation_labels':['eq:bid','eq:ask','eq:litBid','eq:litAsk','eq:latentBid','eq:latentAsk','eq:placementWeights','eq:placementSupportQuote','eq:forcingCap','eq:discreteBidCrossing'],
        'source_counterexample':counterexample,'continuous_execution_reference':references,'nodal_execution_comparison':comparisons,
        'execution_error_summary':error,'reaction_price_samples':reaction,
        'reaction_price_max_abs_midpoint_difference':max(abs(r['difference']) for r in reaction if r['difference'] is not None),
        'ambiguous_reaction_price_frames':sum(r['reaction_price'] is None for r in reaction),
        'distributed_replenishment_reference':kernel,
        'scope':'Saved fields and fixed source geometry only. No new path, trade tape, source, equation or figure.'}
    (out/('paper-audit-'+version+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report
