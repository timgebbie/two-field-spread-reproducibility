from dataclasses import replace
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from functions.core import Model, ModelExit, State, placement, external_source, placement_weights, observe, field_step, execute, advance, stationary


def reference(x,q,side):
    # Independent infinite-line reaction-off step-source solution, used only
    # to test stationary numerical relaxation. D=nu=source amplitude=1.
    z=(x-q)*(1 if side==0 else -1)
    tail=.5*np.exp(-np.abs(z))
    return np.where(z<=0,1-tail,tail)


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=Model(dx=.2,du=.01)
        cls.ref,cls.relaxation=stationary(cls.m)

    def test_diffusion_cancellation_eigenmode(self):
        m=Model(x_min=0,x_max=10,dx=.2,du=.005,nu=.4,kappa=0)
        z=np.sin(np.pi*m.x/10);z[[0,-1]]=0
        rho=np.array([z,2*z]);initial=rho.copy()
        gain=1-m.nu*m.du-4*m.D*m.du/m.dx**2*np.sin(np.pi/(2*(len(z)-1)))**2
        for _ in range(25):rho,_=field_step(m,rho,np.zeros_like(rho))
        np.testing.assert_allclose(rho,initial*gain**25,atol=5e-15,rtol=5e-15)

    def test_reaction_uses_one_frozen_state(self):
        m=Model(x_min=0,x_max=4,dx=1,du=.1,D=0,nu=0,kappa=.5)
        rho=np.array([[0,2,2,2,0],[0,3,3,3,0]],dtype=float)
        new,terms=field_step(m,rho,np.zeros_like(rho))
        np.testing.assert_allclose(new[:,1:-1],np.array([[1.7]*3,[2.7]*3]),atol=1e-15)
        np.testing.assert_allclose(new[0]-new[1],rho[0]-rho[1],atol=1e-15)
        self.assertAlmostEqual(rho.sum()-new.sum(),2*terms['matched'])

    def test_full_volume_budget_with_reservoir_flux(self):
        m=self.m;rho=self.ref.copy();rho[:,1:-1]*=.7
        S=sum(external_source(m,placement(m,[.02,.01])))
        add=np.zeros_like(rho);add[0,20]=.04/m.dx;add[1,-21]=.03/m.dx
        new,t=field_step(m,rho,S,add)
        change=m.dx*(new[:,1:-1]-rho[:,1:-1]).sum(axis=1)
        expected=t['boundary_flux']-t['cancelled']-t['matched']+t['external']+t['completed']
        np.testing.assert_allclose(change,expected,atol=3e-15)
        self.assertGreater(abs(t['boundary_flux']).max(),0)

    def test_positivity_rejects_unsafe_step(self):
        m=replace(self.m,du=1.)
        with self.assertRaises(ModelExit):field_step(m,self.ref,np.zeros_like(self.ref))
        bad=self.ref.copy();bad[0,5]=-1e-12
        with self.assertRaises(ModelExit):field_step(self.m,bad,np.zeros_like(bad))

    def test_source_support_and_normalization(self):
        m=self.m;q=placement(m,[.3,.1]);g=placement_weights(m,q)
        lit,latent=external_source(m,q)
        np.testing.assert_allclose(m.dx*g.sum(axis=1),1,atol=2e-16)
        self.assertTrue(np.all(g[0,m.x>q[0]]==0))
        self.assertTrue(np.all(g[1,m.x<q[1]]==0))
        core=(m.x>q[0])&(m.x<q[1])
        self.assertTrue(np.all((lit+latent)[:,core]==0))
        self.assertAlmostEqual(q.mean(),m.mu0-m.chi_m*(.1-.3))
        self.assertAlmostEqual(q[1]-q[0],m.Sigma0+m.chi_s*.4)

    def test_reject_truncated_or_unresolved_completion(self):
        with self.assertRaises(ModelExit):placement_weights(self.m,[-11.7,11.7])
        with self.assertRaises(ModelExit):placement_weights(replace(self.m,placement_width=.001),[-6.05,6.05])

    def test_causal_opposite_side_completion(self):
        m=self.m;s=State(self.ref.copy());s,r,_=advance(m,s,[0,.02]);v=r['executed_buy']
        self.assertEqual(r['due_bid'],0);self.assertEqual(r['Q_B_quote'],0)
        self.assertAlmostEqual(s.pending[0],v);self.assertLess(r['I_post'],0)
        a=np.exp(-m.du/m.completion_time)
        for k in range(1,8):
            s,r,_=advance(m,s)
            self.assertAlmostEqual(r['due_bid'],v*(1-a)*a**(k-1),delta=2e-17)
            self.assertAlmostEqual(r['Q_B_quote'],v*a**k,delta=2e-17)
            np.testing.assert_allclose(s.completed+s.pending,s.initiated,atol=2e-17)

    def test_immediate_means_next_update(self):
        m=replace(self.m,completion_time=0.)
        s,r,_=advance(m,State(self.ref.copy()),[0,.02])
        self.assertGreater(s.pending[0],0);self.assertEqual(r['due_bid'],0)
        s,r,_=advance(m,s)
        self.assertAlmostEqual(r['due_bid'],.02)
        self.assertEqual(r['Q_B_quote'],0);self.assertEqual(r['Sigma'],m.Sigma0)

    def test_completion_time_preserved_on_refinement(self):
        stocks=[]
        for du in [.01,.005]:
            m=replace(self.m,du=du,chi_s=0,chi_m=0)
            s=State(self.ref.copy(),pending=np.array([.02,0.]),initiated=np.array([.02,0.]))
            for _ in range(round(.1/du)):s,_,_=advance(m,s)
            stocks.append(s.pending[0])
        np.testing.assert_allclose(stocks,.02*np.exp(-.1/self.m.completion_time),atol=2e-17)

    def test_buy_sell_reflection(self):
        buy=sell=State(self.ref.copy())
        for n in range(20):
            v=.02 if n in (0,7) else 0.
            buy,rb,_=advance(self.m,buy,[0,v]);sell,rs,_=advance(self.m,sell,[v,0])
            np.testing.assert_allclose(buy.rho,sell.rho[::-1,::-1],atol=2e-13)
            self.assertAlmostEqual(rb['p_a'],-rs['p_b'],delta=2e-12)
            self.assertAlmostEqual(rb['spread'],rs['spread'],delta=2e-12)

    def test_execution_cap_priority_and_no_reservoir_consumption(self):
        m=self.m;pre=self.ref.copy();post,removed,actual,unfilled,obs=execute(m,pre,[0,100.])
        self.assertTrue(np.all(post>=0));self.assertTrue(np.all(removed[:,[0,-1]]==0))
        self.assertGreater(unfilled[1],0);self.assertLess(actual[1],100)
        ids=np.flatnonzero(removed[1]>0)
        self.assertTrue(np.all(m.x[ids]>=obs['p_a']))
        self.assertTrue(np.all(m.x[ids]<=obs['p_a']+m.execution_depth))
        np.testing.assert_allclose(m.dx*(pre-post).sum(axis=1),actual,atol=1e-15)
        small,removed,actual,unfilled,_=execute(m,pre,[0,.001])
        self.assertEqual(np.count_nonzero(removed),1)
        self.assertAlmostEqual(actual[1],.001)

    def test_threshold_failures_are_explicit(self):
        with self.assertRaises(ModelExit):observe(self.m,np.zeros_like(self.ref))
        z=np.linspace(.2,0,len(self.m.x));touch=np.array([z,z[::-1]])
        with self.assertRaises(ModelExit):observe(self.m,touch)
        with self.assertRaises(ModelExit):observe(replace(self.m,slope_min=10),self.ref)

    def test_threshold_uses_paper_supremum_and_infimum(self):
        m=Model(x_min=-4,x_max=4,dx=1,du=.1)
        # Disjoint above-threshold islands on each side; inward crossings
        # are -0.5 and +0.5, not the outer crossings at -2.5 and +2.5.
        bid=np.array([1, .2, 0, .2, 0, 0, 0, 0, 0])
        obs=observe(m,np.array([bid,bid[::-1]]))
        self.assertEqual(obs['p_b'],-.5);self.assertEqual(obs['p_a'],.5)
        self.assertEqual(obs['crossings_b'],2);self.assertEqual(obs['crossings_a'],2)
        plateau=bid.copy();plateau[2:4]=.1
        with self.assertRaises(ModelExit):observe(m,np.array([plateau,bid[::-1]]))

    def test_stationary_reference_has_no_spurious_inventory(self):
        self.assertLess(self.relaxation['max_rate_residual'],1e-8)
        s=State(self.ref.copy())
        for _ in range(20):s,r,_=advance(self.m,s)
        self.assertLess(np.max(np.abs(s.rho-self.ref)),3e-9)
        np.testing.assert_array_equal(s.initiated,0);np.testing.assert_array_equal(s.pending,0)

    def test_stationary_solver_against_analytic_control(self):
        errors=[]
        for dx in [.2,.1]:
            m=replace(self.m,dx=dx,du=.2*dx*dx,kappa=0)
            exact=np.array([reference(m.x,-6,0),reference(m.x,6,1)])
            m=replace(m,boundary_bid=tuple(exact[0,[0,-1]]),boundary_ask=tuple(exact[1,[0,-1]]))
            rho,_=stationary(m)
            errors.append(float(np.max(np.abs(rho-exact))))
        self.assertLess(errors[1],.6*errors[0])
        self.assertLess(errors[1],.03) # nodal source step gives first-order edge error


if __name__=='__main__':unittest.main()
