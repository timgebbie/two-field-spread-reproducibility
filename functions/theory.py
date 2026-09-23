"""Controlled whole-line, reaction-off theory; no DTRW solver.

Coordinate x is log price; t is operational lag. See provenance/EQUATION-MAP.md.
"""
import numpy as np
from scipy.special import erf, log_ndtr


def _scalar(value, name, strictly_positive=False):
    value = float(value)
    if not np.isfinite(value) or value < 0 or (strictly_positive and value == 0):
        raise ValueError(f'{name} must be finite and ' + ('positive' if strictly_positive else 'nonnegative'))
    return value


def _array(value, name, strictly_positive=False):
    a = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(a)) or np.any(a < 0) or (strictly_positive and np.any(a == 0)):
        raise ValueError(f'{name} must be finite and ' + ('positive' if strictly_positive else 'nonnegative'))
    return a


def heat_kernel(t, D=1., nu=1., distance=0.):
    """Impulse density response at positive lag; deliberately excludes t=0."""
    t = _array(t, 'lag', True)
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu')
    d = _scalar(distance, 'distance')
    return np.exp(-nu*t - d*d/(4*D*t))/np.sqrt(4*np.pi*D*t)


def uniform_kernel(t, D=1., nu=1., distance=0., width=1.):
    """Unit-mass uniform supply at outward distances [d,d+w].

    Difference of Gaussian tails evaluated in log space to avoid cancellation
    in distant tails. width=0 returns the point-source limit explicitly.
    """
    t = _array(t, 'lag', True)
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu')
    d, w = _scalar(distance, 'distance'), _scalar(width, 'width')
    if w == 0:
        return heat_kernel(t, D, nu, d)
    scale = np.sqrt(2*D*t)
    la, lb = log_ndtr(-d/scale), log_ndtr(-(d+w)/scale)
    return np.exp(-nu*t + la)*(-np.expm1(lb-la))/w


def peak_lag(distance, D=1., nu=1.):
    """Interior maximum for d>0, including nu=0. No finite peak for d=0."""
    d = _array(distance, 'distance', True)
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu')
    return (d*d/D)/(1+np.sqrt(1+4*nu*d*d/D))


def integrated_attenuation(distance, D=1., nu=1., width=0.):
    """Ratio of integrated density responses, requiring nu>0.

    This is not a delivered-volume fraction for the two-density model.
    """
    d = _array(distance, 'distance')
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu', True)
    w = _scalar(width, 'width')
    ell = np.sqrt(D/nu)
    shape = 1. if w == 0 else -np.expm1(-w/ell)/(w/ell)
    return np.exp(-d/ell)*shape


def penetration(edge_density, threshold, D=1., nu=1.):
    """Inward exponential branch only: 0 < threshold < edge density."""
    edge = _scalar(edge_density, 'edge_density', True)
    eps = _array(threshold, 'threshold', True)
    if np.any(eps >= edge):
        raise ValueError('threshold must be below edge density on the inward branch')
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu', True)
    return np.sqrt(D/nu)*np.log(edge/eps)


def stationary_step(x, q=0., side='bid', D=1., nu=1., supply=1.):
    """Exact infinite-line D*rho''-nu*rho+S=0, kappa=0.

    S=supply to the left of q for bid, right for ask. Each far reservoir
    equals supply/nu. Positive density leaks into the source-free interval.
    """
    D, nu = _scalar(D, 'D', True), _scalar(nu, 'nu', True)
    supply = _scalar(supply, 'supply', True)
    x = np.asarray(x, dtype=float)
    if np.any(~np.isfinite(x)) or not np.isfinite(q):
        raise ValueError('x and q must be finite')
    if side not in ('bid', 'ask'):
        raise ValueError('side must be bid or ask')
    z = (x-q)/np.sqrt(D/nu)*(1 if side == 'bid' else -1)
    tail = .5*np.exp(-np.abs(z))
    return (supply/nu)*np.where(z <= 0, 1-tail, tail)


def window_response(T, slope=1., D=1., nu=1.):
    """Displacement / constant switched-on same-side depletion current."""
    T = _array(T, 'window')
    slope, D = _scalar(slope, 'slope', True), _scalar(D, 'D', True)
    nu = _scalar(nu, 'nu')
    if nu == 0:
        return np.sqrt(T)/(slope*np.sqrt(np.pi*D))
    return erf(np.sqrt(nu*T))/(2*slope*np.sqrt(D*nu))


def window_capacity(T, slope=1., D=1., nu=1.):
    """T/C(T): current divided by window-average displacement rate."""
    T = _array(T, 'window', True)
    return T/window_response(T, slope, D, nu)
