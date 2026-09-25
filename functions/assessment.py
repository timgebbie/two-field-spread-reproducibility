"""Focused mesh, market-maker and order-flow experiments; unchanged core."""
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
import json
import numpy as np
from functions.core import Model,State,advance,stationary,observe
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
    for event in range(n):
        for k in range(gap):
            request=[0.,0.]
            if k==gap-1:request[1 if signs[event]>0 else 0]=c['child_volume']
            state,r,d=advance(m,state,request)
            max_budget=max(max_budget,r['budget_error']);max_ledger=max(max_ledger,r['ledger_error'])
            min_spread=min(min_spread,r['spread']);unfilled+=r['unfilled_buy']+r['unfilled_sell']
        t,ff=trade_record(m,r,d['removed'],event+1,int(parents[event]))
        values[event]=[t['execution_log_price'] if key=='execution_log_price' else t['filled_quantity'] if key=='filled_quantity' else r[key] for key in LONG_COLUMNS]
        for f in ff:fills.append([f['grid_index'],f['filled_quantity']])
        offsets.append(len(fills))
        if name=='lmf-moving-0':first_tape.append(t)
    if unfilled>1e-9:raise ValueError('Unfilled long-run demand: '+name)
    if first_tape:finish_tape(first_tape)
    return {'name':name,'seed':seed,'kind':kind,'options':options,'values':values,'signs':signs,'parents':parents,
      'runs':runs,'fills':np.array(fills),'offsets':np.array(offsets,dtype=np.int32),'tape':first_tape,
      'summary':{'max_budget_error':max_budget,'max_ledger_error':max_ledger,'minimum_spread':min_spread,
                 'unfilled':unfilled,'initialization':relax,'events_including_burn':n}}


def execute_jobs(worker,jobs,workers):
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(worker,j):j[0] for j in jobs}
        for future in as_completed(pending):
            result=future.result();results.append(result);print('Assessment completed: '+pending[future],flush=True)
    return results


def assess(root,c,version):
    a=c['assessment'];base=c['model'];out=root/'outputs'
    jobs=[(x['name'],base,x['options'],c['events'],c['horizon'],a['sample_du']) for x in a['runs']]
    result=execute_jobs(finite_run,jobs,a['workers'])
    arrays={};summaries=[]
    for name,rows,summary,x,rho in sorted(result):
        arrays[name]=rows;arrays[name+'-x']=x;arrays[name+'-final-density']=rho;summaries.append(summary)
    np.savez_compressed(out/('assessment-'+version+'.npz'),**arrays)
    (out/('assessment-'+version+'.json')).write_text(json.dumps({'runs':summaries,'status':'numerical assessment; see comparisons'},indent=2)+'\n')
    return arrays,summaries


def market_maker_runs(root,c,version):
    a=c['assessment'];base=c['model'];jobs=[]
    for resolution,grid in a['market_maker_grids'].items():
        for flow in ('directional','balanced'):
            events=[dict(e,side='sell' if flow=='balanced' and j%2 else 'buy') for j,e in enumerate(c['events'])]
            for mode,override in a['market_maker_modes'].items():
                if resolution=='fine' and (flow!='balanced' or mode not in ('moving','fixed','width-fixed')):continue
                prefix='' if resolution=='primary' else resolution+'-'
                jobs.append((prefix+flow+'-'+mode,base,dict(grid,**override),events,c['horizon'],a['sample_du']))
    result=execute_jobs(finite_run,jobs,a['workers']);arrays={};summaries=[]
    for name,rows,summary,x,rho in sorted(result):arrays[name]=rows;summaries.append(summary)
    np.savez_compressed(root/'outputs'/('market-maker-'+version+'.npz'),**arrays)
    (root/'outputs'/('market-maker-'+version+'.json')).write_text(json.dumps(summaries,indent=2)+'\n')
    return arrays,summaries


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
    rows=[]
    for label,left,right in pairs:
        x,y=a[left],a[right];np.testing.assert_allclose(x[:,0],y[:,0],rtol=0,atol=1e-12)
        delta=np.max(np.abs(x[:,[3,4]]-y[:,[3,4]]),axis=0)
        response=np.max(np.abs((x[:,[3,4]]-x[0,[3,4]])-(y[:,[3,4]]-y[0,[3,4]])),axis=0)
        rows.append({'comparison':label,'left':left,'right':right,'max_mid_difference':float(delta[0]),
          'max_spread_difference':float(delta[1]),'max_mid_response_difference':float(response[0]),
          'max_spread_response_difference':float(response[1])})
    result={'quote_tolerance':c['assessment']['quote_comparison_atol'],'comparisons':rows,
      'finest_grid_tolerance_passed':all(x['max_spread_difference']<=c['assessment']['quote_comparison_atol'] for x in rows if x['comparison'] in ('grid-on-node-fine','grid-half-cell-fine')),
      'interpretation':'Nodal source/grid-phase effects dominate this pilot. Half-cell padding preserves reflection but shifts each reservoir outward by dx/2; the separate domain checks quantify the truncation effect. Scientific acceptance remains pending.'}
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
