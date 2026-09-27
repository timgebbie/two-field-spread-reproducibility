"""Reproduce the numerical pilot, or render its verified saved data."""
from pathlib import Path
import argparse
import platform
import shutil
import subprocess
import sys
import unittest
import numpy as np
import matplotlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from functions.experiments import VERSION,load_config,run_experiments,dump,save_manifest,verify_manifest
from functions.assessment import assess,market_maker_runs,statistical_runs,comparison_report,analyse_statistics,resolution_runs,analyse_resolution,diagnose_resolution


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-only',action='store_true',help='Verify saved data and inputs; rebuild figures/video without solving')
    parser.add_argument('--diagnose-only',action='store_true',help='Verify saved data and reproduce the bounded non-evolving operator diagnosis')
    args=parser.parse_args()
    if (np.__version__,matplotlib.__version__)!=('2.3.5','3.10.8'):
        raise SystemExit('Install the pinned dependencies in pyproject.toml before reproducing')
    if not shutil.which('ffmpeg'):raise SystemExit('FFmpeg with libx264 must be installed and on PATH for the video')
    c,m=load_config(ROOT)
    if args.diagnose_only:
        if args.render_only:raise SystemExit('Select one saved-data route')
        verify_manifest(ROOT)
        diagnose_resolution(ROOT,c,VERSION)
        verify_manifest(ROOT)
        print(VERSION+' frozen-state diagnosis reproduced; no new path evolved.')
        return
    if args.render_only:verify_manifest(ROOT)
    else:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():raise SystemExit(1)
        assess(ROOT,c,VERSION)
        numerical=comparison_report(ROOT,c,VERSION)
        market_maker_runs(ROOT,c,VERSION)
        statistical_runs(ROOT,c,VERSION)
        analyse_statistics(ROOT,c,VERSION)
        resolution_runs(ROOT,c,VERSION)
        analyse_resolution(ROOT,c,VERSION)
        report=run_experiments(ROOT,c,m,result.testsRun)
        diagnose_resolution(ROOT,c,VERSION)
        dump(ROOT/'outputs'/('environment-'+VERSION+'.json'),{'python':platform.python_version(),'numpy':np.__version__,
            'matplotlib':matplotlib.__version__,'platform':platform.system(),
            'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]})
        print('Finest-grid tolerance passed: '+str(numerical['finest_grid_tolerance_passed']),flush=True)
    from functions.render import render,render_assessment
    render(ROOT,c,m)
    render_assessment(ROOT,c)
    if not args.render_only:save_manifest(ROOT)
    else:verify_manifest(ROOT)
    print(VERSION+' reproduction complete; convergence acceptance remains pending.')


if __name__=='__main__':main()
