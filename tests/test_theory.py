"""Independent quadrature, root and limit checks of the evaluators."""
from pathlib import Path
import math
import sys
import unittest

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq, minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from functions import theory as th


class TheoryTests(unittest.TestCase):
    def test_heat_mass_with_cancellation(self):
        for D, nu, t in [(.3, .2, .1), (2., 1., 3.)]:
            value = quad(lambda x: float(th.heat_kernel(t, D, nu, abs(x))), -np.inf, np.inf)[0]
            self.assertAlmostEqual(value, math.exp(-nu*t), delta=2e-10)

    def test_peak_against_scalar_optimization(self):
        for D, nu, d in [(1., 0., 2.), (.3, 2., 1.7), (2., .2, .4)]:
            # Independent log-kernel objective, optimized without using the peak.
            f = lambda z: nu*math.exp(z)+.5*z+d*d/(4*D*math.exp(z))
            opt = minimize_scalar(f, bounds=(-15, 15), method='bounded', options={'xatol':1e-12})
            self.assertAlmostEqual(math.exp(opt.x)/th.peak_lag(d, D, nu), 1., delta=3e-7)

    def test_point_integral_by_quadrature(self):
        for D, nu, d in [(1., 1., 1.3), (.3, 2., 1.7), (2., .2, .4)]:
            # tau=z^2 removes the integrable endpoint singularity.
            direct = quad(lambda z: math.exp(-nu*z*z)/math.sqrt(math.pi*D), 0, np.inf, epsabs=1e-11)[0]
            offset = quad(lambda z: math.exp(-nu*z*z-d*d/(4*D*z*z))/math.sqrt(math.pi*D), 0, np.inf, epsabs=1e-11)[0]
            self.assertAlmostEqual(offset/direct, th.integrated_attenuation(d,D,nu), delta=2e-10)

    def test_uniform_kernel_by_spatial_quadrature(self):
        for t, d, w in [(1e-4,0.,.5),(.01,.3,.5),(1.,1.,.5),(3.,4.,.1)]:
            independent = quad(lambda y: math.exp(-t-y*y/(4*t))/math.sqrt(4*math.pi*t)/w, d,d+w, epsabs=1e-12)[0]
            self.assertAlmostEqual(float(th.uniform_kernel(t,distance=d,width=w)),independent,delta=2e-11)

    def test_uniform_integral_by_time_quadrature(self):
        for d,w in [(0.,.5),(1.3,.5),(2.,1.)]:
            integral = quad(lambda t: float(th.uniform_kernel(t,distance=d,width=w)),0,np.inf,epsabs=2e-11)[0]
            self.assertAlmostEqual(integral/.5, th.integrated_attenuation(d,width=w), delta=1e-9)

    def test_point_source_limit(self):
        ts = np.geomspace(.03,3,25)
        np.testing.assert_allclose(th.uniform_kernel(ts,distance=.7,width=1e-6), th.heat_kernel(ts,distance=.7), rtol=7e-6)
        np.testing.assert_allclose(th.uniform_kernel(ts,width=0),th.heat_kernel(ts),rtol=0,atol=0)
        self.assertAlmostEqual(th.integrated_attenuation(1.,width=1e-9),math.exp(-1),delta=3e-10)

    def test_stationary_equation_and_reflection(self):
        x = np.array([-4.,-2.,-.5,.5,2.,4.]); h=2e-4
        b=th.stationary_step(x)
        residual=(th.stationary_step(x+h)-2*b+th.stationary_step(x-h))/h**2-b+(x<0)
        np.testing.assert_allclose(residual,0,atol=2e-8)
        np.testing.assert_allclose(th.stationary_step(x,side='ask'),th.stationary_step(-x),rtol=0,atol=0)
        np.testing.assert_allclose(b+th.stationary_step(x,side='ask'),1,atol=1e-15)

    def test_stationary_threshold_roots(self):
        for eps in [.03,.1,.3]:
            pb=brentq(lambda x: float(th.stationary_step(x,q=-6)-eps),-6,6)
            pa=brentq(lambda x: float(th.stationary_step(x,q=6,side='ask')-eps),-6,6)
            d=float(th.penetration(.5,eps))
            self.assertAlmostEqual(pb,-6+d,delta=2e-12)
            self.assertAlmostEqual(pa,6-d,delta=2e-12)
            self.assertGreater(pa-pb,0)

    def test_log_threshold_sensitivity(self):
        h=1e-5; eps=.1
        spread=lambda e: 12-2*th.penetration(.5,e)
        derivative=(spread(eps*math.exp(h))-spread(eps*math.exp(-h)))/(2*h)
        self.assertAlmostEqual(derivative,2.,delta=1e-9)

    def test_capacity_from_integrated_kernel(self):
        for D,nu,slope,T in [(1.4,.6,.7,.2),(1.,0.,.1,2.),(.3,2.,2.,5.)]:
            C=quad(lambda z: math.exp(-nu*z*z)/(slope*math.sqrt(math.pi*D)),0,math.sqrt(T),epsabs=1e-12)[0]
            self.assertAlmostEqual(float(th.window_response(T,slope,D,nu)),C,delta=1e-11)
            self.assertAlmostEqual(float(th.window_capacity(T,slope,D,nu))*C,T,delta=1e-10)

    def test_capacity_limits_and_rate_convention(self):
        T=1e-7
        self.assertAlmostEqual(th.window_capacity(T)/math.sqrt(math.pi*T),1,delta=5e-8)
        self.assertAlmostEqual(th.window_capacity(100.)/100.,2,delta=1e-12)
        T=2.; h=1e-5
        endpoint_rate=(th.window_response(T+h,nu=0)-th.window_response(T-h,nu=0))/(2*h)
        self.assertAlmostEqual(1/endpoint_rate/th.window_capacity(T,nu=0),2,delta=2e-9)

    def test_parameter_domains(self):
        invalid=[lambda: th.heat_kernel(0),lambda: th.heat_kernel(1,D=0),lambda: th.heat_kernel(1,nu=-1),
                 lambda: th.peak_lag(0),lambda: th.integrated_attenuation(1,nu=0),
                 lambda: th.penetration(.5,.5),lambda: th.penetration(.5,0),
                 lambda: th.window_capacity(0),lambda: th.uniform_kernel(1,width=-1),
                 lambda: th.stationary_step(0,nu=0),lambda: th.heat_kernel(np.nan)]
        for f in invalid:
            with self.subTest(call=f):
                with self.assertRaises(ValueError): f()


if __name__ == '__main__':
    unittest.main()
