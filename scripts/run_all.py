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
from functions.render import render


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-only',action='store_true',help='Verify saved data and inputs; rebuild figures/video without solving')
    args=parser.parse_args()
    if (np.__version__,matplotlib.__version__)!=('2.3.5','3.10.8'):
        raise SystemExit('Install the pinned dependencies in pyproject.toml before reproducing')
    if not shutil.which('ffmpeg'):raise SystemExit('FFmpeg with libx264 must be installed and on PATH for the video')
    c,m=load_config(ROOT)
    if args.render_only:verify_manifest(ROOT)
    else:
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():raise SystemExit(1)
        report=run_experiments(ROOT,c,m,result.testsRun)
        dump(ROOT/'outputs'/('environment-'+VERSION+'.json'),{'python':platform.python_version(),'numpy':np.__version__,
            'matplotlib':matplotlib.__version__,'platform':platform.system(),
            'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]})
        print('Fine/coarse pilot differences: '+str(report['mesh_pilot']['max_absolute_fine_minus_coarse']),flush=True)
    render(ROOT,c,m)
    if not args.render_only:save_manifest(ROOT)
    else:verify_manifest(ROOT)
    print(VERSION+' reproduction complete; convergence acceptance remains pending.')


if __name__=='__main__':main()
