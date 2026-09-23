"""Minimal Markov DTRW side-density recurrence in operational time.

Rows are [bid, ask]. Interior-node volumes use dx*sum(rho); endpoint
densities are fixed reservoirs, excluded from the standing-volume ledger.
"""
from dataclasses import dataclass, field
import numpy as np


class ModelExit(ValueError):
    """An admissibility condition failed; no clipping or invented quote."""


@dataclass(frozen=True)
class Model:
    x_min: float = -12.
    x_max: float = 12.
    dx: float = .1
    du: float = .002
    D: float = 1.
    nu: float = 1.
    kappa: float = .5
    lit_amplitude: float = 1.
    latent_amplitude: float = 1.
    lit_length: float = 1.
    latent_length: float = 1.
    Sigma0: float = 12.
    mu0: float = 0.
    chi_s: float = .6
    chi_m: float = .1
    completion_time: float = .25
    placement_width: float = .5
    threshold: float = .1
    slope_min: float = 1e-6
    execution_depth: float = 2.
    boundary_bid: tuple = (1., 0.)
    boundary_ask: tuple = (0., 1.)

    def __post_init__(self):
        positive=['dx','du','lit_length','latent_length','placement_width','threshold','slope_min','execution_depth']
        nonnegative=['D','nu','kappa','lit_amplitude','latent_amplitude','Sigma0','chi_s','chi_m','completion_time']
        for name in positive+nonnegative:
            value=getattr(self,name)
            if not np.isfinite(value) or value<0 or (name in positive and value==0):
                raise ValueError('Invalid model parameter: '+name)
        if not np.all(np.isfinite([self.x_min,self.x_max,self.mu0])) or self.x_max<=self.x_min:
            raise ValueError('Invalid spatial domain')
        cells=(self.x_max-self.x_min)/self.dx
        if cells<4 or not np.isclose(cells,round(cells),rtol=0,atol=1e-9):
            raise ValueError('Domain length must be an integer number of grid cells')
        for bc in (self.boundary_bid,self.boundary_ask):
            if np.shape(bc)!=(2,) or np.any(~np.isfinite(bc)) or np.any(np.asarray(bc)<0):
                raise ValueError('Supply two finite nonnegative reservoir densities per side')

    @property
    def x(self):
        return np.linspace(self.x_min,self.x_max,round((self.x_max-self.x_min)/self.dx)+1)


def _density(rho, m):
    rho=np.asarray(rho,dtype=float)
    if rho.shape!=(2,len(m.x)) or np.any(~np.isfinite(rho)) or np.any(rho<0):
        raise ModelExit('Invalid side-density state')
    return rho


def placement(m, pending):
    Q=np.asarray(pending,dtype=float)
    if Q.shape!=(2,) or np.any(~np.isfinite(Q)) or np.any(Q<0):
        raise ModelExit('Invalid pending stock')
    width=m.Sigma0+m.chi_s*Q.sum()
    centre=m.mu0-m.chi_m*(Q[1]-Q[0])
    q=np.array([centre-width/2,centre+width/2])
    if not m.x_min<q[0]<=q[1]<m.x_max:
        raise ModelExit('Placement quotes left the computational domain')
    return q


def external_source(m, q):
    """The paper's lit/latent supply, supported outside the placement quotes."""
    x=m.x;distance=np.array([q[0]-x,x-q[1]])
    outward=np.maximum(distance,0)
    lit=m.lit_amplitude*np.exp(-outward/m.lit_length)*(distance>=0)
    latent=m.latent_amplitude*(-np.expm1(-outward/m.latent_length))*(distance>=0)
    lit[:,[0,-1]]=0;latent[:,[0,-1]]=0
    return lit,latent


def placement_weights(m, q):
    """Uniform nodal weights on outward [q-w,q] / [q,q+w], unit volume.

    The full support must lie among interior node centres; do not renormalize
    a profile truncated by a reservoir. Grid centroid is saved for refinement.
    """
    x=m.x;w=m.placement_width
    if q[0]-w<x[1] or q[1]+w>x[-2]:
        raise ModelExit('Completion support is truncated by a reservoir')
    g=np.array([(x>=q[0]-w)&(x<=q[0]),(x>=q[1])&(x<=q[1]+w)],dtype=float)
    g[:,[0,-1]]=0
    norms=m.dx*g.sum(axis=1)
    if np.any(norms==0):raise ModelExit('Completion support is unresolved')
    return g/norms[:,None]


def observe(m, rho):
    rho=_density(rho,m);x=m.x;prices=[];slopes=[]
    for side,y in enumerate(rho):
        z=y-m.threshold
        if (side==0 and not z[0]>0>z[-1]) or (side==1 and not z[0]<0<z[-1]):
            raise ModelExit('Threshold is unattained or meets an outer reservoir')
        down=np.flatnonzero((z[:-1]>=0)&(z[1:]<0))
        up=np.flatnonzero((z[:-1]<0)&(z[1:]>=0))
        hits=down if side==0 else up
        if len(hits)!=1 or len(down)+len(up)!=1 or np.any((z[:-1]==0)&(z[1:]==0)):
            raise ModelExit('Ambiguous or non-transverse threshold crossing')
        j=int(hits[0]);slope=(y[j+1]-y[j])/m.dx
        if abs(slope)<m.slope_min:raise ModelExit('Ill-conditioned threshold slope')
        prices.append(x[j]+(m.threshold-y[j])/slope);slopes.append(slope)
    pb,pa=prices
    contact_roundoff=32*np.finfo(float).eps*max(1.,m.x_max-m.x_min)
    if pa-pb<=contact_roundoff:raise ModelExit('Ordered two-boundary interpretation has exited or is numerically unresolved')
    return {'p_b':pb,'p_a':pa,'midpoint':(pb+pa)/2,'spread':pa-pb,
            'slope_b':slopes[0],'slope_a':slopes[1]}


def field_step(m, rho, source, completion=None):
    """Frozen-state explicit recurrence before event-integrated consumption."""
    rho=_density(rho,m);source=np.asarray(source,dtype=float)
    add=np.zeros_like(rho) if completion is None else np.asarray(completion,dtype=float)
    for term in (source,add):
        if term.shape!=rho.shape or np.any(~np.isfinite(term)) or np.any(term<0) or np.any(term[:,[0,-1]]!=0):
            raise ModelExit('Invalid interior source or completion increment')
    r=m.D*m.du/m.dx**2
    loss=2*r+m.nu*m.du+m.kappa*m.du*rho[::-1,1:-1]
    if np.any(loss>1):raise ModelExit('Explicit positivity bound failed; reduce the registered step')
    pre=rho.copy()
    pre[:,1:-1]=(1-loss)*rho[:,1:-1]+r*(rho[:,:-2]+rho[:,2:])+m.du*source[:,1:-1]+add[:,1:-1]
    if np.any(~np.isfinite(pre)) or np.any(pre<0):raise ModelExit('Invalid pre-consumption state')
    flux=m.D*m.du/m.dx*(rho[:,0]-rho[:,1]+rho[:,-1]-rho[:,-2])
    cancel=m.nu*m.du*m.dx*rho[:,1:-1].sum(axis=1)
    matched=m.kappa*m.du*m.dx*np.sum(rho[0,1:-1]*rho[1,1:-1])
    return pre,{'boundary_flux':flux,'cancelled':cancel,'matched':matched,
        'external':m.du*m.dx*source[:,1:-1].sum(axis=1),'completed':m.dx*add.sum(axis=1),
        'positivity_load':float(loss.max())}


def execute(m, rho, requested):
    """Capped node-centre price priority, outward from the pre-event crossing.

    requests=[sell,buy]. A node outside the allowed price interval is not
    executable; each retained interior node contributes rho_j*dx volume.
    This convention is explicit and must be examined under mesh refinement.
    """
    pre=_density(rho,m);obs=observe(m,pre);request=np.asarray(requested,dtype=float)
    if request.shape!=(2,) or np.any(~np.isfinite(request)) or np.any(request<0):
        raise ModelExit('Invalid requested event volume')
    post=pre.copy();removed=np.zeros_like(pre);actual=np.zeros(2);x=m.x
    for side,p in enumerate([obs['p_b'],obs['p_a']]):
        ids=np.flatnonzero((x>=p-m.execution_depth)&(x<=p)) if side==0 else np.flatnonzero((x>=p)&(x<=p+m.execution_depth))
        ids=ids[(ids>0)&(ids<len(x)-1)]
        if side==0:ids=ids[::-1]
        remaining=request[side]
        for j in ids:
            if remaining<=0:break
            available=post[side,j]*m.dx
            take=min(available,remaining)
            if take==available:post[side,j]=0.
            else:post[side,j]-=take/m.dx
            removed[side,j]=take/m.dx;remaining-=take
        actual[side]=m.dx*removed[side].sum()
    if np.any(actual-request>1e-12):raise ModelExit('Execution exceeded requested volume')
    # Nonnegative unfilled demand, allowing only floating summation roundoff.
    return post,removed,actual,np.maximum(request-actual,0),obs


@dataclass
class State:
    rho: np.ndarray
    pending: np.ndarray = field(default_factory=lambda: np.zeros(2))
    initiated: np.ndarray = field(default_factory=lambda: np.zeros(2))
    completed: np.ndarray = field(default_factory=lambda: np.zeros(2))
    step: int = 0


def advance(m, state, requested=(0.,0.)):
    """Update n: deliver old cohorts -> quote -> advance -> consume -> append."""
    rho=_density(state.rho,m)
    for stock in (state.pending,state.initiated,state.completed):
        if np.shape(stock)!=(2,) or np.any(~np.isfinite(stock)) or np.any(stock<0):
            raise ModelExit('Invalid completion ledger state')
    if not isinstance(state.step,(int,np.integer)) or state.step<0:
        raise ModelExit('Invalid update index')
    fraction=1. if m.completion_time==0 else -np.expm1(-m.du/m.completion_time)
    due=fraction*state.pending;Q=state.pending-due
    q=placement(m,Q);g=placement_weights(m,q);lit,latent=external_source(m,q)
    pre,terms=field_step(m,rho,lit+latent,due[:,None]*g)
    post,removed,actual,unfilled,pre_obs=execute(m,pre,requested)
    obs=observe(m,post)
    pending=Q+actual[::-1];initiated=state.initiated+actual[::-1];completed=state.completed+due
    before=m.dx*rho[:,1:-1].sum(axis=1);after=m.dx*post[:,1:-1].sum(axis=1)
    error=after-before-(terms['boundary_flux']-terms['cancelled']-terms['matched']+terms['external']+due-actual)
    ledger=initiated-completed-pending
    if np.max(np.abs(error))>1e-10 or np.max(np.abs(ledger))>1e-10:
        raise ModelExit('Volume or completion accounting failed')
    record={'step':state.step,'u_start':state.step*m.du,'u_end':(state.step+1)*m.du,
        **obs,'pre_p_b':pre_obs['p_b'],'pre_p_a':pre_obs['p_a'],'q_b':q[0],'q_a':q[1],
        'mu':q.mean(),'Sigma':q[1]-q[0],'Q_B_quote':Q[0],'Q_A_quote':Q[1],
        'Q_B_post':pending[0],'Q_A_post':pending[1],'I_quote':Q[1]-Q[0],'I_post':pending[1]-pending[0],
        'requested_sell':float(requested[0]),'requested_buy':float(requested[1]),
        'executed_sell':actual[0],'executed_buy':actual[1],'unfilled_sell':unfilled[0],'unfilled_buy':unfilled[1],
        'due_bid':due[0],'due_ask':due[1],'mass_bid':after[0],'mass_ask':after[1],
        'budget_error':float(np.max(np.abs(error))),'ledger_error':float(np.max(np.abs(ledger))),
        'positivity_load':terms['positivity_load'],'min_density':float(post.min()),
        'source_centroid_b':m.dx*np.sum(g[0]*m.x),'source_centroid_a':m.dx*np.sum(g[1]*m.x),
        'source_std_b':np.sqrt(m.dx*np.sum(g[0]*(m.x-m.dx*np.sum(g[0]*m.x))**2)),
        'source_std_a':np.sqrt(m.dx*np.sum(g[1]*(m.x-m.dx*np.sum(g[1]*m.x))**2)),
        'matched_volume':terms['matched']}
    for side,name in enumerate(['bid','ask']):
        for term in ['boundary_flux','cancelled','external']:
            record[term+'_'+name]=terms[term][side]
    detail={'incoming':rho.copy(),'pre_consumption':pre,'post_consumption':post,
        'removed':removed,'completion_increment':due[:,None]*g,
        'lit_increment':m.du*lit,'latent_increment':m.du*latent}
    return State(post,pending,initiated,completed,state.step+1),record,detail


def stationary(m, tolerance=1e-8, max_u=30.):
    """Explicit relaxation with empty pending stock and no executions."""
    if tolerance<=0 or not np.isfinite(tolerance) or max_u<=0 or not np.isfinite(max_u):
        raise ValueError('Invalid relaxation controls')
    rho=np.zeros((2,len(m.x)));rho[0,[0,-1]]=m.boundary_bid;rho[1,[0,-1]]=m.boundary_ask
    lit,latent=external_source(m,placement(m,np.zeros(2)))
    for n in range(int(max_u/m.du)):
        new,_=field_step(m,rho,lit+latent)
        residual=float(np.max(np.abs(new-rho))/m.du);rho=new
        if residual<tolerance:
            observe(m,rho)
            return rho,{'steps':n+1,'operational_duration':(n+1)*m.du,'max_rate_residual':residual,'tolerance':tolerance}
    raise ModelExit('Stationary relaxation did not reach the registered tolerance')
