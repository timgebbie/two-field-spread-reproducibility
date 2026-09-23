"""Reproduce the v0.2.0 controlled theory tables and figures."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys
import unittest
import numpy as np
import scipy
import matplotlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from functions import theory as th
from functions.plotting import render

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def produce():
    cfg_path=ROOT/'config/theory-v0.2.0.json'
    c=json.loads(cfg_path.read_text());out=ROOT/'outputs';out.mkdir(exist_ok=True)
    D,nu,supply=c['D'],c['nu'],c['supply'];ell=np.sqrt(D/nu)
    # Annotations and normalizations are registered for one dimensionless control.
    if (D,nu,supply,c['Sigma'],c['threshold'],c['capacity_slope']) != (1.,1.,1.,12.,.1,1.):
        raise ValueError('Revise registered captions and verification before changing physical parameters.')
    if c['kernel_distances']!=[0.,1.,2.] or c['attenuation_widths']!=[0.,.5,1.] or c['peak_nu_values']!=[0.,.25,1.] or c['uniform_width']!=.5:
        raise ValueError('Registered curve labels must be revised with these parameters.')
    files=[]
    def save(name,columns,names):
        p=out/(name+'-v0.2.0.csv')
        np.savetxt(p,np.column_stack(columns),delimiter=',',header=','.join(names),comments='',fmt='%.17e')
        files.append(p)
    qb,qa=-c['Sigma']/2,c['Sigma']/2;eps=c['threshold'];edge=supply/(2*nu)
    depth=float(th.penetration(edge,eps,D,nu));pb,pa=qb+depth,qa-depth
    if not qb<pb<pa<qa:raise ValueError('Reference requires ordered inward threshold crossings')
    x=np.linspace(c['x_min'],c['x_max'],c['x_count'])
    b=th.stationary_step(x,qb,'bid',D,nu,supply);a=th.stationary_step(x,qa,'ask',D,nu,supply)
    save('reference',[x,b,a,b-a,b+a],['x','rho_B','rho_A','phi','rho'])
    t=np.geomspace(c['lag_min'],c['lag_max'],c['lag_count'])
    save('kernels',[t]+[th.heat_kernel(t,D,nu,d) for d in c['kernel_distances']]+[th.uniform_kernel(t,D,nu,1.,c['uniform_width'])],['lag','point_d0','point_d1','point_d2','uniform_d1_w0p5'])
    d=np.linspace(0,c['distance_max'],c['distance_count'])
    save('peak-lag',[d[1:]]+[th.peak_lag(d[1:],D,n) for n in c['peak_nu_values']],['distance','nu0','nu0p25','nu1'])
    save('attenuation',[d]+[th.integrated_attenuation(d,D,nu,w) for w in c['attenuation_widths']],['distance','point','width0p5','width1'])
    r=np.geomspace(c['threshold_ratio_min'],c['threshold_ratio_max'],c['threshold_ratio_count'])
    depths=th.penetration(edge,r*edge,D,nu);spreads=c['Sigma']-2*depths
    if np.any(spreads<=0):raise ValueError('Registered threshold range must retain positive spread')
    save('threshold',[r,depths,spreads],['threshold_ratio','penetration','spread'])
    T=np.geomspace(c['window_min'],c['window_max'],c['window_count']);slope=c['capacity_slope']
    weak=th.window_capacity(T,slope,D,0)
    save('capacity',[T,th.window_response(T,slope,D,nu),th.window_capacity(T,slope,D,nu),weak,2*weak],['window','response_coefficient','capacity_nu1','capacity_nu0','endpoint_capacity_nu0'])
    summary={'version':c['version'],'scope':c['scope'],'D':D,'nu':nu,'kappa':0.,'ell_nu':ell,
        'q_b':qb,'q_a':qa,'p_b':pb,'p_a':pa,'threshold':eps,'edge_density':edge,'threshold_ratio':eps/edge,
        'penetration':depth,'spread':pa-pb,'placement_width':qa-qb,'slope_magnitude':eps/ell,
        'bid_threshold_residual':float(th.stationary_step(pb,qb,'bid')-eps),
        'ask_threshold_residual':float(th.stationary_step(pa,qa,'ask')-eps),
        'point_attenuation_at_penetration':float(th.integrated_attenuation(depth,D,nu)),
        'uniform_attenuation_at_penetration':float(th.integrated_attenuation(depth,D,nu,.5)),
        'point_peak_lag_at_penetration':float(th.peak_lag(depth,D,nu)),
        'units':'declared dimensionless log-price, density and operational-time units'}
    p=out/'theory-summary-v0.2.0.json';dump(p,summary);files.append(p)
    dump(out/'data-manifest-v0.2.0.json',{'files':{p.name:sha(p) for p in files},
        'configuration':{str(cfg_path.relative_to(ROOT)):sha(cfg_path)},
        'calculation_sources':{name:sha(ROOT/name) for name in ['functions/theory.py','scripts/run_all.py']}})
    dump(out/'environment-v0.2.0.json',{'python':platform.python_version(),'numpy':np.__version__,
        'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'platform':platform.system()})

def verify_saved():
    manifest=json.loads((ROOT/'outputs/data-manifest-v0.2.0.json').read_text())
    for name,expected in manifest['files'].items():
        if sha(ROOT/'outputs'/name)!=expected:raise ValueError('Saved data hash mismatch: '+name)
    for group in ('configuration','calculation_sources'):
        for name,expected in manifest[group].items():
            if sha(ROOT/name)!=expected:raise ValueError('Saved data is stale for: '+name)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plots-only',action='store_true',help='Verify and render saved tables without running evaluators')
    args=parser.parse_args()
    if not args.plots_only:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():raise SystemExit(1)
        produce()
        dump(ROOT/'outputs/verification-v0.2.0.json',{'tests_run':result.testsRun,'failures':len(result.failures),
            'errors':len(result.errors),'scope':'independent evaluator checks; no DTRW validation'})
    verify_saved();render(ROOT)
    print('v0.2.0 theory route complete: 6 tables, 2 figures (PNG/PDF); no DTRW simulation.')

if __name__=='__main__':main()
